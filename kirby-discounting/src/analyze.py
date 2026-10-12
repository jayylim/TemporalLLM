"""Ties together competence checks + fitted discount rates into one
comparison table, and plots normalized hyperbolic discount curves (fraction
of value retained vs delay) against an approximate Kirby-27 human benchmark.
Kirby analogue of ../temporal-discounting/src/analyze.py.

Usage: python src/analyze.py [--config path/to/config.yaml]
       [--mode direct|cot] [--persona|--no-persona]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import (
    load_config,
    resolve_dir_path,
    kirby_result_suffix,
    persona_enabled_from_config,
)
from fit_discounting import hyperbolic_value
from run_experiment import REASONING_MODES

MODEL_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22",
]

MODE_DISPLAY_LABELS = {
    "direct": "direct",
    "cot": "chain-of-thought",
}

DISCOUNTING_GROUP_COLORS = {
    "greater": "#d62728",
    "lesser": "#2ca02c",
}


def merge_keys(fit_df, competence_df):
    keys = ["model_name"]
    for optional in ("persona_enabled", "persona_id", "persona_discounting_group"):
        if optional in fit_df.columns and optional in competence_df.columns:
            keys.append(optional)
    return keys


def build_comparison_table(fit_df, competence_df):
    competence_extra = competence_df.copy()
    for maybe_dup in ("persona_label",):
        if maybe_dup in fit_df.columns and maybe_dup in competence_extra.columns:
            competence_extra = competence_extra.drop(columns=[maybe_dup])
    comparison_df = fit_df.merge(
        competence_extra,
        on=merge_keys(fit_df, competence_df),
        how="left",
    )
    comparison_df["valid_discount_rate"] = (
        comparison_df["overall_passed"] & comparison_df["logistic_k_is_reliable"]
    )
    return comparison_df


def _has_persona_ids(df):
    return "persona_id" in df.columns and df["persona_id"].notna().any()


def plot_discount_curves(comparison_df, config, figures_dir, suffix="", reasoning_mode="direct"):
    if _has_persona_ids(comparison_df):
        return plot_discount_curves_by_persona(
            comparison_df, config, figures_dir, suffix, reasoning_mode
        )

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


def plot_discount_curves_by_persona(comparison_df, config, figures_dir, suffix, reasoning_mode):
    """One figure per model; overlay personas colored by discounting_group."""
    human_k = config["human_benchmark"]["kirby_median_k_per_day"]
    delay_range_days = np.linspace(0, 190, 200)
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
    human_curve = hyperbolic_value(1.0, delay_range_days, human_k)

    written = []
    for model_name, model_df in comparison_df.groupby("model_name", sort=False):
        figure, (axis_geomean, axis_logistic) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
        for _, row in model_df.iterrows():
            group = row.get("persona_discounting_group")
            color = DISCOUNTING_GROUP_COLORS.get(group, "#1f77b4")
            label = row.get("persona_label") or row.get("persona_id") or "persona"
            geomean_style = "-" if row["consistency_passed"] else ":"
            logistic_style = "-" if row["valid_discount_rate"] else ":"
            axis_geomean.plot(
                delay_range_days,
                hyperbolic_value(1.0, delay_range_days, row["geomean_k"]),
                color=color, linestyle=geomean_style,
                label=f"{label}, geomean k={row['geomean_k']:.5f}",
            )
            axis_logistic.plot(
                delay_range_days,
                hyperbolic_value(1.0, delay_range_days, row["logistic_k"]),
                color=color, linestyle=logistic_style,
                label=f"{label}, logistic k={row['logistic_k']:.5f}",
            )

        for axis, title in ((axis_geomean, "Hand-scoring geomean k"),
                             (axis_logistic, "Probabilistic logistic k")):
            axis.plot(delay_range_days, human_curve, color="black", linestyle="--",
                      label=f"human benchmark k={human_k}")
            axis.set_xlabel("Delay (days)")
            axis.set_title(title)
            axis.legend(fontsize=6, loc="upper right")
        axis_geomean.set_ylabel("Fraction of value retained: 1 / (1 + k * delay)")
        figure.suptitle(
            f"Kirby MCQ-27: {model_name} personas [{mode_label}]", fontsize=13
        )
        figure.tight_layout()
        figure_path = os.path.join(
            figures_dir, f"discount_curves{suffix}__{safe_model_fragment(model_name)}.png"
        )
        figure.savefig(figure_path, dpi=150)
        plt.close(figure)
        written.append(figure_path)
    return written[0] if len(written) == 1 else written


def safe_model_fragment(model_name):
    return model_name.replace(":", "__").replace("/", "__")


def resolve_persona_enabled(args, config):
    if getattr(args, "persona", False):
        return True
    if getattr(args, "no_persona", False):
        return False
    return persona_enabled_from_config(config)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct")
    persona_group = arg_parser.add_mutually_exclusive_group()
    persona_group.add_argument("--persona", action="store_true")
    persona_group.add_argument("--no-persona", action="store_true")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    persona_enabled = resolve_persona_enabled(args, config)
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    suffix = kirby_result_suffix(args.mode, persona_enabled, config["kirby"]["variant"])

    fit_df = pd.read_csv(os.path.join(tables_dir, f"discount_rates{suffix}.csv"))
    competence_df = pd.read_csv(os.path.join(tables_dir, f"competence_checks{suffix}.csv"))

    comparison_df = build_comparison_table(fit_df, competence_df)
    comparison_csv_path = os.path.join(tables_dir, f"comparison_summary{suffix}.csv")
    comparison_df.to_csv(comparison_csv_path, index=False)

    display_cols = ["model_name"]
    for optional in ("persona_id", "persona_label", "persona_discounting_group"):
        if optional in comparison_df.columns:
            display_cols.append(optional)
    display_cols.extend([
        "geomean_k", "small_k", "medium_k", "large_k", "overall_consistency",
        "logistic_k", "logistic_k_ci_low", "logistic_k_ci_high", "logistic_beta",
        "rank_monotonicity_passed", "consistency_passed", "logistic_k_is_reliable",
        "valid_discount_rate",
    ])

    print("\n=== Cross-model comparison ===")
    print(comparison_df[[c for c in display_cols if c in comparison_df.columns]].to_string(index=False))
    print(f"\nWrote comparison table to {comparison_csv_path}")

    figure_path = plot_discount_curves(comparison_df, config, figures_dir, suffix, args.mode)
    print(f"Wrote discount-curve plot to {figure_path}")


if __name__ == "__main__":
    main()
