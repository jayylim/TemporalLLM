"""Small shared helpers for loading config.yaml and resolving project paths."""

import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "config.yaml")
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


def variant_suffix(variant):
    """Filename suffix distinguishing item wording variant: "" for verbatim
    (default), "__paraphrased" for the contamination-control reword.
    """
    return "" if variant == "verbatim" else f"__{variant}"
