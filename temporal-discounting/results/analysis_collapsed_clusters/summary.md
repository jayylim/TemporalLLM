# Collapsed-cluster discount fits

Same pipeline as the main Waiting Game analysis: competence gates (monotonicity, money preference, indifference non-increasing) + two-step hyperbolic fit to empirical indifference amounts, with bootstrap 95% CIs. `Valid Discount Rate` = competence pass AND `k_is_reliable`.

Human benchmark (Rachlin et al. 1991): k = 0.01 per month.

## Cluster 1 — by model, all personas + persona-off

Each row pools persona-off control trials with all persona-on trials for that model, then fits separately for each option-order stratum.

| Model | Option order | n trials | n strata collapsed | Competence | k Reliable? | **Valid Discount Rate** | R² | Fitted k [95% CI] |
|---|---|---:|---:|---|---|---|---|---|
| qwen2.5:7b-instruct-q8_0 | pooled | 11340 | 9 | ❌ | ❌ | **❌** | -1.160 | 2.1071 [1.8935, 3.0867] |
| qwen2.5:7b-instruct-q8_0 | sooner_A | 5706 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | sooner_B | 5634 | 9 | ❌ | ✅ | **❌** | 0.945 | 0.1227 [0.0818, 0.1331] |
| qwen3:4b-instruct-2507-q8_0 | pooled | 12600 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | sooner_A | 6340 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | sooner_B | 6260 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | pooled | 11340 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | sooner_A | 5706 | 9 | ❌ | ❌ | **❌** | -92.677 | 5.5438 [3.8994, 5.6511] |
| qwen3:8b-q8_0 | sooner_B | 5634 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | pooled | 11340 | 9 | ❌ | ✅ | **❌** | 0.690 | 1.3533 [0.6356, 5.6511] |
| qwen3:32b-q8_0 | sooner_A | 5706 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6267, 5.6511] |
| qwen3:32b-q8_0 | sooner_B | 5634 | 9 | ❌ | ✅ | **❌** | 0.911 | 0.0258 [0.0098, 0.0742] |
| qwen3.5:9b-q8_0 | pooled | 11340 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [2.6279, 5.6511] |
| qwen3.5:9b-q8_0 | sooner_A | 5706 | 9 | ❌ | ❌ | **❌** | -0.224 | 0.5819 [0.2930, 1.6172] |
| qwen3.5:9b-q8_0 | sooner_B | 5634 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.3064, 5.6511] |
| qwen3.5:27b-q8_0 | pooled | 11302 | 9 | ❌ | ✅ | **❌** | 0.785 | 0.1220 [0.0910, 1.0145] |
| qwen3.5:27b-q8_0 | sooner_A | 5685 | 9 | ❌ | ✅ | **❌** | 0.645 | 0.0889 [0.0500, 1.4565] |
| qwen3.5:27b-q8_0 | sooner_B | 5617 | 9 | ❌ | ✅ | **❌** | 0.896 | 0.3376 [0.0593, 3.3321] |
| qwen3.5:35b-a3b-q8_0 | pooled | 11340 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | sooner_A | 5706 | 9 | ❌ | ❌ | **❌** | -10.074 | 3.4054 [1.8401, 4.8561] |
| qwen3.5:35b-a3b-q8_0 | sooner_B | 5634 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | pooled | 10944 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | sooner_A | 5482 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | sooner_B | 5462 | 9 | ❌ | ❌ | **❌** | 0.073 | 0.0482 [0.0095, 0.2495] |
| mistral:7b-instruct-q8_0 | pooled | 6946 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [3.8210, 5.6511] |
| mistral:7b-instruct-q8_0 | sooner_A | 3554 | 9 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| mistral:7b-instruct-q8_0 | sooner_B | 3392 | 9 | ❌ | ❌ | **❌** | - | 0.0015 [0.0015, 0.0015] |

## Cluster 2 — by model × greater / lesser personas

Persona-off excluded. Within each model, the four *greater* personas are pooled and the four *lesser* personas are pooled; fits are reported for all three option-order conditions (3 × greater + 3 × lesser).

