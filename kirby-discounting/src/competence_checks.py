"""Per-model competence/data-quality gating checks, run before trusting a
fitted discount rate. Kirby-analogues of the Waiting Game's monotonicity +
money-preference checks (../temporal-discounting/src/competence_checks.py),
adapted to a fixed 27-item instrument rather than a synthetic grid:

Check A (rank-order monotonicity): sorting items by their own indifference
k, P(choose LDR) should be non-decreasing as item k increases. This follows
from the item design itself: item k is defined so that a person with a fixed
personal discount rate k_person prefers LDR exactly when k_person < item_k
(see fit_discounting.py docstring), so as item_k rises, predicted choice
flips from SIR to LDR at most once and never flips back -- e.g. Kaplan et
al. (2016) Table 1's canonical "steep discounter" response pattern is
0,0,...,0,1,1,...,1 when items are sorted by ascending k. A model whose
P(choose LDR) *drops* as item_k increases isn't tracking the SIR/LDR/delay
tradeoff coherently. This is the structural analogue of the Waiting Game's
"P(sooner) non-decreasing in amount" check, just along the Kirby items'
built-in one-dimensional difficulty ordering instead of a 2D amount x delay
grid.

Check B (consistency score): per Kaplan et al. (2016)'s convention, the
overall hand-scoring consistency (fraction of the 27 items whose binarized
modal choice matches the best-fit candidate k) must be >= 75% or the model's
run is flagged low-quality/unreliable.

Magnitude-effect check (reported, not gating): does small_k > medium_k >
large_k hold (the classic human "more patience for larger rewards" effect)?

Usage: python src/competence_checks.py [--config path/to/config.yaml] [--mode direct|cot|one_shot|two_shot]
"""

import argparse
import os

import pandas as pd

from config_utils import load_config, load_kirby_items, resolve_dir_path, mode_suffix, variant_suffix
from fit_discounting import hand_scoring_method
from run_experiment import REASONING_MODES


def check_rank_monotonicity(items, p_ldr_by_item, tolerance, max_violations):
    """Sorts items by their own k ascending and counts how many adjacent
    steps see P(choose LDR) *decrease* by more than `tolerance` (a
    violation: as item_k rises, LDR should become easier, not harder, to
    prefer -- see the module docstring). Returns (n_violations, passed).
    """
    scoreable_items = [it for it in items if it["item_id"] in p_ldr_by_item]
    sorted_items = sorted(scoreable_items, key=lambda it: it["k_at_indifference"])
    p_ldr_sequence = [p_ldr_by_item[it["item_id"]] for it in sorted_items]

    n_violations = 0
    for earlier_p, later_p in zip(p_ldr_sequence[:-1], p_ldr_sequence[1:]):
        if (earlier_p - later_p) > tolerance:
            n_violations += 1

    passed = n_violations <= max_violations
    return n_violations, passed


def run_competence_checks_for_model(model_choices_df, items, competence_config):
    hand_scoring_result = hand_scoring_method(model_choices_df, items)
    p_ldr_by_item = hand_scoring_result["p_ldr_by_item"]

    n_rank_violations, rank_monotonicity_passed = check_rank_monotonicity(
        items, p_ldr_by_item,
        competence_config["rank_monotonicity_tolerance"],
        competence_config["max_rank_monotonicity_violations"],
    )

    consistency_passed = hand_scoring_result["overall_consistency"] >= competence_config["min_consistency_score"]

    return {
        "rank_monotonicity_passed": rank_monotonicity_passed,
        "n_rank_monotonicity_violations": n_rank_violations,
        "overall_consistency": hand_scoring_result["overall_consistency"],  # kept for the printed log line only
        "consistency_passed": consistency_passed,
        "magnitude_effect_holds": hand_scoring_result["magnitude_effect_holds"],  # kept for the printed log line only
        "overall_passed": rank_monotonicity_passed and consistency_passed,
        "p_ldr_by_item": p_ldr_by_item,
    }


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

    summary_rows = []
    for model_name in config["models"]:
        model_choices_df = choices_df[choices_df["model_name"] == model_name]
        if model_choices_df.empty:
            print(f"[{model_name}] no parsed choices found, skipping.")
            continue

        result = run_competence_checks_for_model(model_choices_df, items, config["competence_checks"])

        print(f"[{model_name}] rank_monotonicity_passed={result['rank_monotonicity_passed']} "
              f"(violations={result['n_rank_monotonicity_violations']}/26) "
              f"consistency={result['overall_consistency']:.1%} (passed={result['consistency_passed']}) "
              f"magnitude_effect_holds={result['magnitude_effect_holds']} "
              f"-> overall_passed={result['overall_passed']}")

        # Note: overall_consistency and magnitude_effect_holds are NOT
        # duplicated here -- fit_discounting.py's discount_rates.csv already
        # carries both (it computes the same hand-scoring result), and
        # analyze.py merges the two tables on model_name; keeping both
        # columns in both CSVs would produce ambiguous _x/_y suffixes.
        summary_rows.append({
            "model_name": model_name,
            "rank_monotonicity_passed": result["rank_monotonicity_passed"],
            "n_rank_monotonicity_violations": result["n_rank_monotonicity_violations"],
            "consistency_passed": result["consistency_passed"],
            "overall_passed": result["overall_passed"],
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(tables_dir, f"competence_checks{suffix}.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Wrote competence check summary to {summary_csv_path}")


if __name__ == "__main__":
    main()
