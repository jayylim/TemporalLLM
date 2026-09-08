"""Kirby MCQ-27 trial construction: renders the 27 fixed items (verbatim or
paraphrased wording) as A/B prompts with randomized option order (controls
LLM position bias), the same order-bias control used by the sibling Waiting
Game project's 49-cell grid.

Unlike the Waiting Game's synthetic grid, every item's (SIR, LDR, delay) is
fixed by the validated Kirby, Petry & Bickel (1999) instrument -- see
kirby27_items.yaml for the verified table and citations.
"""

import random


def render_verbatim_option_texts(sir_amount_dollars, ldr_amount_dollars, delay_days):
    sooner_option_text = f"${sir_amount_dollars} today"
    later_option_text = f"${ldr_amount_dollars} in {delay_days} days"
    return sooner_option_text, later_option_text


def render_paraphrased_option_texts(sir_amount_dollars, ldr_amount_dollars, delay_days):
    """Contamination-control wording: same dollar amounts/delays (which must
    stay fixed since the instrument's k-values are calibrated to them), but
    reworded surface phrasing so a memorized verbatim response pattern
    (the MCQ-27's exact wording is extremely widely reproduced online) is
    less likely to be trivially pattern-matched. Compare fitted k between
    verbatim and paraphrased runs (config.yaml `kirby.variant`); large
    divergence is evidence of memorization rather than a genuinely computed
    preference.
    """
    sooner_option_text = f"receive ${sir_amount_dollars} right now"
    later_option_text = f"wait {delay_days} days and receive ${ldr_amount_dollars} instead"
    return sooner_option_text, later_option_text


OPTION_TEXT_RENDERERS_BY_VARIANT = {
    "verbatim": render_verbatim_option_texts,
    "paraphrased": render_paraphrased_option_texts,
}


def render_user_prompt(option_a_text, option_b_text):
    return f"A. {option_a_text}\nB. {option_b_text}"


def build_trial(item, sample_index, variant, order_rng):
    """Builds one fully-rendered trial for one Kirby item: assigns A/B order
    and renders prompt text.

    order_rng: a random.Random instance (caller controls seeding for reproducibility).
    """
    render_option_texts = OPTION_TEXT_RENDERERS_BY_VARIANT[variant]
    sooner_option_text, later_option_text = render_option_texts(
        item["sir_amount_dollars"], item["ldr_amount_dollars"], item["delay_days"]
    )

    sooner_is_option_a = order_rng.random() < 0.5  # 50/50 order randomization
    if sooner_is_option_a:
        option_a_text, option_b_text = sooner_option_text, later_option_text
    else:
        option_a_text, option_b_text = later_option_text, sooner_option_text

    trial_id = f"item{item['item_id']}_{variant}_s{sample_index}"

    return {
        "trial_id": trial_id,
        "item_id": item["item_id"],
        "magnitude": item["magnitude"],
        "sir_amount_dollars": item["sir_amount_dollars"],
        "ldr_amount_dollars": item["ldr_amount_dollars"],
        "delay_days": item["delay_days"],
        "item_k": item["k_at_indifference"],
        "variant": variant,
        "sample_index": sample_index,
        "sooner_is_option_a": sooner_is_option_a,
        "option_a_text": option_a_text,
        "option_b_text": option_b_text,
        "user_prompt": render_user_prompt(option_a_text, option_b_text),
    }


def build_all_trials(kirby_config, items):
    """Builds every trial (all 27 items x all samples) for one model, in a
    fixed reproducible order determined by kirby_config['random_seed'].
    """
    order_rng = random.Random(kirby_config["random_seed"])
    variant = kirby_config["variant"]
    n_samples_per_item = kirby_config["n_samples_per_item"]

    all_trials = []
    for item in items:
        for sample_index in range(n_samples_per_item):
            all_trials.append(build_trial(item, sample_index, variant, order_rng))
    return all_trials
