# Kirby MCQ-27: Sanity Check Summary

Modes included: direct. Item variant: verbatim. Approx. human benchmark (Kirby, Petry & Bickel 1999 / Kirby 2009 population norms): k = 0.016 per day.

| Model | Mode | Rank Monotonicity | Consistency | Consistency Pass | Magnitude Effect | logistic beta | logistic k Reliable? | **Valid Discount Rate** | geomean k | logistic k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b-instruct | direct | ❌ | 81.5% | ✅ | ❌ | 0.0023 | ❌ | **❌** | 0.24853 | 0.02124 [0.00000, 1.00000] |

## Column definitions

- **Rank Monotonicity**: sorting the 27 items by their own indifference k, P(choose larger-delayed reward) does not *increase* along that ordering by more than tolerance, for more than the allowed violations (`competence_checks.py::check_rank_monotonicity`) -- the Kirby analogue of the Waiting Game's grid-monotonicity check.
- **Consistency**: fraction of the 27 items whose binarized modal choice matches the best-fit candidate k (Kirby, 2000 / Kaplan et al. 2016 hand-scoring method).
- **Consistency Pass**: Consistency >= 75% (Kaplan et al. 2016 convention).
- **Magnitude Effect**: does `small_k > medium_k > large_k` hold (the classic human "more patience for larger rewards" pattern)? Reported, not gating.
- **logistic beta**: fitted logistic sensitivity of choices to the SIR/LDR/delay tradeoff (probabilistic-logistic MLE method); values below 0.05 mean choices barely track option value at all, so any fitted k is statistically unidentifiable.
- **logistic k Reliable?**: beta >= 0.05 AND fitted k did not land at the optimizer's bound.
- **Valid Discount Rate**: Rank Monotonicity Pass AND Consistency Pass AND logistic k Reliable -- the single bottom-line flag for whether either fitted k should be trusted at all.
- **geomean k**: hand-scoring composite k = geometric mean of small_k/medium_k/large_k, directly comparable to published human percentile norms.
- **logistic k [95% CI]**: MLE-fit discount rate per day (bootstrap 95% CI), from the probabilistic logistic method, shown regardless of reliability.
