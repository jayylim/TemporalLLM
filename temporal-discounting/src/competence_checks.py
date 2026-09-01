"""Per-model competence gating checks, run before fitting discount rates.

Check A (amount monotonicity): P(choose sooner) must be non-decreasing in the
sooner amount x, for each fixed delay. Evaluated on the fit-grid amounts only
(competence-probe $0 cells are excluded so they don't distort the amount
ordering).

Check B (money preference): a model must not prefer $0 now over a positive
amount of money later, at any delay. Uses competence-probe $0 cells when
$0 is not in the main amount grid.

Check C (indifference non-increasing): the empirical 50% immediate equivalents
x*(d) — sooner amount at which P(choose sooner)=0.5 — must be non-increasing
in delay. A rise as delay grows means the delayed $later is valued *more*
when it is farther away, which is incoherent for hyperbolic discounting.

Results are stratified by A/B option order (pooled / sooner_A / sooner_B).

Usage: python src/competence_checks.py [--config path/to/config.yaml]
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
from run_experiment import REASONING_MODES, safe_filename_for_model

MODEL_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f",
]


def fit_grid_choices(model_choices_df):
    """Drops competence-probe rows so monotonicity only sees the fit amounts."""
    if "is_competence_probe" not in model_choices_df.columns:
        return model_choices_df
    probe_mask = model_choices_df["is_competence_probe"].fillna(False).astype(bool)
    return model_choices_df[~probe_mask]


def compute_p_sooner_table(model_choices_df):
    """Pivot table: rows = delay_months, columns = amount_dollars, values =
    P(chose sooner option), computed only over trials that parsed (A or B).
    """
    parsed_rows_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    # chose_sooner_option round-trips through CSV as an object column (mix of
    # bool/NaN) whenever any parse failures exist elsewhere in the dataframe
    # (common for cot/one_shot/two_shot modes), which silently makes the
    # pivoted table object-dtype too and breaks downstream numeric ops
    # (e.g. np.interp in analyze.py). Cast explicitly so it's always float.
    parsed_rows_df["chose_sooner_option"] = parsed_rows_df["chose_sooner_option"].astype(bool).astype(float)
    if parsed_rows_df.empty:
        return pd.DataFrame()
    p_sooner_table = parsed_rows_df.pivot_table(
        index="delay_months",
        columns="amount_dollars",
        values="chose_sooner_option",
        aggfunc="mean",
    )
    return p_sooner_table.sort_index().sort_index(axis=1)


def estimate_indifference_amounts(model_choices_df, delay_grid_months=None):
    """Per delay, interpolate the sooner amount at which P(choose sooner)=0.5.

    Returns a DataFrame with columns delay_months, indifference_amount,
    p_sooner_min, p_sooner_max (diagnostics for whether 0.5 was bracketed).
    """
    fit_df = fit_grid_choices(model_choices_df)
    p_sooner_table = compute_p_sooner_table(fit_df)
    if p_sooner_table.empty:
        return pd.DataFrame(columns=[
            "delay_months", "indifference_amount", "p_sooner_min", "p_sooner_max",
        ])

    if delay_grid_months is None:
        delays = list(p_sooner_table.index)
    else:
        delays = [d for d in delay_grid_months if d in p_sooner_table.index]

    amount_grid = np.sort(p_sooner_table.columns.values.astype(float))
    rows = []
    for delay_months in delays:
        p_values = p_sooner_table.loc[delay_months, amount_grid].values.astype(float)
        indifference = float(np.interp(0.5, p_values, amount_grid))
        rows.append({
            "delay_months": float(delay_months),
            "indifference_amount": indifference,
            "p_sooner_min": float(np.nanmin(p_values)),
            "p_sooner_max": float(np.nanmax(p_values)),
        })
    return pd.DataFrame(rows)


def check_monotonicity(p_sooner_table, monotonicity_tolerance, max_violations_per_delay):
    """Counts, per delay row, how many adjacent-amount steps decrease in
    P(sooner) by more than the tolerance. Returns (violations_per_delay, passed).
    """
    violations_per_delay = {}
    for delay_months, row in p_sooner_table.iterrows():
        sorted_probabilities = row.sort_index().values
        n_violations = 0
        for earlier_p, later_p in zip(sorted_probabilities[:-1], sorted_probabilities[1:]):
            if (earlier_p - later_p) > monotonicity_tolerance:
                n_violations += 1
        violations_per_delay[delay_months] = n_violations

    passed = all(v <= max_violations_per_delay for v in violations_per_delay.values())
    return violations_per_delay, passed


def check_money_preference(p_sooner_table, max_p_sooner_at_zero_amount):
    """Fails if the model chooses '$0 now' over positive delayed money too often,
    at any delay. Assumes amount_dollars == 0 is present (via the fit grid or
    competence_probe_amounts).
    """
    if 0 not in p_sooner_table.columns:
        return {}, False, "amount $0 missing from data (add competence_probe_amounts: [0])"

    p_sooner_at_zero_by_delay = p_sooner_table[0].to_dict()
    passed = all(p <= max_p_sooner_at_zero_amount for p in p_sooner_at_zero_by_delay.values())
    return p_sooner_at_zero_by_delay, passed, None


def check_indifference_nonincreasing(indifference_df, tolerance, max_violations):
    """Requires empirical x*(d) to be non-increasing in delay.

    Counts adjacent delay steps where x*(d_{i+1}) - x*(d_i) > tolerance.
    Returns (n_violations, passed, amounts_by_delay dict).
    """
    if indifference_df is None or len(indifference_df) < 2:
        return 0, False, {}

    sorted_df = indifference_df.sort_values("delay_months")
    amounts = sorted_df["indifference_amount"].values.astype(float)
    delays = sorted_df["delay_months"].values
    n_violations = 0
    for earlier_x, later_x in zip(amounts[:-1], amounts[1:]):
        if (later_x - earlier_x) > tolerance:
            n_violations += 1

    amounts_by_delay = {
        float(d): float(x) for d, x in zip(delays, amounts)
    }
    passed = n_violations <= max_violations
    return n_violations, passed, amounts_by_delay


def run_competence_checks_for_model(model_choices_df, competence_config, fitting_config=None,
                                     delay_grid_months=None):
    fit_grid_df = fit_grid_choices(model_choices_df)
    p_sooner_fit_table = compute_p_sooner_table(fit_grid_df)
    # Money preference needs the $0 column; use the full frame (fit + probes).
    p_sooner_full_table = compute_p_sooner_table(model_choices_df)

    violations_per_delay, monotonicity_passed = check_monotonicity(
        p_sooner_fit_table,
        competence_config["monotonicity_tolerance"],
        competence_config["max_violations_per_delay"],
    )
    p_sooner_at_zero_by_delay, money_preference_passed, money_pref_note = check_money_preference(
        p_sooner_full_table,
        competence_config["max_p_sooner_at_zero_amount"],
    )

    indifference_df = estimate_indifference_amounts(model_choices_df, delay_grid_months)
    n_indiff_violations, indifference_nonincreasing_passed, amounts_by_delay = (
        check_indifference_nonincreasing(
            indifference_df,
            competence_config.get("indifference_nonincreasing_tolerance", 0.0),
            competence_config.get("max_indifference_violations", 0),
        )
    )

    fitting_config = fitting_config or {}
    k_lower_bound = float(fitting_config.get("k_lower_bound", 1e-6))
    k_upper_bound = float(fitting_config.get("k_upper_bound", 10.0))

    overall_passed = (
        monotonicity_passed
        and money_preference_passed
        and indifference_nonincreasing_passed
    )

    return {
        "monotonicity_passed": monotonicity_passed,
        "monotonicity_violations_per_delay": violations_per_delay,
        "money_preference_passed": money_preference_passed,
        "money_preference_note": money_pref_note,
        "p_sooner_at_zero_by_delay": p_sooner_at_zero_by_delay,
        "indifference_nonincreasing_passed": indifference_nonincreasing_passed,
        "n_indifference_violations": n_indiff_violations,
        "indifference_amounts_by_delay": amounts_by_delay,
        "indifference_points": indifference_df,
        "overall_passed": overall_passed,
        "k_lower_bound": k_lower_bound,
        "k_upper_bound": k_upper_bound,
        "p_sooner_table": p_sooner_fit_table,
    }


def plot_indifference_equivalents(indifference_records, figures_dir, suffix, reasoning_mode,
                                   later_amount_dollars):
    """Plots raw 50% immediate equivalents x*(d) vs delay, one panel per option-order stratum."""
    if not indifference_records:
        return None

    records_df = pd.DataFrame(indifference_records)
    order_levels = [label for label, _ in OPTION_ORDER_STRATA if label in set(records_df["option_order"])]
    if not order_levels:
        order_levels = sorted(records_df["option_order"].unique())

    n_orders = len(order_levels)
    figure, axes = plt.subplots(1, n_orders, figsize=(5.5 * n_orders, 5), squeeze=False)

    for order_index, option_order in enumerate(order_levels):
        axis = axes[0][order_index]
        order_df = records_df[records_df["option_order"] == option_order]
        model_names = list(dict.fromkeys(order_df["model_name"]))

        for model_index, model_name in enumerate(model_names):
            model_df = order_df[order_df["model_name"] == model_name].sort_values("delay_months")
            if model_df.empty:
                continue
            color = MODEL_COLORS[model_index % len(MODEL_COLORS)]
            passed = bool(model_df["indifference_nonincreasing_passed"].iloc[0])
            marker = "o" if passed else "x"
            axis.plot(
                model_df["delay_months"], model_df["indifference_amount"],
                marker=marker, color=color, linewidth=1.5,
                label=f"{model_name}" + ("" if passed else " (non-incr FAIL)"),
            )

        axis.set_xlabel("Delay (months)")
        axis.set_ylabel(f"50% immediate equivalent of ${later_amount_dollars}")
        axis.set_title(f"option_order={option_order} [{reasoning_mode}]")
        axis.legend(fontsize=6, loc="best")
        axis.set_ylim(bottom=0)

    figure.suptitle(
        "Raw 50% immediate equivalents (must be non-increasing in delay)",
        fontsize=12, y=1.02,
    )
    figure.tight_layout()
    figure_path = os.path.join(figures_dir, f"indifference_equivalents{suffix}.png")
    figure.savefig(figure_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return figure_path


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
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    later_amount = config["waiting_game"]["later_amount_dollars"]

    choices_csv_path = os.path.join(processed_dir, f"choices{suffix}.csv")
    choices_df = pd.read_csv(choices_csv_path)

    summary_rows = []
    indifference_plot_records = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        for option_order, sooner_is_a in OPTION_ORDER_STRATA:
            stratum_df = filter_by_option_order(model_choices_df, sooner_is_a)
            if stratum_df.empty:
                print(f"[{model_name} / {option_order}] no trials, skipping.")
                continue

            result = run_competence_checks_for_model(
                stratum_df, config["competence_checks"], config.get("fitting"),
                delay_grid_months,
            )

            note = f" ({result['money_preference_note']})" if result["money_preference_note"] else ""
            print(f"[{model_name} / {option_order}] "
                  f"mono={result['monotonicity_passed']} "
                  f"money={result['money_preference_passed']}{note} "
                  f"indiff_nonincr={result['indifference_nonincreasing_passed']} "
                  f"(violations={result['n_indifference_violations']}) "
                  f"-> overall_passed={result['overall_passed']}")
            print(f"  indifference x*(d): {result['indifference_amounts_by_delay']}")

            for delay, amount in result["indifference_amounts_by_delay"].items():
                indifference_plot_records.append({
                    "model_name": model_name,
                    "option_order": option_order,
                    "delay_months": delay,
                    "indifference_amount": amount,
                    "indifference_nonincreasing_passed": result["indifference_nonincreasing_passed"],
                })

            summary_rows.append({
                "model_name": model_name,
                "persona_enabled": persona_enabled,
                "option_order": option_order,
                "monotonicity_passed": result["monotonicity_passed"],
                "money_preference_passed": result["money_preference_passed"],
                "indifference_nonincreasing_passed": result["indifference_nonincreasing_passed"],
                "n_indifference_violations": result["n_indifference_violations"],
                "overall_passed": result["overall_passed"],
                "k_lower_bound": result["k_lower_bound"],
                "k_upper_bound": result["k_upper_bound"],
            })

    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(tables_dir, f"competence_checks{suffix}.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Wrote competence check summary to {summary_csv_path}")

    figure_path = plot_indifference_equivalents(
        indifference_plot_records, figures_dir, suffix, args.mode, later_amount
    )
    if figure_path:
        print(f"Wrote indifference-equivalents plot to {figure_path}")


if __name__ == "__main__":
    main()
