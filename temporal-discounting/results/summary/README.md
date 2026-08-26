# Waiting Game — factor summary

Clean tables for scanning results across **model**, **trial type** (prompting
mode: direct / chain-of-thought / one-shot / two-shot), and **persona** (on/off).

Human benchmark (Rachlin et al. 1991): k = 0.01 per month.
Reasonable k bounds (hits cut from reliability, still reported): [1e-06, 10.0].

## Files

| File | Contents |
|---|---|
| `by_condition.csv` | One row per **model × trial_type × persona** with competence gates, fit reliability, and fitted k. **Start here.** |
| `by_factor.csv` | Rollups: pass rates and mean/median k (when valid) by each factor alone and useful pairs (e.g. trial_type × persona). |
| `by_demographics.csv` | Present only when persona-on runs exist: gender / age-band strata from `analyze.py`. |
| `sanity_check_summary.md` | Human-readable checklist table (same content as `results/tables/sanity_check_summary.md`). |

## `by_condition.csv` columns

- **model_name** / **model_family**: full Ollama tag and coarse family (qwen2.5, qwen3, llama3.1, mistral).
- **trial_type**: prompting condition (`direct`, `chain-of-thought`, `one-shot`, `two-shot`).
- **persona**: `on` or `off` demographic persona framing.
- **competence_passed**: monotonicity AND money-preference both pass.
- **k_reliable**: choice sensitivity adequate AND fitted k not at bound.
- **valid_discount_rate**: competence_passed AND k_reliable — trust the fitted k only when this is true.
- **k**, **k_ci_low**, **k_ci_high**, **beta**: hyperbolic fit (shown even when invalid; check flags first).

Regenerate with: `python src/compare_modes.py`
