# Waiting Game: Sanity Check Summary (order = `pooled`)

Option-order stratum: **pooled**. Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

**Bound-agnostic reliability:** fitted k is *not* rejected for landing at the
optimizer's lower/upper bound, and R² is not used as a gate (flat indifference
curves that yield extreme k still count). `k Reliable?` requires only: k is
finite and ≥ 3 indifference points.
Valid discount rate = Competence Pass AND that bound-agnostic k Reliable.
Valid cells in this file: **8 / 81**.

Fitting method: per delay, interpolate the sooner amount at P(choose sooner)=0.5, then
nonlinear least-squares fit of x(d) = $later / (1 + k*d) to those empirical immediate equivalents.

| Model | Persona | Persona ID | Group | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| llama3.1:8b-instruct-q8_0 | off | - | - | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.9307, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6375, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | substance_use | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [1.2368, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [1.7326, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.3478, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.1061, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6145, 5.6511] |
| mistral:7b-instruct-q8_0 | off | - | - | ❌ | ❌ | ❌ | ❌ | -0.480 | ✅ | **❌** | 2.2931 [0.0162, 5.0379] |
| mistral:7b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ❌ | ❌ | -0.388 | ✅ | **❌** | 1.7326 [0.1459, 5.6511] |
| mistral:7b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.1656, 5.6511] |
| mistral:7b-instruct-q8_0 | on | substance_use | greater | ❌ | ❌ | ✅ | ❌ | -2.870 | ✅ | **❌** | 3.1918 [0.3301, 5.6511] |
| mistral:7b-instruct-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [2.7248, 5.6511] |
| mistral:7b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ❌ | ❌ | -0.692 | ✅ | **❌** | 3.8823 [0.0256, 5.5161] |
| mistral:7b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ❌ | ❌ | -0.172 | ✅ | **❌** | 0.0682 [0.0036, 3.8647] |
| mistral:7b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ❌ | ❌ | -0.509 | ✅ | **❌** | 0.1518 [0.0279, 4.6644] |
| mistral:7b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ❌ | ❌ | 0.729 | ✅ | **❌** | 1.0009 [0.0042, 4.9838] |
| qwen2.5:7b-instruct-q8_0 | off | - | - | ❌ | ❌ | ❌ | ❌ | -2.262 | ✅ | **❌** | 2.6214 [0.4610, 3.2934] |
| qwen2.5:7b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ❌ | ❌ | -1.503 | ✅ | **❌** | 2.7434 [1.0327, 3.4508] |
| qwen2.5:7b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ❌ | ❌ | -0.432 | ✅ | **❌** | 1.8029 [0.4797, 3.2861] |
| qwen2.5:7b-instruct-q8_0 | on | substance_use | greater | ❌ | ❌ | ❌ | ❌ | -1.654 | ✅ | **❌** | 2.6677 [0.9737, 3.3816] |
| qwen2.5:7b-instruct-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ❌ | ❌ | -0.797 | ✅ | **❌** | 1.6332 [0.4246, 2.2430] |
| qwen2.5:7b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ❌ | ❌ | -0.327 | ✅ | **❌** | 0.0627 [0.0246, 1.0437] |
| qwen2.5:7b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ❌ | ❌ | -0.407 | ✅ | **❌** | 0.1186 [0.0515, 1.9256] |
| qwen2.5:7b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ❌ | ❌ | -0.199 | ✅ | **❌** | 0.0863 [0.0540, 1.3590] |
| qwen3.5:27b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | 0.886 | ✅ | **❌** | 0.0216 [0.0101, 0.0349] |
| qwen3.5:27b-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | retail_spending | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | sugary_food | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | exercise | lesser | ❌ | ✅ | ✅ | ❌ | 0.056 | ✅ | **❌** | 0.0032 [0.0026, 0.0129] |
| qwen3.5:27b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0024] |
| qwen3.5:27b-q8_0 | on | no_smoking_drinking | lesser | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 0.0015 [0.0015, 0.0015] |
| qwen3.5:27b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ✅ | ❌ | 0.549 | ✅ | **❌** | 0.0048 [0.0015, 0.0055] |
| qwen3.5:35b-a3b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | -1.523 | ✅ | **❌** | 4.4792 [0.5036, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | -4.125 | ✅ | **❌** | 4.4103 [0.4081, 5.6217] |
| qwen3.5:35b-a3b-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ❌ | ❌ | -0.051 | ✅ | **❌** | 0.0908 [0.0196, 1.3384] |
| qwen3.5:35b-a3b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | -0.715 | ✅ | **❌** | 0.6193 [0.1376, 2.2833] |
| qwen3.5:35b-a3b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ❌ | ❌ | -1.293 | ✅ | **❌** | 0.9238 [0.0601, 3.3571] |
| qwen3.5:9b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | -2.229 | ✅ | **❌** | 4.3999 [2.8981, 5.6511] |
| qwen3.5:9b-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.1565, 5.6511] |
| qwen3.5:9b-q8_0 | on | retail_spending | greater | ❌ | ✅ | ❌ | ❌ | -0.689 | ✅ | **❌** | 0.0205 [0.0020, 2.5175] |
| qwen3.5:9b-q8_0 | on | substance_use | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.3478, 5.6511] |
| qwen3.5:9b-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| qwen3.5:9b-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | -0.822 | ✅ | **❌** | 0.6839 [0.0160, 3.1719] |
| qwen3.5:9b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ❌ | ❌ | -0.668 | ✅ | **❌** | 0.0071 [0.0016, 0.0248] |
| qwen3.5:9b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | -0.760 | ✅ | **❌** | 1.0014 [0.0108, 3.9500] |
| qwen3.5:9b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ❌ | ❌ | -1.168 | ✅ | **❌** | 0.0083 [0.0025, 0.0826] |
| qwen3:32b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | 0.931 | ✅ | **❌** | 0.0252 [0.0203, 0.0277] |
| qwen3:32b-q8_0 | on | phone_social_media | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | retail_spending | greater | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | sugary_food | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | -0.113 | ✅ | **❌** | 0.0147 [0.0098, 0.0825] |
| qwen3:32b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ✅ | ❌ | 0.556 | ✅ | **❌** | 0.0098 [0.0098, 0.0160] |
| qwen3:32b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | 0.294 | ✅ | **❌** | 0.0751 [0.0304, 0.5938] |
| qwen3:32b-q8_0 | on | strategy_games | lesser | ✅ | ✅ | ✅ | ✅ | -7.903 | ✅ | **✅** | 0.0020 [0.0015, 0.0034] |
| qwen3:4b-instruct-2507-q8_0 | off | - | - | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | exercise | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | mindfulness | lesser | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | no_smoking_drinking | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ❌ | ❌ | -0.388 | ✅ | **❌** | 1.7326 [0.1617, 5.6511] |
| qwen3:8b-q8_0 | off | - | - | ❌ | ❌ | ❌ | ❌ | -6.681 | ✅ | **❌** | 5.2091 [2.0211, 5.6101] |
| qwen3:8b-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | exercise | lesser | ❌ | ❌ | ❌ | ❌ | -344.765 | ✅ | **❌** | 5.4560 [4.6891, 5.6511] |
| qwen3:8b-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ❌ | ❌ | -6.736 | ✅ | **❌** | 5.0513 [1.6166, 5.6101] |
| qwen3:8b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ❌ | ❌ | -6.736 | ✅ | **❌** | 5.0513 [1.6081, 5.6101] |

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay.
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay.
- **Indiff. Non-incr.**: empirical 50% immediate equivalents x*(d) are non-increasing in delay.
- **Competence Pass**: Monotonicity AND Money Pref. AND Indiff. Non-incr. all pass.
- **R^2 (indiff. fit)**: goodness of fit of the hyperbolic indifference curve to the per-delay 50% switching points.
- **k Reliable?**: k is finite and ≥ 3 indifference points (bound hits and R² ignored).
- **Valid Discount Rate**: Competence Pass AND k Reliable (bound-agnostic).
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI.
- **Persona**: on/off behavioral persona framing; Persona ID / Group when persona-on.
