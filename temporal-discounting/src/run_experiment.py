"""Main experiment driver: loops models x trials, calling Ollama and logging
every raw completion incrementally so the run is resumable after interruption.

Supports four reasoning modes (--mode), per Ross, Kim & Lo (2024) sec. 4's
prompting-intervention case study (direct / zero-shot CoT / one-shot /
two-shot), extrapolated here from their gambling-game experiment to the
waiting game:
  direct:    original minimal-instruction, single-letter-response prompt.
  cot:       chain-of-thought prompt that requires step-by-step reasoning
             before a "FINAL ANSWER: A/B" line.
  one_shot:  direct-style prompt preceded by 1 worked example (see
             waiting_game.build_few_shot_messages_for_mode).
  two_shot:  direct-style prompt preceded by 2 worked examples.
Each mode writes to its own raw file (via config_utils.result_suffix) so it
never overwrites another mode's data. Persona-on runs add a further
`__persona` suffix.

Usage: python src/run_experiment.py [--config path/to/config.yaml]
       [--mode direct|cot|one_shot|two_shot] [--persona|--no-persona]
"""

import argparse
import json
import os
import time

from tqdm import tqdm

from config_utils import load_config, resolve_dir_path, result_suffix, persona_enabled_from_config
from ollama_client import OllamaClient
from persona import (
    compose_system_prompt_with_persona,
    empty_persona_fields,
    make_persona_sampler,
)
from waiting_game import build_all_trials, build_few_shot_messages_for_mode

REASONING_MODES = ["direct", "cot", "one_shot", "two_shot"]

# (system_prompt config key, num_predict config key) per mode. one_shot/
# two_shot reuse the direct-mode answer format so the few-shot variable is
# isolated from the CoT-reasoning variable.
PROMPT_CONFIG_KEYS_BY_MODE = {
    "direct": ("system_prompt", "num_predict"),
    "cot": ("cot_system_prompt", "cot_num_predict"),
    "one_shot": ("system_prompt", "num_predict"),
    "two_shot": ("system_prompt", "num_predict"),
}


def safe_filename_for_model(model_name):
    return model_name.replace(":", "__").replace("/", "__")


def load_completed_trial_ids(raw_jsonl_path):
    """Reads an existing raw jsonl file and returns the set of trial_ids
    already logged, so run_experiment.py can skip them on restart.
    """
    completed_trial_ids = set()
    if not os.path.exists(raw_jsonl_path):
        return completed_trial_ids

    with open(raw_jsonl_path, "r") as raw_file:
        for line in raw_file:
            line = line.strip()
            if not line:
                continue
            try:
                logged_record = json.loads(line)
                completed_trial_ids.add(logged_record["trial_id"])
            except (json.JSONDecodeError, KeyError):
                continue  # skip corrupted lines rather than crash a multi-hour run
    return completed_trial_ids


def run_experiment_for_model(model_name, all_trials, base_system_prompt, temperature, num_predict,
                              keep_alive, reasoning_mode, ollama_client, raw_jsonl_path,
                              few_shot_messages=None, sample_persona_fn=None,
                              persona_enabled=False, prompt_template=None):
    few_shot_messages = few_shot_messages or []
    completed_trial_ids = load_completed_trial_ids(raw_jsonl_path)
    pending_trials = [t for t in all_trials if t["trial_id"] not in completed_trial_ids]

    print(f"[{model_name} / {reasoning_mode} / persona={persona_enabled}] "
          f"{len(completed_trial_ids)} trials already done, {len(pending_trials)} remaining.")

    with open(raw_jsonl_path, "a") as raw_file:
        for trial in tqdm(pending_trials, desc=f"{model_name} [{reasoning_mode}]"):
            if persona_enabled:
                persona_fields = sample_persona_fn()
                system_prompt = compose_system_prompt_with_persona(
                    base_system_prompt, persona_fields, prompt_template
                )
                persona_log = {
                    "persona_enabled": True,
                    "persona_surname": persona_fields["persona_surname"],
                    "persona_age": persona_fields["persona_age"],
                    "persona_gender": persona_fields["persona_gender"],
                }
            else:
                system_prompt = base_system_prompt
                persona_log = empty_persona_fields()

            if few_shot_messages:
                raw_response_text = ollama_client.chat(
                    model_name=model_name,
                    system_prompt=system_prompt,
                    messages=few_shot_messages + [{"role": "user", "content": trial["user_prompt"]}],
                    temperature=temperature,
                    num_predict=num_predict,
                    keep_alive=keep_alive,
                )
            else:
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
                             help="direct: minimal single-letter prompt. cot: chain-of-thought prompt. "
                                  "one_shot/two_shot: direct-style prompt preceded by worked examples.")
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
    prompt_template = persona_config.get("prompt_template")

    few_shot_messages = build_few_shot_messages_for_mode(waiting_game_config, args.mode)
    if few_shot_messages:
        print(f"Mode = {args.mode}: prepending {len(few_shot_messages) // 2} worked example(s) to every trial.")

    sample_persona_fn, _ = make_persona_sampler(persona_config)
    if persona_enabled:
        print("Persona ON: each trial draws a random surname/age/gender from config.")
    else:
        print("Persona OFF.")

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
          f"({len(all_trials) - n_probe} fit-grid + {n_probe} competence-probe). "
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
            few_shot_messages=few_shot_messages,
            sample_persona_fn=sample_persona_fn,
            persona_enabled=persona_enabled,
            prompt_template=prompt_template,
        )

        is_last_model = model_index == len(model_names) - 1
        if not is_last_model:
            ollama_client.unload_model(model_name)  # free RAM before loading next model


if __name__ == "__main__":
    main()
