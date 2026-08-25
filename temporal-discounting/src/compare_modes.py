"""Cross-mode comparison: aggregates comparison_summary{mode}.csv across
every reasoning mode that has been run (direct / cot / one_shot / two_shot),
to test whether prompting interventions change competence-check pass rates
or hyperbolic-fit reliability for each model.

Motivation (see PREREGISTRATION.md "Exploratory extension"): Ross, Kim & Lo
(2024) sec. 4 found that, for GPT-4's risk/loss aversion in their gambling
game, direct prompting and zero-shot CoT often failed to reliably elicit the
intended economic behavior, while one-shot prompting was more effective
(two-shot showed mixed results). This script lets us check whether the same
pattern holds for our local Qwen models' time-discounting *competence*
(monotonicity + money preference) in the waiting game -- an extrapolation the
original paper did not itself test.

Usage: python src/compare_modes.py [--config path/to/config.yaml]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import load_config, resolve_dir_path, mode_suffix
from run_experiment import REASONING_MODES

MODE_DISPLAY_LABELS = {
    "direct": "direct",
    "cot": "chain-of-thought",
    "one_shot": "one-shot",
    "two_shot": "two-shot",
}
MODE_COLORS = {
    "direct": "#1f77b4",
    "cot": "#ff7f0e",
    "one_shot": "#2ca02c",
    "two_shot": "#d62728",
}
MODE_SORT_ORDER = {mode: index for index, mode in enumerate(REASONING_MODES)}


def checkmark(is_true):
    return "\u2705" if bool(is_true) else "\u274c"


def format_k_with_ci(row):
    if pd.isna(row["k"]):
        return "-"
    return f"{row['k']:.4f} [{row['k_ci_low']:.4f}, {row['k_ci_high']:.4f}]"


def build_sanity_check_markdown(combined_df, human_k):
    """One presentable Markdown table with every sanity check (competence
    gate + fit-reliability gate) side by side, across every model x mode
    that has been run, sorted model-major / mode-minor for easy scanning.
    """
    sortable_df = combined_df.copy()
    sortable_df["_mode_order"] = sortable_df["reasoning_mode"].map(MODE_SORT_ORDER)
    sortable_df = sortable_df.sort_values(["model_name", "_mode_order"])

    header = (
        "| Model | Mode | Monotonicity | Money Pref. | Competence Pass | "
        "Beta (choice sens.) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |"
    )
    separator = "|---|---|---|---|---|---|---|---|---|"
    rows = [header, separator]
    for _, row in sortable_df.iterrows():
        mode_label = MODE_DISPLAY_LABELS.get(row["reasoning_mode"], row["reasoning_mode"])
        rows.append(
            f"| {row['model_name']} | {mode_label} | {checkmark(row['monotonicity_passed'])} | "
            f"{checkmark(row['money_preference_passed'])} | {checkmark(row['overall_passed'])} | "
            f"{row['beta']:.4f} | {checkmark(row['k_is_reliable'])} | "
            f"**{checkmark(row['valid_discount_rate'])}** | {format_k_with_ci(row)} |"
        )
    table_markdown = "\n".join(rows)

    modes_present = ", ".join(MODE_DISPLAY_LABELS.get(m, m) for m in sortable_df["reasoning_mode"].unique())
    legend = f"""# Waiting Game: Sanity Check Summary

Modes included: {modes_present}. Human benchmark (Rachlin et al. 1991): k = {human_k} per month.

{table_markdown}

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay (`competence_checks.py::check_monotonicity`).
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay (`check_money_preference`).
- **Competence Pass**: Monotonicity AND Money Pref. both pass (`overall_passed`).
- **Beta (choice sens.)**: fitted logistic sensitivity of choices to the amount/delay tradeoff; values below 0.05 mean choices barely track option value at all, so any fitted k is statistically unidentifiable (`fit_discounting.py::LOW_SENSITIVITY_BETA_THRESHOLD`).
- **k Reliable?**: beta >= 0.05 AND fitted k did not land at the optimizer's boundary (1e-6 or 10.0).
- **Valid Discount Rate**: Competence Pass AND k Reliable \u2014 the single bottom-line flag for whether the fitted k should be trusted at all.
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI, shown regardless of reliability (compare against the "k Reliable?"/"Valid Discount Rate" columns before interpreting).
"""
    return legend


def load_available_mode_tables(tables_dir, modes):
    """Loads comparison_summary{mode}.csv for every mode that has already
    been run through analyze.py. Modes with no output yet are skipped (not
    an error), since this script is meant to be re-run incrementally as more
    modes finish.
    """
    mode_tables = {}
    for reasoning_mode in modes:
        csv_path = os.path.join(tables_dir, f"comparison_summary{mode_suffix(reasoning_mode)}.csv")
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
            mode_df.loc[m, "k"] if (m in mode_df.index and bool(mode_df.loc[m, "valid_discount_rate"])) else np.nan
            for m in model_names
        ]
        axis_k.bar(x_positions, k_values, width=bar_width, color=color, label=label)

    axis_competence.set_xticks(np.arange(n_models))
    axis_competence.set_xticklabels(model_names, rotation=20, ha="right")
    axis_competence.set_ylim(-0.1, 1.1)
    axis_competence.set_ylabel("Valid discount rate (competence-checks pass AND k reliable)")
    axis_competence.set_title("Does prompting yield a valid hyperbolic fit?")
    axis_competence.legend(fontsize=8)

    axis_k.axhline(human_k, color="black", linestyle="--", linewidth=1, label=f"human benchmark k={human_k}")
    axis_k.set_xticks(np.arange(n_models))
    axis_k.set_xticklabels(model_names, rotation=20, ha="right")
    axis_k.set_ylabel("Fitted k per month (only shown where valid_discount_rate=True)")
    axis_k.set_title("Fitted hyperbolic discount rate by mode")
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
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]

    mode_tables = load_available_mode_tables(tables_dir, REASONING_MODES)
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
        "model_name", "reasoning_mode", "monotonicity_passed", "money_preference_passed",
        "k_is_reliable", "valid_discount_rate", "k",
    ]].sort_values(["model_name", "reasoning_mode"]).to_string(index=False))
    print(f"\nWrote combined table to {combined_csv_path}")

    figure_path = plot_competence_and_k_by_mode(combined_df, list(mode_tables.keys()), human_k, figures_dir)
    print(f"Wrote mode-comparison plot to {figure_path}")

    sanity_check_markdown = build_sanity_check_markdown(combined_df, human_k)
    sanity_check_path = os.path.join(tables_dir, "sanity_check_summary.md")
    with open(sanity_check_path, "w") as markdown_file:
        markdown_file.write(sanity_check_markdown)
    print(f"Wrote presentable sanity-check summary table to {sanity_check_path}")


if __name__ == "__main__":
    main()
