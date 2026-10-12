"""Small shared helpers for loading config.yaml and resolving project paths."""

import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "config_q8.yaml")  # change this if changing the models i want to use
    with open(config_path, "r") as config_file:
        return yaml.safe_load(config_file)


def load_kirby_items(config):
    """Loads kirby27_items.yaml (path from config['kirby']['items_file'])."""
    items_path = os.path.join(PROJECT_ROOT, config["kirby"]["items_file"])
    with open(items_path, "r") as items_file:
        return yaml.safe_load(items_file)["items"]


def resolve_dir_path(relative_dir_path):
    """Turns a config.yaml directory path into an absolute path, creating it if needed."""
    absolute_dir_path = os.path.join(PROJECT_ROOT, relative_dir_path)
    os.makedirs(absolute_dir_path, exist_ok=True)
    return absolute_dir_path


def mode_suffix(reasoning_mode):
    """Filename suffix distinguishing reasoning modes: "" for the original
    direct-answer mode (keeps existing filenames unchanged/backward
    compatible), "__cot" for chain-of-thought mode, etc.
    """
    return "" if reasoning_mode == "direct" else f"__{reasoning_mode}"


def persona_suffix(persona_enabled):
    """Filename suffix for persona-on runs so they never overwrite no-persona data."""
    return "__persona" if persona_enabled else ""


def result_suffix(reasoning_mode, persona_enabled=False):
    """Combined mode + persona suffix used for raw/processed/results filenames."""
    return f"{mode_suffix(reasoning_mode)}{persona_suffix(persona_enabled)}"


def variant_suffix(variant):
    """Filename suffix distinguishing item wording variant: "" for verbatim
    (default), "__paraphrased" for the contamination-control reword.
    """
    return "" if variant == "verbatim" else f"__{variant}"


def kirby_result_suffix(reasoning_mode, persona_enabled, variant):
    """Mode + persona + Kirby wording-variant suffix for all Kirby pipeline files."""
    return f"{result_suffix(reasoning_mode, persona_enabled)}{variant_suffix(variant)}"


def persona_enabled_from_config(config):
    persona_config = config.get("persona") or {}
    return bool(persona_config.get("enabled", False))
