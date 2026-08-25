"""Fits a hyperbolic discounting model per model via maximum likelihood on
the raw trial-level binary choices, with bootstrap 95% CIs.

Model (discounted-random-utility, logistic link -- Holt & Laury 2002 /
Andersen et al. 2008 style, as used in Goli & Singh 2305.02531 sec 3.3):

    V(amount, delay) = amount / (1 + k * delay)      # hyperbolic value
    P(choose sooner) = sigmoid(beta * (V_sooner - V_later))

Free parameters: k (discount rate, per month) and beta (choice sensitivity /
inverse noise). Fit by minimizing the trial-level Bernoulli negative
log-likelihood.

Usage: python src/fit_discounting.py [--config path/to/config.yaml]
"""

import argparse
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config_utils import load_config, resolve_dir_path, mode_suffix
from run_experiment import REASONING_MODES

PARAM_BOUNDS = [(1e-6, 10.0), (1e-6, 20.0)]  # (k, beta)
INITIAL_PARAMS = [0.01, 1.0]
LOW_SENSITIVITY_BETA_THRESHOLD = 0.05  # beta below this means choices barely track option value -> k is unidentifiable
BOUNDARY_RELATIVE_TOLERANCE = 1e-3


def is_near_bound(value, lower_bound, upper_bound):
    bound_span = upper_bound - lower_bound
    near_lower = (value - lower_bound) <= BOUNDARY_RELATIVE_TOLERANCE * bound_span
    near_upper = (upper_bound - value) <= BOUNDARY_RELATIVE_TOLERANCE * bound_span
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


def fit_k_and_beta(model_choices_df, later_amount_dollars):
    """One MLE fit on the given trials. Returns (k, beta) or (nan, nan) if it fails."""
    fit_result = minimize(
        negative_log_likelihood,
        x0=INITIAL_PARAMS,
        args=(model_choices_df, later_amount_dollars),
        method="L-BFGS-B",
        bounds=PARAM_BOUNDS,
    )
    if not fit_result.success:
        return np.nan, np.nan
    fitted_k, fitted_beta = fit_result.x
    return fitted_k, fitted_beta


def bootstrap_k_confidence_interval(model_choices_df, later_amount_dollars, n_bootstrap, bootstrap_seed):
    """Row-level (trial-level) bootstrap over the parsed trials, refitting k each time."""
    bootstrap_rng = np.random.default_rng(bootstrap_seed)
    n_trials = len(model_choices_df)

    bootstrap_k_values = []
    for _ in range(n_bootstrap):
        resample_indices = bootstrap_rng.integers(0, n_trials, size=n_trials)
        resampled_df = model_choices_df.iloc[resample_indices]
        bootstrap_k, _ = fit_k_and_beta(resampled_df, later_amount_dollars)
        if not np.isnan(bootstrap_k):
            bootstrap_k_values.append(bootstrap_k)

    if len(bootstrap_k_values) == 0:
        return np.nan, np.nan
    ci_low, ci_high = np.percentile(bootstrap_k_values, [2.5, 97.5])
    return ci_low, ci_high


def fit_discounting_for_model(model_choices_df, later_amount_dollars, n_bootstrap, bootstrap_seed):
    parsed_trials_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    parsed_trials_df["chose_sooner_option"] = parsed_trials_df["chose_sooner_option"].astype(bool)

    fitted_k, fitted_beta = fit_k_and_beta(parsed_trials_df, later_amount_dollars)
    ci_low, ci_high = bootstrap_k_confidence_interval(
        parsed_trials_df, later_amount_dollars, n_bootstrap, bootstrap_seed
    )

    # Low beta means P(sooner) barely responds to option value -> the likelihood
    # surface over k is nearly flat, so a fitted k (esp. one sitting at a bound)
    # should not be read as a meaningful discount rate.
    low_choice_sensitivity = fitted_beta < LOW_SENSITIVITY_BETA_THRESHOLD
    k_at_boundary = is_near_bound(fitted_k, *PARAM_BOUNDS[0])

    return {
        "k": fitted_k,
        "beta": fitted_beta,
        "k_ci_low": ci_low,
        "k_ci_high": ci_high,
        "n_trials_fit": len(parsed_trials_df),
        "low_choice_sensitivity": low_choice_sensitivity,
        "k_at_boundary": k_at_boundary,
        "k_is_reliable": (not low_choice_sensitivity) and (not k_at_boundary),
    }


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])

    choices_csv_path = os.path.join(processed_dir, f"choices{mode_suffix(args.mode)}.csv")
    choices_df = pd.read_csv(choices_csv_path)
    later_amount_dollars = config["waiting_game"]["later_amount_dollars"]
    n_bootstrap = config["fitting"]["n_bootstrap"]
    bootstrap_seed = config["fitting"]["bootstrap_seed"]

    fit_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping fit.")
            continue

        fit_result = fit_discounting_for_model(
            model_choices_df, later_amount_dollars, n_bootstrap, bootstrap_seed
        )
        reliability_note = "" if fit_result["k_is_reliable"] else "  [UNRELIABLE: low choice sensitivity or k at bound]"
        print(f"[{model_name}] k={fit_result['k']:.5f} "
              f"95% CI=[{fit_result['k_ci_low']:.5f}, {fit_result['k_ci_high']:.5f}] "
              f"beta={fit_result['beta']:.3f} (n={fit_result['n_trials_fit']}){reliability_note}")

        fit_rows.append(dict(model_name=model_name, **fit_result))

    fit_df = pd.DataFrame(fit_rows)
    fit_csv_path = os.path.join(tables_dir, f"discount_rates{mode_suffix(args.mode)}.csv")
    fit_df.to_csv(fit_csv_path, index=False)
    print(f"Wrote fitted discount rates to {fit_csv_path}")


if __name__ == "__main__":
    main()
