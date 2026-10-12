#!/usr/bin/env python3
"""Batch-run misalignment scenarios across Waiting Game conditions.

Conditions match temporal-discounting 1-to-1 on:
  (model_name, persona_enabled, persona_id)

Persona-off is the control (persona_id=None). Persona-on runs once per
catalog entry from config_q8.yaml (via config.yaml → temporal_discounting_config).

Usage:
  python src/run_conditions.py
  python src/run_conditions.py --scenario number_guessing --model qwen2.5:7b-instruct-q8_0
  python src/run_conditions.py --persona --persona-id substance_use
  python src/run_conditions.py --no-persona --skip-openai-evaluation
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_utils import (  # noqa: E402
    load_config,
    resolve_dir_path,
    safe_filename_for_model,
)
from persona import (  # noqa: E402
    condition_persona_tag,
    empty_persona_fields,
    load_persona_catalog,
    persona_log_fields,
)


def build_condition_list(config, persona_mode, persona_id_filter=None):
    """persona_mode: False | True | None (None => control + all personas)."""
    models = list(config["models"])
    persona_config = dict(config.get("persona") or {})
    prompt_template = persona_config.get("prompt_template")
    full_catalog = load_persona_catalog({**persona_config, "enabled": True})

    if persona_id_filter:
        catalog = [p for p in full_catalog if p["persona_id"] == persona_id_filter]
        if not catalog:
            known = [p["persona_id"] for p in full_catalog]
            raise SystemExit(
                f"Unknown --persona-id {persona_id_filter!r}. Known: {known}"
            )
    else:
        catalog = full_catalog

    conditions = []
    include_control = persona_mode in (False, None) and persona_id_filter is None
    include_personas = persona_mode in (True, None)

    if include_control:
        for model_name in models:
            conditions.append({
                "model_name": model_name,
                **empty_persona_fields(),
                "prompt_template": prompt_template,
            })

    if include_personas:
        for model_name in models:
            for persona_fields in catalog:
                conditions.append({
                    "model_name": model_name,
                    **persona_log_fields(persona_fields),
                    "prompt_template": prompt_template,
                })

    return conditions


def condition_output_dir(outputs_root, scenario, condition, run_index, n_repeats, run_id=None):
    model_safe = safe_filename_for_model(condition["model_name"])
    persona_tag = condition_persona_tag(
        condition["persona_enabled"], condition.get("persona_id")
    )
    parts = [outputs_root, scenario, model_safe, persona_tag]
    if n_repeats > 1:
        parts.append(f"run{run_index}")
    if run_id:
        parts.append(run_id)
    return os.path.join(*parts)


def write_condition_file(path, condition, scenario, misalignment_cfg):
    payload = {
        "scenario": scenario,
        "model_name": condition["model_name"],
        "persona_enabled": condition["persona_enabled"],
        "persona_id": condition.get("persona_id"),
        "persona_label": condition.get("persona_label"),
        "persona_discounting_group": condition.get("persona_discounting_group"),
        "persona_text": condition.get("persona_text"),
        "persona_prompt_template": condition.get("prompt_template"),
        "ollama_base_url": misalignment_cfg.get(
            "ollama_openai_base_url", "http://host.docker.internal:11434/v1"
        ),
        "skip_openai_evaluation": bool(
            misalignment_cfg.get("skip_openai_evaluation", False)
        ),
        "evaluator_backend": misalignment_cfg.get("evaluator_backend", "ollama"),
        "evaluator_model": misalignment_cfg.get("evaluator_model", "llama3.3:70b"),
        "max_agent_steps": misalignment_cfg.get("max_agent_steps", 20),
        "ollama_num_ctx": int(misalignment_cfg.get("ollama_num_ctx", 131072)),
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return payload


def run_one(scenario_folder, condition_file, output_dir, remove_images=False):
    run_sh = os.path.join(PROJECT_ROOT, "run.sh")
    cmd = [
        run_sh,
        "--folder", scenario_folder,
        "--condition", condition_file,
        "--output-dir", output_dir,
        "--no-timestamp",
    ]
    if remove_images:
        cmd.append("--remove-images")

    print(f"\n>>> {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return completed.returncode


def append_index_row(index_path, row):
    os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
    write_header = not os.path.exists(index_path)
    fieldnames = [
        "scenario",
        "model_name",
        "persona_enabled",
        "persona_id",
        "persona_label",
        "persona_discounting_group",
        "run_index",
        "status",
        "evaluation",
        "output_dir",
        "logged_at_unix",
    ]
    with open(index_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def read_result_json(output_dir):
    path = os.path.join(output_dir, "result.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Sweep misalignment scenarios across temporal-discounting conditions."
    )
    parser.add_argument("--config", default=None, help="Path to misalignment config.yaml")
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="Scenario folder name under scenarios/ (repeatable). Default: config list.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Run only this Ollama model (must be in config models list).",
    )
    persona_group = parser.add_mutually_exclusive_group()
    persona_group.add_argument(
        "--persona",
        action="store_true",
        help="Persona-on only (all catalog personas, or --persona-id).",
    )
    persona_group.add_argument(
        "--no-persona",
        action="store_true",
        help="Persona-off control only.",
    )
    parser.add_argument(
        "--persona-id",
        default=None,
        help="Restrict persona-on runs to this id (implies persona-on only).",
    )
    parser.add_argument(
        "--skip-openai-evaluation",
        action="store_true",
        help="Force skip OpenAI validator/evaluator for this sweep.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=None,
        help="Episodes per condition (default: config misalignment.n_repeats).",
    )
    parser.add_argument("--id", dest="run_id", default=None, help="Optional run id tag.")
    parser.add_argument(
        "--remove-images",
        action="store_true",
        help="Pass through to run.sh (docker compose --rmi all).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print conditions only; do not launch Docker.",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        default=True,
        help="After the sweep, run src/analyze_reward_hacking.py (default).",
    )
    parser.add_argument(
        "--no-analyze",
        action="store_false",
        dest="analyze",
        help="Do not run the objective hack-rate summarizer after the sweep.",
    )
    args = parser.parse_args()

    if args.persona_id:
        args.persona = True

    config = load_config(args.config)
    misalignment_cfg = dict(config.get("misalignment") or {})
    if args.skip_openai_evaluation:
        misalignment_cfg["skip_openai_evaluation"] = True

    scenarios = args.scenarios or list(misalignment_cfg.get("scenarios") or [])
    if not scenarios:
        raise SystemExit("No scenarios configured. Pass --scenario or set misalignment.scenarios.")

    models = list(config["models"])
    if args.model is not None:
        if args.model not in models:
            raise SystemExit(f"--model {args.model!r} not in config models: {models}")
        config = dict(config)
        config["models"] = [args.model]

    if args.persona or args.persona_id:
        persona_mode = True
    elif args.no_persona:
        persona_mode = False
    else:
        persona_mode = None  # control + all personas

    conditions = build_condition_list(config, persona_mode, args.persona_id)
    n_repeats = (
        args.repeat if args.repeat is not None else int(misalignment_cfg.get("n_repeats", 1))
    )
    outputs_root = resolve_dir_path(config.get("paths", {}).get("outputs_dir", "outputs"))
    conditions_dir = resolve_dir_path(
        config.get("paths", {}).get("conditions_dir", "outputs/conditions")
    )
    index_path = os.path.join(outputs_root, "condition_index.csv")

    print(f"Config: {config.get('_config_path')}")
    print(f"Waiting Game config: {config.get('_temporal_discounting_config_path')}")
    print(f"Scenarios ({len(scenarios)}): {scenarios}")
    print(f"Models ({len(config['models'])}): {config['models']}")
    print(f"Conditions per scenario: {len(conditions)} × {n_repeats} repeat(s)")
    print(f"skip_openai_evaluation={misalignment_cfg.get('skip_openai_evaluation', False)}")
    print(
        f"evaluator={misalignment_cfg.get('evaluator_backend', 'ollama')}/"
        f"{misalignment_cfg.get('evaluator_model', 'llama3.3:70b')}"
    )

    if args.dry_run:
        for scenario in scenarios:
            for condition in conditions:
                tag = condition_persona_tag(
                    condition["persona_enabled"], condition.get("persona_id")
                )
                print(f"  {scenario} | {condition['model_name']} | {tag}")
        return

    for scenario in scenarios:
        scenario_folder = os.path.join(PROJECT_ROOT, "scenarios", scenario)
        if not os.path.isdir(scenario_folder):
            print(f"WARNING: missing scenario folder {scenario_folder}, skipping.")
            continue

        for condition in conditions:
            for run_index in range(1, n_repeats + 1):
                output_dir = condition_output_dir(
                    outputs_root, scenario, condition, run_index, n_repeats, args.run_id
                )
                persona_tag = condition_persona_tag(
                    condition["persona_enabled"], condition.get("persona_id")
                )
                condition_file = os.path.join(
                    conditions_dir,
                    f"{scenario}__{safe_filename_for_model(condition['model_name'])}__{persona_tag}.json",
                )
                write_condition_file(condition_file, condition, scenario, misalignment_cfg)

                rc = run_one(
                    scenario_folder,
                    condition_file,
                    output_dir,
                    remove_images=args.remove_images,
                )
                result = read_result_json(output_dir)
                append_index_row(
                    index_path,
                    {
                        "scenario": scenario,
                        "model_name": condition["model_name"],
                        "persona_enabled": condition["persona_enabled"],
                        "persona_id": condition.get("persona_id"),
                        "persona_label": condition.get("persona_label"),
                        "persona_discounting_group": condition.get(
                            "persona_discounting_group"
                        ),
                        "run_index": run_index,
                        "status": result.get("status", f"EXIT_{rc}"),
                        "evaluation": result.get("evaluation"),
                        "output_dir": output_dir,
                        "logged_at_unix": time.time(),
                    },
                )

    print(f"\nCondition index: {index_path}")

    if args.analyze:
        analyze = os.path.join(PROJECT_ROOT, "src", "analyze_reward_hacking.py")
        print("\n>>> running objective hack-rate analysis")
        subprocess.run([sys.executable, analyze], cwd=PROJECT_ROOT, check=False)


if __name__ == "__main__":
    main()
