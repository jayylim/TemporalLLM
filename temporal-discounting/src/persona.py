"""Demographic persona sampling for the Waiting Game.

When enabled, each trial gets a randomly drawn persona (US-census surname,
age 20-80, gender) prepended to the system prompt so the model answers as
that person. Demographics are logged with every trial for stratified analysis.
"""

import os
import random

from config_utils import PROJECT_ROOT

DEFAULT_GENDERS = ["male", "female"]
DEFAULT_PROMPT_TEMPLATE = (
    "You are a {age}-year-old {gender} with the surname {surname}. "
    "Answer the following questions as this person would."
)


def load_surnames(surnames_file_path):
    """Loads one surname per line from a text file (Census top-N list)."""
    absolute_path = surnames_file_path
    if not os.path.isabs(absolute_path):
        absolute_path = os.path.join(PROJECT_ROOT, absolute_path)

    with open(absolute_path, "r") as surnames_file:
        surnames = [line.strip() for line in surnames_file if line.strip()]
    if not surnames:
        raise ValueError(f"No surnames found in {absolute_path}")
    return surnames


def sample_persona(persona_rng, surnames, age_min, age_max, genders):
    """Draws one (surname, age, gender) triple."""
    return {
        "persona_surname": persona_rng.choice(surnames),
        "persona_age": persona_rng.randint(age_min, age_max),
        "persona_gender": persona_rng.choice(genders),
    }


def render_persona_preamble(persona_fields, prompt_template):
    return prompt_template.format(
        surname=persona_fields["persona_surname"],
        age=persona_fields["persona_age"],
        gender=persona_fields["persona_gender"],
    )


def compose_system_prompt_with_persona(base_system_prompt, persona_fields, prompt_template):
    """Prepends the persona framing to the task system prompt."""
    preamble = render_persona_preamble(persona_fields, prompt_template)
    return f"{preamble}\n\n{base_system_prompt}"


def make_persona_sampler(persona_config):
    """Returns (sample_fn, enabled) where sample_fn() -> persona dict or None.

    sample_fn draws a fresh persona each call when enabled; returns None when
    persona is disabled (so callers can always call it and unpack safely).
    """
    enabled = bool(persona_config.get("enabled", False))
    if not enabled:
        return (lambda: None), False

    surnames = load_surnames(persona_config["surnames_file"])
    age_min = int(persona_config.get("age_min", 20))
    age_max = int(persona_config.get("age_max", 80))
    genders = list(persona_config.get("genders", DEFAULT_GENDERS))
    prompt_template = persona_config.get("prompt_template", DEFAULT_PROMPT_TEMPLATE)
    persona_rng = random.Random(persona_config.get("random_seed", 20260826))

    def sample_fn():
        fields = sample_persona(persona_rng, surnames, age_min, age_max, genders)
        fields["persona_prompt_preamble"] = render_persona_preamble(fields, prompt_template)
        return fields

    return sample_fn, True


def empty_persona_fields():
    """Null persona columns for no-persona runs (keeps CSV schema stable)."""
    return {
        "persona_enabled": False,
        "persona_surname": None,
        "persona_age": None,
        "persona_gender": None,
    }
