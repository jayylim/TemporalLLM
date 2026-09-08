"""Cross-mode comparison: aggregates comparison_summary{mode}.csv across
every reasoning mode that has been run (direct / cot), to test whether
prompting interventions change competence-check pass rates or hyperbolic-fit
reliability for each model.

Also writes a clean factor-summary folder (`results/summary/`) with:
  - by_condition.csv  — one row per model × trial_type × persona
  - by_factor.csv     — rollups of pass rates / mean k by each factor
  - README.md         — column definitions

Usage: python src/compare_modes.py [--config path/to/config.yaml]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import load_config, resolve_dir_path, result_suffix
from run_experiment import REASONING_MODES

MODE_DISPLAY_LABELS = {
    "direct": "direct",
    "cot": "chain-of-thought",
}
MODE_COLORS = {
    "direct": "#1f77b4",
    "cot": "#ff7f0e",
}
MODE_SORT_ORDER = {mode: index for index, mode in enumerate(REASONING_MODES)}
PERSONA_CONDITIONS = [False, True]

# Clean column order for the factor-summary condition table.
CONDITION_SUMMARY_COLUMNS = [
    "model_name",
    "model_family",
    "trial_type",
    "persona",
    "persona_id",
    "persona_label",
    "persona_discounting_group",
    "option_order",
    "monotonicity_passed",
    "money_preference_passed",
    "indifference_nonincreasing_passed",
    "competence_passed",
    "k_reliable",
    "valid_discount_rate",
    "k",
    "k_ci_low",
    "k_ci_high",
    "r_squared",
    "n_indifference_points",
    "k_at_boundary",
    "k_lower_bound",
    "k_upper_bound",
    "n_trials_fit",
]

OPTION_ORDER_SORT = {"pooled": 0, "sooner_A": 1, "sooner_B": 2}


def checkmark(is_true):
    return "\u2705" if bool(is_true) else "\u274c"


def format_k_with_ci(row):
    if pd.isna(row["k"]):
        return "-"
    return f"{row['k']:.4f} [{row['k_ci_low']:.4f}, {row['k_ci_high']:.4f}]"


def model_family_from_name(model_name):
    """Coarse family label for factor rollups (qwen2.5 / qwen3 / llama3.1 / mistral)."""
    name = str(model_name).lower()
    if name.startswith("qwen2.5"):
        return "qwen2.5"
    if name.startswith("qwen3"):
        return "qwen3"
    if name.startswith("llama3.1") or name.startswith("llama3"):
        return "llama3.1"
    if name.startswith("mistral"):
        return "mistral"
    return name.split(":")[0]


def build_condition_summary(combined_df):
    """One clean row per model × trial_type × persona × persona_id × option_order."""
    summary_df = combined_df.copy()
    summary_df["trial_type"] = summary_df["reasoning_mode"].map(
        lambda mode: MODE_DISPLAY_LABELS.get(mode, mode)
    )
    summary_df["persona"] = summary_df["persona_enabled"].map(
        lambda enabled: "on" if bool(enabled) else "off"
    )
    if "option_order" not in summary_df.columns:
        summary_df["option_order"] = "pooled"
    for col in ("persona_id", "persona_label", "persona_discounting_group"):
        if col not in summary_df.columns:
            summary_df[col] = None
    summary_df["model_family"] = summary_df["model_name"].map(model_family_from_name)
    summary_df["competence_passed"] = summary_df["overall_passed"]
    summary_df["k_reliable"] = summary_df["k_is_reliable"]

    for optional_col in [
        "k_lower_bound", "k_upper_bound", "k_at_boundary", "n_trials_fit",
        "r_squared", "n_indifference_points", "indifference_nonincreasing_passed",
    ]:
        if optional_col not in summary_df.columns:
            summary_df[optional_col] = np.nan

    summary_df["_mode_order"] = summary_df["reasoning_mode"].map(MODE_SORT_ORDER)
    summary_df["_order_order"] = summary_df["option_order"].map(
        lambda o: OPTION_ORDER_SORT.get(o, 99)
    )
    summary_df["_group_order"] = summary_df["persona_discounting_group"].map(
        lambda g: {"greater": 0, "lesser": 1}.get(g, 2)
    )
    summary_df = summary_df.sort_values(
        ["model_name", "_mode_order", "persona", "_group_order", "persona_id", "_order_order"]
    ).reset_index(drop=True)

    present_cols = [c for c in CONDITION_SUMMARY_COLUMNS if c in summary_df.columns]
    return summary_df[present_cols]


def _factor_rollup(group_df, factor_name, factor_value):
    n = len(group_df)
    competence = group_df["competence_passed"].astype(bool)
    valid = group_df["valid_discount_rate"].astype(bool)
    valid_k = group_df.loc[valid, "k"]
    r2_series = group_df["r_squared"] if "r_squared" in group_df.columns else pd.Series(dtype=float)
    return {
        "factor": factor_name,
        "level": factor_value,
        "n_conditions": n,
        "n_competence_passed": int(competence.sum()),
        "pct_competence_passed": float(competence.mean()) if n else np.nan,
        "n_valid_discount_rate": int(valid.sum()),
        "pct_valid_discount_rate": float(valid.mean()) if n else np.nan,
        "mean_k_when_valid": float(valid_k.mean()) if len(valid_k) else np.nan,
        "median_k_when_valid": float(valid_k.median()) if len(valid_k) else np.nan,
        "mean_r_squared": float(r2_series.mean()) if len(r2_series) else np.nan,
    }


def build_factor_rollups(condition_df):
    """Summaries across model / model_family / trial_type / persona / option_order."""
    rows = []

    single_factors = [
        ("model_name", "model"),
        ("model_family", "model_family"),
        ("trial_type", "trial_type"),
        ("persona", "persona"),
        ("persona_id", "persona_id"),
        ("persona_discounting_group", "persona_discounting_group"),
        ("option_order", "option_order"),
    ]
    for col, factor_name in single_factors:
        if col not in condition_df.columns:
            continue
        for level, group_df in condition_df.groupby(col, dropna=False):
            rows.append(_factor_rollup(group_df, factor_name, str(level)))

    # Useful pairwise views for the main experimental axes.
    pair_specs = [
        (("trial_type", "persona"), "trial_type_x_persona"),
        (("model_family", "trial_type"), "model_family_x_trial_type"),
        (("model_family", "persona"), "model_family_x_persona"),
        (("model_name", "persona"), "model_x_persona"),
        (("model_name", "trial_type"), "model_x_trial_type"),
        (("option_order", "trial_type"), "option_order_x_trial_type"),
        (("option_order", "persona"), "option_order_x_persona"),
        (("model_name", "option_order"), "model_x_option_order"),
        (("persona_discounting_group", "persona"), "discounting_group_x_persona"),
        (("model_family", "persona_discounting_group"), "model_family_x_discounting_group"),
        (("model_name", "persona_id"), "model_x_persona_id"),
    ]
    for cols, factor_name in pair_specs:
        if any(c not in condition_df.columns for c in cols):
            continue
        for level_values, group_df in condition_df.groupby(list(cols), dropna=False):
            if not isinstance(level_values, tuple):
                level_values = (level_values,)
            level = " | ".join(str(v) for v in level_values)
            rows.append(_factor_rollup(group_df, factor_name, level))

    rollup_df = pd.DataFrame(rows)
    if rollup_df.empty:
        return rollup_df
    return rollup_df.sort_values(["factor", "level"]).reset_index(drop=True)


def load_persona_strata(tables_dir, modes):
    """Loads comparison_summary_by_persona* tables written by analyze.py."""
    strata_frames = []
    for reasoning_mode in modes:
        for persona_enabled in PERSONA_CONDITIONS:
            if not persona_enabled:
                continue  # persona strata only exist for persona-on runs
            suffix = result_suffix(reasoning_mode, persona_enabled)
            csv_path = os.path.join(tables_dir, f"comparison_summary_by_persona{suffix}.csv")
            if not os.path.exists(csv_path):
                continue
            strata_df = pd.read_csv(csv_path)
            strata_df["trial_type"] = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
            strata_df["persona"] = "on"
            strata_frames.append(strata_df)
            print(f"[persona strata / {reasoning_mode}] loaded {csv_path}")
    if not strata_frames:
        return pd.DataFrame()
    return pd.concat(strata_frames, ignore_index=True)


def write_summary_readme(summary_dir, human_k, k_lower_bound, k_upper_bound):
    readme = f"""# Waiting Game — factor summary

