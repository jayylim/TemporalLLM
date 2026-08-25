"""Ties together competence checks + fitted discount rates into one
comparison table, and plots discount curves (indifference amount vs delay)
against the Rachlin et al. (1991) human benchmark.

Usage: python src/analyze.py [--config path/to/config.yaml]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import load_config, resolve_dir_path, mode_suffix
from competence_checks import compute_p_sooner_table
from fit_discounting import hyperbolic_value
from run_experiment import REASONING_MODES

MODEL_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

MODE_DISPLAY_LABELS = {
    "direct": "direct",
    "cot": "chain-of-thought",
    "one_shot": "one-shot",
    "two_shot": "two-shot",
}


def build_comparison_table(fit_df, competence_df):
    comparison_df = fit_df.merge(competence_df, on="model_name", how="left")
    comparison_df["valid_discount_rate"] = (
        comparison_df["overall_passed"] & comparison_df["k_is_reliable"]
    )
    return comparison_df


def empirical_indifference_amounts(model_choices_df, delay_grid_months):
    """For each delay, linearly interpolates the sooner amount x at which
    P(choose sooner) = 0.5, from the empirical per-cell probabilities.
    Caveat: this inversion assumes P(sooner) is increasing in x; if a model
    fails the monotonicity competence check the result is only approximate.
    """
    p_sooner_table = compute_p_sooner_table(model_choices_df)
    amount_grid = np.sort(p_sooner_table.columns.values)

    indifference_amount_by_delay = {}
    for delay_months in delay_grid_months:
        if delay_months not in p_sooner_table.index:
            continue
        p_sooner_values = p_sooner_table.loc[delay_months, amount_grid].values
        indifference_amount_by_delay[delay_months] = np.interp(0.5, p_sooner_values, amount_grid)
    return indifference_amount_by_delay


def fitted_indifference_curve(k, later_amount_dollars, delay_range_months):
    """x*(d) solving amount = later_amount / (1 + k*d) at indifference (V_sooner == V_later)."""
    return hyperbolic_value(later_amount_dollars, delay_range_months, k)


def plot_discount_curves(choices_df, comparison_df, config, figures_dir, suffix="", reasoning_mode="direct"):
    later_amount_dollars = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]

    delay_range_months = np.linspace(min(delay_grid_months), max(delay_grid_months), 200)

    figure, axis = plt.subplots(figsize=(8, 6))

    for model_index, row in comparison_df.iterrows():
        model_name = row["model_name"]
        model_color = MODEL_COLORS[model_index % len(MODEL_COLORS)]
        model_choices_df = choices_df[choices_df["model_name"] == model_name]

        empirical_points = empirical_indifference_amounts(model_choices_df, delay_grid_months)
        axis.scatter(
            list(empirical_points.keys()), list(empirical_points.values()),
            color=model_color, label=f"{model_name} (empirical)", zorder=3,
        )

        fitted_curve = fitted_indifference_curve(row["k"], later_amount_dollars, delay_range_months)
        line_style = "-" if row["valid_discount_rate"] else ":"
        fit_label_suffix = "" if row["valid_discount_rate"] else " (fit unreliable)"
        axis.plot(
            delay_range_months, fitted_curve,
            color=model_color, linestyle=line_style,
            label=f"{model_name} fit, k={row['k']:.4f}{fit_label_suffix}",
        )

    human_benchmark_curve = fitted_indifference_curve(human_k, later_amount_dollars, delay_range_months)
    axis.plot(
        delay_range_months, human_benchmark_curve,
        color="black", linestyle="--",
        label=f"Human benchmark (Rachlin et al. 1991), k={human_k}",
    )

    axis.set_xlabel("Delay to later reward (months)")
    axis.set_ylabel(f"Indifference amount now (of ${later_amount_dollars} later)")
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
    axis.set_title(f"Waiting Game: discount curves by model [{mode_label}]")
    axis.legend(fontsize=8, loc="upper right")
    figure.tight_layout()

    figure_path = os.path.join(figures_dir, f"discount_curves{suffix}.png")
    figure.savefig(figure_path, dpi=150)
    plt.close(figure)
    return figure_path


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    suffix = mode_suffix(args.mode)

    choices_df = pd.read_csv(os.path.join(processed_dir, f"choices{suffix}.csv"))
    fit_df = pd.read_csv(os.path.join(tables_dir, f"discount_rates{suffix}.csv"))
    competence_df = pd.read_csv(os.path.join(tables_dir, f"competence_checks{suffix}.csv"))

    comparison_df = build_comparison_table(fit_df, competence_df)
    comparison_csv_path = os.path.join(tables_dir, f"comparison_summary{suffix}.csv")
    comparison_df.to_csv(comparison_csv_path, index=False)

    print("\n=== Cross-model comparison ===")
    print(comparison_df[[
        "model_name", "k", "k_ci_low", "k_ci_high", "beta",
        "monotonicity_passed", "money_preference_passed", "k_is_reliable", "valid_discount_rate",
    ]].to_string(index=False))
    print(f"\nWrote comparison table to {comparison_csv_path}")

    figure_path = plot_discount_curves(choices_df, comparison_df, config, figures_dir, suffix, args.mode)
    print(f"Wrote discount-curve plot to {figure_path}")


if __name__ == "__main__":
    main()
