# Waiting Game: Sanity Check Summary

Modes included: direct, one-shot, two-shot. Human benchmark (Rachlin et al. 1991): k = 0.01 per month.
Reasonable k bounds (hits cut from reliability, still reported): [1e-06, 10.0].

Fitting method: per delay, interpolate the sooner amount at P(choose sooner)=0.5, then
nonlinear least-squares fit of x(d) = $later / (1 + k*d) to those empirical immediate equivalents.
Results stratified by A/B option order (pooled / sooner_A / sooner_B).

| Model | Mode | Persona | Order | Monotonicity | Money Pref. | Indiff. Non-incr. | Competence Pass | R^2 (indiff. fit) | k Reliable? | **Valid Discount Rate** | Fitted k [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| llama3.1:8b-instruct-q4_K_M | direct | off | pooled | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | direct | off | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | direct | off | sooner_B | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.3873, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | direct | on | pooled | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | direct | on | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | direct | on | sooner_B | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | one-shot | off | pooled | ❌ | ❌ | ❌ | ❌ | 0.008 | ❌ | **❌** | 0.1622 [0.1398, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | one-shot | off | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [1.7656, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | one-shot | off | sooner_B | ❌ | ✅ | ❌ | ❌ | -0.513 | ❌ | **❌** | 0.1063 [0.0146, 0.1474] |
| llama3.1:8b-instruct-q4_K_M | one-shot | on | pooled | ❌ | ❌ | ❌ | ❌ | 0.521 | ✅ | **❌** | 0.1272 [0.0464, 1.5442] |
| llama3.1:8b-instruct-q4_K_M | one-shot | on | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.6439, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | one-shot | on | sooner_B | ❌ | ✅ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0146, 0.1104] |
| llama3.1:8b-instruct-q4_K_M | two-shot | off | pooled | ❌ | ❌ | ✅ | ❌ | 0.725 | ✅ | **❌** | 0.2517 [0.1051, 0.7333] |
| llama3.1:8b-instruct-q4_K_M | two-shot | off | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.1991, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | two-shot | off | sooner_B | ❌ | ❌ | ✅ | ❌ | 0.759 | ✅ | **❌** | 0.1085 [0.0146, 0.2517] |
| llama3.1:8b-instruct-q4_K_M | two-shot | on | pooled | ❌ | ❌ | ✅ | ❌ | 0.759 | ✅ | **❌** | 0.1085 [0.1085, 0.2583] |
| llama3.1:8b-instruct-q4_K_M | two-shot | on | sooner_A | ❌ | ❌ | ❌ | ❌ | 0.403 | ❌ | **❌** | 0.2583 [0.1085, 5.7385] |
| llama3.1:8b-instruct-q4_K_M | two-shot | on | sooner_B | ❌ | ❌ | ❌ | ❌ | -0.057 | ❌ | **❌** | 0.0809 [0.0146, 0.1085] |
| mistral:7b-instruct-q4_K_M | direct | off | pooled | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.1622, 5.7385] |
| mistral:7b-instruct-q4_K_M | direct | off | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| mistral:7b-instruct-q4_K_M | direct | off | sooner_B | ❌ | ✅ | ❌ | ❌ | -0.003 | ❌ | **❌** | 0.0183 [0.0018, 0.0471] |
| mistral:7b-instruct-q4_K_M | direct | on | pooled | ❌ | ❌ | ❌ | ❌ | -8.272 | ❌ | **❌** | 3.8849 [0.0464, 5.5833] |
| mistral:7b-instruct-q4_K_M | direct | on | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [1.7656, 5.7385] |
| mistral:7b-instruct-q4_K_M | direct | on | sooner_B | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0066] |
| mistral:7b-instruct-q4_K_M | one-shot | off | pooled | ❌ | ❌ | ❌ | ❌ | -0.206 | ❌ | **❌** | 0.1893 [0.0238, 4.0851] |
| mistral:7b-instruct-q4_K_M | one-shot | off | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7370, 5.7385] |
| mistral:7b-instruct-q4_K_M | one-shot | off | sooner_B | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0022] |
| mistral:7b-instruct-q4_K_M | one-shot | on | pooled | ❌ | ✅ | ❌ | ❌ | 0.118 | ❌ | **❌** | 0.1663 [0.0020, 3.8592] |
| mistral:7b-instruct-q4_K_M | one-shot | on | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [3.1533, 5.7385] |
| mistral:7b-instruct-q4_K_M | one-shot | on | sooner_B | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0018] |
| mistral:7b-instruct-q4_K_M | two-shot | off | pooled | ❌ | ❌ | ❌ | ❌ | -2.236 | ❌ | **❌** | 3.7160 [0.1085, 5.7060] |
| mistral:7b-instruct-q4_K_M | two-shot | off | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| mistral:7b-instruct-q4_K_M | two-shot | off | sooner_B | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0035] |
| mistral:7b-instruct-q4_K_M | two-shot | on | pooled | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.3722, 5.7385] |
| mistral:7b-instruct-q4_K_M | two-shot | on | sooner_A | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.7333, 5.7385] |
| mistral:7b-instruct-q4_K_M | two-shot | on | sooner_B | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0040] |
| qwen2.5:1.5b-instruct | direct | off | pooled | ❌ | ❌ | ❌ | ❌ | -1.385 | ❌ | **❌** | 0.5359 [0.0034, 3.6317] |
| qwen2.5:1.5b-instruct | direct | off | sooner_A | ❌ | ❌ | ❌ | ❌ | -99.232 | ❌ | **❌** | 5.6425 [3.1533, 5.7385] |
| qwen2.5:1.5b-instruct | direct | off | sooner_B | ❌ | ✅ | ❌ | ❌ | -2.098 | ❌ | **❌** | 0.0017 [0.0014, 0.0112] |
| qwen2.5:1.5b-instruct | direct | on | pooled | ❌ | ✅ | ❌ | ❌ | -2.891 | ❌ | **❌** | 3.5312 [0.3820, 4.7526] |
| qwen2.5:1.5b-instruct | direct | on | sooner_A | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0016] |
| qwen2.5:1.5b-instruct | direct | on | sooner_B | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.6533, 5.7385] |
| qwen2.5:1.5b-instruct | one-shot | off | pooled | ❌ | ❌ | ❌ | ❌ | 0.322 | ❌ | **❌** | 0.1127 [0.0150, 0.9450] |
| qwen2.5:1.5b-instruct | one-shot | off | sooner_A | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:1.5b-instruct | one-shot | off | sooner_B | ✅ | ✅ | ✅ | ✅ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0014] |
| qwen2.5:1.5b-instruct | one-shot | on | pooled | ❌ | ❌ | ❌ | ❌ | -0.826 | ❌ | **❌** | 0.0014 [0.0014, 0.0052] |
| qwen2.5:1.5b-instruct | one-shot | on | sooner_A | ❌ | ❌ | ❌ | ❌ | -0.508 | ❌ | **❌** | 3.1533 [2.4919, 3.1533] |
| qwen2.5:1.5b-instruct | one-shot | on | sooner_B | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0014] |
| qwen2.5:1.5b-instruct | two-shot | off | pooled | ❌ | ❌ | ❌ | ❌ | -0.390 | ❌ | **❌** | 0.2719 [0.0393, 3.3172] |
| qwen2.5:1.5b-instruct | two-shot | off | sooner_A | ❌ | ❌ | ❌ | ❌ | -0.862 | ❌ | **❌** | 2.5311 [0.1653, 4.6672] |
| qwen2.5:1.5b-instruct | two-shot | off | sooner_B | ❌ | ✅ | ❌ | ❌ | -4.970 | ❌ | **❌** | 0.0493 [0.0052, 0.1089] |
| qwen2.5:1.5b-instruct | two-shot | on | pooled | ❌ | ❌ | ❌ | ❌ | -1.258 | ❌ | **❌** | 0.0428 [0.0028, 2.0240] |
| qwen2.5:1.5b-instruct | two-shot | on | sooner_A | ❌ | ❌ | ❌ | ❌ | -0.559 | ❌ | **❌** | 0.0017 [0.0014, 0.0321] |
| qwen2.5:1.5b-instruct | two-shot | on | sooner_B | ❌ | ✅ | ❌ | ❌ | -133.442 | ❌ | **❌** | 0.1344 [0.0463, 0.7427] |
| qwen2.5:3b-instruct | direct | off | pooled | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:3b-instruct | direct | off | sooner_A | ✅ | ❌ | ❌ | ❌ | -0.508 | ❌ | **❌** | 3.1533 [3.1533, 5.7385] |
| qwen2.5:3b-instruct | direct | off | sooner_B | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:3b-instruct | direct | on | pooled | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:3b-instruct | direct | on | sooner_A | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:3b-instruct | direct | on | sooner_B | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:3b-instruct | one-shot | off | pooled | ❌ | ✅ | ❌ | ❌ | -3.457 | ❌ | **❌** | 3.5494 [1.6445, 4.4708] |
| qwen2.5:3b-instruct | one-shot | off | sooner_A | ❌ | ✅ | ❌ | ❌ | -2.971 | ❌ | **❌** | 3.8461 [3.8304, 3.8530] |
| qwen2.5:3b-instruct | one-shot | off | sooner_B | ❌ | ✅ | ❌ | ❌ | -0.966 | ❌ | **❌** | 1.4151 [1.2503, 1.6979] |
| qwen2.5:3b-instruct | one-shot | on | pooled | ❌ | ✅ | ❌ | ❌ | -3.137 | ❌ | **❌** | 4.5154 [2.9625, 5.7385] |
| qwen2.5:3b-instruct | one-shot | on | sooner_A | ❌ | ✅ | ❌ | ❌ | -0.810 | ❌ | **❌** | 5.5064 [5.5051, 5.7385] |
| qwen2.5:3b-instruct | one-shot | on | sooner_B | ✅ | ✅ | ❌ | ❌ | -5.980 | ❌ | **❌** | 3.6562 [3.4287, 3.9872] |
| qwen2.5:3b-instruct | two-shot | off | pooled | ✅ | ✅ | ❌ | ❌ | -0.375 | ❌ | **❌** | 0.0239 [0.0074, 0.0824] |
| qwen2.5:3b-instruct | two-shot | off | sooner_A | ✅ | ✅ | ✅ | ✅ | 0.396 | ❌ | **❌** | 0.1546 [0.1493, 0.1647] |
| qwen2.5:3b-instruct | two-shot | off | sooner_B | ✅ | ✅ | ❌ | ❌ | -14.153 | ❌ | **❌** | 0.0014 [0.0014, 0.0014] |
| qwen2.5:3b-instruct | two-shot | on | pooled | ✅ | ✅ | ❌ | ❌ | 0.504 | ✅ | **❌** | 0.0172 [0.0056, 0.0449] |
| qwen2.5:3b-instruct | two-shot | on | sooner_A | ✅ | ✅ | ✅ | ✅ | 0.469 | ❌ | **❌** | 0.1774 [0.1543, 0.2018] |
| qwen2.5:3b-instruct | two-shot | on | sooner_B | ✅ | ✅ | ✅ | ✅ | - | ❌ | **❌** | 0.0014 [0.0014, 0.0014] |
| qwen2.5:7b-instruct | direct | off | pooled | ❌ | ❌ | ✅ | ❌ | 0.639 | ✅ | **❌** | 1.2393 [1.0245, 5.7385] |
| qwen2.5:7b-instruct | direct | off | sooner_A | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:7b-instruct | direct | off | sooner_B | ✅ | ❌ | ✅ | ❌ | 0.878 | ✅ | **❌** | 0.4904 [0.4650, 0.5307] |
| qwen2.5:7b-instruct | direct | on | pooled | ❌ | ❌ | ✅ | ❌ | 0.615 | ✅ | **❌** | 1.1923 [0.4801, 5.5265] |
| qwen2.5:7b-instruct | direct | on | sooner_A | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen2.5:7b-instruct | direct | on | sooner_B | ✅ | ❌ | ❌ | ❌ | 0.881 | ✅ | **❌** | 0.1442 [0.0747, 0.1666] |
| qwen2.5:7b-instruct | one-shot | off | pooled | ❌ | ✅ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0150, 0.0447] |
| qwen2.5:7b-instruct | one-shot | off | sooner_A | ❌ | ✅ | ✅ | ❌ | 0.733 | ✅ | **❌** | 0.0150 [0.0150, 0.0150] |
| qwen2.5:7b-instruct | one-shot | off | sooner_B | ✅ | ✅ | ✅ | ✅ | 0.811 | ✅ | **✅** | 0.0447 [0.0447, 0.0447] |
| qwen2.5:7b-instruct | one-shot | on | pooled | ❌ | ✅ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0150, 0.0447] |
| qwen2.5:7b-instruct | one-shot | on | sooner_A | ❌ | ✅ | ✅ | ❌ | 0.733 | ✅ | **❌** | 0.0150 [0.0150, 0.0197] |
| qwen2.5:7b-instruct | one-shot | on | sooner_B | ✅ | ✅ | ✅ | ✅ | 0.811 | ✅ | **✅** | 0.0447 [0.0447, 0.0447] |
| qwen2.5:7b-instruct | two-shot | off | pooled | ❌ | ❌ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0447, 0.0447] |
| qwen2.5:7b-instruct | two-shot | off | sooner_A | ❌ | ✅ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0447, 0.0447] |
| qwen2.5:7b-instruct | two-shot | off | sooner_B | ✅ | ❌ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0447, 0.0447] |
| qwen2.5:7b-instruct | two-shot | on | pooled | ❌ | ❌ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0228, 0.0447] |
| qwen2.5:7b-instruct | two-shot | on | sooner_A | ❌ | ✅ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0150, 0.0447] |
| qwen2.5:7b-instruct | two-shot | on | sooner_B | ✅ | ❌ | ✅ | ❌ | 0.811 | ✅ | **❌** | 0.0447 [0.0316, 0.0447] |
| qwen3:4b-instruct-2507-q4_K_M | direct | off | pooled | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [4.0641, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | direct | off | sooner_A | ✅ | ✅ | ❌ | ❌ | 0.525 | ✅ | **❌** | 1.1310 [1.1122, 1.1310] |
| qwen3:4b-instruct-2507-q4_K_M | direct | off | sooner_B | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | direct | on | pooled | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | direct | on | sooner_A | ❌ | ✅ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | direct | on | sooner_B | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | off | pooled | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | off | sooner_A | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | off | sooner_B | ✅ | ✅ | ✅ | ✅ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | on | pooled | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | on | sooner_A | ✅ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.6439, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | one-shot | on | sooner_B | ✅ | ✅ | ✅ | ✅ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | off | pooled | ❌ | ❌ | ❌ | ❌ | 0.410 | ❌ | **❌** | 1.6682 [0.6176, 5.4172] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | off | sooner_A | ✅ | ✅ | ❌ | ❌ | -10.532 | ❌ | **❌** | 5.4172 [5.4172, 5.4172] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | off | sooner_B | ✅ | ❌ | ❌ | ❌ | 0.674 | ✅ | **❌** | 0.6176 [0.6176, 0.6176] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | on | pooled | ❌ | ❌ | ✅ | ❌ | - | ❌ | **❌** | 5.7385 [0.6439, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | on | sooner_A | ✅ | ✅ | ✅ | ✅ | - | ❌ | **❌** | 5.7385 [5.7385, 5.7385] |
| qwen3:4b-instruct-2507-q4_K_M | two-shot | on | sooner_B | ❌ | ❌ | ✅ | ❌ | 0.689 | ✅ | **❌** | 0.6439 [0.6439, 0.6439] |
| qwen3:8b | direct | off | pooled | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | direct | off | sooner_A | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | direct | off | sooner_B | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | direct | on | pooled | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | direct | on | sooner_A | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | direct | on | sooner_B | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | one-shot | off | pooled | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | one-shot | off | sooner_A | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | one-shot | off | sooner_B | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | one-shot | on | pooled | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | one-shot | on | sooner_A | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | one-shot | on | sooner_B | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | two-shot | off | pooled | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | two-shot | off | sooner_A | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | two-shot | off | sooner_B | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | two-shot | on | pooled | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | two-shot | on | sooner_A | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |
| qwen3:8b | two-shot | on | sooner_B | ✅ | ❌ | ❌ | ❌ | - | ❌ | **❌** | - |

## Column definitions

- **Monotonicity**: P(choose sooner) does not decrease as the sooner amount increases, for every delay (`competence_checks.py::check_monotonicity`).
- **Money Pref.**: model doesn't prefer $0 now over positive delayed money, at any delay (`check_money_preference`).
- **Indiff. Non-incr.**: empirical 50% immediate equivalents x*(d) are non-increasing in delay (`check_indifference_nonincreasing`).
- **Competence Pass**: Monotonicity AND Money Pref. AND Indiff. Non-incr. all pass (`overall_passed`).
- **R^2 (indiff. fit)**: goodness of fit of the hyperbolic indifference curve to the per-delay 50% switching points.
- **k Reliable?**: R^2 above threshold, enough indifference points, AND fitted k did not land at the optimizer's boundary ([1e-06, 10.0]). Bound hits are cut from reliability; the bound values themselves are still reported.
- **Valid Discount Rate**: Competence Pass AND k Reliable — the single bottom-line flag for whether the fitted k should be trusted at all.
- **Fitted k [95% CI]**: hyperbolic discount rate per month with bootstrap 95% CI, shown regardless of reliability (compare against the "k Reliable?"/"Valid Discount Rate" columns before interpreting).
- **Persona**: on/off demographic persona framing; demographic strata (gender, age band) are in `by_demographics.csv` / `comparison_summary_by_demographics*.csv` when persona-on data exists.
- **Order**: `pooled` / `sooner_A` / `sooner_B` — whether the sooner option was listed as A or B (or all trials pooled).
