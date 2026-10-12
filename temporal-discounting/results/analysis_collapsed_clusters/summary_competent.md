# Collapsed-cluster discount fits (competent personas only)

Inclusion is gated by the same competence-pass cells as `results/analysis_k_always_reliable/successful_conditions.md` (from `results/summary/by_condition.csv`). For each **model × option_order**, only those persona / persona-off conditions are pooled, then hyperbolic k is refit.

Under the always-reliable framing used in that report, **Valid (always-reliable)** is ✅ whenever ≥1 competent persona×order cell contributed. Single-persona rows must reproduce that file's fitted k.

Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

## Cluster 1 — by model, competent personas + off (when competent)

| Model | Option order | Personas included | n | Pooled competence | **Valid (always-reliable)** | R² | Fitted k [95% CI] |
|---|---|---|---:|---|---|---|---|
| qwen2.5:7b-instruct-q8_0 | sooner_B | `mindfulness` | 626 | ✅ | **✅** | 0.556 | 0.0098 [0.0098, 0.0224] |
| qwen3:4b-instruct-2507-q8_0 | pooled | `off,mindfulness` | 2520 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | sooner_A | `off,exercise,mindfulness` | 1902 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | sooner_B | `off` | 626 | ✅ | **✅** | - | 5.6511 [5.5239, 5.6511] |
| qwen3:8b-q8_0 | sooner_A | `retail_spending,sugary_food` | 1268 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | pooled | `phone_social_media,strategy_games,sugary_food` | 3780 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | sooner_A | `phone_social_media,retail_spending,sugary_food` | 1902 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | sooner_B | `phone_social_media,strategy_games,sugary_food` | 1878 | ✅ | **✅** | - | 5.6511 [0.6375, 5.6511] |
| qwen3.5:27b-q8_0 | pooled | `no_smoking_drinking,retail_spending,sugary_food` | 3780 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | sooner_A | `no_smoking_drinking,retail_spending,strategy_games` | 1902 | ✅ | **✅** | 0.796 | 0.0081 [0.0064, 0.0190] |
| qwen3.5:27b-q8_0 | sooner_B | `no_smoking_drinking,retail_spending` | 1252 | ✅ | **✅** | - | 0.0015 [0.0018, 1.8826] |
| qwen3.5:35b-a3b-q8_0 | sooner_B | `off` | 626 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |

## Cluster 2 — by model × greater / lesser (competent personas only)

Persona-off excluded. Within each model × option_order, only competence-passing personas in that discounting group are pooled (same cells as `successful_conditions.md`).

| Model | Group | Option order | Personas included | n | Pooled competence | **Valid (always-reliable)** | R² | Fitted k [95% CI] |
|---|---|---|---|---:|---|---|---|---|
| qwen2.5:7b-instruct-q8_0 | lesser | sooner_B | `mindfulness` | 626 | ✅ | **✅** | 0.556 | 0.0098 [0.0098, 0.0224] |
| qwen3:4b-instruct-2507-q8_0 | lesser | pooled | `mindfulness` | 1260 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | lesser | sooner_A | `exercise,mindfulness` | 1268 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | greater | sooner_A | `retail_spending,sugary_food` | 1268 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | greater | pooled | `phone_social_media,sugary_food` | 2520 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | greater | sooner_A | `phone_social_media,retail_spending,sugary_food` | 1902 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | greater | sooner_B | `phone_social_media,sugary_food` | 1252 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | lesser | pooled | `strategy_games` | 1260 | ✅ | **✅** | -7.903 | 0.0020 [0.0015, 0.0034] |
| qwen3:32b-q8_0 | lesser | sooner_B | `strategy_games` | 626 | ✅ | **✅** | - | 0.0015 [0.0015, 0.0015] |
| qwen3.5:27b-q8_0 | greater | pooled | `retail_spending,sugary_food` | 2520 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | greater | sooner_A | `retail_spending` | 634 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | greater | sooner_B | `retail_spending` | 626 | ✅ | **✅** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | lesser | pooled | `no_smoking_drinking` | 1260 | ✅ | **✅** | - | 0.0015 [0.0015, 0.0015] |
| qwen3.5:27b-q8_0 | lesser | sooner_A | `no_smoking_drinking,strategy_games` | 1268 | ✅ | **✅** | 0.139 | 0.0035 [0.0026, 0.0054] |
| qwen3.5:27b-q8_0 | lesser | sooner_B | `no_smoking_drinking` | 626 | ✅ | **✅** | - | 0.0015 [0.0015, 0.0015] |

## Models with 0 successful conditions

Same list as `successful_conditions.md` — no competent persona×order cells, so nothing to pool:

- `qwen3.5:9b-q8_0`
- `llama3.1:8b-instruct-q8_0`
- `mistral:7b-instruct-q8_0`
