"""Waiting Game trial construction: builds the delay x amount grid and renders
the A/B prompts with randomized option order (controls LLM position bias).
"""

import random


def build_cell_grid(delay_grid_months, amount_grid_dollars, competence_probe_amounts=None):
    """Returns the full delay x amount grid as a flat list of cell dicts.

    Grid lengths are arbitrary: any number of delays/amounts works. Optional
    `competence_probe_amounts` (e.g. [$0]) are appended when missing from the
    main amount grid so money-preference competence can still be evaluated
    after the fit grid dropped the $0 cell.
    """
    amounts_for_grid = list(amount_grid_dollars)
    for probe_amount in (competence_probe_amounts or []):
        if probe_amount not in amounts_for_grid:
            amounts_for_grid.append(probe_amount)

    trial_cells = []
    for delay_months in delay_grid_months:
        for amount_dollars in amounts_for_grid:
            trial_cells.append({
                "delay_months": delay_months,
                "amount_dollars": amount_dollars,
            })
    return trial_cells


def format_delay_duration(delay_months):
    """Human-readable delay phrase for prompts.

    Keeps data units as months, but renders the prompt text in the most
    natural unit: days/weeks for sub-month delays, years for whole-year
    multiples, otherwise months.
    """
    if delay_months < 1:
        approx_days = delay_months * 30.437  # mean Gregorian month length
        if approx_days < 10:
            n_days = max(1, int(round(approx_days)))
            return "1 day" if n_days == 1 else f"{n_days} days"
        n_weeks = max(1, int(round(approx_days / 7.0)))
        return "1 week" if n_weeks == 1 else f"{n_weeks} weeks"

    if float(delay_months) == int(delay_months):
        n_months = int(delay_months)
        if n_months >= 12 and n_months % 12 == 0:
            n_years = n_months // 12
            return "1 year" if n_years == 1 else f"{n_years} years"
        return "1 month" if n_months == 1 else f"{n_months} months"
    return f"{delay_months} months"


def render_option_texts(sooner_amount_dollars, delay_months, later_amount_dollars):
    """Renders sooner/later options with explicit receive/wait framing.

    Example:
      Receive $100 now
      Wait until 12 months to receive $1000
    """
    sooner_option_text = f"Receive ${sooner_amount_dollars} now"
    later_option_text = (
        f"Wait until {format_delay_duration(delay_months)} to receive "
        f"${later_amount_dollars}"
    )
    return sooner_option_text, later_option_text


def render_user_prompt(option_a_text, option_b_text):
    return f"A: {option_a_text}\nB: {option_b_text}"


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


def build_all_trials(waiting_game_config):
    """Builds every trial (all cells x all samples) for one model, in a fixed
    reproducible order determined by waiting_game_config['random_seed'].
    """
    order_rng = random.Random(waiting_game_config["random_seed"])

    trial_cells = build_cell_grid(
        waiting_game_config["delay_grid_months"],
        waiting_game_config["amount_grid_dollars"],
        waiting_game_config.get("competence_probe_amounts"),
    )
    later_amount_dollars = waiting_game_config["later_amount_dollars"]
    n_samples_per_cell = waiting_game_config["n_samples_per_cell"]
    fit_amount_set = set(waiting_game_config["amount_grid_dollars"])

    all_trials = []
    for trial_cell in trial_cells:
        for sample_index in range(n_samples_per_cell):
            trial = build_trial(
                trial_cell["delay_months"],
                trial_cell["amount_dollars"],
                later_amount_dollars,
                sample_index,
                order_rng,
            )
            # Probe-only cells ($0) are kept for competence checks but excluded
            # from hyperbolic fitting so the redesigned fit grid stays clean.
            trial["is_competence_probe"] = trial_cell["amount_dollars"] not in fit_amount_set
            all_trials.append(trial)
    return all_trials
