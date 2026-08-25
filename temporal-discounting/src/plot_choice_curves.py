"""Visualizes raw choice behavior directly, one figure per model: a subplot
per delay, showing the empirical P(choose sooner) curve across amounts plus
jittered dots for a handful of individual raw trials per cell (i.e. actual
instances, not just the aggregate probability).

Usage: python src/plot_choice_curves.py [--config path/to/config.yaml]
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
from run_experiment import REASONING_MODES, safe_filename_for_model

JITTER_HEIGHT = 0.06          # vertical spread of the individual-trial dots around y=0 or y=1
SAMPLE_DOT_ALPHA = 0.45
CURVE_COLOR = "#1f77b4"
SAMPLE_DOT_COLOR = "#d62728"


def select_sample_trials(model_choices_df, delay_months, amount_dollars, n_trials_to_plot, trial_selection_rng):
    """Picks up to n_trials_to_plot raw (parsed) trials from one (delay, amount) cell."""
    cell_df = model_choices_df[
        (model_choices_df["delay_months"] == delay_months)
        & (model_choices_df["amount_dollars"] == amount_dollars)
    ].dropna(subset=["chose_sooner_option"])

    n_available = len(cell_df)
    if n_available == 0:
        return cell_df

    n_to_select = min(n_trials_to_plot, n_available)
    selected_positions = trial_selection_rng.choice(n_available, size=n_to_select, replace=False)
    return cell_df.iloc[selected_positions]


def plot_model_choice_curves(model_name, model_choices_df, delay_grid_months, amount_grid_dollars,
                              n_trials_to_plot, trial_selection_seed, reasoning_mode="direct"):
    p_sooner_table = compute_p_sooner_table(model_choices_df)
    trial_selection_rng = np.random.default_rng(trial_selection_seed)

    n_delays = len(delay_grid_months)
    n_cols = 4
    n_rows = int(np.ceil(n_delays / n_cols))
    figure, axes_grid = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3.2 * n_rows), squeeze=False)

    for delay_index, delay_months in enumerate(delay_grid_months):
        axis = axes_grid[delay_index // n_cols][delay_index % n_cols]

        # Aggregate empirical curve: P(choose sooner) vs amount, over all N samples.
        if delay_months in p_sooner_table.index:
            p_sooner_row = p_sooner_table.loc[delay_months, amount_grid_dollars]
            axis.plot(amount_grid_dollars, p_sooner_row.values, "-o", color=CURVE_COLOR,
                       label="P(choose sooner), all samples", zorder=3)

        # A few raw individual trials per cell, jittered so 0/1 outcomes are visible as a cloud.
        for amount_dollars in amount_grid_dollars:
            sample_trials_df = select_sample_trials(
                model_choices_df, delay_months, amount_dollars, n_trials_to_plot, trial_selection_rng
            )
            if sample_trials_df.empty:
                continue
            chose_sooner_values = sample_trials_df["chose_sooner_option"].astype(float).values
            y_jitter = trial_selection_rng.uniform(-JITTER_HEIGHT, JITTER_HEIGHT, size=len(chose_sooner_values))
            x_jitter = trial_selection_rng.uniform(-3, 3, size=len(chose_sooner_values))
            axis.scatter(
                amount_dollars + x_jitter, chose_sooner_values + y_jitter,
                color=SAMPLE_DOT_COLOR, alpha=SAMPLE_DOT_ALPHA, s=14, zorder=2,
                label=f"{n_trials_to_plot} sampled raw trials" if amount_dollars == amount_grid_dollars[0] else None,
            )

        axis.set_ylim(-0.15, 1.15)
        axis.set_title(f"delay = {delay_months} mo")
        axis.set_xlabel("sooner amount ($)")
        axis.set_ylabel("chose sooner (0/1)")

    # hide unused subplot cells if n_delays doesn't fill the grid exactly
    for empty_index in range(n_delays, n_rows * n_cols):
        axes_grid[empty_index // n_cols][empty_index % n_cols].axis("off")

    handles, labels = axes_grid[0][0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, 1.02))
    figure.suptitle(f"Waiting Game raw choices: {model_name} [{reasoning_mode}]", y=1.06, fontsize=13)
    figure.tight_layout()
    return figure


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    suffix = mode_suffix(args.mode)

    choices_df = pd.read_csv(os.path.join(processed_dir, f"choices{suffix}.csv"))
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    amount_grid_dollars = config["waiting_game"]["amount_grid_dollars"]
    n_trials_to_plot = config["visualization"]["n_sample_trials_to_plot_per_cell"]
    trial_selection_seed = config["visualization"]["trial_selection_seed"]

    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        figure = plot_model_choice_curves(
            model_name, model_choices_df, delay_grid_months, amount_grid_dollars,
            n_trials_to_plot, trial_selection_seed, reasoning_mode=args.mode,
        )
        figure_path = os.path.join(
            figures_dir, f"choice_curves_{safe_filename_for_model(model_name)}{suffix}.png"
        )
        figure.savefig(figure_path, dpi=150, bbox_inches="tight")
        plt.close(figure)
        print(f"[{model_name}] wrote {figure_path}")


if __name__ == "__main__":
    main()
