"""Cross-mode comparison: aggregates comparison_summary{mode}.csv across
every reasoning mode that has been run, and writes a presentable
sanity-check summary table -- Kirby analogue of
../temporal-discounting/src/compare_modes.py.

Usage: python src/compare_modes.py [--config path/to/config.yaml]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import load_config, resolve_dir_path, mode_suffix, variant_suffix
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


def checkmark(is_true):
    return "\u2705" if bool(is_true) else "\u274c"


def format_k_with_ci(row):
    if pd.isna(row["logistic_k"]):
        return "-"
    return f"{row['logistic_k']:.5f} [{row['logistic_k_ci_low']:.5f}, {row['logistic_k_ci_high']:.5f}]"


def build_sanity_check_markdown(combined_df, human_k, variant):
    sortable_df = combined_df.copy()
    sortable_df["_mode_order"] = sortable_df["reasoning_mode"].map(MODE_SORT_ORDER)
    sortable_df = sortable_df.sort_values(["model_name", "_mode_order"])

    header = (
        "| Model | Mode | Rank Monotonicity | Consistency | Consistency Pass | "
        "Magnitude Effect | logistic beta | logistic k Reliable? | **Valid Discount Rate** | "
        "geomean k | logistic k [95% CI] |"
    )
    separator = "|---|---|---|---|---|---|---|---|---|---|---|"
    rows = [header, separator]
    for _, row in sortable_df.iterrows():
        mode_label = MODE_DISPLAY_LABELS.get(row["reasoning_mode"], row["reasoning_mode"])
        magnitude_effect_cell = (
            checkmark(row["magnitude_effect_holds"]) if pd.notna(row["magnitude_effect_holds"]) else "n/a"
        )
        rows.append(
            f"| {row['model_name']} | {mode_label} | {checkmark(row['rank_monotonicity_passed'])} | "
            f"{row['overall_consistency']:.1%} | {checkmark(row['consistency_passed'])} | "
            f"{magnitude_effect_cell} | {row['logistic_beta']:.4f} | {checkmark(row['logistic_k_is_reliable'])} | "
            f"**{checkmark(row['valid_discount_rate'])}** | {row['geomean_k']:.5f} | {format_k_with_ci(row)} |"
        )
    table_markdown = "\n".join(rows)

    modes_present = ", ".join(MODE_DISPLAY_LABELS.get(m, m) for m in sortable_df["reasoning_mode"].unique())
    legend = f"""# Kirby MCQ-27: Sanity Check Summary

Modes included: {modes_present}. Item variant: {variant}. Approx. human benchmark (Kirby, Petry & Bickel 1999 / Kirby 2009 population norms): k = {human_k} per day.

{table_markdown}

## Column definitions

