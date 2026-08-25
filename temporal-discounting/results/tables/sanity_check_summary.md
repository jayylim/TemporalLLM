# Waiting Game: Sanity Check Summary

Modes included: one-shot, two-shot. Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

| Model | Mode | Monotonicity | Money Pref. | Competence Pass | Beta (choice sens.) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|
| qwen2.5:1.5b-instruct | one-shot | ❌ | ❌ | ❌ | 0.0007 | ❌ | **❌** | 10.0000 [10.0000, 10.0000] |
| qwen2.5:1.5b-instruct | two-shot | ❌ | ❌ | ❌ | 0.0007 | ❌ | **❌** | 10.0000 [10.0000, 10.0000] |
| qwen2.5:3b-instruct | one-shot | ❌ | ✅ | ❌ | 0.0026 | ❌ | **❌** | 0.0033 [0.0015, 0.0057] |
| qwen2.5:3b-instruct | two-shot | ❌ | ✅ | ❌ | 0.0016 | ❌ | **❌** | 10.0000 [10.0000, 10.0000] |
| qwen2.5:7b-instruct | one-shot | ❌ | ✅ | ❌ | 0.0027 | ❌ | **❌** | 0.0079 [0.0057, 0.0104] |
| qwen2.5:7b-instruct | two-shot | ❌ | ✅ | ❌ | 0.0025 | ❌ | **❌** | 0.0085 [0.0060, 0.0112] |

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay (`competence_checks.py::check_monotonicity`).
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay (`check_money_preference`).
- **Competence Pass**: Monotonicity AND Money Pref. both pass (`overall_passed`).
- **Beta (choice sens.)**: fitted logistic sensitivity of choices to the amount/delay tradeoff; values below 0.05 mean choices barely track option value at all, so any fitted k is statistically unidentifiable (`fit_discounting.py::LOW_SENSITIVITY_BETA_THRESHOLD`).
- **k Reliable?**: beta >= 0.05 AND fitted k did not land at the optimizer's boundary (1e-6 or 10.0).
- **Valid Discount Rate**: Competence Pass AND k Reliable — the single bottom-line flag for whether the fitted k should be trusted at all.
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI, shown regardless of reliability (compare against the "k Reliable?"/"Valid Discount Rate" columns before interpreting).
