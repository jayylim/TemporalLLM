# Waiting Game: Sanity Check Summary

Modes included: one-shot, two-shot. Human benchmark (Rachlin et al. 1991): k = 0.01 per month.
Reasonable k bounds (hits cut from reliability, still reported): [1e-06, 10.0].

| Model | Mode | Persona | Monotonicity | Money Pref. | Competence Pass | Beta (choice sens.) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b-instruct | one-shot | off | ❌ | ❌ | ❌ | 0.0007 | ❌ | **❌** | 10.0000 [10.0000, 10.0000] |
| qwen2.5:1.5b-instruct | two-shot | off | ❌ | ❌ | ❌ | 0.0007 | ❌ | **❌** | 10.0000 [10.0000, 10.0000] |
| qwen2.5:3b-instruct | one-shot | off | ❌ | ✅ | ❌ | 0.0026 | ❌ | **❌** | 0.0033 [0.0015, 0.0057] |
| qwen2.5:3b-instruct | two-shot | off | ❌ | ✅ | ❌ | 0.0016 | ❌ | **❌** | 10.0000 [10.0000, 10.0000] |
| qwen2.5:7b-instruct | one-shot | off | ❌ | ✅ | ❌ | 0.0027 | ❌ | **❌** | 0.0079 [0.0057, 0.0104] |
| qwen2.5:7b-instruct | two-shot | off | ❌ | ✅ | ❌ | 0.0025 | ❌ | **❌** | 0.0085 [0.0060, 0.0112] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | off | ❌ | ✅ | ❌ | 12.3448 | ✅ | **❌** | 5.7463 [4.6730, 6.4355] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | off | ❌ | ❌ | ❌ | 0.0010 | ❌ | **❌** | 0.0736 [0.0502, 10.0000] |

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay (`competence_checks.py::check_monotonicity`).
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay (`check_money_preference`).
- **Competence Pass**: Monotonicity AND Money Pref. both pass (`overall_passed`).
- **Beta (choice sens.)**: fitted logistic sensitivity of choices to the amount/delay tradeoff; values below 0.05 mean choices barely track option value at all, so any fitted k is statistically unidentifiable (`fit_discounting.py`).
- **k Reliable?**: beta >= threshold AND fitted k did not land at the optimizer's boundary ([1e-06, 10.0]). Bound hits are cut from reliability; the bound values themselves are still reported.
- **Valid Discount Rate**: Competence Pass AND k Reliable — the single bottom-line flag for whether the fitted k should be trusted at all.
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI, shown regardless of reliability (compare against the "k Reliable?"/"Valid Discount Rate" columns before interpreting).
- **Persona**: on/off demographic persona framing; demographic strata (gender, age band) are in `by_demographics.csv` / `comparison_summary_by_demographics*.csv` when persona-on data exists.