Clean tables for scanning results across **model**, **trial type** (prompting
mode: direct / chain-of-thought), **persona** (on/off), **persona_id** /
**persona_discounting_group** (behavioral personas), and **option_order**
(pooled / sooner_A / sooner_B).

Human benchmark (Rachlin et al. 1991): k = {human_k} per month.
Reasonable k bounds (hits cut from reliability, still reported): [{k_lower_bound}, {k_upper_bound}].

## Files

| File | Contents |
|---|---|
| `by_condition.csv` | One row per **model × trial_type × persona × persona_id × option_order** with competence gates, fit reliability, and fitted k. **Start here.** |
| `by_factor.csv` | Rollups: pass rates and mean/median k (when valid) by each factor alone and useful pairs (e.g. trial_type × persona). |
| `by_persona.csv` | Present only when persona-on runs exist: discounting_group / persona_id strata from `analyze.py`. |
| `sanity_check_summary.md` | Human-readable checklist table (same content as `results/tables/sanity_check_summary.md`). |

## `by_condition.csv` columns

- **model_name** / **model_family**: full Ollama tag and coarse family (qwen2.5, qwen3, llama3.1, mistral).
- **trial_type**: prompting condition (`direct`, `chain-of-thought`).
- **persona**: `on` or `off` behavioral persona framing.
- **persona_id** / **persona_label** / **persona_discounting_group**: specific lifestyle persona and researcher-only greater/lesser tag (null when persona=off).
- **option_order**: `pooled` (all trials), `sooner_A` (sooner listed as option A), or `sooner_B` (sooner listed as option B).
- **competence_passed**: monotonicity AND money-preference AND indifference-nonincreasing all pass.
- **k_reliable**: hyperbolic NLS R^2 adequate, enough indifference points, AND fitted k not at bound.
- **valid_discount_rate**: competence_passed AND k_reliable — trust the fitted k only when this is true.
- **k**, **k_ci_low**, **k_ci_high**, **r_squared**: two-step hyperbolic fit to empirical immediate equivalents (shown even when invalid; check flags first).

