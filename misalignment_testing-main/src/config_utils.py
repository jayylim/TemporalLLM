"""Load misalignment config, optionally merging models/persona from Waiting Game config."""

import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_path(path, base_dir=PROJECT_ROOT):
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(base_dir, path))


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path=None):
    """Loads misalignment config.yaml and merges sibling temporal-discounting config.

    Merge rules:
      - models, persona, ollama from temporal_discounting_config unless overridden
        locally in this config
      - misalignment.* and paths.* always from this config
    """
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    else:
        config_path = _resolve_path(config_path)

    local = load_yaml(config_path)
    sibling_rel = local.get("temporal_discounting_config")
    sibling = {}
    if sibling_rel:
        sibling_path = _resolve_path(sibling_rel, base_dir=os.path.dirname(config_path))
        if not os.path.exists(sibling_path):
            raise FileNotFoundError(
                f"temporal_discounting_config not found: {sibling_path} "
                f"(referenced from {config_path})"
            )
        sibling = load_yaml(sibling_path)

    merged = dict(sibling)
    # Local keys override sibling (models/persona/ollama can be pinned here).
    for key, value in local.items():
        if key == "temporal_discounting_config":
            continue
        merged[key] = value

    if "models" not in merged:
        raise ValueError(
            "No models list found. Set models in config.yaml or point "
            "temporal_discounting_config at config_q8.yaml."
        )
    if "persona" not in merged:
        raise ValueError(
            "No persona block found. Set persona in config.yaml or point "
            "temporal_discounting_config at config_q8.yaml."
        )

    merged["_config_path"] = config_path
    merged["_temporal_discounting_config_path"] = (
        _resolve_path(sibling_rel, base_dir=os.path.dirname(config_path))
        if sibling_rel
        else None
    )
    return merged


def resolve_dir_path(relative_dir_path, create=True):
    absolute_dir_path = os.path.join(PROJECT_ROOT, relative_dir_path)
    if create:
        os.makedirs(absolute_dir_path, exist_ok=True)
    return absolute_dir_path


def safe_filename_for_model(model_name):
    """Same sanitization as temporal-discounting (':' and '/' -> '__')."""
    return model_name.replace(":", "__").replace("/", "__")


def persona_enabled_from_config(config):
    persona_config = config.get("persona") or {}
    return bool(persona_config.get("enabled", False))


DEFAULT_HACKING_SCENARIOS = (
    "financial_audit",
    "number_guessing",
    "sys-main-audit",
)


def hacking_scenarios_from_config(config=None):
    """Scenarios in the reward-hacking sweep (config list, else the RH defaults)."""
    if config is None:
        try:
            config = load_config()
        except (FileNotFoundError, ValueError):
            return list(DEFAULT_HACKING_SCENARIOS)
    scenarios = list((config.get("misalignment") or {}).get("scenarios") or [])
    return scenarios or list(DEFAULT_HACKING_SCENARIOS)
