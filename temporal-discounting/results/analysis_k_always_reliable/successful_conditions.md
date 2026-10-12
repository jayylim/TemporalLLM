# Waiting Game: Successful Conditions (k always reliable)

Only rows with **Competence Pass = True**. Under this analysis, fitted k is always treated as reliable, so **Valid Discount Rate = Competence Pass**.

Failed persona / option-order cells are omitted (no pooled fallbacks). Models with **zero** successful rows are listed at the bottom.

Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

## qwen2.5:7b-instruct-q8_0

Successful rows: **1**.

| Persona ID | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|
| mindfulness | sooner_B | ✅ | ✅ | ✅ | 0.556 | **✅** | 0.0098 [0.0098, 0.0221] |

## qwen3:4b-instruct-2507-q8_0

Successful rows: **6**.

| Persona ID | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|
| off | pooled | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| off | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| off | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [3.1061, 5.6511] |
| exercise | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| mindfulness | pooled | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| mindfulness | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |

## qwen3:8b-q8_0

Successful rows: **2**.

| Persona ID | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|
| retail_spending | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| sugary_food | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |

## qwen3:32b-q8_0

Successful rows: **9**.

| Persona ID | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|
| phone_social_media | pooled | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| phone_social_media | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| phone_social_media | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| retail_spending | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| sugary_food | pooled | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| sugary_food | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| sugary_food | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| strategy_games | pooled | ✅ | ✅ | ✅ | -7.903 | **✅** | 0.0020 [0.0015, 0.0034] |
| strategy_games | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 0.0015 [0.0015, 0.0015] |

## qwen3.5:27b-q8_0

Successful rows: **8**.

| Persona ID | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|
| retail_spending | pooled | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| retail_spending | sooner_A | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| retail_spending | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| sugary_food | pooled | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |
| no_smoking_drinking | pooled | ✅ | ✅ | ✅ | - | **✅** | 0.0015 [0.0015, 0.0015] |
| no_smoking_drinking | sooner_A | ✅ | ✅ | ✅ | -7.085 | **✅** | 0.0021 [0.0015, 0.0032] |
| no_smoking_drinking | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 0.0015 [0.0015, 0.0015] |
| strategy_games | sooner_A | ✅ | ✅ | ✅ | 0.760 | **✅** | 0.0072 [0.0059, 0.0102] |

## qwen3.5:35b-a3b-q8_0

Successful rows: **1**.

| Persona ID | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | R^2 | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|
| off | sooner_B | ✅ | ✅ | ✅ | - | **✅** | 5.6511 [5.6511, 5.6511] |

## Models with 0 successful conditions

These models had **no** competence-passing cells (any persona × option-order). They are omitted from the tables above.

- `qwen3.5:9b-q8_0`
- `llama3.1:8b-instruct-q8_0`
- `mistral:7b-instruct-q8_0`

## Coverage

- Models with ≥1 success: **6** — `qwen2.5:7b-instruct-q8_0`, `qwen3:4b-instruct-2507-q8_0`, `qwen3:8b-q8_0`, `qwen3:32b-q8_0`, `qwen3.5:27b-q8_0`, `qwen3.5:35b-a3b-q8_0`
- Models with 0 successes: **3** — `qwen3.5:9b-q8_0`, `llama3.1:8b-instruct-q8_0`, `mistral:7b-instruct-q8_0`
