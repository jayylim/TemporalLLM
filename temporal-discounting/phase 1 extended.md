
# Phase 1 Extended (Phase 1b): Dual-Instrument Discounting Pipelines

| Repo | Instrument |
|---|---|
| `temporal-discounting/` | Waiting Game (Rachlin-style synthetic delay × amount grid) |
| `kirby-discounting/` | Kirby Monetary Choice Questionnaire (MCQ-27) |

Shared design choices: local Ollama, A/B forced choice, reasoning modes (`direct` / `cot`), temperature 1.0, bootstrap CIs, human k as **reference overlay only** (never a pass/fail gate). The scientific question of interest is whether models exhibit **coherent temporal preference at all**, not whether fitted k matches human norms.

---

# Part A — Waiting Game (`temporal-discounting/`)

## Purpose

Forced binary choices between a *sooner* dollar amount available now and a **fixed** *later* payoff ($1000) after delay \(d\) (months). Recover hyperbolic discount rate \(k\) **per month** via empirical immediate equivalents, gated by competence + fit reliability.

## Trial design

| Parameter | Value |
|---|---|
| Later amount | **$1000** |
| Delays (months) | `[1, 3, 6, 12, 36, 60, 120]` |
| Fit sooner amounts ($) | `[100, 250, 400, 550, 700, 900]` |
| Competence probes | `$0` now vs $1000 later (per delay); flagged `is_competence_probe`; **excluded from fit** |
| Samples / cell (i.e. trials per amount-delay pair) | **30** (`temperature: 1.0`) |
| Trials / model / mode×persona ...
| Order seed | `20260820` |

**Sytem Prompt**:
```
You are playing a game where you are given two monetary options.
One is available sooner, and one is available later.
You must choose one.

When answering, respond with only the letter of the option
you choose (A or B). Do not explain your choice.
```

**Option wording** (delays rendered as days/weeks/years in the prompt only):

```
Receive $X now
Wait until {duration} to receive $1000
```

Each trial assigns sooner/later to A vs B with P(`sooner_is_option_a`)= 0.5 (i.e. randomised option order)

## Models, modes, persona

**Models (9):** 
- qwen2.5:7b-instruct-q8_0             
- qwen3:4b-instruct-2507-q8_0          
- qwen3:8b-q8_0                        
- qwen3:32b-q8_0                       
- qwen3.5:9b-q8_0                      # (ollama_client think:false still required)
- qwen3.5:27b-q8_0                     # (ollama_client think:false still required)
- qwen3.5:35b-a3b-q8_0                 # (ollama_client think:false still required)
- llama3.1:8b-instruct-q8_0     
- mistral:7b-instruct-q8_0     
**Reasoning modes** (`--mode`):
| Mode | Behavior |
|---|---|
| `direct` | Letter A/B only; `num_predict: 5` |
| `cot` | Single call: step-by-step then `FINAL ANSWER: A/B`; `cot_num_predict: 100` |

Filename suffixes: `""`, `__cot`, plus `__persona` when persona is on.

**Persona** (toggle `--persona` / `--no-persona`; config default off): when on, the full trial grid is run once under each of 8 behavioral lifestyle personas (4 hypothesised *greater* discounting, 4 *lesser*). The persona text is prepended to the system prompt; `discounting_group` is logged for analysis only and never shown to the model. Persona-off is the control.

Greater: substance use, sugary food, phone/social media, retail spending.  
Lesser: mindfulness, no smoking/drinking, strategy games, exercise.

## Competence checks

All three must pass (`overall_passed`). Evaluated for each **option-order** condition:

| Check | Rule | Config |
|---|---|---|
| **A Amount monotonicity** | On fit grid: P(choose sooner) non-decreasing in sooner amount, per delay | tol `0.0`; ≤1 violation / delay |
| **B Money preference** | Via $0 probe: P(choose $0 now) ≤ 0.5 at every delay | `max_p_sooner_at_zero_amount: 0.5` |
| **C Indifference non-increasing** | Empirical 50% immediate equivalents \(x^*(d)\) non-increasing in delay | tol `0.0`; 0 rises allowed |

