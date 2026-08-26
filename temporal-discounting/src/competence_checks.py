"""Per-model competence gating checks, run before fitting discount rates.

Check A (monotonicity): P(choose sooner) must be non-decreasing in the sooner
amount x, for each fixed delay. Evaluated on the fit-grid amounts only
(competence-probe $0 cells are excluded so they don't distort the amount
ordering). A model that chooses the sooner option less often as it gets
larger isn't tracking amount at all.

Check B (money preference): a model must not prefer $0 now over a positive
amount of money later, at any delay. Uses competence-probe $0 cells when
$0 is not in the main amount grid.

Reliability note (reported here for the competence table, computed in
fit_discounting): fitted k landing at the configured upper/lower bound is
cut from k_is_reliable / valid_discount_rate, but the bound values
themselves are still reported so the exclusion rule is auditable.

Usage: python src/competence_checks.py [--config path/to/config.yaml]
       [--mode ...] [--persona|--no-persona]
"""

import argparse
import os

import pandas as pd

from config_utils import (
    load_config,
    resolve_dir_path,
    result_suffix,
    persona_enabled_from_config,
)
from run_experiment import REASONING_MODES


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
    p_sooner_table = parsed_rows_df.pivot_table(
        index="delay_months",
        columns="amount_dollars",
        values="chose_sooner_option",
        aggfunc="mean",
    )
    return p_sooner_table.sort_index().sort_index(axis=1)


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


def run_competence_checks_for_model(model_choices_df, competence_config, fitting_config=None):
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

    fitting_config = fitting_config or {}
    k_lower_bound = float(fitting_config.get("k_lower_bound", 1e-6))
    k_upper_bound = float(fitting_config.get("k_upper_bound", 10.0))

    return {
        "monotonicity_passed": monotonicity_passed,
        "monotonicity_violations_per_delay": violations_per_delay,
        "money_preference_passed": money_preference_passed,
        "money_preference_note": money_pref_note,
        "p_sooner_at_zero_by_delay": p_sooner_at_zero_by_delay,
        "overall_passed": monotonicity_passed and money_preference_passed,
        # Reasonable k bounds reported alongside competence (cuts applied in fit).
        "k_lower_bound": k_lower_bound,
        "k_upper_bound": k_upper_bound,
        "p_sooner_table": p_sooner_fit_table,
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

    summary_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        result = run_competence_checks_for_model(
            model_choices_df, config["competence_checks"], config.get("fitting")
        )

        note = f" ({result['money_preference_note']})" if result["money_preference_note"] else ""
        print(f"[{model_name}] monotonicity_passed={result['monotonicity_passed']} "
              f"money_preference_passed={result['money_preference_passed']}{note} "
              f"-> overall_passed={result['overall_passed']} "
              f"(k bounds [{result['k_lower_bound']}, {result['k_upper_bound']}] "
              f"cut from reliability when hit)")
        print(f"  monotonicity violations per delay: {result['monotonicity_violations_per_delay']}")
        print(f"  P(choose $0 now) per delay: {result['p_sooner_at_zero_by_delay']}")

        summary_rows.append({
            "model_name": model_name,
            "persona_enabled": persona_enabled,
            "monotonicity_passed": result["monotonicity_passed"],
            "money_preference_passed": result["money_preference_passed"],
            "overall_passed": result["overall_passed"],
            "k_lower_bound": result["k_lower_bound"],
            "k_upper_bound": result["k_upper_bound"],
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(tables_dir, f"competence_checks{suffix}.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Wrote competence check summary to {summary_csv_path}")


if __name__ == "__main__":
    main()
