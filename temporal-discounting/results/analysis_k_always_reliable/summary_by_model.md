# Waiting Game: Per-Model Persona Summary

One table per model. Rows match the model's **choice-curve** conditions: persona-off control, then each persona id. Stats use `option_order = pooled` (same pooling as `choice_curves.png` / `choice_curves__persona__{id}.png`).

Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

**Analysis rule:** fitted k is treated as **always reliable** (including always-sooner / always-later / missing R² / bound-adjacent fits). `Valid Discount Rate` = Competence Pass only. Fitted k [95% CI] is always shown.

## qwen2.5:7b-instruct-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ❌ | ❌ | ❌ | -2.262 | ✅ | **❌** | 2.6214 [0.4610, 3.2934] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ❌ | ❌ | ❌ | ❌ | -1.654 | ✅ | **❌** | 2.6677 [0.9737, 3.3816] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ❌ | ❌ | ❌ | ❌ | -1.503 | ✅ | **❌** | 2.7434 [1.0327, 3.4508] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ❌ | ❌ | ❌ | ❌ | -0.432 | ✅ | **❌** | 1.8029 [0.4797, 3.2861] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ❌ | ❌ | ❌ | -0.327 | ✅ | **❌** | 0.0627 [0.0246, 1.0437] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ❌ | ❌ | ❌ | -0.407 | ✅ | **❌** | 0.1186 [0.0515, 1.9256] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ❌ | ❌ | ❌ | -0.199 | ✅ | **❌** | 0.0863 [0.0540, 1.3590] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ❌ | ❌ | ❌ | -0.797 | ✅ | **❌** | 1.6332 [0.4246, 2.2430] |

## qwen3:4b-instruct-2507-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ❌ | ❌ | ❌ | -0.388 | ✅ | **❌** | 1.7326 [0.1617, 5.6511] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |

## qwen3:8b-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ❌ | ❌ | ❌ | -6.681 | ✅ | **❌** | 5.2091 [2.0211, 5.6101] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ❌ | ❌ | ❌ | -6.736 | ✅ | **❌** | 5.0513 [1.6166, 5.6101] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ❌ | ❌ | ❌ | -6.736 | ✅ | **❌** | 5.0513 [1.6081, 5.6101] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ❌ | ❌ | ❌ | -344.765 | ✅ | **❌** | 5.4560 [4.6891, 5.6511] |

## qwen3:32b-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ✅ | ❌ | ❌ | 0.931 | ✅ | **❌** | 0.0252 [0.0203, 0.0277] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ✅ | ✅ | ❌ | 0.556 | ✅ | **❌** | 0.0098 [0.0098, 0.0160] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ✅ | ❌ | ❌ | 0.294 | ✅ | **❌** | 0.0751 [0.0304, 0.5938] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ✅ | ✅ | ✅ | ✅ | -7.903 | ✅ | **✅** | 0.0020 [0.0015, 0.0034] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ✅ | ❌ | ❌ | -0.113 | ✅ | **❌** | 0.0147 [0.0098, 0.0825] |

## qwen3.5:9b-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ✅ | ❌ | ❌ | -2.229 | ✅ | **❌** | 4.3999 [2.8981, 5.6511] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.3478, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.1565, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ❌ | ✅ | ❌ | ❌ | -0.689 | ✅ | **❌** | 0.0205 [0.0020, 2.5175] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ✅ | ❌ | ❌ | -0.668 | ✅ | **❌** | 0.0071 [0.0016, 0.0248] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ✅ | ❌ | ❌ | -0.760 | ✅ | **❌** | 1.0014 [0.0108, 3.9500] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ✅ | ❌ | ❌ | -1.168 | ✅ | **❌** | 0.0083 [0.0025, 0.0826] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ✅ | ❌ | ❌ | -0.822 | ✅ | **❌** | 0.6839 [0.0160, 3.1719] |

## qwen3.5:27b-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ✅ | ❌ | ❌ | 0.886 | ✅ | **❌** | 0.0216 [0.0101, 0.0349] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0024] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 0.0015 [0.0015, 0.0015] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ✅ | ✅ | ❌ | 0.549 | ✅ | **❌** | 0.0048 [0.0015, 0.0055] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ✅ | ✅ | ❌ | 0.056 | ✅ | **❌** | 0.0032 [0.0026, 0.0129] |

## qwen3.5:35b-a3b-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ✅ | ❌ | ❌ | -1.523 | ✅ | **❌** | 4.4792 [0.5036, 5.6511] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ❌ | ❌ | ❌ | -0.051 | ✅ | **❌** | 0.0908 [0.0196, 1.3384] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ✅ | ❌ | ❌ | -0.715 | ✅ | **❌** | 0.6193 [0.1376, 2.2833] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ✅ | ❌ | ❌ | -1.293 | ✅ | **❌** | 0.9238 [0.0601, 3.3571] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ✅ | ❌ | ❌ | -4.125 | ✅ | **❌** | 4.4103 [0.4081, 5.6217] |

## llama3.1:8b-instruct-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.9307, 5.6511] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [1.2368, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [1.7326, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6375, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.1061, 5.6511] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6145, 5.6511] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.3478, 5.6511] |

## mistral:7b-instruct-q8_0

| Persona | Persona ID | Group | Choice-curve figure | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | - | - | `choice_curves.png` | ❌ | ❌ | ❌ | ❌ | -0.480 | ✅ | **❌** | 2.2931 [0.0162, 5.0379] |
| on | substance_use | greater | `choice_curves__persona__substance_use.png` | ❌ | ❌ | ✅ | ❌ | -2.870 | ✅ | **❌** | 3.1918 [0.3301, 5.6511] |
| on | sugary_food | greater | `choice_curves__persona__sugary_food.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [2.7248, 5.6511] |
| on | phone_social_media | greater | `choice_curves__persona__phone_social_media.png` | ❌ | ❌ | ❌ | ❌ | -0.388 | ✅ | **❌** | 1.7326 [0.1459, 5.6511] |
| on | retail_spending | greater | `choice_curves__persona__retail_spending.png` | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.1656, 5.6511] |
| on | mindfulness | lesser | `choice_curves__persona__mindfulness.png` | ❌ | ❌ | ❌ | ❌ | -0.172 | ✅ | **❌** | 0.0682 [0.0036, 3.8647] |
| on | no_smoking_drinking | lesser | `choice_curves__persona__no_smoking_drinking.png` | ❌ | ❌ | ❌ | ❌ | -0.509 | ✅ | **❌** | 0.1518 [0.0279, 4.6644] |
| on | strategy_games | lesser | `choice_curves__persona__strategy_games.png` | ❌ | ❌ | ❌ | ❌ | 0.729 | ✅ | **❌** | 1.0009 [0.0042, 4.9838] |
| on | exercise | lesser | `choice_curves__persona__exercise.png` | ❌ | ❌ | ❌ | ❌ | -0.692 | ✅ | **❌** | 3.8823 [0.0256, 5.5161] |

## Column definitions

- **Persona / Persona ID / Group**: control (`off`) or a lifestyle persona (greater/lesser discounting group). Same stratification as choice-curve figures.
- **Choice-curve figure**: corresponding file under `results/figures/{model}/`.
- **Competence Pass**: monotonicity ∧ money preference ∧ indifference non-increasing (evaluated on pooled trials for that persona).
- **k Reliable?**: always ✅ under this analysis (fitted k still reported as-is).
- **Valid Discount Rate**: Competence Pass (k reliability not used as a gate).
- **Fitted k [95% CI]**: hyperbolic discount rate per month on pooled trials (shown even for always-sooner / always-later patterns).