- **Rank Monotonicity**: sorting the 27 items by their own indifference k, P(choose larger-delayed reward) does not *decrease* along that ordering by more than tolerance, for more than the allowed violations (`competence_checks.py::check_rank_monotonicity`) -- the Kirby analogue of the Waiting Game's grid-monotonicity check.
- **Consistency**: fraction of the 27 items whose binarized modal choice matches the best-fit candidate k (Kirby, 2000 / Kaplan et al. 2016 hand-scoring method).
- **Consistency Pass**: Consistency >= 75% (Kaplan et al. 2016 convention).
- **Magnitude Effect**: does `small_k > medium_k > large_k` hold (the classic human "more patience for larger rewards" pattern)? Reported, not gating.
- **logistic beta**: fitted logistic sensitivity of choices to the SIR/LDR/delay tradeoff (probabilistic-logistic MLE method); values below 0.05 mean choices barely track option value at all, so any fitted k is statistically unidentifiable.
- **logistic k Reliable?**: beta >= 0.05 AND fitted k did not land at the optimizer's bound.
- **Valid Discount Rate**: Rank Monotonicity Pass AND Consistency Pass AND logistic k Reliable -- the single bottom-line flag for whether either fitted k should be trusted at all.
- **geomean k**: hand-scoring composite k = geometric mean of small_k/medium_k/large_k, directly comparable to published human percentile norms.
- **logistic k [95% CI]**: MLE-fit discount rate per day (bootstrap 95% CI), from the probabilistic logistic method, shown regardless of reliability.
"""
    return legend


def load_available_mode_tables(tables_dir, modes, variant_suffix_str):
    mode_tables = {}
    for reasoning_mode in modes:
        csv_path = os.path.join(tables_dir, f"comparison_summary{mode_suffix(reasoning_mode)}{variant_suffix_str}.csv")
        if not os.path.exists(csv_path):
            print(f"[{reasoning_mode}] no comparison_summary found at {csv_path}, skipping "
                  f"(run analyze.py --mode {reasoning_mode} first).")
            continue
        mode_df = pd.read_csv(csv_path)
        mode_df["reasoning_mode"] = reasoning_mode
        mode_tables[reasoning_mode] = mode_df
    return mode_tables


def plot_competence_and_k_by_mode(combined_df, modes_present, human_k, figures_dir):
    model_names = sorted(combined_df["model_name"].unique())
    n_models = len(model_names)
    n_modes = len(modes_present)
    bar_width = 0.8 / max(n_modes, 1)

    figure, (axis_competence, axis_k) = plt.subplots(1, 2, figsize=(14, 5.5))

    for mode_index, reasoning_mode in enumerate(modes_present):
        mode_df = combined_df[combined_df["reasoning_mode"] == reasoning_mode].set_index("model_name")
        x_positions = np.arange(n_models) + (mode_index - (n_modes - 1) / 2) * bar_width
        color = MODE_COLORS.get(reasoning_mode, None)
        label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)

        valid_discount_rate = [
            float(mode_df.loc[m, "valid_discount_rate"]) if m in mode_df.index else np.nan
            for m in model_names
        ]
        axis_competence.bar(x_positions, valid_discount_rate, width=bar_width, color=color, label=label)

        k_values = [
            mode_df.loc[m, "geomean_k"] if (m in mode_df.index and bool(mode_df.loc[m, "consistency_passed"])) else np.nan
            for m in model_names
        ]
        axis_k.bar(x_positions, k_values, width=bar_width, color=color, label=label)

    axis_competence.set_xticks(np.arange(n_models))
    axis_competence.set_xticklabels(model_names, rotation=20, ha="right")
    axis_competence.set_ylim(-0.1, 1.1)
    axis_competence.set_ylabel("Valid discount rate (all gates pass)")
    axis_competence.set_title("Does prompting yield a valid Kirby-27 fit?")
    axis_competence.legend(fontsize=8)

    axis_k.axhline(human_k, color="black", linestyle="--", linewidth=1, label=f"human benchmark k={human_k}")
    axis_k.set_xticks(np.arange(n_models))
    axis_k.set_xticklabels(model_names, rotation=20, ha="right")
    axis_k.set_ylabel("geomean k per day (only shown where consistency_passed=True)")
    axis_k.set_title("Hand-scoring geomean discount rate by mode")
    axis_k.legend(fontsize=8)

    figure.suptitle("Effect of reasoning mode on Kirby MCQ-27 results")
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
    human_k = config["human_benchmark"]["kirby_median_k_per_day"]
    variant_suffix_str = variant_suffix(config["kirby"]["variant"])

    mode_tables = load_available_mode_tables(tables_dir, REASONING_MODES, variant_suffix_str)
    if not mode_tables:
        print("No comparison_summary tables found for any mode. Run the pipeline (run_experiment.py -> "
              "parse_responses.py -> competence_checks.py -> fit_discounting.py -> analyze.py) for at "
              "least one --mode first.")
        return

    combined_df = pd.concat(mode_tables.values(), ignore_index=True)
    combined_csv_path = os.path.join(tables_dir, "comparison_summary_by_mode.csv")
    combined_df.to_csv(combined_csv_path, index=False)

    print(f"\n=== Cross-mode comparison ({', '.join(mode_tables.keys())}) ===")
    print(combined_df[[
        "model_name", "reasoning_mode", "rank_monotonicity_passed", "consistency_passed",
        "logistic_k_is_reliable", "valid_discount_rate", "geomean_k", "logistic_k",
    ]].sort_values(["model_name", "reasoning_mode"]).to_string(index=False))
    print(f"\nWrote combined table to {combined_csv_path}")

    figure_path = plot_competence_and_k_by_mode(combined_df, list(mode_tables.keys()), human_k, figures_dir)
    print(f"Wrote mode-comparison plot to {figure_path}")

    sanity_check_markdown = build_sanity_check_markdown(combined_df, human_k, config["kirby"]["variant"])
    sanity_check_path = os.path.join(tables_dir, "sanity_check_summary.md")
    with open(sanity_check_path, "w") as markdown_file:
        markdown_file.write(sanity_check_markdown)
    print(f"Wrote presentable sanity-check summary table to {sanity_check_path}")


if __name__ == "__main__":
    main()
