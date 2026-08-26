# Kirby MCQ-27: Sanity Check Summary

Modes included: direct, chain-of-thought, one-shot, two-shot. Item variant: verbatim. Approx. human benchmark (Kirby, Petry & Bickel 1999 / Kirby 2009 population norms): k = 0.016 per day.

| Model | Mode | Rank Monotonicity | Consistency | Consistency Pass | Magnitude Effect | logistic beta | logistic k Reliable? | **Valid Discount Rate** | geomean k | logistic k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b-instruct | direct | ❌ | 66.7% | ❌ | ❌ | 0.0102 | ❌ | **❌** | 0.00185 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:1.5b-instruct | chain-of-thought | ❌ | 70.4% | ❌ | ❌ | 0.0078 | ❌ | **❌** | 0.00016 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:1.5b-instruct | one-shot | ❌ | 70.4% | ❌ | ❌ | 0.0024 | ❌ | **❌** | 0.10859 | 0.12595 [0.00000, 1.00000] |
| qwen2.5:1.5b-instruct | two-shot | ❌ | 88.9% | ✅ | ❌ | 0.0142 | ❌ | **❌** | 0.19905 | 1.00000 [0.00973, 1.00000] |
| qwen2.5:3b-instruct | direct | ❌ | 96.3% | ✅ | ❌ | 0.0617 | ❌ | **❌** | 0.24853 | 1.00000 [1.00000, 1.00000] |
| qwen2.5:3b-instruct | chain-of-thought | ❌ | 92.6% | ✅ | ❌ | 0.0218 | ❌ | **❌** | 0.00020 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:3b-instruct | one-shot | ❌ | 100.0% | ✅ | ❌ | 0.4492 | ❌ | **❌** | 0.00016 | 0.00000 [0.00000, 0.00001] |
| qwen2.5:3b-instruct | two-shot | ❌ | 77.8% | ✅ | ✅ | 0.0162 | ❌ | **❌** | 0.03948 | 1.00000 [0.20499, 1.00000] |
| qwen2.5:7b-instruct | direct | ❌ | 88.9% | ✅ | ❌ | 0.0425 | ❌ | **❌** | 0.17047 | 0.11692 [0.07418, 0.19082] |
| qwen2.5:7b-instruct | chain-of-thought | ❌ | 55.6% | ❌ | ❌ | 0.0002 | ❌ | **❌** | 0.00695 | 0.00000 [0.00000, 1.00000] |
| qwen2.5:7b-instruct | one-shot | ❌ | 100.0% | ✅ | ❌ | 0.1349 | ❌ | **❌** | 0.00016 | 0.00000 [0.00000, 0.00000] |
| qwen2.5:7b-instruct | two-shot | ❌ | 85.2% | ✅ | ❌ | 0.0403 | ❌ | **❌** | 0.17047 | 0.20834 [0.12627, 0.43952] |
| qwen3:4b-instruct-2507-q4_K_M | direct | ❌ | 74.1% | ❌ | ✅ | 0.0287 | ❌ | **❌** | 0.00040 | 0.00000 [0.00000, 0.00000] |
| qwen3:4b-instruct-2507-q4_K_M | chain-of-thought | ❌ | 66.7% | ❌ | ❌ | 0.0047 | ❌ | **❌** | 0.00170 | 0.00000 [0.00000, 0.05023] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | ✅ | 100.0% | ✅ | ❌ | 2.3809 | ❌ | **❌** | 0.24853 | 1.00000 [1.00000, 1.00000] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | ✅ | 100.0% | ✅ | ❌ | 0.7621 | ✅ | **✅** | 0.24853 | 0.32981 [0.31115, 0.35651] |
| qwen3:8b | direct | ❌ | 88.9% | ✅ | ❌ | 0.0285 | ❌ | **❌** | 0.09351 | 1.00000 [0.39674, 1.00000] |
| qwen3:8b | chain-of-thought | ❌ | 59.3% | ❌ | ❌ | 0.0000 | ❌ | **❌** | 0.14471 | 0.00000 [0.00000, 1.00000] |
| qwen3:8b | one-shot | ❌ | 63.0% | ❌ | ❌ | 0.0013 | ❌ | **❌** | 0.01254 | 0.01822 [0.00000, 1.00000] |
| qwen3:8b | two-shot | ❌ | 77.8% | ✅ | ✅ | 0.0130 | ❌ | **❌** | 0.03135 | 0.04200 [0.01394, 1.00000] |

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
