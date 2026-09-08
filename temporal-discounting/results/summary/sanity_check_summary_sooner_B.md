# Waiting Game: Sanity Check Summary (order = `sooner_B`)

Option-order stratum: **sooner_B**. Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

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
| llama3.1:8b-instruct-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | -0.032 | ✅ | **❌** | 0.6145 [0.0711, 5.4913] |
| llama3.1:8b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ❌ | ❌ | 0.228 | ✅ | **❌** | 0.1656 [0.0098, 0.6375] |
| llama3.1:8b-instruct-q8_0 | on | retail_spending | greater | ❌ | ✅ | ❌ | ❌ | -0.145 | ✅ | **❌** | 0.2158 [0.0089, 4.6882] |
| llama3.1:8b-instruct-q8_0 | on | substance_use | greater | ❌ | ✅ | ❌ | ❌ | -0.416 | ✅ | **❌** | 0.0216 [0.0015, 0.2557] |
| llama3.1:8b-instruct-q8_0 | on | sugary_food | greater | ❌ | ❌ | ❌ | ❌ | -0.574 | ✅ | **❌** | 0.0075 [0.0062, 4.6882] |
| llama3.1:8b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ❌ | ❌ | -0.500 | ✅ | **❌** | 0.0020 [0.0015, 0.1960] |
| llama3.1:8b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ❌ | ❌ | -0.208 | ✅ | **❌** | 0.0697 [0.0160, 1.7326] |
| llama3.1:8b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ❌ | ❌ | ❌ | -0.130 | ✅ | **❌** | 0.0265 [0.0240, 4.9877] |
| llama3.1:8b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ❌ | ❌ | -0.067 | ✅ | **❌** | 0.0729 [0.0095, 2.4910] |
| mistral:7b-instruct-q8_0 | off | - | - | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0089] |
| mistral:7b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ❌ | ❌ | -0.479 | ✅ | **❌** | 0.0256 [0.0018, 0.1483] |
| mistral:7b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ❌ | ❌ | -0.987 | ✅ | **❌** | 0.0024 [0.0015, 0.0251] |
| mistral:7b-instruct-q8_0 | on | substance_use | greater | ❌ | ❌ | ❌ | ❌ | 0.279 | ✅ | **❌** | 0.0541 [0.0043, 0.3691] |
| mistral:7b-instruct-q8_0 | on | sugary_food | greater | ❌ | ❌ | ❌ | ❌ | -1.592 | ✅ | **❌** | 0.0067 [0.0021, 4.9877] |
| mistral:7b-instruct-q8_0 | on | exercise | lesser | ❌ | ✅ | ❌ | ❌ | -0.740 | ✅ | **❌** | 0.0028 [0.0015, 0.0178] |
| mistral:7b-instruct-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0089] |
| mistral:7b-instruct-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0108] |
| mistral:7b-instruct-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0020] |
| qwen2.5:7b-instruct-q8_0 | off | - | - | ✅ | ❌ | ✅ | ❌ | 0.970 | ✅ | **❌** | 0.1443 [0.1349, 0.1487] |
| qwen2.5:7b-instruct-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | 0.952 | ✅ | **❌** | 0.4579 [0.2039, 0.6393] |
| qwen2.5:7b-instruct-q8_0 | on | retail_spending | greater | ❌ | ❌ | ✅ | ❌ | 0.788 | ✅ | **❌** | 0.1102 [0.0895, 0.2493] |
| qwen2.5:7b-instruct-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | 0.901 | ✅ | **❌** | 0.3444 [0.2204, 0.6511] |
| qwen2.5:7b-instruct-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | on | exercise | lesser | ❌ | ❌ | ✅ | ❌ | 0.830 | ✅ | **❌** | 0.1005 [0.0957, 0.2055] |
| qwen2.5:7b-instruct-q8_0 | on | mindfulness | lesser | ✅ | ✅ | ✅ | ✅ | 0.556 | ✅ | **✅** | 0.0098 [0.0098, 0.0221] |
| qwen2.5:7b-instruct-q8_0 | on | no_smoking_drinking | lesser | ✅ | ❌ | ✅ | ❌ | 0.763 | ✅ | **❌** | 0.0165 [0.0146, 0.0267] |
| qwen2.5:7b-instruct-q8_0 | on | strategy_games | lesser | ✅ | ❌ | ✅ | ❌ | 0.909 | ✅ | **❌** | 0.0361 [0.0206, 0.0385] |
| qwen3.5:27b-q8_0 | off | - | - | ❌ | ✅ | ❌ | ❌ | 0.869 | ✅ | **❌** | 0.0372 [0.0223, 0.1559] |
| qwen3.5:27b-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | retail_spending | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | on | exercise | lesser | ❌ | ✅ | ✅ | ❌ | 0.595 | ✅ | **❌** | 0.0069 [0.0015, 0.0113] |
| qwen3.5:27b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0015] |
| qwen3.5:27b-q8_0 | on | no_smoking_drinking | lesser | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 0.0015 [0.0015, 0.0015] |
| qwen3.5:27b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 0.0015 [0.0015, 0.0015] |
| qwen3.5:35b-a3b-q8_0 | off | - | - | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | exercise | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [4.8006, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | mindfulness | lesser | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6371, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ✅ | ❌ | 0.703 | ✅ | **❌** | 1.3054 [0.3297, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6375, 5.6511] |
| qwen3.5:9b-q8_0 | off | - | - | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3.5:9b-q8_0 | on | phone_social_media | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| qwen3.5:9b-q8_0 | on | retail_spending | greater | ❌ | ❌ | ❌ | ❌ | -1.239 | ✅ | **❌** | 0.0164 [0.0021, 4.9004] |
| qwen3.5:9b-q8_0 | on | substance_use | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.6375, 5.6511] |
| qwen3.5:9b-q8_0 | on | sugary_food | greater | ❌ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [0.7176, 5.6511] |
| qwen3.5:9b-q8_0 | on | exercise | lesser | ❌ | ❌ | ❌ | ❌ | -0.477 | ✅ | **❌** | 0.1301 [0.0036, 1.9350] |
| qwen3.5:9b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ✅ | ❌ | 0.583 | ✅ | **❌** | 0.0055 [0.0015, 0.0167] |
| qwen3.5:9b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ❌ | ❌ | -1.279 | ✅ | **❌** | 0.0201 [0.0017, 0.6950] |
| qwen3.5:9b-q8_0 | on | strategy_games | lesser | ❌ | ✅ | ✅ | ❌ | -10.126 | ✅ | **❌** | 0.0020 [0.0015, 0.0732] |
| qwen3:32b-q8_0 | off | - | - | ❌ | ✅ | ✅ | ❌ | 0.587 | ✅ | **❌** | 0.0056 [0.0055, 0.0173] |
| qwen3:32b-q8_0 | on | phone_social_media | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | retail_spending | greater | ❌ | ✅ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | sugary_food | greater | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | on | exercise | lesser | ❌ | ✅ | ✅ | ❌ | 0.556 | ✅ | **❌** | 0.0098 [0.0098, 0.0098] |
| qwen3:32b-q8_0 | on | mindfulness | lesser | ❌ | ✅ | ✅ | ❌ | 0.556 | ✅ | **❌** | 0.0098 [0.0098, 0.0098] |
| qwen3:32b-q8_0 | on | no_smoking_drinking | lesser | ❌ | ✅ | ✅ | ❌ | 0.556 | ✅ | **❌** | 0.0098 [0.0056, 0.0104] |
| qwen3:32b-q8_0 | on | strategy_games | lesser | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 0.0015 [0.0015, 0.0015] |
| qwen3:4b-instruct-2507-q8_0 | off | - | - | ✅ | ✅ | ✅ | ✅ | - | ✅ | **✅** | 5.6511 [3.1061, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | exercise | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | mindfulness | lesser | ✅ | ❌ | ✅ | ❌ | 0.688 | ✅ | **❌** | 0.6375 [0.2493, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | no_smoking_drinking | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | on | strategy_games | lesser | ❌ | ❌ | ✅ | ❌ | 0.788 | ✅ | **❌** | 0.1102 [0.1102, 0.1102] |
| qwen3:8b-q8_0 | off | - | - | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | phone_social_media | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | retail_spending | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | substance_use | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | sugary_food | greater | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | exercise | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | mindfulness | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | no_smoking_drinking | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | on | strategy_games | lesser | ✅ | ❌ | ✅ | ❌ | - | ✅ | **❌** | 5.6511 [5.6511, 5.6511] |

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
