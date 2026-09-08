"""Ties together competence checks + fitted discount rates into one
comparison table, and plots discount curves (indifference amount vs delay)
against the Rachlin et al. (1991) human benchmark.

Also reports results stratified by persona on/off, A/B option order
(pooled / sooner_A / sooner_B), and when behavioral persona data is present,
by persona_id and hypothesised discounting_group (greater / lesser).

Usage: python src/analyze.py [--config path/to/config.yaml]
       [--mode ...] [--persona|--no-persona]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import (
    OPTION_ORDER_STRATA,
    filter_by_option_order,
    load_config,
    resolve_dir_path,
    result_suffix,
    persona_enabled_from_config,
)
from fit_discounting import (
    fit_discounting_for_model,
    fitting_bounds_from_config,
    hyperbolic_value,
)
from competence_checks import estimate_indifference_amounts, run_competence_checks_for_model
from persona import iter_persona_groups
from run_experiment import REASONING_MODES

MODEL_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f",
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
    for optional in (
        "persona_enabled",
        "persona_id",
        "persona_discounting_group",
        "option_order",
    ):
        if optional in fit_df.columns and optional in competence_df.columns:
            keys.append(optional)
    return keys


def build_comparison_table(fit_df, competence_df):
    drop_cols = [c for c in ("k_lower_bound", "k_upper_bound") if c in competence_df.columns]
    competence_extra = competence_df.drop(columns=drop_cols, errors="ignore")
    for maybe_dup in ("persona_label",):
        if maybe_dup in fit_df.columns and maybe_dup in competence_extra.columns:
            competence_extra = competence_extra.drop(columns=[maybe_dup])
    comparison_df = fit_df.merge(
        competence_extra,
        on=merge_keys(fit_df, competence_df),
        how="left",
    )
    comparison_df["valid_discount_rate"] = (
        comparison_df["overall_passed"] & comparison_df["k_is_reliable"]
    )
    return comparison_df


def empirical_indifference_amounts(model_choices_df, delay_grid_months):
    """Wrapper returning {delay: amount} from the shared indifference estimator."""
    indifference_df = estimate_indifference_amounts(model_choices_df, delay_grid_months)
    return {
        row["delay_months"]: row["indifference_amount"]
        for _, row in indifference_df.iterrows()
    }


def fitted_indifference_curve(k, later_amount_dollars, delay_range_months):
    """x*(d) solving amount = later_amount / (1 + k*d) at indifference (V_sooner == V_later)."""
    return hyperbolic_value(later_amount_dollars, delay_range_months, k)


def _has_persona_ids(df):
    return "persona_id" in df.columns and df["persona_id"].notna().any()


def plot_discount_curves(choices_df, comparison_df, config, figures_dir, suffix="", reasoning_mode="direct"):
    """One panel per option_order (control) or per model (persona-on, pooled only)."""
    if _has_persona_ids(comparison_df):
        return plot_discount_curves_by_persona(
            choices_df, comparison_df, config, figures_dir, suffix, reasoning_mode
        )

    later_amount_dollars = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]
    delay_range_months = np.linspace(min(delay_grid_months), max(delay_grid_months), 200)

    if "option_order" in comparison_df.columns:
        order_levels = [label for label, _ in OPTION_ORDER_STRATA
                        if label in set(comparison_df["option_order"])]
        if not order_levels:
            order_levels = sorted(comparison_df["option_order"].unique())
    else:
        order_levels = ["pooled"]

    n_orders = len(order_levels)
    figure, axes = plt.subplots(1, n_orders, figsize=(5.5 * n_orders, 5.5), squeeze=False)

    persona_label = "persona-on" if ("persona_enabled" in comparison_df.columns
                                     and bool(comparison_df["persona_enabled"].iloc[0])) else "persona-off"
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)

    for order_index, option_order in enumerate(order_levels):
        axis = axes[0][order_index]
        if "option_order" in comparison_df.columns:
            order_comp = comparison_df[comparison_df["option_order"] == option_order]
            sooner_is_a = dict(OPTION_ORDER_STRATA).get(option_order)
            order_choices = filter_by_option_order(choices_df, sooner_is_a)
        else:
            order_comp = comparison_df
            order_choices = choices_df

        model_names = list(dict.fromkeys(order_comp["model_name"]))
        for model_index, model_name in enumerate(model_names):
            row = order_comp[order_comp["model_name"] == model_name].iloc[0]
            model_color = MODEL_COLORS[model_index % len(MODEL_COLORS)]
            model_choices_df = order_choices[order_choices["model_name"] == model_name]

            empirical_points = empirical_indifference_amounts(model_choices_df, delay_grid_months)
            axis.plot(
                list(empirical_points.keys()), list(empirical_points.values()),
                color=model_color, marker="o", linestyle="none",
                label=f"{model_name} (50% equiv.)", zorder=3,
            )

            if not pd.isna(row["k"]):
                fitted_curve = fitted_indifference_curve(
                    row["k"], later_amount_dollars, delay_range_months
                )
                line_style = "-" if row["valid_discount_rate"] else ":"
                fit_label_suffix = "" if row["valid_discount_rate"] else " (unreliable)"
                axis.plot(
                    delay_range_months, fitted_curve,
                    color=model_color, linestyle=line_style,
                    label=f"{model_name} fit, k={row['k']:.4f}{fit_label_suffix}",
                )

        human_benchmark_curve = fitted_indifference_curve(
            human_k, later_amount_dollars, delay_range_months
        )
        axis.plot(
            delay_range_months, human_benchmark_curve,
            color="black", linestyle="--",
            label=f"Human (Rachlin 1991), k={human_k}",
        )

        axis.set_xlabel("Delay to later reward (months)")
        axis.set_ylabel(f"Indifference amount now (of ${later_amount_dollars} later)")
        axis.set_title(f"option_order={option_order}")
        axis.legend(fontsize=6, loc="upper right")
        axis.set_ylim(bottom=0)

    figure.suptitle(
        f"Waiting Game: raw 50% equivalents + hyperbolic fits "
        f"[{mode_label}, {persona_label}]",
        fontsize=12, y=1.02,
    )
    figure.tight_layout()

    figure_path = os.path.join(figures_dir, f"discount_curves{suffix}.png")
    figure.savefig(figure_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return figure_path


def plot_discount_curves_by_persona(choices_df, comparison_df, config, figures_dir,
                                    suffix="", reasoning_mode="direct"):
    """One panel per model; persona curves overlaid (pooled option order only)."""
    later_amount_dollars = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    human_k = config["human_benchmark"]["rachlin_1991_k_per_month"]
    delay_range_months = np.linspace(min(delay_grid_months), max(delay_grid_months), 200)
    mode_label = MODE_DISPLAY_LABELS.get(reasoning_mode, reasoning_mode)

    pooled_comp = comparison_df
    if "option_order" in comparison_df.columns:
        pooled_comp = comparison_df[comparison_df["option_order"] == "pooled"]
    pooled_choices = filter_by_option_order(choices_df, None)

    model_names = list(dict.fromkeys(pooled_comp["model_name"]))
    if not model_names:
        return None

    n_models = len(model_names)
    n_cols = min(3, n_models)
    n_rows = int(np.ceil(n_models / n_cols))
    figure, axes = plt.subplots(
        n_rows, n_cols, figsize=(5.5 * n_cols, 4.5 * n_rows), squeeze=False
    )

    for model_index, model_name in enumerate(model_names):
        axis = axes[model_index // n_cols][model_index % n_cols]
        model_comp = pooled_comp[pooled_comp["model_name"] == model_name]
        model_choices = pooled_choices[pooled_choices["model_name"] == model_name]

        for persona_index, (_, row) in enumerate(model_comp.iterrows()):
            persona_id = row.get("persona_id")
            group = row.get("persona_discounting_group")
            label = row.get("persona_label") or persona_id
            color = DISCOUNTING_GROUP_COLORS.get(
                group, MODEL_COLORS[persona_index % len(MODEL_COLORS)]
            )
            persona_choices = model_choices[model_choices["persona_id"] == persona_id]
            empirical_points = empirical_indifference_amounts(persona_choices, delay_grid_months)
            axis.plot(
                list(empirical_points.keys()), list(empirical_points.values()),
                color=color, marker="o", linestyle="none", alpha=0.8, zorder=3,
            )
            if not pd.isna(row["k"]):
                fitted_curve = fitted_indifference_curve(
                    row["k"], later_amount_dollars, delay_range_months
                )
                line_style = "-" if row["valid_discount_rate"] else ":"
                axis.plot(
                    delay_range_months, fitted_curve,
                    color=color, linestyle=line_style,
                    label=f"{label} ({group}), k={row['k']:.4f}",
                )

        human_benchmark_curve = fitted_indifference_curve(
            human_k, later_amount_dollars, delay_range_months
        )
        axis.plot(
            delay_range_months, human_benchmark_curve,
            color="black", linestyle="--", label=f"Human k={human_k}",
        )
        axis.set_title(model_name, fontsize=9)
        axis.set_xlabel("Delay (months)")
        axis.set_ylabel(f"Indiff. now (of ${later_amount_dollars})")
        axis.legend(fontsize=5, loc="upper right")
        axis.set_ylim(bottom=0)

    for empty_index in range(n_models, n_rows * n_cols):
        axes[empty_index // n_cols][empty_index % n_cols].axis("off")

    figure.suptitle(
        f"Waiting Game persona curves [{mode_label}, pooled order]",
        fontsize=12, y=1.01,
    )
    figure.tight_layout()
    figure_path = os.path.join(figures_dir, f"discount_curves{suffix}.png")
    figure.savefig(figure_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return figure_path


def fit_stratum(model_choices_df, later_amount_dollars, n_bootstrap, bootstrap_seed,
                fitting_bounds, competence_config, fitting_config, stratum_meta,
                delay_grid_months=None):
    """Competence + fit for one persona / discounting-group stratum."""
    if model_choices_df.dropna(subset=["chose_sooner_option"]).empty:
        return None

    competence = run_competence_checks_for_model(
        model_choices_df, competence_config, fitting_config, delay_grid_months
    )
    stratum_bootstrap = min(n_bootstrap, 200)
    fit_result = fit_discounting_for_model(
        model_choices_df, later_amount_dollars, stratum_bootstrap, bootstrap_seed,
        fitting_bounds, delay_grid_months,
    )
    fit_result.pop("indifference_points", None)
    row = dict(stratum_meta)
    row.update({
        "monotonicity_passed": competence["monotonicity_passed"],
        "money_preference_passed": competence["money_preference_passed"],
        "indifference_nonincreasing_passed": competence["indifference_nonincreasing_passed"],
        "n_indifference_violations": competence["n_indifference_violations"],
        "overall_passed": competence["overall_passed"],
        "k": fit_result["k"],
        "r_squared": fit_result["r_squared"],
        "k_ci_low": fit_result["k_ci_low"],
        "k_ci_high": fit_result["k_ci_high"],
        "k_at_boundary": fit_result["k_at_boundary"],
        "k_is_reliable": fit_result["k_is_reliable"],
        "k_lower_bound": fit_result["k_lower_bound"],
        "k_upper_bound": fit_result["k_upper_bound"],
        "n_trials_fit": fit_result["n_trials_fit"],
        "n_indifference_points": fit_result["n_indifference_points"],
        "valid_discount_rate": competence["overall_passed"] and fit_result["k_is_reliable"],
    })
    return row


def build_persona_strata_table(choices_df, config, persona_enabled):
    """When persona is on, refit/check per model × discounting_group (pooled order).

    Per-persona_id fits also appear here (and in comparison_summary) so group
    contrasts and individual personas are both recorded.
    """
    if not persona_enabled:
        return pd.DataFrame()
    if "persona_discounting_group" not in choices_df.columns:
        return pd.DataFrame()
    if choices_df["persona_discounting_group"].isna().all():
        return pd.DataFrame()

    later_amount = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    n_bootstrap = config["fitting"]["n_bootstrap"]
    bootstrap_seed = config["fitting"]["bootstrap_seed"]
    fitting_bounds = fitting_bounds_from_config(config["fitting"])
    competence_config = config["competence_checks"]
    fitting_config = config["fitting"]

    rows = []
    for model_name in config["models"]:
        model_df = choices_df[choices_df["model_name"] == model_name]
        if model_df.empty:
            continue

        for group_name, group_df in model_df.groupby("persona_discounting_group"):
            stratum = fit_stratum(
                group_df, later_amount, n_bootstrap, bootstrap_seed, fitting_bounds,
                competence_config, fitting_config,
                {
                    "model_name": model_name,
                    "option_order": "pooled",
                    "stratum_type": "discounting_group",
                    "stratum_value": str(group_name),
                },
                delay_grid_months,
            )
            if stratum:
                rows.append(stratum)

        for persona_id, discounting_group, persona_label, persona_df in iter_persona_groups(
            model_df
        ):
            stratum = fit_stratum(
                persona_df, later_amount, n_bootstrap, bootstrap_seed, fitting_bounds,
                competence_config, fitting_config,
                {
                    "model_name": model_name,
                    "option_order": "pooled",
                    "stratum_type": "persona_id",
                    "stratum_value": str(persona_id),
                    "persona_label": persona_label,
                    "persona_discounting_group": discounting_group,
                },
                delay_grid_months,
            )
            if stratum:
                rows.append(stratum)

    return pd.DataFrame(rows)


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
    suffix = result_suffix(args.mode, persona_enabled)

    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])
    figures_dir = resolve_dir_path(config["paths"]["results_figures_dir"])

    choices_df = pd.read_csv(os.path.join(processed_dir, f"choices{suffix}.csv"))
    fit_df = pd.read_csv(os.path.join(tables_dir, f"discount_rates{suffix}.csv"))
    competence_df = pd.read_csv(os.path.join(tables_dir, f"competence_checks{suffix}.csv"))

    comparison_df = build_comparison_table(fit_df, competence_df)
    comparison_csv_path = os.path.join(tables_dir, f"comparison_summary{suffix}.csv")
    comparison_df.to_csv(comparison_csv_path, index=False)

    print(f"\n=== Cross-model comparison (persona={persona_enabled}) ===")
    display_cols = [
        "model_name", "persona_id", "persona_discounting_group", "option_order",
        "k", "k_ci_low", "k_ci_high", "r_squared",
        "n_indifference_points", "k_lower_bound", "k_upper_bound", "k_at_boundary",
        "monotonicity_passed", "money_preference_passed",
        "indifference_nonincreasing_passed", "k_is_reliable", "valid_discount_rate",
    ]
    display_cols = [c for c in display_cols if c in comparison_df.columns]
    print(comparison_df[display_cols].to_string(index=False))
    print(f"\nWrote comparison table to {comparison_csv_path}")
    print(f"k bounds (reported; hits cut from reliability): "
          f"[{config['fitting'].get('k_lower_bound', 1e-6)}, "
          f"{config['fitting'].get('k_upper_bound', 10.0)}]")

    figure_path = plot_discount_curves(
        choices_df, comparison_df, config, figures_dir, suffix, args.mode
    )
    if figure_path:
        print(f"Wrote discount-curve plot to {figure_path}")

    strata_df = build_persona_strata_table(choices_df, config, persona_enabled)
    if not strata_df.empty:
        strata_path = os.path.join(tables_dir, f"comparison_summary_by_persona{suffix}.csv")
        strata_df.to_csv(strata_path, index=False)
        print(f"\n=== Persona strata (discounting_group / persona_id) ===")
        print_cols = [
            c for c in (
                "model_name", "stratum_type", "stratum_value",
                "persona_discounting_group", "overall_passed", "k_is_reliable",
                "valid_discount_rate", "k", "n_trials_fit",
            ) if c in strata_df.columns
        ]
        print(strata_df[print_cols].to_string(index=False))
        print(f"Wrote persona strata table to {strata_path}")
    else:
        print("No persona strata to report (persona off or no persona columns).")


if __name__ == "__main__":
    main()
