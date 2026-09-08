"""Two-step hyperbolic discounting fit (Rachlin-style immediate equivalents).

For each model / condition / A/B-option-order stratum:

  1. For each delay d, estimate the sooner amount x*(d) at which the model is
     equally likely to choose sooner vs later ($later_amount), by interpolating
     the empirical P(choose sooner) curve across the amount grid to P=0.5.
  2. Fit the hyperbolic indifference function
         x*(d) = later_amount / (1 + k * d)
     to those empirical immediate equivalents via nonlinear least squares.

Bootstrap 95% CIs resample trials, recompute indifference points, and refit k.
Fits landing at the configured k bounds (or with poor R^2 / too few points)
are flagged unreliable; bound values themselves are still reported.

Results are stratified by A/B option order (pooled / sooner_A / sooner_B).

Usage: python src/fit_discounting.py [--config path/to/config.yaml]
       [--mode ...] [--persona|--no-persona]
"""

import argparse
import os

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from competence_checks import estimate_indifference_amounts
from config_utils import (
    OPTION_ORDER_STRATA,
    filter_by_option_order,
    load_config,
    resolve_dir_path,
    result_suffix,
    persona_enabled_from_config,
)
from persona import iter_persona_groups
from run_experiment import REASONING_MODES

BOUNDARY_RELATIVE_TOLERANCE = 1e-3
INITIAL_K = 0.01


def fitting_bounds_from_config(fitting_config):
    """Reads k bounds + quality gates from config."""
    k_lower = float(fitting_config.get("k_lower_bound", 1e-6))
    k_upper = float(fitting_config.get("k_upper_bound", 10.0))
    min_r_squared = float(fitting_config.get("min_r_squared", 0.5))
    min_n_points = int(fitting_config.get("min_n_indifference_points", 3))
    return {
        "k_lower_bound": k_lower,
        "k_upper_bound": k_upper,
        "min_r_squared": min_r_squared,
        "min_n_indifference_points": min_n_points,
    }


def is_near_bound(value, lower_bound, upper_bound):
    """True if `value` is at/near either optimizer bound (degenerate fit)."""
    if np.isnan(value):
        return True
    lower_tol = max(BOUNDARY_RELATIVE_TOLERANCE * abs(lower_bound), 1e-12)
    upper_tol = max(BOUNDARY_RELATIVE_TOLERANCE * abs(upper_bound), 1e-12)
    near_lower = abs(value - lower_bound) <= lower_tol
    near_upper = abs(value - upper_bound) <= upper_tol
    return near_lower or near_upper


def hyperbolic_value(amount_dollars, delay_months, k):
    return amount_dollars / (1.0 + k * delay_months)


def hyperbolic_indifference_curve(delay_months, k, later_amount_dollars):
    """x*(d) = later / (1 + k*d) — immediate equivalent of a delayed reward."""
    return later_amount_dollars / (1.0 + k * np.asarray(delay_months, dtype=float))


def trials_for_fitting(model_choices_df):
    """Drops competence-probe cells ($0) and parse failures before analysis."""
    parsed_trials_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    if "is_competence_probe" in parsed_trials_df.columns:
        probe_mask = parsed_trials_df["is_competence_probe"].fillna(False).astype(bool)
        parsed_trials_df = parsed_trials_df[~probe_mask]
    parsed_trials_df["chose_sooner_option"] = parsed_trials_df["chose_sooner_option"].astype(bool)
    return parsed_trials_df