## Fitting

**Two-step hyperbolic NLS** (Rachlin-style; not logistic DRU):

1. Per delay, interpolate the sooner amount where P(choose sooner) = 0.5 over the fit amount grid.
2. Fit \(x^*(d) = 1000 / (1 + k \cdot d)\) by nonlinear least squares.

Bootstrap: 1000 trial-level resamples, seed 42 → 95% CI. Bounds \(k \in [10^{-6}, 10]\) per month.

**`k_is_reliable`:** not NaN; not near bound; R² ≥ 0.5; ≥ 3 indifference points.

**`valid_discount_rate`:** `overall_passed` ∧ `k_is_reliable`. Bound hits are still reported but cut from reliability. Human benchmark (Rachlin et al. 1991, \(k = 0.01\)/month) is a **plot reference only**.

## Stratification by option order

**Option order** (competence, fit, tables, discount-curve panels):

| Stratum | Filter |
|---|---|
| `pooled` | all trials |
| `sooner_A` | sooner listed as option A |
| `sooner_B` | sooner listed as option B |

Persona-on strata (`persona_id`; hypothesised `discounting_group` greater/lesser) use **pooled** order in `comparison_summary_by_persona*.csv`. Competence/fit for persona-on are computed per persona_id (not pooled across personas).

## Other Conditions

Explicit prompt setting

Behavioral personas hypothesised to increase (`greater`) or decrease (`lesser`) discounting — see Persona section above. Control = no persona preamble.

## Pipeline & artifacts

```
run_experiment.py      → data/raw/{model}{suffix}.jsonl
parse_responses.py     → data/processed/choices{suffix}.csv
competence_checks.py   → results/tables/competence_checks{suffix}.csv
                       → results/figures/indifference_equivalents{suffix}.png
fit_discounting.py     → results/tables/discount_rates{suffix}.csv
                       → results/tables/indifference_amounts{suffix}.csv
analyze.py             → results/tables/comparison_summary{suffix}.csv
                       → results/figures/discount_curves{suffix}.png
                       → (+ comparison_summary_by_persona{suffix}.csv if persona)
plot_choice_curves.py  → results/figures/{model}/choice_curves{suffix}.png
                       → results/figures/{model}/choice_curves{suffix}__{persona_id}.png
                       (foldered by model; one figure per persona when persona-on)
compare_modes.py       → results/tables/comparison_summary_by_mode.csv
                       → results/tables/sanity_check_summary.md
                       → results/figures/mode_comparison.png
                       → results/summary/{by_condition,by_factor,by_persona*,README,sanity_check_summary}
```

Supporting modules: `waiting_game.py`, `persona.py`, `ollama_client.py`, `config_utils.py`. Config: `config.yaml`.

```mermaid
flowchart TD
    config[config.yaml] --> wg[waiting_game.py]
    config --> persona[persona.py]
    wg --> run[run_experiment.py]
    persona --> run
    run --> ollama[Ollama]
    ollama --> raw[data/raw/*.jsonl]
    raw --> parse[parse_responses.py]
    parse --> choices[data/processed/choices*.csv]
    choices --> comp[competence_checks.py]
    choices --> fit[fit_discounting.py]
    comp --> analyze[analyze.py]
    fit --> analyze
    analyze --> compare[compare_modes.py]
    analyze --> tables[results/tables + figures]
    compare --> summary[results/summary/]
```

---

# Part B — Kirby MCQ-27 (`kirby-discounting/`)

## Purpose

