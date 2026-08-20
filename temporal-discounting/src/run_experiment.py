"""Main experiment driver: loops models x trials, calling Ollama and logging
every raw completion incrementally so the run is resumable after interruption.

Supports two reasoning modes (--mode):
  direct: original minimal-instruction, single-letter-response prompt.
  cot:    chain-of-thought prompt that requires step-by-step reasoning before
          a "FINAL ANSWER: A/B" line. Writes to separate raw files so it never
          overwrites the direct-mode data.

Usage: python src/run_experiment.py [--config path/to/config.yaml] [--mode direct|cot]
"""

import argparse
import json
import os
import time

from tqdm import tqdm

from config_utils import load_config, resolve_dir_path, mode_suffix
from ollama_client import OllamaClient
from waiting_game import build_all_trials


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


def run_experiment_for_model(model_name, all_trials, system_prompt, temperature, num_predict,
                              keep_alive, reasoning_mode, ollama_client, raw_jsonl_path):
    completed_trial_ids = load_completed_trial_ids(raw_jsonl_path)
    pending_trials = [t for t in all_trials if t["trial_id"] not in completed_trial_ids]

    print(f"[{model_name} / {reasoning_mode}] {len(completed_trial_ids)} trials already done, "
          f"{len(pending_trials)} remaining.")

    with open(raw_jsonl_path, "a") as raw_file:
        for trial in tqdm(pending_trials, desc=f"{model_name} [{reasoning_mode}]"):
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
            logged_record["raw_response_text"] = raw_response_text
            logged_record["logged_at_unix"] = time.time()

            raw_file.write(json.dumps(logged_record) + "\n")
            raw_file.flush()  # survive interruption without losing this trial


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=["direct", "cot"], default="direct",
                             help="direct: minimal single-letter prompt. cot: chain-of-thought prompt.")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    waiting_game_config = config["waiting_game"]
    ollama_config = config["ollama"]

    if args.mode == "direct":
        system_prompt = waiting_game_config["system_prompt"]
        num_predict = waiting_game_config["num_predict"]
    else:
        system_prompt = waiting_game_config["cot_system_prompt"]
        num_predict = waiting_game_config["cot_num_predict"]
    temperature = waiting_game_config["temperature"]
    keep_alive = ollama_config["keep_alive"]

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
    print(f"Built {len(all_trials)} trials per model. Mode = {args.mode}.")

    raw_dir = resolve_dir_path(config["paths"]["data_raw_dir"])

    model_names = config["models"]
    for model_index, model_name in enumerate(model_names):
        raw_jsonl_path = os.path.join(
            raw_dir, f"{safe_filename_for_model(model_name)}{mode_suffix(args.mode)}.jsonl"
        )

        run_experiment_for_model(
            model_name=model_name,
            all_trials=all_trials,
            system_prompt=system_prompt,
            temperature=temperature,
            num_predict=num_predict,
            keep_alive=keep_alive,
            reasoning_mode=args.mode,
            ollama_client=ollama_client,
            raw_jsonl_path=raw_jsonl_path,
        )

        is_last_model = model_index == len(model_names) - 1
        if not is_last_model:
            ollama_client.unload_model(model_name)  # free RAM before loading next model


if __name__ == "__main__":
    main()