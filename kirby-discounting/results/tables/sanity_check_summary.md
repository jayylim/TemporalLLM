# Kirby MCQ-27: Sanity Check Summary

Modes included: direct, one-shot, two-shot. Item variant: verbatim. Approx. human benchmark (Kirby, Petry & Bickel 1999 / Kirby 2009 population norms): k = 0.016 per day.

| Model | Mode | Rank Monotonicity | Consistency | Consistency Pass | Magnitude Effect | logistic beta | logistic k Reliable? | **Valid Discount Rate** | geomean k | logistic k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b-instruct | direct | ❌ | 81.5% | ✅ | ❌ | 0.0093 | ❌ | **❌** | 0.00018 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:1.5b-instruct | one-shot | ❌ | 66.7% | ❌ | ❌ | 0.0029 | ❌ | **❌** | 0.10859 | 0.24342 [0.00000, 1.00000] |
| qwen2.5:1.5b-instruct | two-shot | ❌ | 92.6% | ✅ | ❌ | 0.0143 | ❌ | **❌** | 0.19905 | 1.00000 [0.97444, 1.00000] |
| qwen2.5:3b-instruct | direct | ❌ | 96.3% | ✅ | ❌ | 0.0644 | ❌ | **❌** | 0.24853 | 1.00000 [1.00000, 1.00000] |
| qwen2.5:3b-instruct | one-shot | ❌ | 100.0% | ✅ | ❌ | 0.1456 | ❌ | **❌** | 0.00016 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:3b-instruct | two-shot | ❌ | 92.6% | ✅ | ✅ | 0.0621 | ❌ | **❌** | 0.17054 | 1.00000 [0.65924, 1.00000] |
| qwen2.5:7b-instruct | direct | ❌ | 88.9% | ✅ | ❌ | 0.0406 | ❌ | **❌** | 0.17047 | 0.14140 [0.08785, 0.25195] |
| qwen2.5:7b-instruct | one-shot | ❌ | 85.2% | ✅ | ❌ | 0.0388 | ❌ | **❌** | 0.00016 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:7b-instruct | two-shot | ❌ | 85.2% | ✅ | ❌ | 0.0297 | ❌ | **❌** | 0.17047 | 0.42246 [0.19828, 1.00000] |
| qwen3:4b-instruct-2507-q4_K_M | direct | ❌ | 77.8% | ✅ | ✅ | 0.0302 | ❌ | **❌** | 0.00040 | 0.00000 [0.00000, 0.00000] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | ✅ | 100.0% | ✅ | ❌ | 2.3809 | ❌ | **❌** | 0.24853 | 1.00000 [1.00000, 1.00000] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | ✅ | 100.0% | ✅ | ❌ | 0.7970 | ✅ | **✅** | 0.24853 | 0.28568 [0.27177, 0.30925] |

## Column definitions

- **Rank Monotonicity**: sorting the 27 items by their own indifference k, P(choose larger-delayed reward) does not *decrease* along that ordering by more than tolerance, for more than the allowed violations (`competence_checks.py::check_rank_monotonicity`) -- the Kirby analogue of the Waiting Game's grid-monotonicity check.
- **Consistency**: fraction of the 27 items whose binarized modal choice matches the best-fit candidate k (Kirby, 2000 / Kaplan et al. 2016 hand-scoring method).
- **Consistency Pass**: Consistency >= 75% (Kaplan et al. 2016 convention).
- **Magnitude Effect**: does `small_k > medium_k > large_k` hold (the classic human "more patience for larger rewards" pattern)? Reported, not gating.
- **logistic beta**: fitted logistic sensitivity of choices to the SIR/LDR/delay tradeoff (probabilistic-logistic MLE method); values below 0.05 mean choices barely track option value at all, so any fitted k is statistically unidentifiable.
- **logistic k Reliable?**: beta >= 0.05 AND fitted k did not land at the optimizer's bound.
- **Valid Discount Rate**: Rank Monotonicity Pass AND Consistency Pass AND logistic k Reliable -- the single bottom-line flag for whether either fitted k should be trusted at all.
- **geomean k**: hand-scoring composite k = geometric mean of small_k/medium_k/large_k, directly comparable to published human percentile norms.
- **logistic k [95% CI]**: MLE-fit discount rate per day (bootstrap 95% CI), from the probabilistic logistic method, shown regardless of reliability.
