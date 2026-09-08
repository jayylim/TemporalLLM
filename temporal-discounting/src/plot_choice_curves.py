"""Visualizes raw choice behavior, clustered by model folder.

Writes under results/figures/{model}/:
  - choice_curves{mode_suffix}.png              (persona-off control)
  - choice_curves{mode_suffix}__persona__{id}.png  (one figure per persona)

Each figure has a subplot per delay: empirical P(choose sooner) vs amount,
plus jittered dots for a few raw trials per cell.

Usage: python src/plot_choice_curves.py [--config path/to/config.yaml]
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
    result_suffix,
    persona_enabled_from_config,
)
from competence_checks import compute_p_sooner_table, fit_grid_choices
from persona import iter_persona_groups
from run_experiment import REASONING_MODES, safe_filename_for_model

JITTER_HEIGHT = 0.06          # vertical spread of the individual-trial dots around y=0 or y=1
SAMPLE_DOT_ALPHA = 0.45
CURVE_COLOR = "#1f77b4"
SAMPLE_DOT_COLOR = "#d62728"
DISCOUNTING_GROUP_COLORS = {
    "greater": "#d62728",
    "lesser": "#2ca02c",
}


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


def plot_choice_curves(title, choices_df, delay_grid_months, amount_grid_dollars,
                       n_trials_to_plot, trial_selection_seed, curve_color=CURVE_COLOR):
    """One figure: subplot per delay for a single condition (control or one persona)."""
    fit_choices_df = fit_grid_choices(choices_df)
    p_sooner_table = compute_p_sooner_table(fit_choices_df)
    trial_selection_rng = np.random.default_rng(trial_selection_seed)

    n_delays = len(delay_grid_months)
    n_cols = 4
    n_rows = int(np.ceil(n_delays / n_cols))
    figure, axes_grid = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3.2 * n_rows), squeeze=False)

    for delay_index, delay_months in enumerate(delay_grid_months):
        axis = axes_grid[delay_index // n_cols][delay_index % n_cols]

        if delay_months in p_sooner_table.index:
            available_amounts = [a for a in amount_grid_dollars if a in p_sooner_table.columns]
            if available_amounts:
                p_sooner_row = p_sooner_table.loc[delay_months, available_amounts]
                axis.plot(
                    available_amounts, p_sooner_row.values.astype(float), "-o",
                    color=curve_color, label="P(choose sooner), all samples", zorder=3,
                )

        for amount_dollars in amount_grid_dollars:
            sample_trials_df = select_sample_trials(
                fit_choices_df, delay_months, amount_dollars, n_trials_to_plot, trial_selection_rng
            )
            if sample_trials_df.empty:
                continue
            chose_sooner_values = sample_trials_df["chose_sooner_option"].astype(float).values
            y_jitter = trial_selection_rng.uniform(-JITTER_HEIGHT, JITTER_HEIGHT, size=len(chose_sooner_values))
            amount_span = max(amount_grid_dollars) - min(amount_grid_dollars)
            x_jitter_scale = max(amount_span * 0.01, 1.0)
            x_jitter = trial_selection_rng.uniform(-x_jitter_scale, x_jitter_scale, size=len(chose_sooner_values))
            axis.scatter(
                amount_dollars + x_jitter, chose_sooner_values + y_jitter,
                color=SAMPLE_DOT_COLOR, alpha=SAMPLE_DOT_ALPHA, s=14, zorder=2,
                label=f"{n_trials_to_plot} sampled raw trials" if amount_dollars == amount_grid_dollars[0] else None,
            )

        axis.set_ylim(-0.15, 1.15)
        axis.set_title(f"delay = {delay_months} mo")
        axis.set_xlabel("sooner amount ($)")
        axis.set_ylabel("chose sooner (0/1)")

    for empty_index in range(n_delays, n_rows * n_cols):
        axes_grid[empty_index // n_cols][empty_index % n_cols].axis("off")

    handles, labels = axes_grid[0][0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, 1.02))
    figure.suptitle(title, y=1.06, fontsize=13)
    figure.tight_layout()
    return figure


def resolve_persona_enabled(args, config):
    if getattr(args, "persona", False):
        return True
    if getattr(args, "no_persona", False):
        return False
    return persona_enabled_from_config(config)


def model_figures_dir(figures_dir, model_name):
    model_dir = os.path.join(figures_dir, safe_filename_for_model(model_name))
    os.makedirs(model_dir, exist_ok=True)
    return model_dir


def save_choice_figure(figure, figure_path):
    figure.savefig(figure_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"wrote {figure_path}")


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
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    suffix = result_suffix(args.mode, persona_enabled)

    choices_csv = os.path.join(processed_dir, f"choices{suffix}.csv")
    if not os.path.exists(choices_csv):
        print(f"No choices file at {choices_csv}; run parse_responses.py first.")
        return

    choices_df = pd.read_csv(choices_csv)
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    amount_grid_dollars = config["waiting_game"]["amount_grid_dollars"]
    n_trials_to_plot = config["visualization"]["n_sample_trials_to_plot_per_cell"]
    trial_selection_seed = config["visualization"]["trial_selection_seed"]

    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        model_dir = model_figures_dir(figures_dir, model_name)

        if persona_enabled:
            wrote_any = False
            for persona_id, discounting_group, persona_label, persona_df in iter_persona_groups(
                model_choices_df
            ):
                if persona_id is None:
                    continue
                group_tag = f", {discounting_group}" if discounting_group else ""
                title = (
                    f"Waiting Game raw choices: {model_name} "
                    f"[{args.mode}, {persona_label or persona_id}{group_tag}]"
                )
                curve_color = DISCOUNTING_GROUP_COLORS.get(discounting_group, CURVE_COLOR)
                figure = plot_choice_curves(
                    title, persona_df, delay_grid_months, amount_grid_dollars,
                    n_trials_to_plot, trial_selection_seed, curve_color=curve_color,
                )
                figure_path = os.path.join(
                    model_dir, f"choice_curves{suffix}__{persona_id}.png"
                )
                save_choice_figure(figure, figure_path)
                wrote_any = True
            if not wrote_any:
                print(f"[{model_name}] persona-on but no persona_id rows; skipping.")
        else:
            title = f"Waiting Game raw choices: {model_name} [{args.mode}]"
            figure = plot_choice_curves(
                title, model_choices_df, delay_grid_months, amount_grid_dollars,
                n_trials_to_plot, trial_selection_seed,
            )
            figure_path = os.path.join(model_dir, f"choice_curves{suffix}.png")
            save_choice_figure(figure, figure_path)


if __name__ == "__main__":
    main()
