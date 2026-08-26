"""Fits a hyperbolic discounting model per model via maximum likelihood on
the raw trial-level binary choices, with bootstrap 95% CIs.

Model (discounted-random-utility, logistic link -- Holt & Laury 2002 /
Andersen et al. 2008 style, as used in Goli & Singh 2305.02531 sec 3.3):

    V(amount, delay) = amount / (1 + k * delay)      # hyperbolic value
    P(choose sooner) = sigmoid(beta * (V_sooner - V_later))

Free parameters: k (discount rate, per month) and beta (choice sensitivity /
inverse noise). Fit by minimizing the trial-level Bernoulli negative
log-likelihood.

Fits landing at the configured k bounds are flagged unreliable (cut from
valid_discount_rate) but the bound values themselves are still reported.

Usage: python src/fit_discounting.py [--config path/to/config.yaml]
       [--mode ...] [--persona|--no-persona]
"""

import argparse
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config_utils import (
    load_config,
    resolve_dir_path,
    result_suffix,
    persona_enabled_from_config,
)
from run_experiment import REASONING_MODES

BOUNDARY_RELATIVE_TOLERANCE = 1e-3
INITIAL_PARAMS = [0.01, 1.0]


def fitting_bounds_from_config(fitting_config):
    """Reads (k, beta) optimizer bounds + reliability threshold from config,
    with the historical hard-coded defaults as fallbacks.
    """
    k_lower = float(fitting_config.get("k_lower_bound", 1e-6))
    k_upper = float(fitting_config.get("k_upper_bound", 10.0))
    beta_lower = float(fitting_config.get("beta_lower_bound", 1e-6))
    beta_upper = float(fitting_config.get("beta_upper_bound", 20.0))
    low_beta_threshold = float(fitting_config.get("low_sensitivity_beta_threshold", 0.05))
    return {
        "param_bounds": [(k_lower, k_upper), (beta_lower, beta_upper)],
        "k_lower_bound": k_lower,
        "k_upper_bound": k_upper,
        "beta_lower_bound": beta_lower,
        "beta_upper_bound": beta_upper,
        "low_sensitivity_beta_threshold": low_beta_threshold,
    }


def is_near_bound(value, lower_bound, upper_bound):
    """True if `value` is at/near either optimizer bound (degenerate fit).

    Uses a per-bound relative tolerance so a lower bound of 1e-6 does not
    incorrectly flag every small-but-valid k (e.g. human-scale ~0.01) as a
    boundary hit — which the old span-relative rule did, because 0.1% of a
    [1e-6, 10] span is 0.01 absolute.
    """
    if np.isnan(value):
        return True
    lower_tol = max(BOUNDARY_RELATIVE_TOLERANCE * abs(lower_bound), 1e-12)
    upper_tol = max(BOUNDARY_RELATIVE_TOLERANCE * abs(upper_bound), 1e-12)
    near_lower = abs(value - lower_bound) <= lower_tol
    near_upper = abs(value - upper_bound) <= upper_tol
    return near_lower or near_upper


def hyperbolic_value(amount_dollars, delay_months, k):
    return amount_dollars / (1.0 + k * delay_months)


def sigmoid(x):
    clipped_x = np.clip(x, -500, 500)  # avoid exp() overflow far from the decision boundary
    return 1.0 / (1.0 + np.exp(-clipped_x))


def choice_probabilities(model_choices_df, later_amount_dollars, k, beta):
    sooner_value = hyperbolic_value(model_choices_df["amount_dollars"].values, 0.0, k)
    later_value = hyperbolic_value(later_amount_dollars, model_choices_df["delay_months"].values, k)
    return sigmoid(beta * (sooner_value - later_value))


def negative_log_likelihood(params, model_choices_df, later_amount_dollars):
    k, beta = params
    chose_sooner = model_choices_df["chose_sooner_option"].values.astype(float)

    p_sooner = choice_probabilities(model_choices_df, later_amount_dollars, k, beta)
    p_sooner = np.clip(p_sooner, 1e-9, 1 - 1e-9)  # avoid log(0)

    log_likelihood = chose_sooner * np.log(p_sooner) + (1 - chose_sooner) * np.log(1 - p_sooner)
    return -np.sum(log_likelihood)


def fit_k_and_beta(model_choices_df, later_amount_dollars, param_bounds):
    """One MLE fit on the given trials. Returns (k, beta) or (nan, nan) if it fails."""
    fit_result = minimize(
        negative_log_likelihood,
        x0=INITIAL_PARAMS,
        args=(model_choices_df, later_amount_dollars),
        method="L-BFGS-B",
        bounds=param_bounds,
    )
    if not fit_result.success:
        return np.nan, np.nan
    fitted_k, fitted_beta = fit_result.x
    return fitted_k, fitted_beta