| Model | Group | Option order | n trials | n personas | Competence | k Reliable? | **Valid Discount Rate** | R² | Fitted k [95% CI] |
|---|---|---|---:|---:|---|---|---|---|---|
| qwen2.5:7b-instruct-q8_0 | greater | pooled | 5040 | 4 | ❌ | ❌ | **❌** | -17.835 | 4.1677 [3.3559, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | greater | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | greater | sooner_B | 2504 | 4 | ❌ | ✅ | **❌** | 0.943 | 0.4448 [0.3146, 0.7728] |
| qwen2.5:7b-instruct-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | -0.929 | 1.5880 [0.0893, 1.7462] |
| qwen2.5:7b-instruct-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.1756, 5.6511] |
| qwen2.5:7b-instruct-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ✅ | **❌** | 0.895 | 0.0317 [0.0211, 0.0375] |
| qwen3:4b-instruct-2507-q8_0 | greater | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | greater | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | greater | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:4b-instruct-2507-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [0.6375, 5.6511] |
| qwen3:8b-q8_0 | greater | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | greater | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | greater | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:8b-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.4495, 5.6511] |
| qwen3:8b-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | -1.663 | 0.0304 [0.0106, 0.5604] |
| qwen3:8b-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | greater | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | greater | sooner_A | 2536 | 4 | ✅ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | greater | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3:32b-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ✅ | **❌** | 0.586 | 0.0103 [0.0098, 0.0122] |
| qwen3:32b-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ✅ | **❌** | 0.524 | 0.6037 [0.0570, 0.6310] |
| qwen3:32b-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ✅ | **❌** | 0.556 | 0.0098 [0.0057, 0.0098] |
| qwen3.5:9b-q8_0 | greater | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [4.9877, 5.6511] |
| qwen3.5:9b-q8_0 | greater | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | -2.106 | 3.1546 [0.1793, 5.5459] |
| qwen3.5:9b-q8_0 | greater | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [4.5985, 5.6511] |
| qwen3.5:9b-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | -0.282 | 0.0764 [0.0041, 0.2583] |
| qwen3.5:9b-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | -1.566 | 0.1404 [0.0452, 0.7471] |
| qwen3.5:9b-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | -0.333 | 0.0130 [0.0015, 0.0592] |
| qwen3.5:27b-q8_0 | greater | pooled | 5002 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | greater | sooner_A | 2515 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | greater | sooner_B | 2487 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:27b-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | -51.411 | 0.0017 [0.0015, 0.0023] |
| qwen3.5:27b-q8_0 | lesser | sooner_A | 2536 | 4 | ✅ | ✅ | **✅** | 0.537 | 0.0044 [0.0035, 0.0056] |
| qwen3.5:27b-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 0.0015 [0.0015, 0.0015] |
| qwen3.5:35b-a3b-q8_0 | greater | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | greater | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | greater | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| qwen3.5:35b-a3b-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | -1.342 | 1.0294 [0.2870, 3.7398] |
| qwen3.5:35b-a3b-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ✅ | **❌** | 0.950 | 0.0233 [0.0092, 0.0379] |
| qwen3.5:35b-a3b-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [4.7625, 5.6511] |
| llama3.1:8b-instruct-q8_0 | greater | pooled | 4644 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | greater | sooner_A | 2312 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | greater | sooner_B | 2332 | 4 | ❌ | ❌ | **❌** | 0.293 | 0.0654 [0.0026, 0.2596] |
| llama3.1:8b-instruct-q8_0 | lesser | pooled | 5040 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | lesser | sooner_A | 2536 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| llama3.1:8b-instruct-q8_0 | lesser | sooner_B | 2504 | 4 | ❌ | ✅ | **❌** | 0.538 | 0.1076 [0.0098, 0.2493] |
| mistral:7b-instruct-q8_0 | greater | pooled | 2930 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [4.5787, 5.6511] |
| mistral:7b-instruct-q8_0 | greater | sooner_A | 1502 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| mistral:7b-instruct-q8_0 | greater | sooner_B | 1428 | 4 | ❌ | ❌ | **❌** | -2.070 | 0.0020 [0.0015, 0.1229] |
| mistral:7b-instruct-q8_0 | lesser | pooled | 2942 | 4 | ❌ | ❌ | **❌** | -29.975 | 4.4098 [0.1000, 5.6383] |
| mistral:7b-instruct-q8_0 | lesser | sooner_A | 1511 | 4 | ❌ | ❌ | **❌** | - | 5.6511 [5.6511, 5.6511] |
| mistral:7b-instruct-q8_0 | lesser | sooner_B | 1431 | 4 | ❌ | ❌ | **❌** | - | 0.0015 [0.0015, 0.0015] |
