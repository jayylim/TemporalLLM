"""Parses raw Ollama completions into A/B choices.

Robust to stray punctuation, "Option A" phrasing, refusals, and (in --mode
cot) long reasoning text preceding a "FINAL ANSWER: A/B" line. Unparseable
responses are logged as parse failures (None) rather than guessed/imputed,
per PREREGISTRATION.md.

Usage: python src/parse_responses.py [--config path/to/config.yaml] [--mode direct|cot]
"""

import argparse
import json
import os
import re

import pandas as pd

from config_utils import load_config, resolve_dir_path, mode_suffix
from run_experiment import safe_filename_for_model

# Tried in priority order. For CoT text, the reasoning body often mentions
# both option letters many times, so the tagged "FINAL ANSWER" line is
# checked first, and the fallback patterns take the LAST match in the text
# (closest to the model's actual conclusion) rather than the first.
FINAL_ANSWER_PATTERN = re.compile(r"final\s*answer\s*[:\-]?\s*\**\s*([ab])\b", re.IGNORECASE)
EXACT_LETTER_PATTERN = re.compile(r"^[\s\"'`*.]*([ab])[\s\"'`*.:)]*$", re.IGNORECASE)
LEADING_LETTER_PATTERN = re.compile(r"^[\s\"'`*.]*([ab])\b", re.IGNORECASE)
OPTION_WORD_PATTERN = re.compile(r"option\s+([ab])\b", re.IGNORECASE)
STANDALONE_LETTER_PATTERN = re.compile(r"\b([ab])\b", re.IGNORECASE)


def find_last_match(pattern, text):
    all_matches = list(pattern.finditer(text))
    return all_matches[-1] if all_matches else None


def parse_choice_letter(raw_response_text):
    """Returns 'A', 'B', or None (parse failure) from one raw completion."""
    if raw_response_text is None:
        return None

    stripped_text = raw_response_text.strip()
    if stripped_text == "":
        return None

    final_answer_match = find_last_match(FINAL_ANSWER_PATTERN, stripped_text)
    if final_answer_match:
        return final_answer_match.group(1).upper()

    exact_match = EXACT_LETTER_PATTERN.search(stripped_text)
    if exact_match:
        return exact_match.group(1).upper()

    leading_match = LEADING_LETTER_PATTERN.search(stripped_text)
    if leading_match:
        return leading_match.group(1).upper()

    option_word_match = find_last_match(OPTION_WORD_PATTERN, stripped_text)
    if option_word_match:
        return option_word_match.group(1).upper()

    standalone_match = find_last_match(STANDALONE_LETTER_PATTERN, stripped_text)
    if standalone_match:
        return standalone_match.group(1).upper()

    return None  # e.g. refusals, unrelated text -> logged as parse failure


def choice_was_sooner_option(parsed_choice_letter, sooner_is_option_a):
    if parsed_choice_letter is None:
        return None
    chose_option_a = parsed_choice_letter == "A"
    return chose_option_a == sooner_is_option_a


def has_final_answer_tag(raw_response_text):
    """Diagnostic only: did the model follow the CoT output-format instruction?"""
    return FINAL_ANSWER_PATTERN.search(raw_response_text or "") is not None


def parse_raw_jsonl_file(raw_jsonl_path):
    """Reads one model's raw jsonl file and returns a list of parsed trial dicts."""
    parsed_rows = []
    with open(raw_jsonl_path, "r") as raw_file:
        for line in raw_file:
            line = line.strip()
            if not line:
                continue
            trial_record = json.loads(line)

            raw_response_text = trial_record["raw_response_text"]
            parsed_choice_letter = parse_choice_letter(raw_response_text)
            chose_sooner_option = choice_was_sooner_option(
                parsed_choice_letter, trial_record["sooner_is_option_a"]
            )

            parsed_rows.append({
                "model_name": trial_record["model_name"],
                "reasoning_mode": trial_record.get("reasoning_mode", "direct"),
                "trial_id": trial_record["trial_id"],
                "delay_months": trial_record["delay_months"],
                "amount_dollars": trial_record["amount_dollars"],
                "sample_index": trial_record["sample_index"],
                "sooner_is_option_a": trial_record["sooner_is_option_a"],
                "raw_response_text": raw_response_text,
                "raw_response_length_chars": len(raw_response_text or ""),
                "final_answer_tag_found": has_final_answer_tag(raw_response_text),
                "parsed_choice_letter": parsed_choice_letter,
                "chose_sooner_option": chose_sooner_option,
            })
    return parsed_rows


def compute_parse_failure_rate(parsed_rows):
    n_total = len(parsed_rows)
    if n_total == 0:
        return 0.0
    n_failures = sum(1 for row in parsed_rows if row["parsed_choice_letter"] is None)
    return n_failures / n_total


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--config", default=None)
    arg_parser.add_argument("--mode", choices=["direct", "cot"], default="direct")
    args = arg_parser.parse_args()

    config = load_config(args.config)
    raw_dir = resolve_dir_path(config["paths"]["data_raw_dir"])
    processed_dir = resolve_dir_path(config["paths"]["data_processed_dir"])

    all_parsed_rows = []
    for model_name in config["models"]:
        raw_jsonl_path = os.path.join(
            raw_dir, f"{safe_filename_for_model(model_name)}{mode_suffix(args.mode)}.jsonl"
        )
        if not os.path.exists(raw_jsonl_path):
            print(f"[{model_name} / {args.mode}] no raw data file found at {raw_jsonl_path}, skipping.")
            continue

        model_parsed_rows = parse_raw_jsonl_file(raw_jsonl_path)
        parse_failure_rate = compute_parse_failure_rate(model_parsed_rows)
        message = (f"[{model_name} / {args.mode}] parsed {len(model_parsed_rows)} trials, "
                    f"parse-failure rate = {parse_failure_rate:.1%}")
        if args.mode == "cot":
            n_with_tag = sum(1 for row in model_parsed_rows if row["final_answer_tag_found"])
            message += f", FINAL ANSWER tag present = {n_with_tag / len(model_parsed_rows):.1%}"
        print(message)

        all_parsed_rows.extend(model_parsed_rows)

    choices_dataframe = pd.DataFrame(all_parsed_rows)
    processed_csv_path = os.path.join(processed_dir, f"choices{mode_suffix(args.mode)}.csv")
    choices_dataframe.to_csv(processed_csv_path, index=False)
    print(f"Wrote {len(choices_dataframe)} parsed trials to {processed_csv_path}")


if __name__ == "__main__":
    main()
