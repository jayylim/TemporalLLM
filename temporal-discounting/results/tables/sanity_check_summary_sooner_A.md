# Waiting Game: Sanity Check Summary (order = `sooner_A`)

Option-order stratum: **sooner_A**. Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

**Bound-agnostic reliability:** fitted k is *not* rejected for landing at the
optimizer's lower/upper bound, and R² is not used as a gate (flat indifference
curves that yield extreme k still count). `k Reliable?` requires only: k is
finite and ≥ 3 indifference points.
Valid discount rate = Competence Pass AND that bound-agnostic k Reliable.
Valid cells in this file: **11 / 81**.

Fitting method: per delay, interpolate the sooner amount at P(choose sooner)=0.5, then
nonlinear least-squares fit of x(d) = $later / (1 + k*d) to those empirical immediate equivalents.

| Model | Persona | Persona ID | Group | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| llama3.1:8b-instruct-q8_0 | off | - | - | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.4058, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.1061, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [3.5596, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.5310, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.4095, 5.6511] |
| mistral:7b-instruct-q8_0 | off | - | - | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| mistral:7b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| mistral:7b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| mistral:7b-instruct-q8_0 | on | substance_use | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.3064, 5.6511] |
| mistral:7b-instruct-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [1.5373, 5.6511] |
| mistral:7b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.8484, 5.6511] |
| mistral:7b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [1.7326, 5.6511] |
| mistral:7b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.2980, 5.6511] |
| mistral:7b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.2836, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | off | - | - | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.8911, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | exercise | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.9655, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | mindfulness | lesser | ✅ | ❌ | ❌ | ❌ | -12.058 | ✅ | **❌** | 4.1345 [4.0643, 4.2607] |
| qwen2.5:7b-instruct-q8_0 | on | no_smoking_drinking | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | strategy_games | lesser | ✅ | ❌ | ❌ | ❌ | -195.477 | ✅ | **❌** | 5.3931 [4.6686, 5.6511] |
| qwen3.5:27b-q8_0 | off | - | - | ❌ | ✅ | ✅ | ❌ | 0.896 | ✅ | **❌** | 0.0104 [0.0076, 0.0172] |
| qwen3.5:27b-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | retail_spending | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | exercise | lesser | ✅ | ✅ | ❌ | ❌ | 0.757 | ✅ | **❌** | 0.0097 [0.0052, 0.0219] |
| qwen3.5:27b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ❌ | ❌ | 0.388 | ✅ | **❌** | 0.0043 [0.0028, 0.0079] |
| qwen3.5:27b-q8_0 | on | no_smoking_drinking | lesser | ✅ | ✅ | ✅ | ✅ | -7.085 | ✅ | **✅** | 0.0021 [0.0015, 0.0032] |
| qwen3.5:27b-q8_0 | on | strategy_games | lesser | ✅ | ✅ | ✅ | ✅ | 0.760 | ✅ | **✅** | 0.0072 [0.0059, 0.0102] |
| qwen3.5:35b-a3b-q8_0 | off | - | - | ❌ | ✅ | ✅ | ❌ | 0.923 | ✅ | **❌** | 0.0208 [0.0130, 0.0330] |
| qwen3.5:35b-a3b-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.5985, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6377, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | 0.317 | ✅ | **❌** | 0.0258 [0.0132, 0.1560] |
| qwen3.5:35b-a3b-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ❌ | ❌ | 0.002 | ✅ | **❌** | 0.0074 [0.0015, 0.0177] |
| qwen3.5:35b-a3b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | 0.385 | ✅ | **❌** | 0.0329 [0.0121, 0.4335] |
| qwen3.5:35b-a3b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ❌ | ❌ | 0.853 | ✅ | **❌** | 0.0174 [0.0094, 0.0280] |
| qwen3.5:9b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | 0.702 | ✅ | **❌** | 0.2162 [0.1400, 0.5430] |
| qwen3.5:9b-q8_0 | on | phone_social_media | greater | ❌ | ✅ | ❌ | ❌ | -0.895 | ✅ | **❌** | 3.1630 [0.0031, 4.4946] |
| qwen3.5:9b-q8_0 | on | retail_spending | greater | ❌ | ✅ | ❌ | ❌ | -0.286 | ✅ | **❌** | 0.0825 [0.0031, 0.2028] |
| qwen3.5:9b-q8_0 | on | substance_use | greater | ❌ | ✅ | ❌ | ❌ | -0.552 | ✅ | **❌** | 0.2624 [0.0084, 2.2516] |
| qwen3.5:9b-q8_0 | on | sugary_food | greater | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.0945, 5.6511] |
| qwen3.5:9b-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | -0.728 | ✅ | **❌** | 0.2364 [0.0087, 1.3443] |
| qwen3.5:9b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ❌ | ❌ | -1.621 | ✅ | **❌** | 0.0475 [0.0023, 0.8178] |
| qwen3.5:9b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | 0.400 | ✅ | **❌** | 0.8799 [0.1039, 5.2618] |
| qwen3.5:9b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ❌ | ❌ | -1.150 | ✅ | **❌** | 0.0179 [0.0095, 1.0802] |
| qwen3:32b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | 0.940 | ✅ | **❌** | 0.0412 [0.0375, 0.0658] |
| qwen3:32b-q8_0 | on | phone_social_media | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | retail_spending | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | sugary_food | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | exercise | lesser | ❌ | ✅ | ✅ | ❌ | 0.688 | ✅ | **❌** | 0.6375 [0.6108, 0.6375] |
| qwen3:32b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ❌ | ❌ | 0.816 | ✅ | **❌** | 0.0269 [0.0216, 0.0828] |
| qwen3:32b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6375, 5.6511] |
| qwen3:32b-q8_0 | on | strategy_games | lesser | ✅ | ❌ | ✅ | ❌ | 0.486 | ✅ | **❌** | 0.0048 [0.0038, 0.0058] |
| qwen3:4b-instruct-2507-q8_0 | off | - | - | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | exercise | lesser | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | mindfulness | lesser | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | no_smoking_drinking | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | strategy_games | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | off | - | - | ✅ | ❌ | ❌ | ❌ | -16.355 | ✅ | **❌** | 0.0041 [0.0039, 0.0048] |
| qwen3:8b-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | retail_spending | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | sugary_food | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | -1.235 | ✅ | **❌** | 2.1293 [0.7089, 2.3123] |
| qwen3:8b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ❌ | ❌ | -10.720 | ✅ | **❌** | 0.0044 [0.0042, 0.0050] |
| qwen3:8b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | -23.028 | ✅ | **❌** | 5.4281 [4.2989, 5.6049] |
| qwen3:8b-q8_0 | on | strategy_games | lesser | ✅ | ✅ | ❌ | ❌ | -26.155 | ✅ | **❌** | 0.0079 [0.0068, 0.0089] |

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
