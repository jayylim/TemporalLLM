"""Main experiment driver: loops models x trials, calling Ollama and logging
every raw completion incrementally so the run is resumable after interruption.

Supports two reasoning modes (--mode):
  direct:    original minimal-instruction, single-letter-response prompt.
  cot:       chain-of-thought prompt that requires step-by-step reasoning
             before a "FINAL ANSWER: A/B" line.
Each mode writes to its own raw file (via config_utils.result_suffix) so it
never overwrites another mode's data. Persona-on runs add a further
`__persona` suffix and execute the full trial grid once under each
configured behavioral persona.

Usage: python src/run_experiment.py [--config path/to/config.yaml]
       [--mode direct|cot] [--persona|--no-persona]
"""

import argparse
import json
import os
import time

from tqdm import tqdm

from config_utils import load_config, resolve_dir_path, result_suffix, persona_enabled_from_config
from ollama_client import OllamaClient
from persona import (
    completion_key,
    compose_system_prompt_with_persona,
    empty_persona_fields,
    make_persona_catalog,
    persona_log_fields,
)
from waiting_game import build_all_trials

REASONING_MODES = ["direct", "cot"]

PROMPT_CONFIG_KEYS_BY_MODE = {
    "direct": ("system_prompt", "num_predict"),
    "cot": ("cot_system_prompt", "cot_num_predict"),
}


def safe_filename_for_model(model_name):
    return model_name.replace(":", "__").replace("/", "__")


def load_completed_keys(raw_jsonl_path):
    """Reads an existing raw jsonl file and returns completion keys already
    logged, so run_experiment.py can skip them on restart.
    """
    completed_keys = set()
    if not os.path.exists(raw_jsonl_path):
        return completed_keys

    with open(raw_jsonl_path, "r") as raw_file:
        for line in raw_file:
            line = line.strip()
            if not line:
                continue
            try:
                logged_record = json.loads(line)
                completed_keys.add(completion_key(logged_record))
            except (json.JSONDecodeError, KeyError):
                continue  # skip corrupted lines rather than crash a multi-hour run
    return completed_keys


def build_work_items(all_trials, persona_catalog, persona_enabled):
    """(persona_fields_or_None, trial) pairs covering control or every persona."""
    if not persona_enabled:
        return [(None, trial) for trial in all_trials]
    return [
        (persona_fields, trial)
        for persona_fields in persona_catalog
        for trial in all_trials
    ]


def run_experiment_for_model(model_name, all_trials, base_system_prompt, temperature, num_predict,
                              keep_alive, reasoning_mode, ollama_client, raw_jsonl_path,
                              persona_catalog=None, persona_enabled=False, prompt_template=None):
    persona_catalog = persona_catalog or []
    work_items = build_work_items(all_trials, persona_catalog, persona_enabled)
    completed_keys = load_completed_keys(raw_jsonl_path)
    pending_items = [
        (persona_fields, trial)
        for persona_fields, trial in work_items
        if completion_key({
            "persona_id": None if persona_fields is None else persona_fields["persona_id"],
            "trial_id": trial["trial_id"],
        }) not in completed_keys
    ]

    n_personas = len(persona_catalog) if persona_enabled else 0
    print(f"[{model_name} / {reasoning_mode} / persona={persona_enabled}"
          f"{f' x{n_personas}' if persona_enabled else ''}] "
          f"{len(completed_keys)} trials already done, {len(pending_items)} remaining.")

    with open(raw_jsonl_path, "a") as raw_file:
        for persona_fields, trial in tqdm(pending_items, desc=f"{model_name} [{reasoning_mode}]"):
            if persona_enabled:
                system_prompt = compose_system_prompt_with_persona(
                    base_system_prompt, persona_fields, prompt_template
                )
                persona_log = persona_log_fields(persona_fields)
            else:
                system_prompt = base_system_prompt
                persona_log = empty_persona_fields()

            raw_response_text = ollama_client.generate(
                model_name=model_name,
                system_prompt=system_prompt,
                user_prompt=trial["user_prompt"],
                temperature=temperature,
                num_predict=num_predict,
                keep_alive=keep_alive,
            )

            logged_record = dict(trial)  # copy trial fields (prompt, order, ids)
            logged_record["model_name"] = model_name
            logged_record["reasoning_mode"] = reasoning_mode
            logged_record.update(persona_log)
            logged_record["raw_response_text"] = raw_response_text
            logged_record["logged_at_unix"] = time.time()

            raw_file.write(json.dumps(logged_record) + "\n")
            raw_file.flush()  # survive interruption without losing this trial


