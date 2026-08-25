# Preregistration: Kirby MCQ-27 Discounting in Local Qwen2.5 Models

Sibling project to `../temporal-discounting` (Waiting Game): same three models, same
overall pipeline architecture, different instrument. Fixed before running the full
N=30 experiment (pilot excluded).

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
  across model sizes (1.5b vs 3b vs 7b), with no directional prediction preregistered.
- H4: Fitted k values differ from the approximate Kirby population benchmark
  (`config.yaml: human_benchmark.kirby_median_k_per_day`).
- H5 (magnitude effect, exploratory/reported not gating): `small_k > medium_k > large_k`,
  the classic human "more patience for larger rewards" pattern.

## Design (see `config.yaml` / `kirby27_items.yaml` for exact values)

- 27 fixed items x 30 samples x 3 models = 2,430 forced binary choices per reasoning mode.
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
   not impute.
2. Run competence checks (`competence_checks.py`) per model **before** trusting a fit. A
   model failing rank-monotonicity or the 75% consistency threshold is reported as "no
   valid discount rate" and excluded from k comparison (but still shown in the summary
   table).
3. For models passing competence checks, both scoring methods above are fit
   (`fit_discounting.py`).
4. Compare fitted k across models and against the approximate human benchmark
   (`analyze.py`, `compare_modes.py`); no p-value threshold is preregistered, as this is
   an exploratory 3-model comparison, not a hypothesis test with inferential claims.

## Deviations from the sibling Waiting Game project

- The Waiting Game's two competence checks (grid monotonicity, money preference at $0)
  don't translate literally to a fixed 27-item instrument with no $0 option; they are
  replaced by the rank-monotonicity check (H1) and the consistency-score gate (H2), which
  serve the same purpose (flagging models whose choices don't track option value at all).
- Delay units are **days** here (matching the Kirby instrument's native units) vs.
  **months** in the Waiting Game; `fitting.k_lower_bound`/`k_upper_bound` in `config.yaml`
  are scaled accordingly (Kirby items' own k range is ~0.00016-0.25/day).

## Notes / Deferred Items

- Paraphrased-variant contamination check (see Design section): implemented in code,
  not yet executed -- would require doubling the call budget for this pass.
- Prompt-mode axis (one-shot/two-shot/CoT, mirroring the sibling project's extension):
  infrastructure is implemented (`kirby_game.build_few_shot_messages_for_mode`,
  `--mode` flag across all scripts) but this preregistration covers whichever mode(s)
  were actually executed -- see the run log / `results/tables/sanity_check_summary.md`
  for which modes have completed data.
- Convergent-validity correlation against the Waiting Game's independently-fit k (central
  deliverable of `phase 1 extended.md`'s Kirby module) is a natural next step once both
  projects have comparable completed runs, but is out of scope for this pipeline alone.
- No mechanistic/activation access needed here; Phase 3 (steering) would still require a
  HF/transformers or MLX backend.
