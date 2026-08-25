"""Fits a discount rate per model on the Kirby MCQ-27 data, via two methods
(both reported, per phase_1_extended.md's Kirby module design):

1. Standard hand/consistency method (Kirby, 2000; implemented per Kaplan
   et al. 2016 "MCQ Scorer", https://doi.org/10.1007/s40614-016-0070-9):
   binarize each item by its modal (>50%) sampled choice, then find the
   k-value that maximizes consistency across items (ties broken by geometric
   mean of tied candidates). Computed separately for small/medium/large
   magnitude subsets (9 items each) and overall (all 27 items pooled), per
   Kirby's standard convention. `geomean_k` = geometric mean of
   small_k/medium_k/large_k, directly comparable to published human
   population percentile norms (Kirby, 2009).

2. Probabilistic logistic method (adapting Wileyto et al., 2004): instead of
   binarizing, fits a discounted-random-utility logistic model (same
   functional form as ../temporal-discounting/src/fit_discounting.py, now
   generalized so SIR/LDR amounts vary per item instead of a single shared
   "later amount") via MLE on the raw (non-binarized) trial-level choices,
   with bootstrap 95% CIs. This is the primary quantity used for statistical
   comparison across models/conditions; avoids the information loss of
   binarizing stochastic LLM outputs. Hand-scoring above is retained purely
   for comparability to human normative tables.

Usage: python src/fit_discounting.py [--config path/to/config.yaml] [--mode direct|cot|one_shot|two_shot]
"""

import argparse
import math
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config_utils import load_config, load_kirby_items, resolve_dir_path, mode_suffix, variant_suffix
from run_experiment import REASONING_MODES

INITIAL_PARAMS = [0.01, 1.0]
BOUNDARY_RELATIVE_TOLERANCE = 1e-3
CANDIDATE_BOUNDARY_FACTOR = 10.0  # candidate k for "always chooses LDR" / "always chooses SIR" boundary regions


# ---------------------------------------------------------------------------
# Method 1: hand/consistency-maximization scoring
# ---------------------------------------------------------------------------

def binarize_item_choices(model_choices_df):
    """Per item_id, the modal (>50%) sampled choice: 1 if LDR chosen more
    often than not across the N sampled completions for that item, else 0.
    Exact 50/50 ties are counted as choosing SIR (0), the more conservative
    (patience-skeptical) tie-break.
    """
    parsed_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    parsed_df["chose_ldr"] = (~parsed_df["chose_sooner_option"].astype(bool)).astype(int)
    p_ldr_by_item = parsed_df.groupby("item_id")["chose_ldr"].mean()
    modal_choice_by_item = (p_ldr_by_item > 0.5).astype(int).to_dict()
    return modal_choice_by_item, p_ldr_by_item.to_dict()


def geometric_mean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def consistency_max_k(items_subset, modal_choice_by_item):
    """Finds the candidate discount rate k that maximizes the number of
    items whose predicted choice (LDR if candidate_k < item_k, else SIR)
    matches the binarized modal choice. Interior candidates are the
    geometric-mean midpoints between consecutive sorted item k-values. Two
    boundary regions represent "always prefers LDR" (classified using a
    value below the smallest item k, but *reported* as that smallest k,
    since it's the shallowest discount rate consistent with the data) and
    "always prefers SIR" (classified using, and reported as, the largest
    item k) -- matching the standard MCQ convention that an all-immediate or
    all-delayed respondent is assigned the extreme rank's k value (see e.g.
    the PhenX Toolkit MCQ scoring protocol). Ties are broken by taking the
    geometric mean of all tied (reported) candidates.

    Returns (best_k, consistency_score, n_items_scored).
    """
    scoreable_items = [it for it in items_subset if it["item_id"] in modal_choice_by_item]
    n_items = len(scoreable_items)
    if n_items == 0:
        return np.nan, np.nan, 0

    sorted_items = sorted(scoreable_items, key=lambda it: it["k_at_indifference"])
    sorted_ks = [it["k_at_indifference"] for it in sorted_items]

    # (classification_k, reported_k) pairs: classification_k is used to
    # predict each item's choice; reported_k is what gets returned if this
    # candidate wins (equal to classification_k for interior midpoints).
    candidates = [(sorted_ks[0] / CANDIDATE_BOUNDARY_FACTOR, sorted_ks[0])]
    for lower_k, upper_k in zip(sorted_ks[:-1], sorted_ks[1:]):
        midpoint_k = math.sqrt(lower_k * upper_k)
        candidates.append((midpoint_k, midpoint_k))
    candidates.append((sorted_ks[-1], sorted_ks[-1]))

    best_consistency = -1
    tied_reported_ks = []
    for classification_k, reported_k in candidates:
        n_correct = 0
        for item in sorted_items:
            predicted_chose_ldr = 1 if classification_k < item["k_at_indifference"] else 0
            actual_chose_ldr = modal_choice_by_item[item["item_id"]]
            if predicted_chose_ldr == actual_chose_ldr:
                n_correct += 1
        consistency = n_correct / n_items
        if consistency > best_consistency + 1e-12:
            best_consistency = consistency
            tied_reported_ks = [reported_k]
        elif abs(consistency - best_consistency) <= 1e-12:
            tied_reported_ks.append(reported_k)

    best_k = tied_reported_ks[0] if len(tied_reported_ks) == 1 else geometric_mean(tied_reported_ks)
    return best_k, best_consistency, n_items


