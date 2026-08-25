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


def build_few_shot_messages(example_defs, order_rng):
    """Renders a list of worked examples (config `one_shot_examples` /
    `two_shot_examples`) into alternating user/assistant chat turns, with the
    A/B order randomized per example (using order_rng) so the assistant's
    demonstrated answer isn't trivially always the same letter. Always uses
    verbatim-style wording (the few-shot examples aren't scored items, so the
    paraphrase contamination control doesn't apply to them).
    """
    example_messages = []
    for example in example_defs:
        sooner_option_text, later_option_text = render_verbatim_option_texts(
            example["sir_amount_dollars"], example["ldr_amount_dollars"], example["delay_days"]
        )

        sooner_is_option_a = order_rng.random() < 0.5
        if sooner_is_option_a:
            option_a_text, option_b_text = sooner_option_text, later_option_text
        else:
            option_a_text, option_b_text = later_option_text, sooner_option_text

        correct_choice_is_sooner = example["correct_choice"] == "sooner"
        correct_letter = "A" if (correct_choice_is_sooner == sooner_is_option_a) else "B"

        example_messages.append({"role": "user", "content": render_user_prompt(option_a_text, option_b_text)})
        example_messages.append({"role": "assistant", "content": correct_letter})
    return example_messages


def build_few_shot_messages_for_mode(kirby_config, reasoning_mode):
    """Returns the rendered few-shot example turns for `--mode one_shot` /
    `--mode two_shot`, or [] for any other mode (direct/cot use no examples).
    """
    example_config_key_by_mode = {
        "one_shot": "one_shot_examples",
        "two_shot": "two_shot_examples",
    }
    example_config_key = example_config_key_by_mode.get(reasoning_mode)
    if example_config_key is None:
        return []

    order_rng = random.Random(kirby_config["few_shot_example_order_seed"])
    return build_few_shot_messages(kirby_config[example_config_key], order_rng)


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