def fit_k_to_indifference_points(indifference_df, later_amount_dollars, k_lower, k_upper):
    """Nonlinear least-squares fit of x(d)=later/(1+k*d) to indifference points.

    Returns (k, r_squared) or (nan, nan) if the fit fails / has too few points.
    """
    if indifference_df is None or len(indifference_df) == 0:
        return np.nan, np.nan

    delays = indifference_df["delay_months"].values.astype(float)
    amounts = indifference_df["indifference_amount"].values.astype(float)
    if len(delays) < 2:
        return np.nan, np.nan

    def model(delay, k):
        return hyperbolic_indifference_curve(delay, k, later_amount_dollars)

    try:
        popt, _ = curve_fit(
            model,
            delays,
            amounts,
            p0=[INITIAL_K],
            bounds=([k_lower], [k_upper]),
            maxfev=5000,
        )
        fitted_k = float(popt[0])
    except (RuntimeError, ValueError):
        return np.nan, np.nan

    predicted = model(delays, fitted_k)
    residuals = amounts - predicted
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((amounts - np.mean(amounts)) ** 2))
    r_squared = np.nan if ss_tot <= 0 else 1.0 - (ss_res / ss_tot)
    return fitted_k, r_squared


def bootstrap_k_confidence_interval(parsed_trials_df, later_amount_dollars, delay_grid_months,
                                     n_bootstrap, bootstrap_seed, k_lower, k_upper):
    """Trial-level bootstrap: resample -> indifference points -> refit k."""
    bootstrap_rng = np.random.default_rng(bootstrap_seed)
    n_trials = len(parsed_trials_df)
    if n_trials == 0:
        return np.nan, np.nan

    bootstrap_k_values = []
    for _ in range(n_bootstrap):
        resample_indices = bootstrap_rng.integers(0, n_trials, size=n_trials)
        resampled_df = parsed_trials_df.iloc[resample_indices]
        indifference_df = estimate_indifference_amounts(resampled_df, delay_grid_months)
        bootstrap_k, _ = fit_k_to_indifference_points(
            indifference_df, later_amount_dollars, k_lower, k_upper
        )
        if not np.isnan(bootstrap_k):
            bootstrap_k_values.append(bootstrap_k)

    if len(bootstrap_k_values) == 0:
        return np.nan, np.nan
    ci_low, ci_high = np.percentile(bootstrap_k_values, [2.5, 97.5])
    return float(ci_low), float(ci_high)


