"""Visualizes raw choice behavior directly, one figure per model: P(choose
LDR) across the 27 items sorted by their own indifference k (the built-in
"difficulty" ordering of the instrument), colored by magnitude band, plus
jittered dots for individual raw trials -- the Kirby analogue of the Waiting
Game's ../temporal-discounting/src/plot_choice_curves.py.

A well-behaved model's curve should trend upward left-to-right (as item k
rises, LDR requires less personal patience to justify, so a rational agent's
P(choose LDR) should rise, not fall); this is exactly what
competence_checks.check_rank_monotonicity tests numerically.

Persona-on runs write one figure per persona id (plus model subdirs matching
the Waiting Game layout).

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
    load_kirby_items,
    resolve_dir_path,
    kirby_result_suffix,
    persona_enabled_from_config,
)
from persona import iter_persona_groups
from run_experiment import REASONING_MODES, safe_filename_for_model

JITTER_HEIGHT = 0.06
SAMPLE_DOT_ALPHA = 0.35
CURVE_COLOR = "#1f77b4"
SAMPLE_DOT_COLOR = "#d62728"
MAGNITUDE_MARKERS = {"small": "o", "medium": "s", "large": "^"}
MAGNITUDE_COLORS = {"small": "#2ca02c", "medium": "#ff7f0e", "large": "#9467bd"}
DISCOUNTING_GROUP_COLORS = {
    "greater": "#d62728",
    "lesser": "#2ca02c",
}


def compute_p_ldr_per_item(model_choices_df):
    parsed_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    parsed_df["chose_ldr"] = (~parsed_df["chose_sooner_option"].astype(bool)).astype(float)
    return parsed_df.groupby("item_id")["chose_ldr"].mean().to_dict()


def select_sample_trials(model_choices_df, item_id, n_trials_to_plot, trial_selection_rng):
    item_df = model_choices_df[model_choices_df["item_id"] == item_id].dropna(subset=["chose_sooner_option"])
    n_available = len(item_df)
    if n_available == 0:
        return item_df
    n_to_select = min(n_trials_to_plot, n_available)
    selected_positions = trial_selection_rng.choice(n_available, size=n_to_select, replace=False)
    return item_df.iloc[selected_positions]


def plot_model_choice_curves(model_name, model_choices_df, items, n_trials_to_plot,
                              trial_selection_seed, reasoning_mode="direct",
                              title=None, curve_color=CURVE_COLOR):
    p_ldr_by_item = compute_p_ldr_per_item(model_choices_df)
    trial_selection_rng = np.random.default_rng(trial_selection_seed)

    sorted_items = sorted(items, key=lambda it: it["k_at_indifference"])
    x_positions = np.arange(len(sorted_items))

    figure, axis = plt.subplots(figsize=(13, 5.5))

    p_ldr_sequence = [p_ldr_by_item.get(it["item_id"], np.nan) for it in sorted_items]
    axis.plot(x_positions, p_ldr_sequence, "-", color=curve_color, zorder=2, linewidth=1.5,
              label="P(choose LDR), all samples")

    for magnitude in ("small", "medium", "large"):
        magnitude_mask = [it["magnitude"] == magnitude for it in sorted_items]
        axis.scatter(
            x_positions[magnitude_mask],
            [p for p, m in zip(p_ldr_sequence, magnitude_mask) if m],
            marker=MAGNITUDE_MARKERS[magnitude], color=MAGNITUDE_COLORS[magnitude],
            s=60, zorder=3, label=f"{magnitude} magnitude",
        )

    for x_position, item in zip(x_positions, sorted_items):
        sample_trials_df = select_sample_trials(
            model_choices_df, item["item_id"], n_trials_to_plot, trial_selection_rng
        )
        if sample_trials_df.empty:
            continue
        chose_ldr_values = (~sample_trials_df["chose_sooner_option"].astype(bool)).astype(float).values
        y_jitter = trial_selection_rng.uniform(-JITTER_HEIGHT, JITTER_HEIGHT, size=len(chose_ldr_values))
        x_jitter = trial_selection_rng.uniform(-0.15, 0.15, size=len(chose_ldr_values))
        axis.scatter(
            x_position + x_jitter, chose_ldr_values + y_jitter,
            color=SAMPLE_DOT_COLOR, alpha=SAMPLE_DOT_ALPHA, s=10, zorder=1,
            label=f"{n_trials_to_plot} sampled raw trials" if x_position == 0 else None,
        )

    axis.set_xticks(x_positions)
    axis.set_xticklabels([f"#{it['item_id']}\nk={it['k_at_indifference']:.4f}" for it in sorted_items],
                          rotation=90, fontsize=6)
    axis.set_ylim(-0.15, 1.15)
    axis.set_xlabel("Kirby MCQ-27 item, sorted by item's own indifference k (harder -> easier to justify waiting)")
    axis.set_ylabel("P(choose larger-delayed reward)")
    axis.legend(fontsize=8, loc="upper right")
    axis.set_title(title or f"Kirby MCQ-27 raw choices: {model_name} [{reasoning_mode}]")
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
    items = load_kirby_items(config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])
    suffix = kirby_result_suffix(args.mode, persona_enabled, config["kirby"]["variant"])

    choices_csv = os.path.join(processed_dir, f"choices{suffix}.csv")
    if not os.path.exists(choices_csv):
        print(f"No choices file at {choices_csv}; run parse_responses.py first.")
        return

    choices_df = pd.read_csv(choices_csv)
    n_trials_to_plot = config["visualization"]["n_sample_trials_to_plot_per_item"]
    trial_selection_seed = config["visualization"]["trial_selection_seed"]

    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        if persona_enabled:
            model_dir = model_figures_dir(figures_dir, model_name)
            wrote_any = False
            for persona_id, discounting_group, persona_label, persona_df in iter_persona_groups(
                model_choices_df
            ):
                if persona_id is None:
                    continue
                group_tag = f", {discounting_group}" if discounting_group else ""
                title = (
                    f"Kirby MCQ-27 raw choices: {model_name} "
                    f"[{args.mode}, {persona_label or persona_id}{group_tag}]"
                )
                curve_color = DISCOUNTING_GROUP_COLORS.get(discounting_group, CURVE_COLOR)
                figure = plot_model_choice_curves(
                    model_name, persona_df, items, n_trials_to_plot, trial_selection_seed,
                    reasoning_mode=args.mode, title=title, curve_color=curve_color,
                )
                figure_path = os.path.join(
                    model_dir, f"choice_curves{suffix}__{persona_id}.png"
                )
                save_choice_figure(figure, figure_path)
                wrote_any = True
            if not wrote_any:
                print(f"[{model_name}] persona-on but no persona_id rows; skipping.")
        else:
            figure = plot_model_choice_curves(
                model_name, model_choices_df, items, n_trials_to_plot, trial_selection_seed,
                reasoning_mode=args.mode,
            )
            # Keep flat filename for persona-off (backward compatible with prior runs).
            figure_path = os.path.join(
                figures_dir, f"choice_curves_{safe_filename_for_model(model_name)}{suffix}.png"
            )
            save_choice_figure(figure, figure_path)


if __name__ == "__main__":
    main()
