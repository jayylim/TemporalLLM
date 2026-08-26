"""Small shared helpers for loading config.yaml and resolving project paths."""

import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    with open(config_path, "r") as config_file:
        return yaml.safe_load(config_file)


def resolve_dir_path(relative_dir_path):
    """Turns a config.yaml directory path into an absolute path, creating it if needed."""
    absolute_dir_path = os.path.join(PROJECT_ROOT, relative_dir_path)
    os.makedirs(absolute_dir_path, exist_ok=True)
    return absolute_dir_path


def mode_suffix(reasoning_mode):
    """Filename suffix distinguishing reasoning modes: "" for the original
    direct-answer mode (keeps existing filenames unchanged/backward
    compatible), "__cot" for chain-of-thought mode.
    """
    return "" if reasoning_mode == "direct" else f"__{reasoning_mode}"


def persona_suffix(persona_enabled):
    """Filename suffix for persona-on runs so they never overwrite no-persona data."""
    return "__persona" if persona_enabled else ""


def result_suffix(reasoning_mode, persona_enabled=False):
    """Combined mode + persona suffix used for raw/processed/results filenames."""
    return f"{mode_suffix(reasoning_mode)}{persona_suffix(persona_enabled)}"


def persona_enabled_from_config(config):
    persona_config = config.get("persona") or {}
    return bool(persona_config.get("enabled", False))
