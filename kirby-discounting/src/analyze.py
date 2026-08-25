"""Ties together competence checks + fitted discount rates into one
comparison table, and plots normalized hyperbolic discount curves (fraction
of value retained vs delay) against an approximate Kirby-27 human benchmark.
Kirby analogue of ../temporal-discounting/src/analyze.py.

Usage: python src/analyze.py [--config path/to/config.yaml] [--mode direct|cot|one_shot|two_shot]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import load_config, resolve_dir_path, mode_suffix, variant_suffix
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
        comparison_df["overall_passed"] & comparison_df["logistic_k_is_reliable"]
    )
    return comparison_df


def plot_discount_curves(comparison_df, config, figures_dir, suffix="", reasoning_mode="direct"):
    human_k = config["human_benchmark"]["kirby_median_k_per_day"]
    max_delay_days = 190
    delay_range_days = np.linspace(0, max_delay_days, 200)

    figure, (axis_geomean, axis_logistic) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    for model_index, row in comparison_df.iterrows():
        model_name = row["model_name"]
        model_color = MODEL_COLORS[model_index % len(MODEL_COLORS)]

        geomean_line_style = "-" if row["consistency_passed"] else ":"
        geomean_curve = hyperbolic_value(1.0, delay_range_days, row["geomean_k"])
        axis_geomean.plot(
            delay_range_days, geomean_curve, color=model_color, linestyle=geomean_line_style,
            label=f"{model_name}, geomean k={row['geomean_k']:.5f}"
            + ("" if row["consistency_passed"] else " (low consistency)"),
        )

        logistic_line_style = "-" if row["valid_discount_rate"] else ":"
        logistic_curve = hyperbolic_value(1.0, delay_range_days, row["logistic_k"])
        axis_logistic.plot(
            delay_range_days, logistic_curve, color=model_color, linestyle=logistic_line_style,
            label=f"{model_name}, logistic k={row['logistic_k']:.5f}"
            + ("" if row["valid_discount_rate"] else " (unreliable)"),
        )

    human_curve = hyperbolic_value(1.0, delay_range_days, human_k)
    for axis, title in ((axis_geomean, "Hand-scoring method (geomean of small/medium/large k)"),
                         (axis_logistic, "Probabilistic logistic method (MLE k)")):
        axis.plot(delay_range_days, human_curve, color="black", linestyle="--",
                  label=f"Approx. human benchmark, k={human_k}")
        axis.set_xlabel("Delay (days)")
        axis.set_title(title)
        axis.legend(fontsize=7, loc="upper right")

    axis_geomean.set_ylabel("Fraction of value retained: 1 / (1 + k * delay)")
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
    figure.suptitle(f"Kirby MCQ-27: discount curves by model [{mode_label}]", fontsize=13)
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
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    suffix = mode_suffix(args.mode) + variant_suffix(config["kirby"]["variant"])

    fit_df = pd.read_csv(os.path.join(tables_dir, f"discount_rates{suffix}.csv"))
    competence_df = pd.read_csv(os.path.join(tables_dir, f"competence_checks{suffix}.csv"))

    comparison_df = build_comparison_table(fit_df, competence_df)
    comparison_csv_path = os.path.join(tables_dir, f"comparison_summary{suffix}.csv")
    comparison_df.to_csv(comparison_csv_path, index=False)

    print("\n=== Cross-model comparison ===")
    print(comparison_df[[
        "model_name", "geomean_k", "small_k", "medium_k", "large_k", "overall_consistency",
        "logistic_k", "logistic_k_ci_low", "logistic_k_ci_high", "logistic_beta",
        "rank_monotonicity_passed", "consistency_passed", "logistic_k_is_reliable", "valid_discount_rate",
    ]].to_string(index=False))
    print(f"\nWrote comparison table to {comparison_csv_path}")

    figure_path = plot_discount_curves(comparison_df, config, figures_dir, suffix, args.mode)
    print(f"Wrote discount-curve plot to {figure_path}")


if __name__ == "__main__":
    main()