def resolve_persona_enabled(args, config):
    if args.persona:
        return True
    if args.no_persona:
        return False
    return persona_enabled_from_config(config)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct",
                             help="direct: minimal single-letter prompt. cot: chain-of-thought prompt.")
    arg_parser.add_argument("--model", default=None,
                             help="Run only this model (must appear in config.yaml models list). "
                                  "Useful when other models' results are already collected.")
    persona_group = arg_parser.add_mutually_exclusive_group()
    persona_group.add_argument("--persona", action="store_true",
                                help="Force persona-on (overrides config persona.enabled).")
    persona_group.add_argument("--no-persona", action="store_true",
                                help="Force persona-off (overrides config persona.enabled).")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    waiting_game_config = config["waiting_game"]
    ollama_config = config["ollama"]
    persona_config = dict(config.get("persona") or {})
    persona_enabled = resolve_persona_enabled(args, config)
    persona_config["enabled"] = persona_enabled

    system_prompt_key, num_predict_key = PROMPT_CONFIG_KEYS_BY_MODE[args.mode]
    base_system_prompt = waiting_game_config[system_prompt_key]
    num_predict = waiting_game_config[num_predict_key]
    temperature = waiting_game_config["temperature"]
    keep_alive = ollama_config["keep_alive"]

    persona_catalog, _, prompt_template = make_persona_catalog(persona_config)
    if persona_enabled:
        ids = ", ".join(p["persona_id"] for p in persona_catalog)
        print(f"Persona ON: full grid under each of {len(persona_catalog)} personas ({ids}).")
    else:
        print("Persona OFF (control).")

    ollama_client = OllamaClient(
        base_url=ollama_config["base_url"],
        request_timeout_s=ollama_config["request_timeout_s"],
        max_retries=ollama_config["max_retries"],
        retry_backoff_s=ollama_config["retry_backoff_s"],
    )

    # Same trial list (same seed) reused across models AND across reasoning
    # modes so everything sees identical prompts/order assignments -> cleaner
    # comparison. Only the system prompt / num_predict change with --mode.
    all_trials = build_all_trials(waiting_game_config)
    n_probe = sum(1 for t in all_trials if t.get("is_competence_probe"))
    print(f"Built {len(all_trials)} trials per model "
          f"({len(all_trials) - n_probe} fit-grid + {n_probe} competence-probe)"
          f"{f' × {len(persona_catalog)} personas' if persona_enabled else ''}. "
          f"Mode = {args.mode}.")

    raw_dir = resolve_dir_path(config["paths"]["data_raw_dir"])
    suffix = result_suffix(args.mode, persona_enabled)

    model_names = config["models"]
    if args.model is not None:
        if args.model not in model_names:
            raise SystemExit(
                f"--model {args.model!r} is not in config models list: {model_names}"
            )
        model_names = [args.model]
        print(f"Restricting run to single model: {args.model}")

    for model_index, model_name in enumerate(model_names):
        raw_jsonl_path = os.path.join(
            raw_dir, f"{safe_filename_for_model(model_name)}{suffix}.jsonl"
        )

        run_experiment_for_model(
            model_name=model_name,
            all_trials=all_trials,
            base_system_prompt=base_system_prompt,
            temperature=temperature,
            num_predict=num_predict,
            keep_alive=keep_alive,
            reasoning_mode=args.mode,
            ollama_client=ollama_client,
            raw_jsonl_path=raw_jsonl_path,
            persona_catalog=persona_catalog,
            persona_enabled=persona_enabled,
            prompt_template=prompt_template,
        )

        is_last_model = model_index == len(model_names) - 1
        if not is_last_model:
            ollama_client.unload_model(model_name)  # free RAM before loading next model


if __name__ == "__main__":
    main()
