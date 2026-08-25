"""Waiting Game trial construction: builds the delay x amount grid and renders
the A/B prompts with randomized option order (controls LLM position bias).
"""

import random


def build_cell_grid(delay_grid_months, amount_grid_dollars):
    """Returns the full delay x amount grid as a flat list of cell dicts."""
    trial_cells = []
    for delay_months in delay_grid_months:
        for amount_dollars in amount_grid_dollars:
            trial_cells.append({
                "delay_months": delay_months,
                "amount_dollars": amount_dollars,
            })
    return trial_cells


def render_option_texts(sooner_amount_dollars, delay_months, later_amount_dollars):
    sooner_option_text = f"${sooner_amount_dollars} now"
    later_option_text = f"${later_amount_dollars} in {delay_months} months"
    return sooner_option_text, later_option_text


def render_user_prompt(option_a_text, option_b_text):
    return f"A. {option_a_text}\nB. {option_b_text}"


def build_trial(delay_months, amount_dollars, later_amount_dollars, sample_index, order_rng):
    """Builds one fully-rendered trial: assigns A/B order and renders prompt text.

    order_rng: a random.Random instance (caller controls seeding for reproducibility).
    """
    sooner_option_text, later_option_text = render_option_texts(
        amount_dollars, delay_months, later_amount_dollars
    )

    sooner_is_option_a = order_rng.random() < 0.5  # 50/50 order randomization
    if sooner_is_option_a:
        option_a_text, option_b_text = sooner_option_text, later_option_text
    else:
        option_a_text, option_b_text = later_option_text, sooner_option_text

    trial_id = f"d{delay_months}_x{amount_dollars}_s{sample_index}"

    return {
        "trial_id": trial_id,
        "delay_months": delay_months,
        "amount_dollars": amount_dollars,
        "sample_index": sample_index,
        "sooner_is_option_a": sooner_is_option_a,
        "option_a_text": option_a_text,
        "option_b_text": option_b_text,
        "user_prompt": render_user_prompt(option_a_text, option_b_text),
    }


def build_few_shot_messages(example_defs, later_amount_dollars, order_rng):
    """Renders a list of worked examples (config `one_shot_examples` /
    `two_shot_examples`) into alternating user/assistant chat turns, with the
    A/B order randomized per example (using order_rng) so the assistant's
    demonstrated answer isn't trivially always the same letter.
    """
    example_messages = []
    for example in example_defs:
        sooner_option_text, later_option_text = render_option_texts(
            example["sooner_amount_dollars"], example["delay_months"], later_amount_dollars
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


def build_few_shot_messages_for_mode(waiting_game_config, reasoning_mode):
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

    order_rng = random.Random(waiting_game_config["few_shot_example_order_seed"])
    return build_few_shot_messages(
        waiting_game_config[example_config_key],
        waiting_game_config["later_amount_dollars"],
        order_rng,
    )


def build_all_trials(waiting_game_config):
    """Builds every trial (all cells x all samples) for one model, in a fixed
    reproducible order determined by waiting_game_config['random_seed'].
    """
    order_rng = random.Random(waiting_game_config["random_seed"])

    trial_cells = build_cell_grid(
        waiting_game_config["delay_grid_months"],
        waiting_game_config["amount_grid_dollars"],
    )
    later_amount_dollars = waiting_game_config["later_amount_dollars"]
    n_samples_per_cell = waiting_game_config["n_samples_per_cell"]

    all_trials = []
    for trial_cell in trial_cells:
        for sample_index in range(n_samples_per_cell):
            all_trials.append(build_trial(
                trial_cell["delay_months"],
                trial_cell["amount_dollars"],
                later_amount_dollars,
                sample_index,
                order_rng,
            ))
    return all_trials