Standard **Kirby Monetary Choice Questionnaire** ([Kirby, Petry & Bickel, 1999](https://doi.org/10.1037/0096-3445.128.1.78)): 27 fixed SIR-today vs LDR-in-\(D\)-days items, each calibrated to a known hyperbolic indifference \(k\). Estimates discount rate **per day**, comparable to published human MCQ norms (reference median ≈ 0.016/day).

Sibling architecture to the Waiting Game: same Ollama stack and prompt-mode axis; different instrument, gates, and scoring.

## Trial design

Items live in `kirby27_items.yaml` (verified against the MCQ instrument PDF and Kaplan et al. 2016 magnitude/k assignments).

| Feature | Value |
|---|---|
| Items | **27** fixed (9 k-ranks × 3 magnitude bands) |
| Magnitude bands | Small LDR $25–35; medium $50–60; large $75–85 |
| SIR / LDR / delay | $11–$80 / $25–$85 / **7–186 days** |
| Item \(k\) | \(\approx 0.00016\)–\(0.25\) / day; \(k = (LDR - SIR)/(SIR \cdot delay)\) |
| Samples / item | **30** (`temperature: 1.0`) |
| Trials / model / mode | **810** |
| Variant | `verbatim` (default); paraphrased contamination control implemented, not the primary run |
| Order seed | `20260825` |

Prompt style: `$X today` vs `$Y in D days`, A/B order randomized 50/50.

## Models, modes, persona

**Models (9):** `qwen2.5:7b-instruct-fp16`, `qwen3:4b-instruct-2507-fp16`, `qwen3:8b-fp16`, `qwen3:32b-fp16`, `qwen3.5:9b-mlx-bf16`, `qwen3.5:27b-bf16`, `qwen3.5:35b-a3b-bf16`, `llama3.1:8b-instruct-fp16`, `mistral:7b-instruct-fp16`  
(≥4B, Ollama F16; Qwen3.5 uses API `think: false` for instruct/non-thinking.)  
(≥4B, Ollama F16; Qwen3.5 uses API `think: false` for instruct/non-thinking.)

**Modes:** same two as Waiting Game (`direct` / `cot`).

**Persona:** none in this project.

## Competence checks

| Check | Rule | Config |
|---|---|---|
| **A Rank-order monotonicity** | Sort items by ascending item-\(k\); P(choose LDR) should not fall along adjacent pairs | tol `0.0`; ≤ **2** violations of 26 pairs |
| **B Consistency score** | Hand-scoring consistency ≥ **75%** (Kaplan et al. 2016) | `min_consistency_score: 0.75` |
| Magnitude effect | `small_k > medium_k > large_k` | **Reported only**, not a gate |

No $0 money-preference probe (Kirby has no zero-money cell).

## Fitting (two methods, both reported)

### 1. Hand / consistency (Kirby 2000; Kaplan et al. 2016)

Binarize each item by modal choice (P(LDR) > 0.5 → LDR; ties → SIR). Choose the candidate \(k\) maximizing consistency with the modal pattern (ties → geometric mean of tied candidates). Fit overall and by magnitude band; composite **`geomean_k`** = geo-mean(small_k, medium_k, large_k) for human-norm comparison.

### 2. Probabilistic logistic MLE (Wileyto-style; primary for model comparisons)

On raw (non-binarized) trials:

\[
V(A,d) = \frac{A}{1 + k\, d},\quad
P(\text{SIR}) = \sigma\!\big(\beta\,(V_{\text{SIR}} - V_{\text{LDR}})\big)
\]

MLE with bootstrap 1000 (seed 42). Bounds \(k \in [10^{-6}, 1]\), \(\beta \in [10^{-6}, 20]\); low-sensitivity if \(\beta < 0.05\).

**`valid_discount_rate`:** rank-monotonicity pass ∧ consistency pass ∧ logistic fit reliable (adequate \(\beta\), \(k\) not at bound). Human median \(k\) is reference only. **No AUC.**

## Pipeline & artifacts

```
run_experiment.py      → data/raw/{model}{mode}.jsonl
parse_responses.py     → data/processed/choices{mode}.csv
competence_checks.py   → results/tables/competence_checks{mode}.csv
fit_discounting.py     → results/tables/discount_rates{mode}.csv
analyze.py             → results/tables/comparison_summary{mode}.csv
                       → results/figures/discount_curves{mode}.png
plot_choice_curves.py  → results/figures/choice_curves_{model}{mode}.png   # P(LDR) vs item-k
compare_modes.py       → results/tables/comparison_summary_by_mode.csv
                       → results/tables/sanity_check_summary.md
                       → results/figures/mode_comparison.png
```

Supporting: `kirby_game.py`, `kirby27_items.yaml`, `ollama_client.py`, `config_utils.py`. Config: `config.yaml`.

```mermaid
flowchart TD
    config[config.yaml] --> items[kirby27_items.yaml]
    items --> kg[kirby_game.py]
    kg --> run[run_experiment.py]
    run --> ollama[Ollama]
    ollama --> raw[data/raw/*.jsonl]
    raw --> parse[parse_responses.py]
    parse --> choices[data/processed/choices*.csv]
    choices --> comp[competence_checks.py]
    choices --> fit[fit_discounting.py]
    comp --> analyze[analyze.py]
    fit --> analyze
    analyze --> compare[compare_modes.py]
    analyze --> tables[results/tables + figures]
```

---

# Differences between the two paradigms

| Dimension | Waiting Game (`temporal-discounting/`) | Kirby MCQ-27 (`kirby-discounting/`) |
|---|---|---|
| **Core idea** | Sweep a synthetic **delay × sooner-amount** surface; recover an indifference curve | Place the agent on a **pre-calibrated ladder of item-\(k\) ranks** |
| **Stimulus set** | 6 delays × 6 amounts + $0 probes (42 cells) | Fixed **27** human-normed items |
| **Later payoff** | Fixed **$1000** | Varies per item ($25–$85) |
| **Delay unit / range** | **Months** (1–120 ≈ 10 years) | **Days** (7–186) |
| **Samples** | 50 / cell → **2,100** trials / model / condition | 30 / item → **810** trials / model / mode |
| **Models** | 9 (≥4B F16: Qwen2.5/3/3.5 + Llama 3.1 + Mistral) | 9 (same model list) |
| **Persona** | Optional behavioral personas (greater/lesser discounting; control = none) | None |
| **Option-order strata** | Explicit `pooled` / `sooner_A` / `sooner_B` in all results | Order randomized; not a primary analysis stratum |
| **Competence** | Amount monotonicity + money preference ($0) + indifference non-increasing in delay | Rank-order monotonicity along item-\(k\) + ≥75% consistency score |
| **Primary \(k\) estimator** | Per-delay 50% interp → hyperbolic **NLS** on \(x^*(d)\) | Hand consistency **`geomean_k`** + Wileyto-style **logistic MLE** |
| **\(k\) units** | Per **month** | Per **day** |
| **Human reference** | Rachlin 1991 \(k \approx 0.01\)/month (overlay) | Kirby norms median \(\approx 0.016\)/day (overlay) |
| **Contamination risk** | Synthetic wording; less verbatim web copy | Exact MCQ text widely online → paraphrased variant available |
| **What “temporal preference” looks like** | Declining immediate equivalents with delay; money-sensible amount curves | Single switch along the k-rank ladder; high consistency with some interior \(k\) |

**Shared:** Phase 1 IV only; local Ollama; A/B forced choice with order randomization; `direct` / `cot` modes; competence gating before trusting \(k\); bootstrap CIs; human \(k\) never required for a “pass.”

**Convergent validity (not yet automated as a joint table):** correlating Waiting Game \(k\) (per month) with Kirby `geomean_k` / logistic \(k\) (per day) across overlapping models/modes remains the natural cross-instrument check — convert units before comparing, and restrict to conditions that pass each pipeline’s own validity flags.
