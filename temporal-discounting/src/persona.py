"""Behavioral persona framing for the Waiting Game.

When enabled, the full trial grid is run once under each configured persona
(plus a separate persona-off control run). Each persona is a second-person
lifestyle description prepended to the system prompt. Personas are tagged
with a researcher-only discounting_group ("greater" / "lesser") for
stratified analysis; that label is never shown to the model.
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
    """Null persona columns for no-persona runs (keeps CSV schema stable)."""
    return {
        "persona_enabled": False,
        "persona_id": None,
        "persona_label": None,
        "persona_discounting_group": None,
        "persona_text": None,
    }


def persona_log_fields(persona_fields):
    """Fields written to raw jsonl / choices.csv for one persona-on trial."""
    return {
        "persona_enabled": True,
        "persona_id": persona_fields["persona_id"],
        "persona_label": persona_fields["persona_label"],
        "persona_discounting_group": persona_fields["persona_discounting_group"],
        "persona_text": persona_fields["persona_text"],
    }


def completion_key(record):
    """Resume key: persona_id + trial_id so multi-persona files don't collide."""
    persona_id = record.get("persona_id") or "none"
    return f"{persona_id}::{record['trial_id']}"


def iter_persona_groups(choices_df):
    """Yields (persona_id, discounting_group, label, group_df) for analysis loops.

    Persona-off / missing columns -> one pass with persona_id=None.
    """
    if choices_df is None or choices_df.empty:
        return
    if "persona_id" not in choices_df.columns or choices_df["persona_id"].isna().all():
        yield None, None, None, choices_df
        return

    working_df = choices_df.copy()
    # Stable order: greater personas first, then lesser; preserve first-seen
    # order within each group (matches config catalog order when logged that way).
    group_rank = {"greater": 0, "lesser": 1}
    working_df["_group_rank"] = working_df["persona_discounting_group"].map(
        lambda g: group_rank.get(g, 2)
    )
    working_df = working_df.sort_values("_group_rank", kind="mergesort")

    for persona_id, group_df in working_df.groupby("persona_id", sort=False):
        discounting_group = group_df["persona_discounting_group"].iloc[0]
        label = (
            group_df["persona_label"].iloc[0]
            if "persona_label" in group_df.columns
            else persona_id
        )
        yield persona_id, discounting_group, label, group_df.drop(columns=["_group_rank"])
