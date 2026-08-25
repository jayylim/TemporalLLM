# Preregistration: Waiting Game Discounting in Local Qwen2.5 Models

Fixed before running the full N=30 experiment (pilot excluded).

## Hypotheses
- H1: Each model's P(choose sooner option) increases monotonically with the sooner amount `x`, for each fixed delay `d` (competence check).
- H2: Each model prefers any positive delayed amount over $0 now (competence check).
- H3: Fitted hyperbolic discount rate `k` differs across model sizes (1.5b vs 3b vs 7b), with no directional prediction preregistered.
- H4: Fitted `k` values differ from the Rachlin et al. (1991) human benchmark.

## Design (see config.yaml for exact grids)
- 7 delays x 7 amounts x 30 samples x 3 models = 4,410 forced binary choices.
- Order of A/B assignment randomized per trial to control position bias.

## Analysis plan
1. Parse raw completions to A/B (`parse_responses.py`); exclude/report parse failures, do not impute.
2. Run competence checks (`competence_checks.py`) per model **before** fitting. A model failing either check is reported as "no valid discount rate" and excluded from k comparison (but still shown in the parse-rate/competence table).
3. For models passing competence checks, fit hyperbolic discounting `U(x, d) = x / (1 + k*d)` via a discounted-random-utility choice model (logistic link), with bootstrap 95% CIs over trials (`fit_discounting.py`).
4. Compare fitted `k` across models and against the human benchmark (`analyze.py`); no p-value threshold is preregistered as this is an exploratory 3-model comparison, not a hypothesis test with inferential claims.

## Exploratory extension: prompting-format effects on competence/hyperbolic fit (added after direct-mode results)

The N=30 direct-mode run above completed and **all three models failed the competence gate**
(`results/tables/competence_checks.csv`): 1.5b and 3b fail both monotonicity and money-preference;
7b fails monotonicity. Per the analysis plan, this means "no valid discount rate" for all three
models under direct prompting — we cannot yet say whether Qwen2.5 *lacks* hyperbolic-discounting-like
behavior, or whether the minimal single-letter prompt format is failing to *elicit* it.

Ross, Kim & Lo (2024) ["LLM economicus?"](https://arxiv.org/abs/2408.02784) §4 ran a similar
prompting-intervention case study on GPT-4, but for **risk/loss aversion in their gambling game**,
not for time discounting in the waiting game. They found: direct prompting and zero-shot
chain-of-thought (CoT) often failed to reliably shift GPT-4's behavior toward the intended target;
one-shot prompting (a single worked example) was more effective; two-shot prompting showed mixed
results because the model sometimes confounded the two examples. **The paper does not report
CoT/few-shot results for the waiting game itself** — extending this to time discounting here is an
extrapolation, not a replication of a documented finding, and should be reported as such.

### H5-H7 (exploratory, not preregistered before the direct-mode run)
- H5: Zero-shot CoT prompting (`--mode cot`) does not reliably change competence-check pass rates
  relative to direct prompting, consistent with Ross et al.'s null CoT result for risk/loss aversion.
- H6: One-shot prompting (`--mode one_shot`) increases the competence-check pass rate (and/or
  produces a `k_is_reliable` fit) relative to direct/CoT, consistent with Ross et al.'s one-shot
  result for risk/loss aversion.
- H7: Two-shot prompting (`--mode two_shot`) shows mixed/weaker effects than one-shot, consistent
  with Ross et al.'s account of example confounding.

### Method
- `src/waiting_game.py` renders the one/two worked examples (`config.yaml` -> `waiting_game.one_shot_examples`
  / `two_shot_examples`) as prior user/assistant chat turns via `OllamaClient.chat` (Ollama's
  `/api/chat` endpoint), using the **same minimal single-letter answer format as direct mode** so the
  few-shot variable is isolated from the CoT-reasoning variable.
- Example delay/amount values (18 months; $0 and $980) are deliberately **outside** the tested 7x7
  grid (delays 1-120mo, amounts $0-$900 in $150 steps except $0 itself, which is intentionally reused
  since it is literally the target of competence check #2) so the model must generalize the
  demonstrated reasoning pattern rather than memorize the answer to an evaluated cell.
- Same trial grid, same order-randomization seed, and same models as the direct-mode run, for
  clean cross-mode comparison.
- `src/compare_modes.py` aggregates `comparison_summary{mode}.csv` across all modes that have been
  run and plots competence/`k` side by side per model.

### Deviations
Any deviation from this plan (e.g. grid changes, exclusion criteria changes) will be noted in
`analyze.py` output rather than silently applied. This exploratory extension (H5-H7, one_shot/
two_shot modes) is itself a preregistration deviation: it was added *after* observing that direct-mode
Qwen2.5 results failed competence checks, motivated by (but not a direct replication of) Ross et al.
(2024)'s prompting-intervention findings for a different game. Results from H5-H7 should be reported
as hypothesis-generating, not confirmatory.