def bootstrap_k_confidence_interval(model_choices_df, later_amount_dollars, n_bootstrap,
                                     bootstrap_seed, param_bounds):
    """Row-level (trial-level) bootstrap over the parsed trials, refitting k each time."""
    bootstrap_rng = np.random.default_rng(bootstrap_seed)
    n_trials = len(model_choices_df)

    bootstrap_k_values = []
    for _ in range(n_bootstrap):
        resample_indices = bootstrap_rng.integers(0, n_trials, size=n_trials)
        resampled_df = model_choices_df.iloc[resample_indices]
        bootstrap_k, _ = fit_k_and_beta(resampled_df, later_amount_dollars, param_bounds)
        if not np.isnan(bootstrap_k):
            bootstrap_k_values.append(bootstrap_k)

    if len(bootstrap_k_values) == 0:
        return np.nan, np.nan
    ci_low, ci_high = np.percentile(bootstrap_k_values, [2.5, 97.5])
    return ci_low, ci_high


def trials_for_fitting(model_choices_df):
    """Drops competence-probe cells ($0) and parse failures before fitting."""
    parsed_trials_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    if "is_competence_probe" in parsed_trials_df.columns:
        probe_mask = parsed_trials_df["is_competence_probe"].fillna(False).astype(bool)
        parsed_trials_df = parsed_trials_df[~probe_mask]
    parsed_trials_df["chose_sooner_option"] = parsed_trials_df["chose_sooner_option"].astype(bool)
    return parsed_trials_df


def fit_discounting_for_model(model_choices_df, later_amount_dollars, n_bootstrap,
                               bootstrap_seed, fitting_bounds):
    parsed_trials_df = trials_for_fitting(model_choices_df)
    param_bounds = fitting_bounds["param_bounds"]
    k_lower = fitting_bounds["k_lower_bound"]
    k_upper = fitting_bounds["k_upper_bound"]
    low_beta_threshold = fitting_bounds["low_sensitivity_beta_threshold"]

    fitted_k, fitted_beta = fit_k_and_beta(parsed_trials_df, later_amount_dollars, param_bounds)
    ci_low, ci_high = bootstrap_k_confidence_interval(
        parsed_trials_df, later_amount_dollars, n_bootstrap, bootstrap_seed, param_bounds
    )

    # Low beta means P(sooner) barely responds to option value -> the likelihood
    # surface over k is nearly flat, so a fitted k (esp. one sitting at a bound)
    # should not be read as a meaningful discount rate.
    low_choice_sensitivity = (
        np.isnan(fitted_beta) or fitted_beta < low_beta_threshold
    )
    k_at_boundary = is_near_bound(fitted_k, k_lower, k_upper)

    return {
        "k": fitted_k,
        "beta": fitted_beta,
        "k_ci_low": ci_low,
        "k_ci_high": ci_high,
        "n_trials_fit": len(parsed_trials_df),
        "low_choice_sensitivity": low_choice_sensitivity,
        "k_at_boundary": k_at_boundary,
        "k_lower_bound": k_lower,
        "k_upper_bound": k_upper,
        # Cut upper/lower-bound hits from reliability; bounds themselves still reported.
        "k_is_reliable": (not low_choice_sensitivity) and (not k_at_boundary),
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
    n_bootstrap = config["fitting"]["n_bootstrap"]
    bootstrap_seed = config["fitting"]["bootstrap_seed"]
    fitting_bounds = fitting_bounds_from_config(config["fitting"])

    fit_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping fit.")
            continue

        fit_result = fit_discounting_for_model(
            model_choices_df, later_amount_dollars, n_bootstrap, bootstrap_seed, fitting_bounds
        )
        reliability_note = "" if fit_result["k_is_reliable"] else "  [UNRELIABLE: low choice sensitivity or k at bound]"
        print(f"[{model_name}] k={fit_result['k']:.5f} "
              f"95% CI=[{fit_result['k_ci_low']:.5f}, {fit_result['k_ci_high']:.5f}] "
              f"beta={fit_result['beta']:.3f} (n={fit_result['n_trials_fit']}) "
              f"bounds=[{fit_result['k_lower_bound']}, {fit_result['k_upper_bound']}]"
              f"{reliability_note}")

        fit_rows.append(dict(model_name=model_name, persona_enabled=persona_enabled, **fit_result))

    fit_df = pd.DataFrame(fit_rows)
    fit_csv_path = os.path.join(tables_dir, f"discount_rates{suffix}.csv")
    fit_df.to_csv(fit_csv_path, index=False)
    print(f"Wrote fitted discount rates to {fit_csv_path}")


if __name__ == "__main__":
    main()
