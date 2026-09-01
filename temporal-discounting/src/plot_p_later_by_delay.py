"""Plots P(choose larger-later) vs delay for Qwen models.

One subplot per Qwen model; each subplot overlays persona-off and persona-on
curves for a given reasoning/prompt mode.

Aggregates over the Waiting Game amount grid at each delay (competence-probe
$0 cells excluded). Larger-later = not choosing the sooner option.

Usage:
  python src/plot_p_later_by_delay.py [--config path/to/config.yaml]
                                      [--mode direct|cot|one_shot|two_shot]
                                      [--all-modes]
"""

import argparse
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from competence_checks import fit_grid_choices
from config_utils import load_config, resolve_dir_path, result_suffix
from run_experiment import REASONING_MODES

MODE_DISPLAY_LABELS = {
    "direct": "direct",
    "cot": "chain-of-thought",
    "one_shot": "one-shot",
    "two_shot": "two-shot",
}

PERSONA_SERIES = [
    (False, "Persona off", "#1f77b4", "-"),
    (True, "Persona on", "#d62728", "--"),
]


def is_qwen_model(model_name):
    return str(model_name).lower().startswith("qwen")


def compute_p_later_by_delay(choices_df):
    """Return DataFrame with columns model_name, delay_months, p_later, n_trials.

    P(larger-later) is the mean of (~chose_sooner) over parsed fit-grid trials,
    pooling across sooner amounts at each delay.
    """
    fit_df = fit_grid_choices(choices_df)
    parsed_df = fit_df.dropna(subset=["chose_sooner_option"]).copy()
    if parsed_df.empty:
        return pd.DataFrame(columns=["model_name", "delay_months", "p_later", "n_trials"])

    parsed_df["chose_later"] = (~parsed_df["chose_sooner_option"].astype(bool)).astype(float)
    grouped = (
        parsed_df.groupby(["model_name", "delay_months"], as_index=False)
        .agg(p_later=("chose_later", "mean"), n_trials=("chose_later", "size"))
    )
    return grouped.sort_values(["model_name", "delay_months"])


def load_choices_for_persona(processed_dir, reasoning_mode, persona_enabled):
    suffix = result_suffix(reasoning_mode, persona_enabled)
    csv_path = os.path.join(processed_dir, f"choices{suffix}.csv")
    if not os.path.exists(csv_path):
        return None, csv_path
    return pd.read_csv(csv_path), csv_path


def collect_qwen_summaries(processed_dir, reasoning_mode, model_order):
    """Load persona-off/on summaries and return (ordered_qwen_models, summaries_by_persona)."""
    summaries_by_persona = {}
    qwen_models_present = set()

    for persona_enabled, _, _, _ in PERSONA_SERIES:
        choices_df, csv_path = load_choices_for_persona(
            processed_dir, reasoning_mode, persona_enabled
        )
        if choices_df is None:
            summaries_by_persona[persona_enabled] = None
            continue
        summary_df = compute_p_later_by_delay(choices_df)
        summary_df = summary_df[summary_df["model_name"].map(is_qwen_model)]
        summaries_by_persona[persona_enabled] = summary_df
        qwen_models_present.update(summary_df["model_name"].tolist())

    ordered_models = [m for m in model_order if m in qwen_models_present and is_qwen_model(m)]
    ordered_models += sorted(m for m in qwen_models_present if m not in ordered_models)
    return ordered_models, summaries_by_persona


def plot_p_later_by_delay(processed_dir, figures_dir, model_order, reasoning_mode):
    """One subplot per Qwen model; persona-off and persona-on overlaid in each."""
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)
    ordered_models, summaries_by_persona = collect_qwen_summaries(
        processed_dir, reasoning_mode, model_order
    )

    if not ordered_models:
        print(f"[{reasoning_mode}] no Qwen choices found for either persona condition; skipped.")
        return None

    n_models = len(ordered_models)
    n_cols = min(3, n_models)
    n_rows = int(math.ceil(n_models / n_cols))
    figure, axes_grid = plt.subplots(
        n_rows, n_cols, figsize=(4.2 * n_cols, 3.4 * n_rows),
        sharex=True, sharey=True, squeeze=False,
    )
    axes_flat = axes_grid.ravel()

    for axis_index, model_name in enumerate(ordered_models):
        axis = axes_flat[axis_index]
        for persona_enabled, series_label, color, linestyle in PERSONA_SERIES:
            summary_df = summaries_by_persona.get(persona_enabled)
            if summary_df is None or summary_df.empty:
                continue
            model_df = summary_df[summary_df["model_name"] == model_name]
            if model_df.empty:
                continue
            axis.plot(
                model_df["delay_months"], model_df["p_later"],
                marker="o", color=color, linestyle=linestyle,
                label=series_label, linewidth=1.5, markersize=4,
            )

        axis.set_title(model_name, fontsize=9)
        axis.set_ylim(-0.05, 1.05)
        axis.axhline(0.5, color="gray", linestyle=":", linewidth=0.8, zorder=0)
        axis.grid(True, alpha=0.25)
        if axis_index % n_cols == 0:
            axis.set_ylabel("P(choose larger-later)")
        if axis_index // n_cols == n_rows - 1:
            axis.set_xlabel("Delay (months)")

    for empty_axis in axes_flat[n_models:]:
        empty_axis.axis("off")

    handles, labels = axes_flat[0].get_legend_handles_labels()
    if handles:
        figure.legend(
            handles, labels, loc="upper center", ncol=2, fontsize=9,
            bbox_to_anchor=(0.5, 1.02),
        )

    figure.suptitle(
        f"Waiting Game: P(larger-later) vs delay by Qwen model [{mode_label}]",
        fontsize=13, y=1.06 if n_rows == 1 else 1.02,
    )
    figure.tight_layout()

    suffix = result_suffix(reasoning_mode, persona_enabled=False)
    figure_path = os.path.join(figures_dir, f"p_later_by_delay{suffix}.png")
    figure.savefig(figure_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {figure_path}")
    return figure_path


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct")
    arg_parser.add_argument(
        "--all-modes", action="store_true",
        help="Plot every reasoning mode that has at least one choices CSV.",
    )
    args = arg_parser.parse_args()

    config = load_config(args.config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    model_order = list(config["models"])

    modes = REASONING_MODES if args.all_modes else [args.mode]
    for reasoning_mode in modes:
        plot_p_later_by_delay(processed_dir, figures_dir, model_order, reasoning_mode)


if __name__ == "__main__":
    main()
