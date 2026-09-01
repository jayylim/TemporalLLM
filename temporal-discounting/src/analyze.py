"""Ties together competence checks + fitted discount rates into one
comparison table, and plots discount curves (indifference amount vs delay)
against the Rachlin et al. (1991) human benchmark.

Also reports results stratified by persona on/off, A/B option order
(pooled / sooner_A / sooner_B), and when persona data is present, by
demographic factors (gender, age band).

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
from run_experiment import REASONING_MODES

MODEL_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f",
]

MODE_DISPLAY_LABELS = {
    "direct": "direct",
    "cot": "chain-of-thought",
    "one_shot": "one-shot",
    "two_shot": "two-shot",
}

AGE_BAND_EDGES = [20, 35, 50, 65, 81]  # right-exclusive last edge -> 20-34, 35-49, 50-64, 65-80
AGE_BAND_LABELS = ["20-34", "35-49", "50-64", "65-80"]


def merge_keys(fit_df, competence_df):
    keys = ["model_name"]
    for optional in ("persona_enabled", "option_order"):
        if optional in fit_df.columns and optional in competence_df.columns:
            keys.append(optional)
    return keys


def build_comparison_table(fit_df, competence_df):
    drop_cols = [c for c in ("k_lower_bound", "k_upper_bound") if c in competence_df.columns]
    comparison_df = fit_df.merge(
        competence_df.drop(columns=drop_cols, errors="ignore"),
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


def plot_discount_curves(choices_df, comparison_df, config, figures_dir, suffix="", reasoning_mode="direct"):
    """One panel per option_order stratum: raw 50% equivalents + fitted curves."""
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


def age_band_series(ages):
    return pd.cut(
        ages,
        bins=AGE_BAND_EDGES,
        labels=AGE_BAND_LABELS,
        right=False,
        include_lowest=True,
    )


def fit_stratum(model_choices_df, later_amount_dollars, n_bootstrap, bootstrap_seed,
                fitting_bounds, competence_config, fitting_config, stratum_meta,
                delay_grid_months=None):
    """Competence + fit for one demographic stratum. Uses a small bootstrap
    when the stratum is thin so analyze stays cheap.
    """
    if model_choices_df.dropna(subset=["chose_sooner_option"]).empty:
        return None

    competence = run_competence_checks_for_model(
        model_choices_df, competence_config, fitting_config, delay_grid_months
    )
    # Keep demographic strata cheap: reuse the same seed but fewer resamples.
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


def build_demographic_strata_table(choices_df, config, persona_enabled):
    """When persona is on, refit/check per model x gender and model x age-band
    (pooled option order only — demographics × order would explode the table).
    """
    if not persona_enabled:
        return pd.DataFrame()
    if "persona_gender" not in choices_df.columns or choices_df["persona_gender"].isna().all():
        return pd.DataFrame()

    later_amount = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    n_bootstrap = config["fitting"]["n_bootstrap"]
    bootstrap_seed = config["fitting"]["bootstrap_seed"]
    fitting_bounds = fitting_bounds_from_config(config["fitting"])
    competence_config = config["competence_checks"]
    fitting_config = config["fitting"]

    working_df = choices_df.copy()
    working_df["persona_age_band"] = age_band_series(working_df["persona_age"])

    rows = []
    for model_name in config["models"]:
        model_df = working_df[working_df["model_name"] == model_name]
        if model_df.empty:
            continue

        overall = fit_stratum(
            model_df, later_amount, n_bootstrap, bootstrap_seed, fitting_bounds,
            competence_config, fitting_config,
            {
                "model_name": model_name,
                "option_order": "pooled",
                "stratum_type": "persona_on",
                "stratum_value": "all",
            },
            delay_grid_months,
        )
        if overall:
            rows.append(overall)

        for gender, gender_df in model_df.groupby("persona_gender"):
            stratum = fit_stratum(
                gender_df, later_amount, n_bootstrap, bootstrap_seed, fitting_bounds,
                competence_config, fitting_config,
                {
                    "model_name": model_name,
                    "option_order": "pooled",
                    "stratum_type": "gender",
                    "stratum_value": str(gender),
                },
                delay_grid_months,
            )
            if stratum:
                rows.append(stratum)

        for age_band, age_df in model_df.groupby("persona_age_band", observed=True):
            stratum = fit_stratum(
                age_df, later_amount, n_bootstrap, bootstrap_seed, fitting_bounds,
                competence_config, fitting_config,
                {
                    "model_name": model_name,
                    "option_order": "pooled",
                    "stratum_type": "age_band",
                    "stratum_value": str(age_band),
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
        "model_name", "option_order", "k", "k_ci_low", "k_ci_high", "r_squared",
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
    print(f"Wrote discount-curve plot to {figure_path}")

    strata_df = build_demographic_strata_table(choices_df, config, persona_enabled)
    if not strata_df.empty:
        strata_path = os.path.join(tables_dir, f"comparison_summary_by_demographics{suffix}.csv")
        strata_df.to_csv(strata_path, index=False)
        print(f"\n=== Demographic strata (persona-on) ===")
        print(strata_df[[
            "model_name", "stratum_type", "stratum_value",
            "overall_passed", "k_is_reliable", "valid_discount_rate", "k", "n_trials_fit",
        ]].to_string(index=False))
        print(f"Wrote demographic strata table to {strata_path}")
    else:
        print("No persona demographic strata to report (persona off or no persona columns).")


if __name__ == "__main__":
    main()
