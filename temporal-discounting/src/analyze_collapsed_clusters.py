"""Refit hyperbolic k for collapsed-persona clusters.

Uses the same competence checks + two-step hyperbolic fit as analyze.py /
fit_discounting.py / competence_checks.py. Reports all option-order strata
(pooled / sooner_A / sooner_B).

Clusters:
  1. by_model_all_personas
     model × option_order, collapsing persona-off + all persona-on trials.
  2. by_model_discounting_group
     model × greater|lesser × option_order, collapsing the four personas
     within each hypothesised discounting group (persona-off excluded).

Competent-only variant (--competent-only, default):
  Same two clusters, but only pool (model × persona × option_order) cells
  with competence_passed=True in results/summary/by_condition.csv — the same
  inclusion set as analysis_k_always_reliable/successful_conditions.md.
  Single-persona cells must reproduce that file's fitted k.

Outputs under results/analysis_collapsed_clusters/:
  by_model_all_personas.csv / by_model_discounting_group.csv / summary.md
  by_model_competent.csv / by_model_discounting_group_competent.csv
  summary_competent.md
  figures/...

Usage:
  .venv/bin/python src/analyze_collapsed_clusters.py
  .venv/bin/python src/analyze_collapsed_clusters.py --also-all
  .venv/bin/python src/analyze_collapsed_clusters.py --config config_q8.yaml
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyze import (
    MODE_DISPLAY_LABELS,
    MODEL_COLORS,
    DISCOUNTING_GROUP_COLORS,
    empirical_indifference_amounts,
    fit_stratum,
    fitted_indifference_curve,
)
from config_utils import (
    OPTION_ORDER_STRATA,
    filter_by_option_order,
    load_config,
    resolve_dir_path,
)

OPTION_ORDER_SORT = {"pooled": 0, "sooner_A": 1, "sooner_B": 2}
GROUP_SORT = {"greater": 0, "lesser": 1}


def load_combined_choices(processed_dir: str, mode_suffix: str = "") -> pd.DataFrame:
    """Load persona-off and persona-on choice files and concatenate."""
    frames = []
    for persona_tag, label in (("", "off"), ("__persona", "on")):
        path = os.path.join(processed_dir, f"choices{mode_suffix}{persona_tag}.csv")
        if not os.path.exists(path):
            print(f"[warn] missing {path}; skipping persona={label}")
            continue
        df = pd.read_csv(path, low_memory=False)
        frames.append(df)
        print(f"Loaded {path}: {len(df)} rows")
    if not frames:
        raise FileNotFoundError(
            f"No choices*.csv found under {processed_dir} "
            f"(expected choices{mode_suffix}.csv and/or choices{mode_suffix}__persona.csv)"
        )
    combined = pd.concat(frames, ignore_index=True)
    if "persona_discounting_group" in combined.columns:
        combined["persona_discounting_group"] = combined["persona_discounting_group"].where(
            combined["persona_discounting_group"].notna()
            & (combined["persona_discounting_group"].astype(str).str.strip() != ""),
            other=np.nan,
        )
    return combined


def persona_key_from_condition_row(row: pd.Series) -> str:
    """Match successful_conditions.md persona labels: 'off' or persona_id."""
    persona = str(row.get("persona", "")).lower()
    if persona in ("off", "false", "0", ""):
        return "off"
    pid = row.get("persona_id")
    if pd.isna(pid) or pid is None or str(pid).strip() == "":
        return "off"
    return str(pid)


def persona_key_from_choice_row(row: pd.Series) -> str:
    """Map a choice trial to a persona key.

    Only persona_enabled=False is 'off'. Persona-on rows with a missing
    persona_id (data glitch; seen for qwen3:4b) are 'unknown' so they are
    never treated as the persona-off control.
    """
    enabled = row.get("persona_enabled", False)
    if isinstance(enabled, str):
        enabled = enabled.lower() in ("true", "1", "on")
    if not bool(enabled):
        return "off"
    pid = row.get("persona_id")
    if pd.isna(pid) or pid is None or str(pid).strip() == "":
        return "unknown"
    return str(pid)


def load_competent_condition_keys(by_condition_path: str | Path) -> pd.DataFrame:
    """Rows with competence_passed — same set as successful_conditions.md."""
    path = Path(by_condition_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Need {path} to gate competent-only collapses "
            "(same source as analysis_k_always_reliable)."
        )
    df = pd.read_csv(path)
    if "competence_passed" not in df.columns:
        raise ValueError(f"{path} missing competence_passed column")
    ok = df[df["competence_passed"].astype(bool)].copy()
    ok["persona_key"] = ok.apply(persona_key_from_condition_row, axis=1)
    return ok


def competent_keys_for(
    competent_df: pd.DataFrame, model_name: str, option_order: str
) -> set[str]:
    sub = competent_df[
        (competent_df["model_name"] == model_name)
        & (competent_df["option_order"] == option_order)
    ]
    return set(sub["persona_key"].astype(str))


def filter_order_df_to_competent(
    order_df: pd.DataFrame, competent_persona_keys: set[str]
) -> pd.DataFrame:
    if order_df.empty or not competent_persona_keys:
        return order_df.iloc[0:0]
    keys = order_df.apply(persona_key_from_choice_row, axis=1)
    return order_df.loc[keys.isin(competent_persona_keys)].copy()


def list_personas_in_df(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    keys = sorted(set(df.apply(persona_key_from_choice_row, axis=1)))
    # Stable: off first
    if "off" in keys:
        keys = ["off"] + [k for k in keys if k != "off"]
    return ",".join(keys)


def fit_cluster_rows(
    choices_df: pd.DataFrame,
    models: list[str],
    config: dict,
    cluster_meta_builder,
    competent_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """Run competence+fit for each (model, option_order[, group]) stratum.

    If competent_df is provided, only pool persona keys that pass competence
    for that exact (model, option_order), matching successful_conditions.md.
    """
    later_amount = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    n_bootstrap = config["fitting"]["n_bootstrap"]
    bootstrap_seed = config["fitting"]["bootstrap_seed"]
    from fit_discounting import fitting_bounds_from_config

    fitting_bounds = fitting_bounds_from_config(config["fitting"])
    competence_config = config["competence_checks"]
    fitting_config = config["fitting"]

    rows = []
    indifference_records = []

    for model_name in models:
        model_df = choices_df[choices_df["model_name"] == model_name]
        if model_df.empty:
            print(f"[{model_name}] no trials; skip")
            continue

        for option_order, sooner_is_a in OPTION_ORDER_STRATA:
            order_df = filter_by_option_order(model_df, sooner_is_a)
            if order_df.empty:
                continue

            included_keys: set[str] | None = None
            if competent_df is not None:
                included_keys = competent_keys_for(competent_df, model_name, option_order)
                if not included_keys:
                    print(
                        f"[{model_name}] {option_order}: no competent personas "
                        f"(see successful_conditions.md); skip"
                    )
                    continue
                order_df = filter_order_df_to_competent(order_df, included_keys)
                if order_df.empty:
                    print(
                        f"[{model_name}] {option_order}: competent keys "
                        f"{sorted(included_keys)} but no matching trials; skip"
                    )
                    continue

            strata = cluster_meta_builder(model_name, option_order, order_df)
            for meta, stratum_df in strata:
                if stratum_df is None or stratum_df.empty:
                    continue
                personas_included = list_personas_in_df(stratum_df)
                meta = dict(meta)
                meta["personas_included"] = personas_included
                meta["n_personas_collapsed"] = (
                    len(personas_included.split(",")) if personas_included else 0
                )
                if competent_df is not None:
                    meta["competent_only"] = True
                    meta["inclusion_source"] = (
                        "by_condition.csv competence_passed "
                        "(= analysis_k_always_reliable/successful_conditions.md)"
                    )
                tag = (
                    f"{meta.get('cluster')} / {meta.get('stratum_value', 'all')} "
                    f"/ {option_order}"
                )
                print(
                    f"[{model_name}] fitting {tag} "
                    f"(personas={personas_included or '-'}, n={len(stratum_df)}) ..."
                )
                row = fit_stratum(
                    stratum_df,
                    later_amount,
                    n_bootstrap,
                    bootstrap_seed,
                    fitting_bounds,
                    competence_config,
                    fitting_config,
                    meta,
                    delay_grid_months,
                )
                if row is None:
                    continue
                # Always-reliable framing for competent-only pools: inclusion is
                # already competence-gated at the persona×order level.
                if competent_df is not None:
                    row["k_always_reliable"] = True
                    row["valid_under_always_reliable_k"] = True
                rows.append(row)

                empirical = empirical_indifference_amounts(stratum_df, delay_grid_months)
                for delay, amount in empirical.items():
                    indifference_records.append({
                        **{k: meta[k] for k in meta if k != "n_personas_collapsed"},
                        "delay_months": delay,
                        "indifference_amount": amount,
                    })

                k_str = "nan" if pd.isna(row["k"]) else f"{row['k']:.5f}"
                print(
                    f"  -> k={k_str} competence={row['overall_passed']} "
                    f"reliable={row['k_is_reliable']} valid={row['valid_discount_rate']} "
                    f"n_trials={row['n_trials_fit']}"
                )

    return pd.DataFrame(rows), indifference_records


def cluster1_builder(model_name, option_order, order_df):
    """Collapse persona-off + all personas for one model × option_order."""
    n_personas = (
        order_df["persona_id"].dropna().astype(str).str.strip().replace("", np.nan).dropna().nunique()
        if "persona_id" in order_df.columns
        else 0
    )
    has_off = (
        (~order_df["persona_enabled"].astype(bool)).any()
        if "persona_enabled" in order_df.columns
        else True
    )
    # Also count off via persona_key when competent filter already applied
    keys = set(order_df.apply(persona_key_from_choice_row, axis=1)) if not order_df.empty else set()
    if keys:
        n_personas = len(keys)
        has_off = "off" in keys
    meta = {
        "cluster": "by_model_all_personas",
        "model_name": model_name,
        "option_order": option_order,
        "stratum_type": "all_personas_plus_off",
        "stratum_value": "all",
        "n_personas_collapsed": int(n_personas),
        "includes_persona_off": bool(has_off),
    }
    return [(meta, order_df)]


def cluster2_builder(model_name, option_order, order_df):
    """Collapse within greater / lesser personas only (exclude persona-off)."""
    if "persona_discounting_group" not in order_df.columns:
        return []
    on_df = order_df[
        order_df["persona_discounting_group"].notna()
        & (order_df.apply(persona_key_from_choice_row, axis=1) != "off")
    ].copy()
    if on_df.empty:
        return []

    out = []
    for group_name in ("greater", "lesser"):
        group_df = on_df[on_df["persona_discounting_group"] == group_name]
        if group_df.empty:
            continue
        n_personas = group_df["persona_id"].nunique() if "persona_id" in group_df.columns else 0
        meta = {
            "cluster": "by_model_discounting_group",
            "model_name": model_name,
            "option_order": option_order,
            "stratum_type": "discounting_group",
            "stratum_value": group_name,
            "persona_discounting_group": group_name,
            "n_personas_collapsed": int(n_personas),
            "includes_persona_off": False,
        }
        out.append((meta, group_df))
    return out


def sort_result_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["_order_sort"] = out["option_order"].map(lambda o: OPTION_ORDER_SORT.get(o, 99))
    if "stratum_value" in out.columns:
        out["_group_sort"] = out["stratum_value"].map(lambda g: GROUP_SORT.get(g, 50))
    else:
        out["_group_sort"] = 0
    models = list(dict.fromkeys(out["model_name"]))
    out["_model_sort"] = out["model_name"].map(
        lambda m: models.index(m) if m in models else 999
    )
    out = out.sort_values(["_model_sort", "_group_sort", "_order_sort"]).drop(
        columns=["_order_sort", "_group_sort", "_model_sort"]
    )
    return out.reset_index(drop=True)


def _fmt_bool(value) -> str:
    if pd.isna(value):
        return "-"
    return "✅" if bool(value) else "❌"


def _fmt_k(row) -> str:
    if pd.isna(row.get("k")):
        return "-"
    k = float(row["k"])
    lo, hi = row.get("k_ci_low"), row.get("k_ci_high")
    if pd.isna(lo) or pd.isna(hi):
        return f"{k:.4f}"
    return f"{k:.4f} [{float(lo):.4f}, {float(hi):.4f}]"


def _fmt_r2(value) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.3f}"


def build_summary_markdown(
    all_personas_df: pd.DataFrame,
    group_df: pd.DataFrame,
    human_k: float,
    *,
    competent_only: bool = False,
    zero_success_models: list[str] | None = None,
) -> str:
    if competent_only:
        lines = [
            "# Collapsed-cluster discount fits (competent personas only)",
            "",
            "Inclusion is gated by the same competence-pass cells as "
            "`results/analysis_k_always_reliable/successful_conditions.md` "
            "(from `results/summary/by_condition.csv`). For each "
            "**model × option_order**, only those persona / persona-off "
            "conditions are pooled, then hyperbolic k is refit.",
            "",
            "Under the always-reliable framing used in that report, "
            "**Valid (always-reliable)** is ✅ whenever ≥1 competent "
            "persona×order cell contributed. Single-persona rows must "
            "reproduce that file's fitted k.",
            "",
            f"Human benchmark (Rachlin et al. 1991): k = {human_k} per month.",
            "",
            "## Cluster 1 — by model, competent personas + off (when competent)",
            "",
        ]
        header1 = (
            "| Model | Option order | Personas included | n | "
            "Pooled competence | **Valid (always-reliable)** | "
            "R² | Fitted k [95% CI] |"
        )
        sep1 = "|---|---|---|---:|---|---|---|---|"
    else:
        lines = [
            "# Collapsed-cluster discount fits",
            "",
            "Same pipeline as the main Waiting Game analysis: competence gates "
            "(monotonicity, money preference, indifference non-increasing) + "
            "two-step hyperbolic fit to empirical indifference amounts, with "
            "bootstrap 95% CIs. `Valid Discount Rate` = competence pass AND "
            "`k_is_reliable`.",
            "",
            f"Human benchmark (Rachlin et al. 1991): k = {human_k} per month.",
            "",
            "## Cluster 1 — by model, all personas + persona-off",
            "",
            "Each row pools persona-off control trials with all persona-on trials "
            "for that model, then fits separately for each option-order stratum.",
            "",
        ]
        header1 = (
            "| Model | Option order | n trials | n strata collapsed | "
            "Competence | k Reliable? | **Valid Discount Rate** | "
            "R² | Fitted k [95% CI] |"
        )
        sep1 = "|---|---|---:|---:|---|---|---|---|---|"

    if all_personas_df.empty:
        lines.append("_No rows (no competent persona×order cells to pool)._")
    else:
        lines.extend([header1, sep1])
        for _, row in all_personas_df.iterrows():
            if competent_only:
                valid_ar = row.get("valid_under_always_reliable_k", True)
                lines.append(
                    f"| {row['model_name']} | {row['option_order']} | "
                    f"`{row.get('personas_included', '')}` | "
                    f"{int(row['n_trials_fit'])} | "
                    f"{_fmt_bool(row['overall_passed'])} | "
                    f"**{_fmt_bool(valid_ar)}** | {_fmt_r2(row['r_squared'])} | "
                    f"{_fmt_k(row)} |"
                )
            else:
                lines.append(
                    f"| {row['model_name']} | {row['option_order']} | "
                    f"{int(row['n_trials_fit'])} | {int(row.get('n_personas_collapsed', 0))} | "
                    f"{_fmt_bool(row['overall_passed'])} | {_fmt_bool(row['k_is_reliable'])} | "
                    f"**{_fmt_bool(row['valid_discount_rate'])}** | {_fmt_r2(row['r_squared'])} | "
                    f"{_fmt_k(row)} |"
                )

    if competent_only:
        lines.extend([
            "",
            "## Cluster 2 — by model × greater / lesser (competent personas only)",
            "",
            "Persona-off excluded. Within each model × option_order, only "
            "competence-passing personas in that discounting group are pooled "
            "(same cells as `successful_conditions.md`).",
            "",
        ])
        header2 = (
            "| Model | Group | Option order | Personas included | n | "
            "Pooled competence | **Valid (always-reliable)** | "
            "R² | Fitted k [95% CI] |"
        )
        sep2 = "|---|---|---|---|---:|---|---|---|---|"
    else:
        lines.extend([
            "",
            "## Cluster 2 — by model × greater / lesser personas",
            "",
            "Persona-off excluded. Within each model, the four *greater* personas "
            "are pooled and the four *lesser* personas are pooled; fits are "
            "reported for all three option-order conditions (3 × greater + 3 × lesser).",
            "",
        ])
        header2 = (
            "| Model | Group | Option order | n trials | n personas | "
            "Competence | k Reliable? | **Valid Discount Rate** | "
            "R² | Fitted k [95% CI] |"
        )
        sep2 = "|---|---|---|---:|---:|---|---|---|---|---|"

    if group_df.empty:
        lines.append("_No rows._")
    else:
        lines.extend([header2, sep2])
        for _, row in group_df.iterrows():
            if competent_only:
                valid_ar = row.get("valid_under_always_reliable_k", True)
                lines.append(
                    f"| {row['model_name']} | {row['stratum_value']} | {row['option_order']} | "
                    f"`{row.get('personas_included', '')}` | "
                    f"{int(row['n_trials_fit'])} | "
                    f"{_fmt_bool(row['overall_passed'])} | "
                    f"**{_fmt_bool(valid_ar)}** | {_fmt_r2(row['r_squared'])} | "
                    f"{_fmt_k(row)} |"
                )
            else:
                lines.append(
                    f"| {row['model_name']} | {row['stratum_value']} | {row['option_order']} | "
                    f"{int(row['n_trials_fit'])} | {int(row.get('n_personas_collapsed', 0))} | "
                    f"{_fmt_bool(row['overall_passed'])} | {_fmt_bool(row['k_is_reliable'])} | "
                    f"**{_fmt_bool(row['valid_discount_rate'])}** | {_fmt_r2(row['r_squared'])} | "
                    f"{_fmt_k(row)} |"
                )

    if competent_only and zero_success_models:
        lines.extend([
            "",
            "## Models with 0 successful conditions",
            "",
            "Same list as `successful_conditions.md` — no competent persona×order "
            "cells, so nothing to pool:",
            "",
        ])
        for m in zero_success_models:
            lines.append(f"- `{m}`")

    lines.append("")
    return "\n".join(lines)


def plot_cluster1_curves(
    comparison_df: pd.DataFrame,
    indifference_records: list[dict],
    config: dict,
    figures_dir: Path,
    reasoning_mode: str = "direct",
) -> Path | None:
    if comparison_df.empty:
        return None

    later_amount = config["waiting_game"]["later_amount_dollars"]
    delay_grid = config["waiting_game"]["delay_grid_months"]
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]
    delay_range = np.linspace(min(delay_grid), max(delay_grid), 200)
    indiff_df = pd.DataFrame(indifference_records)

    order_levels = [label for label, _ in OPTION_ORDER_STRATA
                    if label in set(comparison_df["option_order"])]
    figure, axes = plt.subplots(1, len(order_levels), figsize=(5.5 * len(order_levels), 5.5),
                                squeeze=False)
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
    models = list(dict.fromkeys(comparison_df["model_name"]))

    for order_index, option_order in enumerate(order_levels):
        axis = axes[0][order_index]
        order_comp = comparison_df[comparison_df["option_order"] == option_order]
        for model_index, model_name in enumerate(models):
            sub = order_comp[order_comp["model_name"] == model_name]
            if sub.empty:
                continue
            row = sub.iloc[0]
            color = MODEL_COLORS[model_index % len(MODEL_COLORS)]
            pts = indiff_df[
                (indiff_df["model_name"] == model_name)
                & (indiff_df["option_order"] == option_order)
            ]
            if not pts.empty:
                axis.plot(
                    pts["delay_months"], pts["indifference_amount"],
                    color=color, marker="o", linestyle="none",
                    label=f"{model_name} (50% equiv.)", zorder=3,
                )
            if not pd.isna(row["k"]):
                curve = fitted_indifference_curve(row["k"], later_amount, delay_range)
                style = "-" if row["valid_discount_rate"] else ":"
                suffix = "" if row["valid_discount_rate"] else " (unreliable)"
                axis.plot(
                    delay_range, curve, color=color, linestyle=style,
                    label=f"{model_name} fit, k={row['k']:.4f}{suffix}",
                )

        human_curve = fitted_indifference_curve(human_k, later_amount, delay_range)
        axis.plot(delay_range, human_curve, color="black", linestyle="--",
                  label=f"Human (Rachlin 1991), k={human_k}")
        axis.set_xlabel("Delay to later reward (months)")
        axis.set_ylabel(f"Indifference amount now (of ${later_amount} later)")
        axis.set_title(f"option_order={option_order}")
        axis.legend(fontsize=6, loc="upper right")
        axis.set_ylim(bottom=0)

    figure.suptitle(
        f"Collapsed: all personas + persona-off [{mode_label}]",
        fontsize=12,
    )
    figure.tight_layout()
    out_path = figures_dir / "discount_curves_by_model_all_personas.png"
    figure.savefig(out_path, dpi=150)
    plt.close(figure)
    return out_path


def plot_cluster2_curves(
    comparison_df: pd.DataFrame,
    indifference_records: list[dict],
    config: dict,
    figures_dir: Path,
    reasoning_mode: str = "direct",
) -> Path | None:
    if comparison_df.empty:
        return None

    later_amount = config["waiting_game"]["later_amount_dollars"]
    delay_grid = config["waiting_game"]["delay_grid_months"]
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]
    delay_range = np.linspace(min(delay_grid), max(delay_grid), 200)
    indiff_df = pd.DataFrame(indifference_records)

    # One panel per option_order; within panel, models × greater/lesser
    order_levels = [label for label, _ in OPTION_ORDER_STRATA
                    if label in set(comparison_df["option_order"])]
    figure, axes = plt.subplots(1, len(order_levels), figsize=(6.0 * len(order_levels), 5.8),
                                squeeze=False)
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
    models = list(dict.fromkeys(comparison_df["model_name"]))

    for order_index, option_order in enumerate(order_levels):
        axis = axes[0][order_index]
        order_comp = comparison_df[comparison_df["option_order"] == option_order]
        for model_index, model_name in enumerate(models):
            model_color = MODEL_COLORS[model_index % len(MODEL_COLORS)]
            for group_name in ("greater", "lesser"):
                sub = order_comp[
                    (order_comp["model_name"] == model_name)
                    & (order_comp["stratum_value"] == group_name)
                ]
                if sub.empty:
                    continue
                row = sub.iloc[0]
                pts = indiff_df[
                    (indiff_df["model_name"] == model_name)
                    & (indiff_df["option_order"] == option_order)
                    & (indiff_df["stratum_value"] == group_name)
                ]
                marker = "o" if group_name == "greater" else "s"
                group_edge = DISCOUNTING_GROUP_COLORS.get(group_name, model_color)
                if not pts.empty:
                    axis.plot(
                        pts["delay_months"], pts["indifference_amount"],
                        color=model_color, marker=marker, linestyle="none",
                        markeredgecolor=group_edge, markeredgewidth=1.2,
                        label=f"{model_name} / {group_name} (50%)", zorder=3,
                    )
                if not pd.isna(row["k"]):
                    curve = fitted_indifference_curve(row["k"], later_amount, delay_range)
                    style = "-" if group_name == "greater" else "--"
                    if not row["valid_discount_rate"]:
                        style = ":"
                    suffix = "" if row["valid_discount_rate"] else " (unreliable)"
                    axis.plot(
                        delay_range, curve, color=model_color, linestyle=style,
                        label=f"{model_name} / {group_name} k={row['k']:.4f}{suffix}",
                    )

        human_curve = fitted_indifference_curve(human_k, later_amount, delay_range)
        axis.plot(delay_range, human_curve, color="black", linestyle="-.",
                  label=f"Human (Rachlin 1991), k={human_k}")
        axis.set_xlabel("Delay to later reward (months)")
        axis.set_ylabel(f"Indifference amount now (of ${later_amount} later)")
        axis.set_title(f"option_order={option_order}")
        axis.legend(fontsize=5.5, loc="upper right")
        axis.set_ylim(bottom=0)

    figure.suptitle(
        f"Collapsed within greater / lesser personas [{mode_label}]",
        fontsize=12,
    )
    figure.tight_layout()
    out_path = figures_dir / "discount_curves_by_model_discounting_group.png"
    figure.savefig(out_path, dpi=150)
    plt.close(figure)
    return out_path


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument(
        "--mode-suffix",
        default="",
        help='Filename mode suffix; "" for direct, "__cot" for chain-of-thought.',
    )
    arg_parser.add_argument(
        "--also-all",
        action="store_true",
        help="Also recompute unrestricted all-persona collapses (slower).",
    )
    arg_parser.add_argument(
        "--by-condition",
        default="results/summary/by_condition.csv",
        help="Competence table used to gate competent-only collapses.",
    )
    args = arg_parser.parse_args()

    config = load_config(args.config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    out_dir = Path(resolve_dir_path("results/analysis_collapsed_clusters"))
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    choices_df = load_combined_choices(processed_dir, args.mode_suffix)
    models = list(config["models"])
    present = set(choices_df["model_name"].unique())
    models = [m for m in models if m in present]
    models.extend(sorted(present - set(models)))

    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]
    competent_df = load_competent_condition_keys(args.by_condition)
    zero_success = [
        m for m in models
        if not (competent_df["model_name"] == m).any()
    ]
    print(
        f"Competent cells loaded: {len(competent_df)} "
        f"(models with ≥1: {len(models) - len(zero_success)}; "
        f"with 0: {len(zero_success)})"
    )

    print("\n=== Competent-only Cluster 1: model × order ===")
    all_c, all_c_indiff = fit_cluster_rows(
        choices_df, models, config, cluster1_builder, competent_df=competent_df
    )
    all_c = sort_result_df(all_c)

    persona_on = (
        choices_df[choices_df["persona_discounting_group"].notna()].copy()
        if "persona_discounting_group" in choices_df.columns
        else choices_df.iloc[0:0]
    )
    print("\n=== Competent-only Cluster 2: model × greater/lesser × order ===")
    group_c, group_c_indiff = fit_cluster_rows(
        persona_on, models, config, cluster2_builder, competent_df=competent_df
    )
    group_c = sort_result_df(group_c)

    all_c_path = out_dir / "by_model_competent.csv"
    group_c_path = out_dir / "by_model_discounting_group_competent.csv"
    all_c.to_csv(all_c_path, index=False)
    group_c.to_csv(group_c_path, index=False)
    print(f"\nWrote {all_c_path}")
    print(f"Wrote {group_c_path}")

    summary_c = build_summary_markdown(
        all_c, group_c, human_k,
        competent_only=True,
        zero_success_models=zero_success,
    )
    summary_c_path = out_dir / "summary_competent.md"
    summary_c_path.write_text(summary_c, encoding="utf-8")
    print(f"Wrote {summary_c_path}")

    fig1c = plot_cluster1_curves(
        all_c, all_c_indiff, config, figures_dir, reasoning_mode="direct"
    )
    if fig1c:
        # Rename default figure names for competent-only
        dest1 = figures_dir / "discount_curves_by_model_competent.png"
        Path(fig1c).replace(dest1)
        print(f"Wrote {dest1}")
    fig2c = plot_cluster2_curves(
        group_c, group_c_indiff, config, figures_dir, reasoning_mode="direct"
    )
    if fig2c:
        dest2 = figures_dir / "discount_curves_by_model_discounting_group_competent.png"
        Path(fig2c).replace(dest2)
        print(f"Wrote {dest2}")

    if all_c_indiff:
        pd.DataFrame(all_c_indiff).to_csv(
            out_dir / "indifference_by_model_competent.csv", index=False
        )
    if group_c_indiff:
        pd.DataFrame(group_c_indiff).to_csv(
            out_dir / "indifference_by_model_discounting_group_competent.csv",
            index=False,
        )

    if args.also_all:
        print("\n=== Cluster 1: by model, collapse all personas + persona-off ===")
        all_df, all_indiff = fit_cluster_rows(
            choices_df, models, config, cluster1_builder
        )
        all_df = sort_result_df(all_df)

        print("\n=== Cluster 2: by model × greater/lesser (personas within group) ===")
        group_df, group_indiff = fit_cluster_rows(
            persona_on, models, config, cluster2_builder
        )
        group_df = sort_result_df(group_df)

        all_path = out_dir / "by_model_all_personas.csv"
        group_path = out_dir / "by_model_discounting_group.csv"
        all_df.to_csv(all_path, index=False)
        group_df.to_csv(group_path, index=False)
        print(f"\nWrote {all_path}")
        print(f"Wrote {group_path}")

        summary_md = build_summary_markdown(all_df, group_df, human_k)
        summary_path = out_dir / "summary.md"
        summary_path.write_text(summary_md, encoding="utf-8")
        print(f"Wrote {summary_path}")

        fig1 = plot_cluster1_curves(all_df, all_indiff, config, figures_dir)
        if fig1:
            print(f"Wrote {fig1}")
        fig2 = plot_cluster2_curves(group_df, group_indiff, config, figures_dir)
        if fig2:
            print(f"Wrote {fig2}")

        if all_indiff:
            pd.DataFrame(all_indiff).to_csv(
                out_dir / "indifference_by_model_all_personas.csv", index=False
            )
        if group_indiff:
            pd.DataFrame(group_indiff).to_csv(
                out_dir / "indifference_by_model_discounting_group.csv", index=False
            )


if __name__ == "__main__":
    main()