def fit_discounting_for_model(model_choices_df, later_amount_dollars, n_bootstrap,
                               bootstrap_seed, fitting_bounds, delay_grid_months=None):
    """Estimate indifference points, then NLS-fit hyperbolic k."""
    parsed_trials_df = trials_for_fitting(model_choices_df)
    k_lower = fitting_bounds["k_lower_bound"]
    k_upper = fitting_bounds["k_upper_bound"]
    min_r_squared = fitting_bounds["min_r_squared"]
    min_n_points = fitting_bounds["min_n_indifference_points"]

    indifference_df = estimate_indifference_amounts(parsed_trials_df, delay_grid_months)
    fitted_k, r_squared = fit_k_to_indifference_points(
        indifference_df, later_amount_dollars, k_lower, k_upper
    )
    ci_low, ci_high = bootstrap_k_confidence_interval(
        parsed_trials_df, later_amount_dollars, delay_grid_months,
        n_bootstrap, bootstrap_seed, k_lower, k_upper,
    )

    n_points = len(indifference_df)
    k_at_boundary = is_near_bound(fitted_k, k_lower, k_upper)
    poor_fit = np.isnan(r_squared) or r_squared < min_r_squared
    too_few_points = n_points < min_n_points
    k_is_reliable = (
        (not np.isnan(fitted_k))
        and (not k_at_boundary)
        and (not poor_fit)
        and (not too_few_points)
    )

    return {
        "k": fitted_k,
        "k_ci_low": ci_low,
        "k_ci_high": ci_high,
        "r_squared": r_squared,
        "n_indifference_points": n_points,
        "n_trials_fit": len(parsed_trials_df),
        "k_at_boundary": k_at_boundary,
        "k_lower_bound": k_lower,
        "k_upper_bound": k_upper,
        "k_is_reliable": k_is_reliable,
        "indifference_points": indifference_df,
    }


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

    choices_csv_path = os.path.join(processed_dir, f"choices{suffix}.csv")
    choices_df = pd.read_csv(choices_csv_path)
    later_amount_dollars = config["waiting_game"]["later_amount_dollars"]
    delay_grid_months = config["waiting_game"]["delay_grid_months"]
    n_bootstrap = config["fitting"]["n_bootstrap"]
    bootstrap_seed = config["fitting"]["bootstrap_seed"]
    fitting_bounds = fitting_bounds_from_config(config["fitting"])

    fit_rows = []
    indifference_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping fit.")
            continue

        for persona_id, discounting_group, persona_label, persona_df in iter_persona_groups(
            model_choices_df
        ):
            persona_tag = f" / {persona_id}" if persona_id is not None else ""
            for option_order, sooner_is_a in OPTION_ORDER_STRATA:
                stratum_df = filter_by_option_order(persona_df, sooner_is_a)
                if stratum_df.empty:
                    print(f"[{model_name}{persona_tag} / {option_order}] no trials, skipping fit.")
                    continue

                fit_result = fit_discounting_for_model(
                    stratum_df, later_amount_dollars, n_bootstrap, bootstrap_seed,
                    fitting_bounds, delay_grid_months,
                )
                indifference_df = fit_result.pop("indifference_points")
                for _, point in indifference_df.iterrows():
                    indifference_rows.append({
                        "model_name": model_name,
                        "persona_enabled": persona_enabled,
                        "persona_id": persona_id,
                        "persona_label": persona_label,
                        "persona_discounting_group": discounting_group,
                        "option_order": option_order,
                        "delay_months": point["delay_months"],
                        "indifference_amount": point["indifference_amount"],
                        "p_sooner_min": point["p_sooner_min"],
                        "p_sooner_max": point["p_sooner_max"],
                    })

                reliability_note = (
                    "" if fit_result["k_is_reliable"]
                    else "  [UNRELIABLE: k at bound, poor R^2, or too few indifference points]"
                )
                r2_str = "nan" if np.isnan(fit_result["r_squared"]) else f"{fit_result['r_squared']:.3f}"
                k_str = "nan" if np.isnan(fit_result["k"]) else f"{fit_result['k']:.5f}"
                ci_lo = fit_result["k_ci_low"]
                ci_hi = fit_result["k_ci_high"]
                ci_str = (
                    f"[{ci_lo:.5f}, {ci_hi:.5f}]"
                    if not (np.isnan(ci_lo) or np.isnan(ci_hi)) else "[nan, nan]"
                )
                print(f"[{model_name}{persona_tag} / {option_order}] k={k_str} 95% CI={ci_str} "
                      f"R^2={r2_str} (n_points={fit_result['n_indifference_points']}, "
                      f"n_trials={fit_result['n_trials_fit']}) "
                      f"bounds=[{fit_result['k_lower_bound']}, {fit_result['k_upper_bound']}]"
                      f"{reliability_note}")
                print(f"  indifference amounts: "
                      + ", ".join(
                          f"d={row['delay_months']:g}->${row['indifference_amount']:.1f}"
                          for _, row in indifference_df.iterrows()
                      ))

                fit_rows.append(dict(
                    model_name=model_name,
                    persona_enabled=persona_enabled,
                    persona_id=persona_id,
                    persona_label=persona_label,
                    persona_discounting_group=discounting_group,
                    option_order=option_order,
                    **fit_result,
                ))

    fit_df = pd.DataFrame(fit_rows)
    fit_csv_path = os.path.join(tables_dir, f"discount_rates{suffix}.csv")
    fit_df.to_csv(fit_csv_path, index=False)
    print(f"Wrote fitted discount rates to {fit_csv_path}")

    indifference_out = pd.DataFrame(indifference_rows)
    indifference_csv_path = os.path.join(tables_dir, f"indifference_amounts{suffix}.csv")
    indifference_out.to_csv(indifference_csv_path, index=False)
    print(f"Wrote empirical indifference amounts to {indifference_csv_path}")


if __name__ == "__main__":
    main()