def hand_scoring_method(model_choices_df, items):
    """Returns overall/small/medium/large/geomean k + overall consistency score."""
    modal_choice_by_item, p_ldr_by_item = binarize_item_choices(model_choices_df)

    overall_k, overall_consistency, n_overall = consistency_max_k(items, modal_choice_by_item)

    magnitude_results = {}
    for magnitude in ("small", "medium", "large"):
        magnitude_items = [it for it in items if it["magnitude"] == magnitude]
        magnitude_k, magnitude_consistency, n_scored = consistency_max_k(magnitude_items, modal_choice_by_item)
        magnitude_results[magnitude] = {
            "k": magnitude_k, "consistency": magnitude_consistency, "n_items_scored": n_scored,
        }

    small_k = magnitude_results["small"]["k"]
    medium_k = magnitude_results["medium"]["k"]
    large_k = magnitude_results["large"]["k"]
    geomean_k = (
        geometric_mean([small_k, medium_k, large_k])
        if all(not np.isnan(k) for k in (small_k, medium_k, large_k))
        else np.nan
    )
    magnitude_effect_holds = (
        (small_k > medium_k > large_k)
        if all(not np.isnan(k) for k in (small_k, medium_k, large_k))
        else None
    )

    return {
        "overall_k": overall_k,
        "overall_consistency": overall_consistency,
        "n_items_scored": n_overall,
        "small_k": small_k,
        "medium_k": medium_k,
        "large_k": large_k,
        "geomean_k": geomean_k,
        "magnitude_effect_holds": magnitude_effect_holds,
        "p_ldr_by_item": p_ldr_by_item,
    }


# ---------------------------------------------------------------------------
# Method 2: probabilistic logistic (discounted-random-utility MLE) scoring
# ---------------------------------------------------------------------------

def hyperbolic_value(amount_dollars, delay_days, k):
    return amount_dollars / (1.0 + k * delay_days)


def sigmoid(x):
    clipped_x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-clipped_x))


def choice_probabilities(trials_df, k, beta):
    sir_value = hyperbolic_value(trials_df["sir_amount_dollars"].values, 0.0, k)
    ldr_value = hyperbolic_value(trials_df["ldr_amount_dollars"].values, trials_df["delay_days"].values, k)
    return sigmoid(beta * (sir_value - ldr_value))  # P(choose SIR / sooner)


def negative_log_likelihood(params, trials_df):
    k, beta = params
    chose_sooner = trials_df["chose_sooner_option"].values.astype(float)

    p_sooner = choice_probabilities(trials_df, k, beta)
    p_sooner = np.clip(p_sooner, 1e-9, 1 - 1e-9)

    log_likelihood = chose_sooner * np.log(p_sooner) + (1 - chose_sooner) * np.log(1 - p_sooner)
    return -np.sum(log_likelihood)


def fit_k_and_beta(trials_df, param_bounds):
    fit_result = minimize(
        negative_log_likelihood,
        x0=INITIAL_PARAMS,
        args=(trials_df,),
        method="L-BFGS-B",
        bounds=param_bounds,
    )
    if not fit_result.success:
        return np.nan, np.nan
    fitted_k, fitted_beta = fit_result.x
    return fitted_k, fitted_beta