Regenerate with: `python src/compare_modes.py`
"""
    readme_path = os.path.join(summary_dir, "README.md")
    with open(readme_path, "w") as readme_file:
        readme_file.write(readme)
    return readme_path


def write_factor_summary_folder(combined_df, tables_dir, summary_dir, human_k,
                                k_lower_bound, k_upper_bound, sanity_check_markdown):
    """Writes the clean results/summary/ factor tables."""
    condition_df = build_condition_summary(combined_df)
    rollup_df = build_factor_rollups(condition_df)
    persona_strata_df = load_persona_strata(tables_dir, REASONING_MODES)

    condition_path = os.path.join(summary_dir, "by_condition.csv")
    rollup_path = os.path.join(summary_dir, "by_factor.csv")
    condition_df.to_csv(condition_path, index=False)
    rollup_df.to_csv(rollup_path, index=False)

    written = [condition_path, rollup_path]

    if not persona_strata_df.empty:
        persona_path = os.path.join(summary_dir, "by_persona.csv")
        persona_strata_df.to_csv(persona_path, index=False)
        written.append(persona_path)

    sanity_path = os.path.join(summary_dir, "sanity_check_summary.md")
    with open(sanity_path, "w") as sanity_file:
        sanity_file.write(sanity_check_markdown)
    written.append(sanity_path)

    readme_path = write_summary_readme(summary_dir, human_k, k_lower_bound, k_upper_bound)
    written.append(readme_path)
    return written, condition_df, rollup_df


def build_sanity_check_markdown(combined_df, human_k, k_lower_bound, k_upper_bound):
    """One presentable Markdown table with every sanity check (competence
    gate + fit-reliability gate) side by side, across every model x mode
    x persona x option_order that has been run.
    """
    sortable_df = combined_df.copy()
    if "option_order" not in sortable_df.columns:
        sortable_df["option_order"] = "pooled"
    sortable_df["_mode_order"] = sortable_df["reasoning_mode"].map(MODE_SORT_ORDER)
    sortable_df["_persona_order"] = sortable_df.get("persona_enabled", False)
    sortable_df["_order_order"] = sortable_df["option_order"].map(
        lambda o: OPTION_ORDER_SORT.get(o, 99)
    )
    sort_cols = ["model_name", "_mode_order"]
    if "persona_enabled" in sortable_df.columns:
        sort_cols.append("_persona_order")
    sort_cols.append("_order_order")
    sortable_df = sortable_df.sort_values(sort_cols)

    has_persona_id = (
        "persona_id" in sortable_df.columns and sortable_df["persona_id"].notna().any()
    )
    has_indiff = "indifference_nonincreasing_passed" in sortable_df.columns
    if has_persona_id and has_indiff:
        header = (
            "| Model | Mode | Persona | Persona ID | Group | Order | Monotonicity | Money Pref. | "
            "Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | "
            "**Valid Discount Rate** | Fitted k [95% CI] |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    elif has_indiff:
        header = (
            "| Model | Mode | Persona | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | "
            "Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    else:
        header = (
            "| Model | Mode | Persona | Order | Monotonicity | Money Pref. | Competence Pass | "
            "R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|---|---|"
    rows = [header, separator]
    for _, row in sortable_df.iterrows():
        mode_label = MODE_DISPLAY_LABELS.get(row["reasoning_mode"], row["reasoning_mode"])
        persona_label = "on" if bool(row.get("persona_enabled", False)) else "off"
        order_label = row.get("option_order", "pooled")
        r2 = row["r_squared"] if "r_squared" in row and not pd.isna(row["r_squared"]) else float("nan")
        r2_str = "-" if pd.isna(r2) else f"{r2:.3f}"
        persona_id = row.get("persona_id")
        persona_id_label = "-" if pd.isna(persona_id) or persona_id is None else str(persona_id)
        group = row.get("persona_discounting_group")
        group_label = "-" if pd.isna(group) or group is None else str(group)
        if has_persona_id and has_indiff:
            rows.append(
                f"| {row['model_name']} | {mode_label} | {persona_label} | {persona_id_label} | "
                f"{group_label} | {order_label} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | "
                f"{checkmark(row['indifference_nonincreasing_passed'])} | "
                f"{checkmark(row['overall_passed'])} | "
                f"{r2_str} | {checkmark(row['k_is_reliable'])} | "
                f"**{checkmark(row['valid_discount_rate'])}** | {format_k_with_ci(row)} |"
            )
        elif has_indiff:
            rows.append(
                f"| {row['model_name']} | {mode_label} | {persona_label} | {order_label} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | "
                f"{checkmark(row['indifference_nonincreasing_passed'])} | "
                f"{checkmark(row['overall_passed'])} | "
                f"{r2_str} | {checkmark(row['k_is_reliable'])} | "
                f"**{checkmark(row['valid_discount_rate'])}** | {format_k_with_ci(row)} |"
            )
        else:
            rows.append(
                f"| {row['model_name']} | {mode_label} | {persona_label} | {order_label} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | {checkmark(row['overall_passed'])} | "
                f"{r2_str} | {checkmark(row['k_is_reliable'])} | "
                f"**{checkmark(row['valid_discount_rate'])}** | {format_k_with_ci(row)} |"
            )
    table_markdown = "\n".join(rows)

    modes_present = ", ".join(MODE_DISPLAY_LABELS.get(m, m) for m in sortable_df["reasoning_mode"].unique())
    legend = f"""# Waiting Game: Sanity Check Summary

