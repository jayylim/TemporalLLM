"""Per-model competence gating checks, run before fitting discount rates.

Check A (monotonicity): P(choose sooner) must be non-decreasing in the sooner
amount x, for each fixed delay. A model that chooses the sooner option less
often as it gets larger isn't tracking amount at all.

Check B (money preference): a model must not prefer $0 now over a positive
amount of money later, at any delay.

Models failing either check are flagged "no valid discount rate" and
excluded from the k comparison in analyze.py, per PREREGISTRATION.md.

Usage: python src/competence_checks.py [--config path/to/config.yaml]
"""

import argparse
import os

import pandas as pd

from config_utils import load_config, resolve_dir_path, mode_suffix


def compute_p_sooner_table(model_choices_df):
    """Pivot table: rows = delay_months, columns = amount_dollars, values =
    P(chose sooner option), computed only over trials that parsed (A or B).
    """
    parsed_rows_df = model_choices_df.dropna(subset=["chose_sooner_option"])
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
    at any delay. Assumes amount_dollars == 0 is present in the grid.
    """
    if 0 not in p_sooner_table.columns:
        return {}, True  # nothing to check if $0 wasn't in the grid

    p_sooner_at_zero_by_delay = p_sooner_table[0].to_dict()
    passed = all(p <= max_p_sooner_at_zero_amount for p in p_sooner_at_zero_by_delay.values())
    return p_sooner_at_zero_by_delay, passed


def run_competence_checks_for_model(model_choices_df, competence_config):
    p_sooner_table = compute_p_sooner_table(model_choices_df)

    violations_per_delay, monotonicity_passed = check_monotonicity(
        p_sooner_table,
        competence_config["monotonicity_tolerance"],
        competence_config["max_violations_per_delay"],
    )
    p_sooner_at_zero_by_delay, money_preference_passed = check_money_preference(
        p_sooner_table,
        competence_config["max_p_sooner_at_zero_amount"],
    )

    return {
        "monotonicity_passed": monotonicity_passed,
        "monotonicity_violations_per_delay": violations_per_delay,
        "money_preference_passed": money_preference_passed,
        "p_sooner_at_zero_by_delay": p_sooner_at_zero_by_delay,
        "overall_passed": monotonicity_passed and money_preference_passed,
        "p_sooner_table": p_sooner_table,
    }


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=["direct", "cot"], default="direct")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])
    tables_dir = resolve_dir_path(config["paths"]["results_tables_dir"])

    choices_csv_path = os.path.join(processed_dir, f"choices{mode_suffix(args.mode)}.csv")
    choices_df = pd.read_csv(choices_csv_path)

    summary_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        result = run_competence_checks_for_model(model_choices_df, config["competence_checks"])

        print(f"[{model_name}] monotonicity_passed={result['monotonicity_passed']} "
              f"money_preference_passed={result['money_preference_passed']} "
              f"-> overall_passed={result['overall_passed']}")
        print(f"  monotonicity violations per delay: {result['monotonicity_violations_per_delay']}")
        print(f"  P(choose $0 now) per delay: {result['p_sooner_at_zero_by_delay']}")

        summary_rows.append({
            "model_name": model_name,
            "monotonicity_passed": result["monotonicity_passed"],
            "money_preference_passed": result["money_preference_passed"],
            "overall_passed": result["overall_passed"],
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(tables_dir, f"competence_checks{mode_suffix(args.mode)}.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Wrote competence check summary to {summary_csv_path}")


if __name__ == "__main__":
    main()
