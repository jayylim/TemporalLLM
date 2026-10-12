"""Behavioral persona framing — mirrored from temporal-discounting/src/persona.py.

Keep field names and prompt composition identical so misalignment results join
1-to-1 with Waiting Game rows on (model_name, persona_id / persona_enabled).
"""

DEFAULT_PROMPT_TEMPLATE = (
    "{persona_text}\n\n"
    "Answer the following questions as this person would."
)


def load_persona_catalog(persona_config):
    """Returns the list of persona dicts from config, validating required fields."""
    personas = list(persona_config.get("personas") or [])
    if not personas:
        raise ValueError(
            "persona.enabled is true but persona.personas is empty; "
            "define at least one behavioral persona in config."
        )

    catalog = []
    seen_ids = set()
    for entry in personas:
        persona_id = entry.get("id")
        text = entry.get("text")
        discounting_group = entry.get("discounting_group")
        if not persona_id or not text:
            raise ValueError(
                f"Each persona needs non-empty 'id' and 'text'; got {entry!r}"
            )
        if persona_id in seen_ids:
            raise ValueError(f"Duplicate persona id: {persona_id!r}")
        if discounting_group not in ("greater", "lesser"):
            raise ValueError(
                f"persona {persona_id!r}: discounting_group must be "
                f"'greater' or 'lesser', got {discounting_group!r}"
            )
        seen_ids.add(persona_id)
        catalog.append({
            "persona_id": persona_id,
            "persona_label": entry.get("label") or persona_id,
            "persona_discounting_group": discounting_group,
            "persona_text": text.strip(),
        })
    return catalog


def render_persona_preamble(persona_fields, prompt_template):
    return prompt_template.format(persona_text=persona_fields["persona_text"]).strip()


def compose_system_prompt_with_persona(base_system_prompt, persona_fields, prompt_template):
    """Prepends the persona framing to the task system prompt.

    Only persona_text enters the prompt; discounting_group is logging-only.
    """
    preamble = render_persona_preamble(persona_fields, prompt_template)
    return f"{preamble}\n\n{base_system_prompt}"


def make_persona_catalog(persona_config):
    """Returns (catalog, enabled, prompt_template).

    catalog is a list of persona field dicts when enabled, else [].
    """
    enabled = bool(persona_config.get("enabled", False))
    prompt_template = persona_config.get("prompt_template", DEFAULT_PROMPT_TEMPLATE)
    if not enabled:
        return [], False, prompt_template
    catalog = load_persona_catalog(persona_config)
    for fields in catalog:
        fields["persona_prompt_preamble"] = render_persona_preamble(fields, prompt_template)
    return catalog, True, prompt_template


def empty_persona_fields():
    """Null persona columns for no-persona runs (keeps schema stable)."""
    return {
        "persona_enabled": False,
        "persona_id": None,
        "persona_label": None,
        "persona_discounting_group": None,
        "persona_text": None,
    }


def persona_log_fields(persona_fields):
    """Fields written to result.json for one persona-on episode."""
    return {
        "persona_enabled": True,
        "persona_id": persona_fields["persona_id"],
        "persona_label": persona_fields["persona_label"],
        "persona_discounting_group": persona_fields["persona_discounting_group"],
        "persona_text": persona_fields["persona_text"],
    }


def condition_persona_tag(persona_enabled, persona_id=None):
    """Directory / filename tag matching temporal-discounting naming."""
    if not persona_enabled:
        return "none"
    if not persona_id:
        raise ValueError("persona_enabled requires persona_id")
    return f"persona__{persona_id}"