Modes included: {modes_present}. Human benchmark (Rachlin et al. 1991): k = {human_k} per month.
Reasonable k bounds (hits cut from reliability, still reported): [{k_lower_bound}, {k_upper_bound}].

Fitting method: per delay, interpolate the sooner amount at P(choose sooner)=0.5, then
nonlinear least-squares fit of x(d) = $later / (1 + k*d) to those empirical immediate equivalents.
Results stratified by A/B option order (pooled / sooner_A / sooner_B).

{table_markdown}

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay (`competence_checks.py::check_monotonicity`).
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay (`check_money_preference`).
- **Indiff. Non-incr.**: empirical 50% immediate equivalents x*(d) are non-increasing in delay (`check_indifference_nonincreasing`).
- **Competence Pass**: Monotonicity AND Money Pref. AND Indiff. Non-incr. all pass (`overall_passed`).
- **R^2 (indiff. fit)**: goodness of fit of the hyperbolic indifference curve to the per-delay 50% switching points.
- **k Reliable?**: R^2 above threshold, enough indifference points, AND fitted k did not land at the optimizer's boundary ([{k_lower_bound}, {k_upper_bound}]). Bound hits are cut from reliability; the bound values themselves are still reported.
- **Valid Discount Rate**: Competence Pass AND k Reliable \u2014 the single bottom-line flag for whether the fitted k should be trusted at all.
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI, shown regardless of reliability (compare against the "k Reliable?"/"Valid Discount Rate" columns before interpreting).
- **Persona**: on/off behavioral persona framing; per-persona and greater/lesser discounting-group strata are in `by_persona.csv` / `comparison_summary_by_persona*.csv` when persona-on data exists.
- **Order**: `pooled` / `sooner_A` / `sooner_B` — whether the sooner option was listed as A or B (or all trials pooled).
"""
    return legend


def _k_reliable_ignoring_bounds(row, min_r_squared=0.5, min_n_points=3):
    """Fit-quality gate without bound or R² cutoffs.

    Bound hits and flat-indifference fits (nan / low R², often extreme k) are
    still counted as reliable when k is finite and enough indifference points
    exist. `min_r_squared` is accepted for API compatibility but unused.
    """
    del min_r_squared  # intentionally unused in this alternate summary
    k = row.get("k")
    if k is None or (isinstance(k, float) and np.isnan(k)) or pd.isna(k):
        return False
    n_points = row.get("n_indifference_points")
    if n_points is None or pd.isna(n_points) or int(n_points) < min_n_points:
        return False
    return True


def build_sanity_check_markdown_for_order(
    order_df, option_order, human_k, min_r_squared=0.5, min_n_points=3
):
    """Sanity-check table for one option_order stratum.

    Differs from the main sanity summary:
      - no Mode column
      - k reliability ignores upper/lower bound hits (R^2 + n_points only)
    """
    sortable_df = order_df.copy()
    sortable_df["_persona_order"] = sortable_df.get("persona_enabled", False)
    if "persona_discounting_group" in sortable_df.columns:
        sortable_df["_group_order"] = sortable_df["persona_discounting_group"].map(
            lambda g: {"greater": 0, "lesser": 1}.get(g, 2) if pd.notna(g) else 3
        )
    else:
        sortable_df["_group_order"] = 3
    sort_cols = ["model_name"]
    if "persona_enabled" in sortable_df.columns:
        sort_cols.append("_persona_order")
    sort_cols.append("_group_order")
    if "persona_id" in sortable_df.columns:
        sort_cols.append("persona_id")
    sortable_df = sortable_df.sort_values(sort_cols)

    has_persona_id = (
        "persona_id" in sortable_df.columns and sortable_df["persona_id"].notna().any()
    )
    has_indiff = "indifference_nonincreasing_passed" in sortable_df.columns

    if has_persona_id and has_indiff:
        header = (
            "| Model | Persona | Persona ID | Group | Monotonicity | Money Pref. | "
            "Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | "
            "**Valid Discount Rate** | Fitted k [95% CI] |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    elif has_indiff:
        header = (
            "| Model | Persona | Monotonicity | Money Pref. | Indiff. Non-incr. | "
            "Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | "
            "Fitted k [95% CI] |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|---|"
    else:
        header = (
            "| Model | Persona | Monotonicity | Money Pref. | Competence Pass | "
            "R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |"
        )
        separator = "|---|---|---|---|---|---|---|---|---|"

    rows = [header, separator]
    n_valid = 0
    n_rows = 0
    for _, row in sortable_df.iterrows():
        n_rows += 1
        persona_label = "on" if bool(row.get("persona_enabled", False)) else "off"
        r2 = row["r_squared"] if "r_squared" in row and not pd.isna(row["r_squared"]) else float("nan")
        r2_str = "-" if pd.isna(r2) else f"{r2:.3f}"
        persona_id = row.get("persona_id")
        persona_id_label = "-" if pd.isna(persona_id) or persona_id is None else str(persona_id)
        group = row.get("persona_discounting_group")
        group_label = "-" if pd.isna(group) or group is None else str(group)

        k_reliable = _k_reliable_ignoring_bounds(row, min_r_squared, min_n_points)
        competence = bool(row.get("overall_passed", False))
        valid = competence and k_reliable
        if valid:
            n_valid += 1

        if has_persona_id and has_indiff:
            rows.append(
                f"| {row['model_name']} | {persona_label} | {persona_id_label} | "
                f"{group_label} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | "
                f"{checkmark(row['indifference_nonincreasing_passed'])} | "
                f"{checkmark(competence)} | "
                f"{r2_str} | {checkmark(k_reliable)} | "
                f"**{checkmark(valid)}** | {format_k_with_ci(row)} |"
            )
        elif has_indiff:
            rows.append(
                f"| {row['model_name']} | {persona_label} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | "
                f"{checkmark(row['indifference_nonincreasing_passed'])} | "
                f"{checkmark(competence)} | "
                f"{r2_str} | {checkmark(k_reliable)} | "
                f"**{checkmark(valid)}** | {format_k_with_ci(row)} |"
            )
        else:
            rows.append(
                f"| {row['model_name']} | {persona_label} | "
                f"{checkmark(row['monotonicity_passed'])} | "
                f"{checkmark(row['money_preference_passed'])} | "
                f"{checkmark(competence)} | "
                f"{r2_str} | {checkmark(k_reliable)} | "
                f"**{checkmark(valid)}** | {format_k_with_ci(row)} |"
            )

    table_markdown = "\n".join(rows)
    return f"""# Waiting Game: Sanity Check Summary (order = `{option_order}`)