def is_near_bound(value, lower_bound, upper_bound):
    bound_span = upper_bound - lower_bound
    near_lower = (value - lower_bound) <= BOUNDARY_RELATIVE_TOLERANCE * bound_span
    near_upper = (upper_bound - value) <= BOUNDARY_RELATIVE_TOLERANCE * bound_span
    return near_lower or near_upper


def bootstrap_k_confidence_interval(trials_df, param_bounds, n_bootstrap, bootstrap_seed):
    bootstrap_rng = np.random.default_rng(bootstrap_seed)
    n_trials = len(trials_df)

    bootstrap_k_values = []
    for _ in range(n_bootstrap):
        resample_indices = bootstrap_rng.integers(0, n_trials, size=n_trials)
        resampled_df = trials_df.iloc[resample_indices]
        bootstrap_k, _ = fit_k_and_beta(resampled_df, param_bounds)
        if not np.isnan(bootstrap_k):
            bootstrap_k_values.append(bootstrap_k)

    if len(bootstrap_k_values) == 0:
        return np.nan, np.nan
    ci_low, ci_high = np.percentile(bootstrap_k_values, [2.5, 97.5])
    return ci_low, ci_high


def probabilistic_logistic_method(model_choices_df, fitting_config):
    parsed_trials_df = model_choices_df.dropna(subset=["chose_sooner_option"]).copy()
    parsed_trials_df["chose_sooner_option"] = parsed_trials_df["chose_sooner_option"].astype(bool)

    param_bounds = [
        (fitting_config["k_lower_bound"], fitting_config["k_upper_bound"]),
        (fitting_config["beta_lower_bound"], fitting_config["beta_upper_bound"]),
    ]

    fitted_k, fitted_beta = fit_k_and_beta(parsed_trials_df, param_bounds)
    ci_low, ci_high = bootstrap_k_confidence_interval(
        parsed_trials_df, param_bounds, fitting_config["n_bootstrap"], fitting_config["bootstrap_seed"]
    )

    low_choice_sensitivity = fitted_beta < fitting_config["low_sensitivity_beta_threshold"]
    k_at_boundary = is_near_bound(fitted_k, *param_bounds[0])

    return {
        "logistic_k": fitted_k,
        "logistic_beta": fitted_beta,
        "logistic_k_ci_low": ci_low,
        "logistic_k_ci_high": ci_high,
        "n_trials_fit": len(parsed_trials_df),
        "low_choice_sensitivity": low_choice_sensitivity,
        "k_at_boundary": k_at_boundary,
        "logistic_k_is_reliable": (not low_choice_sensitivity) and (not k_at_boundary),
    }


def fit_discounting_for_model(model_choices_df, items, fitting_config):
    hand_scoring_result = hand_scoring_method(model_choices_df, items)
    logistic_result = probabilistic_logistic_method(model_choices_df, fitting_config)
    return {**hand_scoring_result, **logistic_result}


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    items = load_kirby_items(config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])
    suffix = mode_suffix(args.mode) + variant_suffix(config["kirby"]["variant"])

    choices_csv_path = os.path.join(processed_dir, f"choices{suffix}.csv")
    choices_df = pd.read_csv(choices_csv_path)
    fitting_config = config["fitting"]

    fit_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping fit.")
            continue

        fit_result = fit_discounting_for_model(model_choices_df, items, fitting_config)
        reliability_note = "" if fit_result["logistic_k_is_reliable"] else "  [UNRELIABLE: low choice sensitivity or k at bound]"
        print(f"[{model_name}] geomean_k={fit_result['geomean_k']:.5f} "
              f"(small={fit_result['small_k']:.5f} medium={fit_result['medium_k']:.5f} large={fit_result['large_k']:.5f}) "
              f"consistency={fit_result['overall_consistency']:.1%} | "
              f"logistic_k={fit_result['logistic_k']:.5f} "
              f"95% CI=[{fit_result['logistic_k_ci_low']:.5f}, {fit_result['logistic_k_ci_high']:.5f}] "
              f"beta={fit_result['logistic_beta']:.3f}{reliability_note}")

        fit_row = {k: v for k, v in fit_result.items() if k != "p_ldr_by_item"}
        fit_rows.append(dict(model_name=model_name, **fit_row))

    fit_df = pd.DataFrame(fit_rows)
    fit_csv_path = os.path.join(tables_dir, f"discount_rates{suffix}.csv")
    fit_df.to_csv(fit_csv_path, index=False)
    print(f"Wrote fitted discount rates to {fit_csv_path}")


if __name__ == "__main__":
    main()
