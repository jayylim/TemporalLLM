# Preregistration: Kirby MCQ-27 Discounting in Local LLMs

Sibling project to `../temporal-discounting` (Waiting Game): same Q8 models, same
persona conditions and reasoning modes, different instrument. Fixed before running
the full N=30 experiment (pilot excluded).

## Instrument

The Kirby Monetary Choice Questionnaire, 27-item version (MCQ-27; [Kirby, Petry & Bickel,
1999](https://doi.org/10.1037/0096-3445.128.1.78)), presents a fixed set of 27
smaller-immediate-reward (SIR) vs. larger-delayed-reward (LDR) choices spanning nine
discount-rate ranks (k from ~0.00016 to 0.25 per day) crossed with three reward-magnitude
bands (small $25-35 LDR, medium $50-60 LDR, large $75-85 LDR). See `kirby27_items.yaml`
for the verified item table and cross-validation sources.

Because LLM responses are stochastic (unlike the single-shot human paper instrument),
each item is sampled N=30 times at temperature=1, yielding an empirical P(choose LDR)
per item rather than a single binary response, per
[phase 1 extended.md](../phase%201%20extended.md)'s Kirby module design.

## Models and independent variables

Default config: `config_q8.yaml` (same Ollama Q8_0 tags as the Waiting Game):

- `qwen2.5:7b-instruct-q8_0`
- `qwen3:4b-instruct-2507-q8_0`
- `qwen3:8b-q8_0`
- `qwen3:32b-q8_0`
- `qwen3.5:9b-q8_0`
- `qwen3.5:27b-q8_0`
- `qwen3.5:35b-a3b-q8_0`
- `llama3.1:8b-instruct-q8_0`
- `mistral:7b-instruct-q8_0`

Other IVs (matched to Waiting Game; Kirby items/procedure unchanged):

- **Reasoning mode**: `direct` | `cot` (`--mode`)
- **Persona**: off (control) vs on × 8 behavioral lifestyles (`--persona` / `--no-persona`):
  greater-discounting hypothesised — `substance_use`, `sugary_food`, `phone_social_media`,
  `retail_spending`; lesser — `mindfulness`, `no_smoking_drinking`, `strategy_games`,
  `exercise`. Persona text is prepended to the system prompt; `discounting_group` is
  logging/analysis only and never shown to the model.

## Hypotheses

- H1: Sorting the 27 items by their own indifference k, each model's P(choose LDR) is
  non-decreasing along that ordering (rank-monotonicity competence check) -- the Kirby
  analogue of the Waiting Game's grid-monotonicity check (H1 in the sibling project).
  (Items are constructed so that any person with a fixed personal discount rate switches
  from preferring SIR to preferring LDR at most once as item k rises, per Kaplan et al.
  2016 Table 1's canonical response patterns.)
- H2: Each model's hand-scoring consistency score (Kirby, 2000 / Kaplan et al., 2016) is
  >= 75%, the standard data-quality threshold for treating a k estimate as meaningful.
- H3: Fitted discount rate (both `geomean_k` and the probabilistic-logistic `k`) differs
  across models, with no directional prediction preregistered.
- H4: Fitted k values differ from the approximate Kirby population benchmark
  (`config_q8.yaml: human_benchmark.kirby_median_k_per_day`).
- H5 (magnitude effect, exploratory/reported not gating): `small_k > medium_k > large_k`,
  the classic human "more patience for larger rewards" pattern.
- H6 (persona, exploratory): under greater-discounting personas, fitted k is higher than
  under lesser-discounting personas and/or the persona-off control (same IV as Waiting Game).

## Design (see `config_q8.yaml` / `kirby27_items.yaml` for exact values)

- 27 fixed items x 30 samples x 9 models = 7,290 forced binary choices per reasoning mode
  (persona-off). Persona-on multiplies by 8 personas.
- Order of A/B assignment randomized per trial to control position bias (same control as
  the sibling Waiting Game project).
- Item wording variant: `verbatim` (exact instrument text) by default. A `paraphrased`
  variant is implemented (`kirby_game.py::render_paraphrased_option_texts`) as a
  contamination control -- the MCQ-27's exact wording is extremely widely reproduced
  online, so verbatim administration risks eliciting memorized response patterns rather
  than a computed preference. Large verbatim-vs-paraphrase divergence in fitted k would be
  evidence of memorization. **Deferred**: not yet run in this pass (see Notes).

## Scoring (two methods, both reported, per Kaplan et al. 2016 / Wileyto et al. 2004)

1. **Hand/consistency method**: binarize each item by its modal (>50%) sampled choice,
   find the k-value maximizing consistency across items (ties -> geometric mean of tied
   candidates). Computed for `small_k`/`medium_k`/`large_k` (9 items each) and `overall_k`
   (all 27 pooled); `geomean_k` = geometric mean of small/medium/large, directly comparable
   to published human population percentile norms.
2. **Probabilistic logistic method**: fits a discounted-random-utility logistic model
   (`V(amount,delay) = amount / (1+k*delay)`, `P(sooner) = sigmoid(beta*(V_sir - V_ldr))`)
   via MLE on the raw (non-binarized) trial-level choices, with bootstrap 95% CIs. Avoids
   the information loss of binarizing stochastic LLM outputs; this is the primary quantity
   for statistical comparison across models/conditions.

## Analysis plan

1. Parse raw completions to A/B (`parse_responses.py`); exclude/report parse failures, do
   not impute. Preserve persona columns when present.
2. Run competence checks (`competence_checks.py`) per model (× persona when enabled)
   **before** trusting a fit. A condition failing rank-monotonicity or the 75% consistency
   threshold is reported as "no valid discount rate" and excluded from k comparison (but
   still shown in the summary table).
3. For conditions passing competence checks, both scoring methods above are fit
   (`fit_discounting.py`).
4. Compare fitted k across models, modes, personas, and against the approximate human
   benchmark (`analyze.py`, `compare_modes.py`); no p-value threshold is preregistered.

## Deviations from the sibling Waiting Game project

- The Waiting Game's two competence checks (grid monotonicity, money preference at $0)
  don't translate literally to a fixed 27-item instrument with no $0 option; they are
  replaced by the rank-monotonicity check (H1) and the consistency-score gate (H2), which
  serve the same purpose (flagging models whose choices don't track option value at all).
- Delay units are **days** here (matching the Kirby instrument's native units) vs.
  **months** in the Waiting Game; `fitting.k_lower_bound`/`k_upper_bound` in `config_q8.yaml`
  are scaled accordingly (Kirby items' own k range is ~0.00016-0.25/day).
- Stimulus is the fixed MCQ-27 item set (not a synthetic delay × amount grid). Models,
  reasoning modes, and persona catalog match the Waiting Game.

## Notes / Deferred Items

- Paraphrased-variant contamination check (see Design section): implemented in code,
  not yet executed -- would require doubling the call budget for this pass.
- Prompt-mode axis historically also included one-shot/two-shot; current pipeline matches
  Waiting Game with `direct` | `cot` only. See run log / `results/tables/sanity_check_summary.md`
  for which modes have completed data.
- Convergent-validity correlation against the Waiting Game's independently-fit k (central
  deliverable of `phase 1 extended.md`'s Kirby module) is a natural next step once both
  projects have comparable completed runs, but is out of scope for this pipeline alone.
- No mechanistic/activation access needed here; Phase 3 (steering) would still require a
  HF/transformers or MLX backend.