Option-order stratum: **{option_order}**. Human benchmark (Rachlin et al. 1991): k = {human_k} per month.

**Bound-agnostic reliability:** fitted k is *not* rejected for landing at the
optimizer's lower/upper bound, and R² is not used as a gate (flat indifference
curves that yield extreme k still count). `k Reliable?` requires only: k is
finite and ≥ {min_n_points} indifference points.
Valid discount rate = Competence Pass AND that bound-agnostic k Reliable.
Valid cells in this file: **{n_valid} / {n_rows}**.

Fitting method: per delay, interpolate the sooner amount at P(choose sooner)=0.5, then
nonlinear least-squares fit of x(d) = $later / (1 + k*d) to those empirical immediate equivalents.

{table_markdown}

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay.
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay.
- **Indiff. Non-incr.**: empirical 50% immediate equivalents x*(d) are non-increasing in delay.
- **Competence Pass**: Monotonicity AND Money Pref. AND Indiff. Non-incr. all pass.
- **R^2 (indiff. fit)**: goodness of fit of the hyperbolic indifference curve to the per-delay 50% switching points.
- **k Reliable?**: k is finite and ≥ {min_n_points} indifference points (bound hits and R² ignored).
- **Valid Discount Rate**: Competence Pass AND k Reliable (bound-agnostic).
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI.
- **Persona**: on/off behavioral persona framing; Persona ID / Group when persona-on.
"""


def write_order_sanity_summaries(
    combined_df, tables_dir, summary_dir, human_k, fitting_config=None
):
    """Writes three bound-agnostic sanity markdown files, one per option_order."""
    fitting_config = fitting_config or {}
    min_r_squared = float(fitting_config.get("min_r_squared", 0.5))
    min_n_points = int(fitting_config.get("min_n_indifference_points", 3))

    working_df = combined_df.copy()
    if "option_order" not in working_df.columns:
        working_df["option_order"] = "pooled"

    written = []
    for option_order, _ in [
        ("pooled", None),
        ("sooner_A", True),
        ("sooner_B", False),
    ]:
        order_df = working_df[working_df["option_order"] == option_order]
        if order_df.empty:
            print(f"[sanity / {option_order}] no rows; skipped.")
            continue
        markdown = build_sanity_check_markdown_for_order(
            order_df, option_order, human_k, min_r_squared, min_n_points
        )
        filename = f"sanity_check_summary_{option_order}.md"
        for target_dir in (tables_dir, summary_dir):
            path = os.path.join(target_dir, filename)
            with open(path, "w") as markdown_file:
                markdown_file.write(markdown)
            written.append(path)
            print(f"Wrote bound-agnostic sanity summary ({option_order}) to {path}")
    return written


def load_available_mode_tables(tables_dir, modes):
    """Loads comparison_summary{mode}{persona}.csv for every mode x persona
    condition that has already been run through analyze.py.
    """
    mode_tables = {}
    for reasoning_mode in modes:
        for persona_enabled in PERSONA_CONDITIONS:
            suffix = result_suffix(reasoning_mode, persona_enabled)
            csv_path = os.path.join(tables_dir, f"comparison_summary{suffix}.csv")
            key = (reasoning_mode, persona_enabled)
            if not os.path.exists(csv_path):
                continue
            mode_df = pd.read_csv(csv_path)
            mode_df["reasoning_mode"] = reasoning_mode
            if "persona_enabled" not in mode_df.columns:
                mode_df["persona_enabled"] = persona_enabled
            mode_tables[key] = mode_df
            print(f"[{reasoning_mode} / persona={persona_enabled}] loaded {csv_path}")
    return mode_tables


def plot_competence_and_k_by_mode(combined_df, modes_present, human_k, figures_dir):
    # Persona-off + pooled option order (fallback to all rows if strata missing).
    plot_df = combined_df[~combined_df["persona_enabled"].astype(bool)].copy()
    if "option_order" in plot_df.columns and (plot_df["option_order"] == "pooled").any():
        plot_df = plot_df[plot_df["option_order"] == "pooled"]

    model_names = sorted(plot_df["model_name"].unique())
    n_models = len(model_names)
    n_modes = len(modes_present)
    bar_width = 0.8 / max(n_modes, 1)

    figure, (axis_competence, axis_k) = plt.subplots(1, 2, figsize=(14, 5.5))

    for mode_index, reasoning_mode in enumerate(modes_present):
        mode_df = plot_df[plot_df["reasoning_mode"] == reasoning_mode].set_index("model_name")
        x_positions = np.arange(n_models) + (mode_index - (n_modes - 1) / 2) * bar_width
        color = MODE_COLORS.get(reasoning_mode, None)
        label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)

        valid_discount_rate = [
            float(mode_df.loc[m, "valid_discount_rate"]) if m in mode_df.index else np.nan
            for m in model_names
        ]
        axis_competence.bar(x_positions, valid_discount_rate, width=bar_width, color=color, label=label)

        k_values = [
            mode_df.loc[m, "k"] if (m in mode_df.index and bool(mode_df.loc[m, "valid_discount_rate"])) else np.nan
            for m in model_names
        ]
        axis_k.bar(x_positions, k_values, width=bar_width, color=color, label=label)

    axis_competence.set_xticks(np.arange(n_models))
    axis_competence.set_xticklabels(model_names, rotation=20, ha="right")
    axis_competence.set_ylim(-0.1, 1.1)
    axis_competence.set_ylabel("Valid discount rate (competence-checks pass AND k reliable)")
    axis_competence.set_title("Does prompting yield a valid hyperbolic fit? (persona-off, pooled order)")
    axis_competence.legend(fontsize=8)

    axis_k.axhline(human_k, color="black", linestyle="--", linewidth=1, label=f"human benchmark k={human_k}")
    axis_k.set_xticks(np.arange(n_models))
    axis_k.set_xticklabels(model_names, rotation=20, ha="right")
    axis_k.set_ylabel("Fitted k per month (only shown where valid_discount_rate=True)")
    axis_k.set_title("Fitted hyperbolic discount rate by mode (persona-off, pooled order)")
    axis_k.legend(fontsize=8)

    figure.suptitle("Effect of reasoning mode (direct / CoT / one-shot / two-shot) on Waiting Game results")
    figure.tight_layout()

    figure_path = os.path.join(figures_dir, "mode_comparison.png")
    figure.savefig(figure_path, dpi=150)
    plt.close(figure)
    return figure_path


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    args = arg_parser.parse_args()

    config = load_config(args.config)
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    summary_dir = resolve_dir_path(
        config["paths"].get("results_summary_dir", "results/summary")
    )
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]
    k_lower = config["fitting"].get("k_lower_bound", 1e-6)
    k_upper = config["fitting"].get("k_upper_bound", 10.0)

    mode_tables = load_available_mode_tables(tables_dir, REASONING_MODES)
    if not mode_tables:
        print("No comparison_summary tables found for any mode. Run the pipeline (run_experiment.py -> "
              "parse_responses.py -> competence_checks.py -> fit_discounting.py -> analyze.py) for at "
              "least one --mode first.")
        return

    combined_df = pd.concat(mode_tables.values(), ignore_index=True)
    if "persona_enabled" not in combined_df.columns:
        combined_df["persona_enabled"] = False
    combined_csv_path = os.path.join(tables_dir, "comparison_summary_by_mode.csv")
    combined_df.to_csv(combined_csv_path, index=False)

    print(f"\n=== Cross-mode comparison ===")
    print_cols = [
        "model_name", "reasoning_mode", "persona_enabled", "persona_id",
        "persona_discounting_group", "option_order",
        "monotonicity_passed", "money_preference_passed",
        "indifference_nonincreasing_passed",
        "k_is_reliable", "valid_discount_rate", "k",
    ]
    print_cols = [c for c in print_cols if c in combined_df.columns]
    sort_cols = [c for c in [
        "model_name", "reasoning_mode", "persona_enabled", "persona_id", "option_order"
    ] if c in combined_df.columns]
    print(combined_df[print_cols].sort_values(sort_cols).to_string(index=False))
    print(f"\nWrote combined table to {combined_csv_path}")

    modes_present = sorted(
        {mode for mode, _ in mode_tables.keys()},
        key=lambda m: MODE_SORT_ORDER.get(m, 99),
    )
    figure_path = plot_competence_and_k_by_mode(combined_df, modes_present, human_k, figures_dir)
    print(f"Wrote mode-comparison plot to {figure_path}")

    sanity_check_markdown = build_sanity_check_markdown(combined_df, human_k, k_lower, k_upper)
    sanity_check_path = os.path.join(tables_dir, "sanity_check_summary.md")
    with open(sanity_check_path, "w") as markdown_file:
        markdown_file.write(sanity_check_markdown)
    print(f"Wrote presentable sanity-check summary table to {sanity_check_path}")

    order_sanity_paths = write_order_sanity_summaries(
        combined_df, tables_dir, summary_dir, human_k, config.get("fitting")
    )

    written_paths, condition_df, rollup_df = write_factor_summary_folder(
        combined_df, tables_dir, summary_dir, human_k, k_lower, k_upper, sanity_check_markdown
    )
    written_paths = list(written_paths) + list(order_sanity_paths)
    print(f"\n=== Factor summary folder ({summary_dir}) ===")
    cond_print = [
        "model_name", "trial_type", "persona", "persona_id",
        "persona_discounting_group", "option_order", "competence_passed",
        "k_reliable", "valid_discount_rate", "k",
    ]
    cond_print = [c for c in cond_print if c in condition_df.columns]
    print(condition_df[cond_print].to_string(index=False))
    print(f"\nFactor rollups ({len(rollup_df)} rows):")
    print(rollup_df.head(20).to_string(index=False))
    for path in written_paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
