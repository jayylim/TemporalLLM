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
Each mode writes to its own raw file (via config_utils.mode_suffix) so it
never overwrites another mode's data.

Usage: python src/run_experiment.py [--config path/to/config.yaml] [--mode direct|cot|one_shot|two_shot]
"""

import argparse
import json
import os
import time

from tqdm import tqdm

from config_utils import load_config, resolve_dir_path, mode_suffix
from ollama_client import OllamaClient
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


def run_experiment_for_model(model_name, all_trials, system_prompt, temperature, num_predict,
                              keep_alive, reasoning_mode, ollama_client, raw_jsonl_path,
                              few_shot_messages=None):
    few_shot_messages = few_shot_messages or []
    completed_trial_ids = load_completed_trial_ids(raw_jsonl_path)
    pending_trials = [t for t in all_trials if t["trial_id"] not in completed_trial_ids]

    print(f"[{model_name} / {reasoning_mode}] {len(completed_trial_ids)} trials already done, "
          f"{len(pending_trials)} remaining.")

    with open(raw_jsonl_path, "a") as raw_file:
        for trial in tqdm(pending_trials, desc=f"{model_name} [{reasoning_mode}]"):
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
            logged_record["raw_response_text"] = raw_response_text
            logged_record["logged_at_unix"] = time.time()

            raw_file.write(json.dumps(logged_record) + "\n")
            raw_file.flush()  # survive interruption without losing this trial


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=REASONING_MODES, default="direct",
                             help="direct: minimal single-letter prompt. cot: chain-of-thought prompt. "
                                  "one_shot/two_shot: direct-style prompt preceded by worked examples.")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    waiting_game_config = config["waiting_game"]
    ollama_config = config["ollama"]

    system_prompt_key, num_predict_key = PROMPT_CONFIG_KEYS_BY_MODE[args.mode]
    system_prompt = waiting_game_config[system_prompt_key]
    num_predict = waiting_game_config[num_predict_key]
    temperature = waiting_game_config["temperature"]
    keep_alive = ollama_config["keep_alive"]

    few_shot_messages = build_few_shot_messages_for_mode(waiting_game_config, args.mode)
    if few_shot_messages:
        print(f"Mode = {args.mode}: prepending {len(few_shot_messages) // 2} worked example(s) to every trial.")

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
            few_shot_messages=few_shot_messages,
        )

        is_last_model = model_index == len(model_names) - 1
        if not is_last_model:
            ollama_client.unload_model(model_name)  # free RAM before loading next model


if __name__ == "__main__":
    main()