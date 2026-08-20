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

## Deviations
Any deviation from this plan (e.g. grid changes, exclusion criteria changes) will be noted in `analyze.py` output rather than silently applied.
