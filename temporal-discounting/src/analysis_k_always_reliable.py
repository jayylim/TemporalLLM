"""Standalone analysis: treat fitted k as always reliable.

Does NOT modify existing pipeline code or overwrite existing summaries.
Reads `results/summary/by_condition.csv` and writes:

  results/analysis_k_always_reliable/
    summary_by_model.md          — one table per model; rows = personas (pooled; matches choice curves)
    successful_conditions.md     — competence-pass rows only; zero-success models listed
    figures/
      k_by_model_persona_off.png
      k_successful_conditions.png
      competence_heatmap.png
      discount_curves.png              — persona-off; legend = fitted curves only
      discount_curves__persona.png     — persona-on panels; legend = fitted curves only
      discount_curves_valid_model_persona.png
          — competence-pass model×persona overlays (model=linestyle, persona=colour)

Bound hits / poor R² do NOT mark k unreliable. Only a completely invalid fit
(missing / non-finite k) is labelled unreliable.

Usage:
  .venv/bin/python src/analysis_k_always_reliable.py
  .venv/bin/python src/analysis_k_always_reliable.py --input results/summary/by_condition.csv
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

OPTION_ORDER_SORT = {"pooled": 0, "sooner_A": 1, "sooner_B": 2}
OPTION_ORDERS = ["pooled", "sooner_A", "sooner_B"]
HUMAN_K = 0.01
DEFAULT_CONFIG_PATH = Path("config_q8.yaml")

# Match analyze.py persona-off / group colouring for the first two figure sets.
MODEL_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22",
]
DISCOUNTING_GROUP_COLORS = {
    "greater": "#d62728",
    "lesser": "#2ca02c",
}

# Per-persona colours for the valid model×persona overlay (stable across models).
PERSONA_COLORS = {
    "off": "#4C78A8",
    "substance_use": "#E45756",
    "sugary_food": "#F58518",
    "phone_social_media": "#EECA3B",
    "retail_spending": "#B279A2",
    "mindfulness": "#54A24B",
    "no_smoking_drinking": "#88D27A",
    "strategy_games": "#72B7B2",
    "exercise": "#1A7F37",
}

# Model identity via line dash + marker shape (overlay figure).
MODEL_LINESTYLES = [
    "-",
    "--",
    "-.",
    ":",
    (0, (5, 1)),
    (0, (3, 1, 1, 1)),
    (0, (5, 1, 1, 1, 1, 1)),
    (0, (8, 2, 1, 2)),
    (0, (2, 2)),
]
MODEL_MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "h"]


def k_is_completely_invalid(row: pd.Series) -> bool:
    """True only when there is no usable fitted k (missing / non-finite).

    Bound hits, nan/low R², and competence failure do NOT count as invalid here.
    """
    k = row.get("k")
    if k is None or pd.isna(k):
        return True
    try:
        return not np.isfinite(float(k))
    except (TypeError, ValueError):
        return True


def fitted_indifference_curve(k, later_amount_dollars, delay_range_months):
    return later_amount_dollars / (1.0 + float(k) * np.asarray(delay_range_months, dtype=float))


def load_waiting_game_params(config_path: Path) -> dict:
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    wg = config["waiting_game"]
    return {
        "later_amount_dollars": float(wg["later_amount_dollars"]),
        "delay_grid_months": list(wg["delay_grid_months"]),
        "human_k": float(config["human_benchmark"]["rachlin_1991_k_per_month"]),
    }


def indifference_lookup(indiff_df: pd.DataFrame, model_name: str, option_order: str,
                        persona_id=None) -> dict[float, float]:
    """{delay: indifference_amount} for one condition from precomputed table."""
    sub = indiff_df[
        (indiff_df["model_name"] == model_name) & (indiff_df["option_order"] == option_order)
    ]
    if persona_id is None or (isinstance(persona_id, float) and np.isnan(persona_id)):
        if "persona_id" in sub.columns:
            sub = sub[sub["persona_id"].isna() | (sub["persona_id"].astype(str).str.strip() == "")]
    else:
        sub = sub[sub["persona_id"] == persona_id]
    return {
        float(r["delay_months"]): float(r["indifference_amount"])
        for _, r in sub.iterrows()
    }


def persona_key_from_row(row: pd.Series) -> str:
    on_off, persona_id, _ = persona_condition_key(row)
    return "off" if on_off == "off" else persona_id


def persona_display_label(row: pd.Series) -> str:
    key = persona_key_from_row(row)
    if key == "off":
        return "persona-off"
    label = row.get("persona_label")
    if label is not None and not pd.isna(label) and str(label).strip():
        group = row.get("persona_discounting_group")
        group_s = f" ({group})" if group is not None and not pd.isna(group) else ""
        return f"{label}{group_s}"
    return key


def load_model_order(config_path: Path) -> list[str]:
    """Model order from config.yaml `models:` list (preserves config sequence)."""
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    models = config.get("models") or []
    return [str(m) for m in models]


def order_models(models, preferred_order: list[str] | None) -> list[str]:
    """Sort model names by config order; any extras follow alphabetically."""
    unique = list(dict.fromkeys(models))
    if not preferred_order:
        return sorted(unique)
    rank = {name: i for i, name in enumerate(preferred_order)}
    return sorted(unique, key=lambda m: (rank.get(m, len(preferred_order)), m))


def checkmark(is_true: bool) -> str:
    return "✅" if bool(is_true) else "❌"


def format_k_with_ci(row: pd.Series) -> str:
    if pd.isna(row.get("k")):
        return "-"
    ci_low = row.get("k_ci_low")
    ci_high = row.get("k_ci_high")
    if pd.isna(ci_low) or pd.isna(ci_high):
        return f"{row['k']:.4f}"
    return f"{row['k']:.4f} [{ci_low:.4f}, {ci_high:.4f}]"


def format_r2(row: pd.Series) -> str:
    r2 = row.get("r_squared")
    if r2 is None or pd.isna(r2):
        return "-"
    return f"{float(r2):.3f}"


def persona_condition_key(row: pd.Series) -> tuple:
    """Group key: persona off vs a specific persona_id."""
    persona = str(row.get("persona", "off")).lower()
    if persona in ("off", "false", "0", ""):
        return ("off", "-", "-")
    persona_id = row.get("persona_id")
    if pd.isna(persona_id) or persona_id is None or str(persona_id).strip() == "":
        persona_id = "-"
    group = row.get("persona_discounting_group")
    if pd.isna(group) or group is None or str(group).strip() == "":
        group = "-"
    return ("on", str(persona_id), str(group))


def load_condition_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "model_name",
        "option_order",
        "competence_passed",
        "k",
        "monotonicity_passed",
        "money_preference_passed",
        "indifference_nonincreasing_passed",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

    if "persona" not in df.columns:
        df["persona"] = "off"
    for col in ("persona_id", "persona_label", "persona_discounting_group"):
        if col not in df.columns:
            df[col] = np.nan

    # Analysis rule: k is always treated as reliable; validity = competence only.
    df = df.copy()
    df["k_always_reliable"] = True
    df["valid_under_always_reliable_k"] = df["competence_passed"].astype(bool)

    df["_order_sort"] = df["option_order"].map(lambda o: OPTION_ORDER_SORT.get(o, 99))
    df["_persona_sort"] = df.apply(
        lambda r: (0 if persona_condition_key(r)[0] == "off" else 1,
                   persona_condition_key(r)[2],
                   persona_condition_key(r)[1]),
        axis=1,
    )
    return df


# Persona row order aligned with choice-curve figure set (control, then greater, then lesser).
PERSONA_ID_ORDER = [
    "substance_use",
    "sugary_food",
    "phone_social_media",
    "retail_spending",
    "mindfulness",
    "no_smoking_drinking",
    "strategy_games",
    "exercise",
]


def _persona_row_sort_key(row: pd.Series) -> tuple:
    """Sort: persona-off first, then PERSONA_ID_ORDER, then any extras alphabetically."""
    on_off, persona_id, group = persona_condition_key(row)
    if on_off == "off":
        return (0, -1, "", "")
    try:
        idx = PERSONA_ID_ORDER.index(persona_id)
    except ValueError:
        idx = len(PERSONA_ID_ORDER)
    return (1, idx, group, persona_id)


def build_summary_by_model_markdown(
    df: pd.DataFrame, model_order: list[str] | None = None
) -> str:
    """One table per model; one row per choice-curve condition (persona-off + each persona).

    Uses option_order == pooled, matching `plot_choice_curves.py` (one figure per
    persona condition, all A/B trials pooled).
    """
    pooled = df[df["option_order"] == "pooled"].copy()
    models = order_models(pooled["model_name"].unique(), model_order)

    parts = [
        "# Waiting Game: Per-Model Persona Summary",
        "",
        "One table per model. Rows match the model's **choice-curve** conditions: "
        "persona-off control, then each persona id. Stats use `option_order = pooled` "
        "(same pooling as `choice_curves.png` / `choice_curves__persona__{id}.png`).",
        "",
        f"Human benchmark (Rachlin et al. 1991): k = {HUMAN_K} per month.",
        "",
        "**Analysis rule:** fitted k is treated as **always reliable** "
        "(including always-sooner / always-later / missing R² / bound-adjacent fits). "
        "`Valid Discount Rate` = Competence Pass only. Fitted k [95% CI] is always shown.",
        "",
    ]

    for model in models:
        model_df = pooled[pooled["model_name"] == model].copy()
        model_df["_row_sort"] = model_df.apply(_persona_row_sort_key, axis=1)
        model_df = model_df.sort_values("_row_sort", kind="mergesort")

        # One row per persona condition (dedupe if needed).
        seen = set()
        rows = []
        for _, row in model_df.iterrows():
            key = persona_condition_key(row)
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

        parts.append(f"## {model}")
        parts.append("")
        parts.append(
            "| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | "
            "Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | "
            "**Valid Discount Rate** | Fitted k [95% CI] |"
        )
        parts.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for row in rows:
            on_off, persona_id, group = persona_condition_key(row)
            persona_label = "off" if on_off == "off" else "on"
            pid_label = "-" if on_off == "off" else persona_id
            group_label = "-" if on_off == "off" else group
            if on_off == "off":
                curve_fig = "`choice_curves.png`"
            else:
                curve_fig = f"`choice_curves__persona__{persona_id}.png`"
            competent = bool(row["competence_passed"])
            parts.append(
                f"| {persona_label} | {pid_label} | {group_label} | {curve_fig} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | "
                f"{checkmark(row['indifference_nonincreasing_passed'])} | "
                f"{checkmark(competent)} | "
                f"{format_r2(row)} | ✅ | "
                f"**{checkmark(competent)}** | {format_k_with_ci(row)} |"
            )
        parts.append("")

    parts.extend(
        [
            "## Column definitions",
            "",
            "- **Persona / Persona ID / Group**: control (`off`) or a lifestyle persona "
            "(greater/lesser discounting group). Same stratification as choice-curve figures.",
            "- **Choice-curve figure**: corresponding file under `results/figures/{model}/`.",
            "- **Competence Pass**: monotonicity ∧ money preference ∧ indifference non-increasing "
            "(evaluated on pooled trials for that persona).",
            "- **k Reliable?**: always ✅ under this analysis (fitted k still reported as-is).",
            "- **Valid Discount Rate**: Competence Pass (k reliability not used as a gate).",
            "- **Fitted k [95% CI]**: hyperbolic discount rate per month on pooled trials "
            "(shown even for always-sooner / always-later patterns).",
            "",
        ]
    )
    return "\n".join(parts)


def select_rows_for_successful_conditions_report(
    df: pd.DataFrame, model_order: list[str] | None = None
) -> tuple[pd.DataFrame, list[str]]:
    """Keep only competence-passing rows.

    - Main tables: every row with competence_passed == True (no pooled fallbacks).
    - Models with zero competence-passing rows are returned separately.
    """
    models = order_models(df["model_name"].unique(), model_order)
    success_by_model = {
        m: bool(df.loc[df["model_name"] == m, "competence_passed"].astype(bool).any())
        for m in models
    }
    zero_success_models = [m for m in models if not success_by_model[m]]
    success_models = [m for m in models if success_by_model[m]]

    out = df[df["competence_passed"].astype(bool)].copy()
    if out.empty:
        return out, zero_success_models

    model_rank = {m: i for i, m in enumerate(success_models)}
    out["_model_sort"] = out["model_name"].map(lambda m: model_rank.get(m, 999))
    out = out.sort_values(
        ["_model_sort", "_persona_sort", "_order_sort"],
        kind="mergesort",
    )
    return out, zero_success_models


def build_successful_conditions_markdown(
    selected_df: pd.DataFrame,
    zero_success_models: list[str],
    all_models: list[str],
    model_order: list[str] | None = None,
) -> str:
    parts = [
        "# Waiting Game: Successful Conditions (k always reliable)",
        "",
        "Only rows with **Competence Pass = True**. "
        "Under this analysis, fitted k is always treated as reliable, so "
        "**Valid Discount Rate = Competence Pass**.",
        "",
        "Failed persona / option-order cells are omitted (no pooled fallbacks). "
        "Models with **zero** successful rows are listed at the bottom.",
        "",
        f"Human benchmark (Rachlin et al. 1991): k = {HUMAN_K} per month.",
        "",
    ]

    success_models = order_models(
        selected_df["model_name"].unique() if not selected_df.empty else [],
        model_order,
    )
    if selected_df.empty:
        parts.append("_No competence-passing conditions._")
        parts.append("")
    else:
        for model in success_models:
            model_df = selected_df[selected_df["model_name"] == model]
            n_valid = len(model_df)
            parts.append(f"## {model}")
            parts.append("")
            parts.append(f"Successful rows: **{n_valid}**.")
            parts.append("")
            parts.append(
                "| Persona ID | Order | Monotonicity | Money Pref. | "
                "Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |"
            )
            parts.append("|---|---|---|---|---|---|---|---|")
            for _, row in model_df.iterrows():
                persona_on = str(row.get("persona", "off")).lower() in ("on", "true", "1")
                pid = row.get("persona_id")
                if not persona_on:
                    pid_label = "off"
                elif pd.isna(pid) or pid is None or str(pid).strip() == "":
                    pid_label = "-"
                else:
                    pid_label = str(pid)
                competent = bool(row["competence_passed"])
                parts.append(
                    f"| {pid_label} | {row['option_order']} | "
                    f"{checkmark(row['monotonicity_passed'])} | "
                    f"{checkmark(row['money_preference_passed'])} | "
                    f"{checkmark(row['indifference_nonincreasing_passed'])} | "
                    f"{format_r2(row)} | **{checkmark(competent)}** | {format_k_with_ci(row)} |"
                )
            parts.append("")

    zero_success_models = order_models(zero_success_models, model_order)
    all_models = order_models(all_models, model_order)

    parts.append("## Models with 0 successful conditions")
    parts.append("")
    if not zero_success_models:
        parts.append("None — every model had at least one competence-passing condition.")
    else:
        parts.append(
            "These models had **no** competence-passing cells "
            "(any persona × option-order). They are omitted from the tables above."
        )
        parts.append("")
        for model in zero_success_models:
            parts.append(f"- `{model}`")
    parts.append("")

    omitted = [m for m in all_models if m in set(zero_success_models)]
    included = [m for m in all_models if m not in set(zero_success_models)]
    parts.append("## Coverage")
    parts.append("")
    parts.append(f"- Models with ≥1 success: **{len(included)}** — {', '.join(f'`{m}`' for m in included) or 'none'}")
    parts.append(f"- Models with 0 successes: **{len(omitted)}** — {', '.join(f'`{m}`' for m in omitted) or 'none'}")
    parts.append("")
    return "\n".join(parts)


def plot_k_by_model_persona_off(
    df: pd.DataFrame, out_path: Path, model_order: list[str] | None = None
) -> None:
    persona_off = df[df["persona"].astype(str).str.lower().isin(["off", "false", "0"])].copy()
    models = order_models(persona_off["model_name"].unique(), model_order)
    orders = OPTION_ORDERS
    x = np.arange(len(models))
    width = 0.25
    colors = {"pooled": "#4C78A8", "sooner_A": "#F58518", "sooner_B": "#54A24B"}

    fig, ax = plt.subplots(figsize=(12, 5.5))
    for i, order in enumerate(orders):
        vals = []
        competent = []
        for model in models:
            sub = persona_off[
                (persona_off["model_name"] == model) & (persona_off["option_order"] == order)
            ]
            if len(sub) == 0 or pd.isna(sub.iloc[0]["k"]):
                vals.append(np.nan)
                competent.append(False)
            else:
                vals.append(float(sub.iloc[0]["k"]))
                competent.append(bool(sub.iloc[0]["competence_passed"]))
        offsets = x + (i - 1) * width
        bars = ax.bar(
            offsets,
            vals,
            width,
            label=order,
            color=colors[order],
            alpha=0.85,
            edgecolor="black",
            linewidth=0.4,
        )
        for bar, ok in zip(bars, competent):
            if ok:
                bar.set_hatch("///")
                bar.set_alpha(1.0)

    ax.axhline(HUMAN_K, color="gray", linestyle="--", linewidth=1, label=f"human k={HUMAN_K}")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Fitted k (per month, log scale)")
    ax.set_title("Persona-off fitted k by option order\n(hatched = competence pass / valid under always-reliable k)")
    ax.legend(frameon=False, ncols=4)
    ax.set_ylim(1e-4, 20)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_k_successful_conditions(
    df: pd.DataFrame, out_path: Path, model_order: list[str] | None = None
) -> None:
    success = df[df["competence_passed"].astype(bool)].copy()
    if success.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "No competence-passing conditions", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, dpi=160)
        plt.close(fig)
        return

    model_rank = {m: i for i, m in enumerate(order_models(success["model_name"].unique(), model_order))}
    success["_model_sort"] = success["model_name"].map(lambda m: model_rank.get(m, 999))
    success["_label"] = success.apply(
        lambda r: (
            f"{r['model_name']}\n"
            f"{'off' if str(r['persona']).lower() in ('off','false','0') else r.get('persona_id', 'on')}"
            f" / {r['option_order']}"
        ),
        axis=1,
    )
    success = success.sort_values(["_model_sort", "_persona_sort", "_order_sort"])

    fig, ax = plt.subplots(figsize=(max(10, 0.35 * len(success)), 5.5))
    colors = success["persona"].astype(str).str.lower().map(
        lambda p: "#4C78A8" if p in ("off", "false", "0") else "#E45756"
    )
    x = np.arange(len(success))
    ax.bar(x, success["k"].astype(float), color=colors, edgecolor="black", linewidth=0.3)
    ax.errorbar(
        x,
        success["k"].astype(float),
        yerr=[
            success["k"].astype(float) - success["k_ci_low"].astype(float),
            success["k_ci_high"].astype(float) - success["k"].astype(float),
        ],
        fmt="none",
        ecolor="black",
        elinewidth=0.8,
        capsize=2,
    )
    ax.axhline(HUMAN_K, color="gray", linestyle="--", linewidth=1, label=f"human k={HUMAN_K}")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(success["_label"], rotation=90, fontsize=7)
    ax.set_ylabel("Fitted k (per month, log scale)")
    ax.set_title("Fitted k for competence-passing conditions only\n(blue = persona-off, red = persona-on)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_competence_heatmap(
    df: pd.DataFrame, out_path: Path, model_order: list[str] | None = None
) -> None:
    """Heatmap: models × (persona_id or off) for pooled competence pass."""
    pooled = df[df["option_order"] == "pooled"].copy()
    pooled["_col"] = pooled.apply(
        lambda r: "persona_off"
        if str(r["persona"]).lower() in ("off", "false", "0")
        else str(r.get("persona_id") or "persona_on"),
        axis=1,
    )
    models = order_models(pooled["model_name"].unique(), model_order)
    # Stable column order: off first, then greater personas, then lesser.
    greater = ["substance_use", "sugary_food", "phone_social_media", "retail_spending"]
    lesser = ["mindfulness", "no_smoking_drinking", "strategy_games", "exercise"]
    cols = ["persona_off"] + greater + lesser
    cols = [c for c in cols if c in set(pooled["_col"])] + [
        c for c in sorted(set(pooled["_col"])) if c not in (["persona_off"] + greater + lesser)
    ]

    mat = np.full((len(models), len(cols)), np.nan)
    for i, model in enumerate(models):
        for j, col in enumerate(cols):
            sub = pooled[(pooled["model_name"] == model) & (pooled["_col"] == col)]
            if len(sub):
                mat[i, j] = 1.0 if bool(sub.iloc[0]["competence_passed"]) else 0.0

    fig, ax = plt.subplots(figsize=(12, max(4, 0.45 * len(models) + 1)))
    cmap = matplotlib.colors.ListedColormap(["#F4C2C2", "#A8D5A2"])
    im = ax.imshow(mat, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(cols)))
    ax.set_xticklabels(cols, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(models)))
    ax.set_yticklabels(models, fontsize=8)
    for i in range(len(models)):
        for j in range(len(cols)):
            if not np.isnan(mat[i, j]):
                ax.text(
                    j, i, "pass" if mat[i, j] == 1 else "fail",
                    ha="center", va="center", fontsize=8,
                    color="#1b5e20" if mat[i, j] == 1 else "#7f1d1d",
                )
    ax.set_title("Pooled competence pass by model × persona\n(valid under always-reliable-k analysis)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_discount_curves_persona_off(
    condition_df: pd.DataFrame,
    indiff_df: pd.DataFrame,
    params: dict,
    out_path: Path,
    model_order: list[str] | None = None,
) -> None:
    """Same layout as results/figures/discount_curves.png (persona-off).

    Legend lists fitted curves only. Bound / R² issues are not labelled unreliable;
    only completely invalid (non-finite) k would be.
    """
    later = params["later_amount_dollars"]
    delay_grid = params["delay_grid_months"]
    human_k = params["human_k"]
    delay_range = np.linspace(min(delay_grid), max(delay_grid), 200)

    persona_off = condition_df[
        condition_df["persona"].astype(str).str.lower().isin(["off", "false", "0", ""])
    ].copy()
    models = order_models(persona_off["model_name"].unique(), model_order)
    order_levels = [o for o in OPTION_ORDERS if o in set(persona_off["option_order"])]
    if not order_levels:
        order_levels = sorted(persona_off["option_order"].unique())

    n_orders = len(order_levels)
    figure, axes = plt.subplots(1, n_orders, figsize=(5.5 * n_orders, 5.5), squeeze=False)

    for order_index, option_order in enumerate(order_levels):
        axis = axes[0][order_index]
        order_comp = persona_off[persona_off["option_order"] == option_order]
        fit_handles: list[Line2D] = []

        for model_index, model_name in enumerate(models):
            sub = order_comp[order_comp["model_name"] == model_name]
            if sub.empty:
                continue
            row = sub.iloc[0]
            model_color = MODEL_COLORS[model_index % len(MODEL_COLORS)]

            empirical = indifference_lookup(indiff_df, model_name, option_order, persona_id=None)
            if empirical:
                axis.plot(
                    list(empirical.keys()), list(empirical.values()),
                    color=model_color, marker="o", linestyle="none", zorder=3,
                )

            if not k_is_completely_invalid(row):
                fitted = fitted_indifference_curve(row["k"], later, delay_range)
                axis.plot(
                    delay_range, fitted,
                    color=model_color, linestyle="-",
                )
                fit_handles.append(
                    Line2D(
                        [0], [0], color=model_color, linestyle="-",
                        label=f"{model_name} fit, k={float(row['k']):.4f}",
                    )
                )

        human_curve = fitted_indifference_curve(human_k, later, delay_range)
        axis.plot(
            delay_range, human_curve,
            color="black", linestyle="--",
        )
        fit_handles.append(
            Line2D(
                [0], [0], color="black", linestyle="--",
                label=f"Human (Rachlin 1991), k={human_k}",
            )
        )
        axis.set_xlabel("Delay to later reward (months)")
        axis.set_ylabel(f"Indifference amount now (of ${int(later)} later)")
        axis.set_title(f"option_order={option_order}")
        axis.legend(handles=fit_handles, fontsize=6, loc="upper right")
        axis.set_ylim(bottom=0)

    figure.suptitle(
        "Waiting Game: raw 50% equivalents + hyperbolic fits "
        "[direct, persona-off; k always-reliable (bound hits OK)]",
        fontsize=12, y=1.02,
    )
    figure.tight_layout()
    figure.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_discount_curves_by_persona(
    condition_df: pd.DataFrame,
    indiff_df: pd.DataFrame,
    params: dict,
    out_path: Path,
    model_order: list[str] | None = None,
) -> None:
    """Same layout as results/figures/discount_curves__persona.png.

    Legend = fitted curves only. Greater/lesser colouring preserved.
    """
    later = params["later_amount_dollars"]
    delay_grid = params["delay_grid_months"]
    human_k = params["human_k"]
    delay_range = np.linspace(min(delay_grid), max(delay_grid), 200)

    pooled = condition_df[
        (condition_df["option_order"] == "pooled")
        & (~condition_df["persona"].astype(str).str.lower().isin(["off", "false", "0", ""]))
    ].copy()
    models = order_models(pooled["model_name"].unique(), model_order)
    if not models:
        return

    n_models = len(models)
    n_cols = min(3, n_models)
    n_rows = int(np.ceil(n_models / n_cols))
    figure, axes = plt.subplots(
        n_rows, n_cols, figsize=(5.5 * n_cols, 4.5 * n_rows), squeeze=False
    )

    for model_index, model_name in enumerate(models):
        axis = axes[model_index // n_cols][model_index % n_cols]
        model_comp = pooled[pooled["model_name"] == model_name].copy()
        model_comp["_row_sort"] = model_comp.apply(_persona_row_sort_key, axis=1)
        model_comp = model_comp.sort_values("_row_sort", kind="mergesort")
        fit_handles: list[Line2D] = []

        for persona_index, (_, row) in enumerate(model_comp.iterrows()):
            persona_id = row.get("persona_id")
            group = row.get("persona_discounting_group")
            label = row.get("persona_label") or persona_id
            color = DISCOUNTING_GROUP_COLORS.get(
                group, MODEL_COLORS[persona_index % len(MODEL_COLORS)]
            )
            empirical = indifference_lookup(
                indiff_df, model_name, "pooled", persona_id=persona_id
            )
            if empirical:
                axis.plot(
                    list(empirical.keys()), list(empirical.values()),
                    color=color, marker="o", linestyle="none", alpha=0.8, zorder=3,
                )
            if not k_is_completely_invalid(row):
                fitted = fitted_indifference_curve(row["k"], later, delay_range)
                group_s = f" ({group})" if group is not None and not pd.isna(group) else ""
                axis.plot(
                    delay_range, fitted,
                    color=color, linestyle="-",
                )
                fit_handles.append(
                    Line2D(
                        [0], [0], color=color, linestyle="-",
                        label=f"{label}{group_s}, k={float(row['k']):.4f}",
                    )
                )

        human_curve = fitted_indifference_curve(human_k, later, delay_range)
        axis.plot(
            delay_range, human_curve,
            color="black", linestyle="--",
        )
        fit_handles.append(
            Line2D(
                [0], [0], color="black", linestyle="--",
                label=f"Human k={human_k}",
            )
        )
        axis.set_title(model_name, fontsize=9)
        axis.set_xlabel("Delay (months)")
        axis.set_ylabel(f"Indiff. now (of ${int(later)})")
        axis.legend(handles=fit_handles, fontsize=5, loc="upper right")
        axis.set_ylim(bottom=0)

    for empty_index in range(n_models, n_rows * n_cols):
        axes[empty_index // n_cols][empty_index % n_cols].axis("off")

    figure.suptitle(
        "Waiting Game persona curves [direct, pooled order; "
        "k always-reliable (bound hits OK)]",
        fontsize=12, y=1.01,
    )
    figure.tight_layout()
    figure.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_discount_curves_valid_model_persona(
    condition_df: pd.DataFrame,
    indiff_df: pd.DataFrame,
    params: dict,
    out_path: Path,
    model_order: list[str] | None = None,
) -> None:
    """One panel per option_order: competence-pass model×persona fitted curves.

    Models distinguished by linestyle (+ marker shape on empirical points);
    personas by colour (consistent across models). Legend = style keys only
    (models / personas / human), not individual data-point series.
    """
    later = params["later_amount_dollars"]
    delay_grid = params["delay_grid_months"]
    human_k = params["human_k"]
    delay_range = np.linspace(min(delay_grid), max(delay_grid), 200)

    valid = condition_df[condition_df["competence_passed"].astype(bool)].copy()
    valid = valid[~valid.apply(k_is_completely_invalid, axis=1)]
    if valid.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "No competence-passing conditions with valid k",
                ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    models = order_models(valid["model_name"].unique(), model_order)
    model_style = {
        m: {
            "linestyle": MODEL_LINESTYLES[i % len(MODEL_LINESTYLES)],
            "marker": MODEL_MARKERS[i % len(MODEL_MARKERS)],
        }
        for i, m in enumerate(models)
    }

    # Persona colour order: off, then PERSONA_ID_ORDER, then leftovers.
    persona_keys_present = sorted(
        {persona_key_from_row(r) for _, r in valid.iterrows()},
        key=lambda p: (
            0 if p == "off" else 1,
            PERSONA_ID_ORDER.index(p) if p in PERSONA_ID_ORDER else len(PERSONA_ID_ORDER),
            p,
        ),
    )
    persona_color = {
        p: PERSONA_COLORS.get(p, MODEL_COLORS[i % len(MODEL_COLORS)])
        for i, p in enumerate(persona_keys_present)
    }
    persona_label_map = {}
    for _, row in valid.iterrows():
        key = persona_key_from_row(row)
        if key not in persona_label_map:
            persona_label_map[key] = persona_display_label(row)

    order_levels = [o for o in OPTION_ORDERS if o in set(valid["option_order"])]
    n_orders = len(order_levels)
    figure, axes = plt.subplots(1, n_orders, figsize=(6.2 * n_orders, 5.8), squeeze=False)

    for order_index, option_order in enumerate(order_levels):
        axis = axes[0][order_index]
        order_df = valid[valid["option_order"] == option_order].copy()
        order_df["_model_sort"] = order_df["model_name"].map(
            lambda m: models.index(m) if m in models else 999
        )
        order_df["_persona_sort"] = order_df.apply(_persona_row_sort_key, axis=1)
        order_df = order_df.sort_values(["_model_sort", "_persona_sort"], kind="mergesort")

        for _, row in order_df.iterrows():
            model_name = row["model_name"]
            pkey = persona_key_from_row(row)
            color = persona_color[pkey]
            ls = model_style[model_name]["linestyle"]
            marker = model_style[model_name]["marker"]
            pid = None if pkey == "off" else row.get("persona_id")

            empirical = indifference_lookup(indiff_df, model_name, option_order, persona_id=pid)
            if empirical:
                axis.plot(
                    list(empirical.keys()), list(empirical.values()),
                    color=color, marker=marker, linestyle="none",
                    markersize=5, alpha=0.75, zorder=3,
                )
            fitted = fitted_indifference_curve(row["k"], later, delay_range)
            axis.plot(
                delay_range, fitted,
                color=color, linestyle=ls, linewidth=1.6, zorder=2,
            )

        human_curve = fitted_indifference_curve(human_k, later, delay_range)
        axis.plot(
            delay_range, human_curve,
            color="black", linestyle="--", linewidth=1.8, zorder=4,
        )
        axis.set_xlabel("Delay to later reward (months)")
        axis.set_ylabel(f"Indifference amount now (of ${int(later)} later)")
        axis.set_title(f"option_order={option_order}")
        axis.set_ylim(bottom=0)

        # Dual legend: models (linestyle) + personas (colour); fitted-curve keys only.
        model_handles = [
            Line2D([0], [0], color="#333333", linestyle=model_style[m]["linestyle"],
                   linewidth=1.6, label=m)
            for m in models
            if m in set(order_df["model_name"])
        ]
        persona_handles = [
            Line2D([0], [0], color=persona_color[p], linestyle="-", linewidth=2.2,
                   label=persona_label_map.get(p, p))
            for p in persona_keys_present
            if p in {persona_key_from_row(r) for _, r in order_df.iterrows()}
        ]
        human_handle = Line2D(
            [0], [0], color="black", linestyle="--", linewidth=1.8,
            label=f"Human (Rachlin 1991), k={human_k}",
        )
        handles = model_handles + persona_handles + [human_handle]
        axis.legend(handles=handles, fontsize=5.5, loc="upper right", frameon=True)

    figure.suptitle(
        "Valid discount curves (competence pass): model = line style, "
        "persona = colour",
        fontsize=12, y=1.02,
    )
    figure.tight_layout()
    figure.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/summary/by_condition.csv"),
        help="Path to by_condition.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/analysis_k_always_reliable"),
        help="Directory for new markdowns and figures",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Config used for model ordering (models: list)",
    )
    args = parser.parse_args()

    repo_src = Path(__file__).resolve().parent
    project_root = repo_src.parent
    input_path = args.input if args.input.is_absolute() else project_root / args.input
    output_dir = args.output_dir if args.output_dir.is_absolute() else project_root / args.output_dir
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    figures_dir = output_dir / "figures"
    os.makedirs(figures_dir, exist_ok=True)

    model_order = load_model_order(config_path)
    df = load_condition_df(input_path)

    by_model_md = build_summary_by_model_markdown(df, model_order)
    by_model_path = output_dir / "summary_by_model.md"
    by_model_path.write_text(by_model_md, encoding="utf-8")

    selected, zero_success = select_rows_for_successful_conditions_report(df, model_order)
    all_models = order_models(df["model_name"].unique(), model_order)
    success_md = build_successful_conditions_markdown(
        selected, zero_success, all_models, model_order
    )
    success_path = output_dir / "successful_conditions.md"
    success_path.write_text(success_md, encoding="utf-8")

    # Also write the selected rows as CSV for downstream use.
    selected_csv = output_dir / "successful_conditions_rows.csv"
    export_cols = [
        c for c in [
            "model_name", "persona", "persona_id", "persona_label",
            "persona_discounting_group", "option_order",
            "monotonicity_passed", "money_preference_passed",
            "indifference_nonincreasing_passed", "competence_passed",
            "k_always_reliable", "valid_under_always_reliable_k",
            "k", "k_ci_low", "k_ci_high", "r_squared", "n_indifference_points",
        ] if c in selected.columns or c in ("k_always_reliable", "valid_under_always_reliable_k")
    ]
    if not selected.empty:
        selected.to_csv(selected_csv, index=False, columns=[c for c in export_cols if c in selected.columns])
    else:
        pd.DataFrame(columns=export_cols).to_csv(selected_csv, index=False)

    plot_k_by_model_persona_off(df, figures_dir / "k_by_model_persona_off.png", model_order)
    plot_k_successful_conditions(df, figures_dir / "k_successful_conditions.png", model_order)
    plot_competence_heatmap(df, figures_dir / "competence_heatmap.png", model_order)

    # Discount-curve figures (always-reliable k legends; curve-only legends).
    tables_dir = project_root / "results" / "tables"
    indiff_off_path = tables_dir / "indifference_amounts.csv"
    indiff_persona_path = tables_dir / "indifference_amounts__persona.csv"
    params = load_waiting_game_params(config_path)

    indiff_off = pd.read_csv(indiff_off_path) if indiff_off_path.exists() else pd.DataFrame()
    indiff_persona = (
        pd.read_csv(indiff_persona_path) if indiff_persona_path.exists() else pd.DataFrame()
    )
    indiff_all = (
        pd.concat([indiff_off, indiff_persona], ignore_index=True)
        if (not indiff_off.empty or not indiff_persona.empty)
        else pd.DataFrame()
    )

    if not indiff_off.empty:
        plot_discount_curves_persona_off(
            df, indiff_off, params,
            figures_dir / "discount_curves.png", model_order,
        )
    if not indiff_persona.empty:
        plot_discount_curves_by_persona(
            df, indiff_persona, params,
            figures_dir / "discount_curves__persona.png", model_order,
        )
    if not indiff_all.empty:
        plot_discount_curves_valid_model_persona(
            df, indiff_all, params,
            figures_dir / "discount_curves_valid_model_persona.png", model_order,
        )

    print(f"Wrote {by_model_path}")
    print(f"Wrote {success_path}")
    print(f"Wrote {selected_csv}")
    print(f"Wrote figures in {figures_dir}")
    print(f"Model order (from {config_path.name}): {model_order}")
    print(
        f"Models with ≥1 success: "
        f"{order_models(set(selected['model_name']) if not selected.empty else [], model_order)}"
    )
    print(f"Models with 0 successes: {zero_success}")


if __name__ == "__main__":
    main()
