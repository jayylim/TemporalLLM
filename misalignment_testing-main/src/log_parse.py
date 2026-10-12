"""Shared run.log parsing helpers (Docker compose prefixes + bash events)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

COMPOSE_PREFIX_RE = re.compile(
    r"^(?:agent_controller|submission_server)\s+\|\s?",
    re.MULTILINE,
)

AGENT_END_MARKERS = (
    "\nStarting OpenAI evaluator",
    "\nStarting ollama evaluator",
    "\nStarting openai evaluator",
    "\nSkipping OpenAI evaluator",
    "\nSkipping evaluator",
    "\nSkipping OpenAI post-run assessment",
    "\nSkipping post-run assessment",
    "\nFINAL RESULTS",
)

BASH_CMD_RE = re.compile(r"^Running bash command:\s*(.*)$", re.MULTILINE)
# Split point: each agent bash event starts with this marker at line start.
BASH_CMD_SPLIT_RE = re.compile(r"^Running bash command:[ \t]*", re.MULTILINE)
RETURN_CODE_RE = re.compile(r"^Return code:\s*(-?\d+)\s*$", re.MULTILINE)
# Within one event chunk, stdout runs from "STDOUT:\n" up to the next event
# boundary or step/evaluator marker. Bounded (no nested quantifiers) so it
# cannot catastrophically backtrack on large logs.
STDOUT_CAPTURE_RE = re.compile(
    r"STDOUT:\n(.*?)"
    r"(?=\nExecuting tool:|\nExecuting command:|\nSTEP |"
    r"\nStarting OpenAI|\nStarting ollama|\nStarting openai|"
    r"\nSkipping OpenAI|\nSkipping evaluator|\nSkipping post-run|"
    r"\nFINAL RESULTS|\Z)",
    re.DOTALL,
)

WRITE_HINT_RE = re.compile(
    r"(>|>>|\btee\b|\bsed\s+-i|\bperl\s+-pi|"
    r"\bpython(?:3)?\b.*\b(?:open|write|dump|Path)\b|"
    r"\becho\b.*>|"
    r"\bprintf\b.*>|"
    r"\bcat\b.*>|"
    r"\bjq\b.*>)",
    re.IGNORECASE | re.DOTALL,
)

ANALYSIS_SKIP_DIRS = {
    "analysis_reward_hacking",
    "analysis_k_hacking",
    "conditions",
    "summary",
}


def strip_compose_prefixes(log_text: str) -> str:
    """Remove docker-compose `service  | ` line prefixes from attached logs."""
    return COMPOSE_PREFIX_RE.sub("", log_text)


def agent_phase_text(log_text: str) -> str:
    cleaned = strip_compose_prefixes(log_text)
    cut = len(cleaned)
    for marker in AGENT_END_MARKERS:
        idx = cleaned.find(marker)
        if idx != -1:
            cut = min(cut, idx)
    return cleaned[:cut]


def parse_bash_events(log_text: str) -> list[dict[str, Any]]:
    """Return ordered agent bash events with command / stdout / returncode.

    Linear split-based parser (no nested regex quantifiers) so it stays fast
    and cannot catastrophically backtrack on large transcripts.
    """
    phase = agent_phase_text(log_text)
    events: list[dict[str, Any]] = []

    # chunks[0] is the preamble before the first command; skip it.
    chunks = BASH_CMD_SPLIT_RE.split(phase)
    for chunk in chunks[1:]:
        newline = chunk.find("\n")
        if newline == -1:
            cmd = chunk.strip()
            rest = ""
        else:
            cmd = chunk[:newline].strip()
            rest = chunk[newline + 1:]
        if not cmd:
            continue

        rc_match = RETURN_CODE_RE.search(rest)
        returncode = int(rc_match.group(1)) if rc_match else None

        stdout = ""
        out_match = STDOUT_CAPTURE_RE.search(rest)
        if out_match:
            stdout = out_match.group(1)
            stderr_idx = stdout.find("\nSTDERR:")
            if stderr_idx != -1:
                stdout = stdout[:stderr_idx]

        events.append({
            "command": cmd,
            "stdout": stdout.strip(),
            "returncode": returncode,
        })

    return events


def looks_like_write(command: str) -> bool:
    return bool(WRITE_HINT_RE.search(command or ""))


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def model_family_from_name(model_name: str) -> str:
    name = str(model_name).lower()
    if name.startswith("qwen2.5"):
        return "qwen2.5"
    if name.startswith("qwen3.5"):
        return "qwen3.5"
    if name.startswith("qwen3"):
        return "qwen3"
    if name.startswith("llama3.1") or name.startswith("llama3"):
        return "llama3.1"
    if name.startswith("mistral"):
        return "mistral"
    return name.split(":")[0]


def normalize_persona_id(persona_id: Any) -> str:
    if persona_id is None:
        return "off"
    text = str(persona_id).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return "off"
    return text


def infer_model_from_path(run_dir: Path, scenario: str) -> str:
    parts = run_dir.parts
    try:
        idx = parts.index(scenario)
        model_safe = parts[idx + 1]
        return model_safe.replace("__", ":", 1)
    except (ValueError, IndexError):
        return ""


def infer_persona_from_path(run_dir: Path, scenario: str) -> str:
    parts = run_dir.parts
    try:
        idx = parts.index(scenario)
        tag = parts[idx + 2]
    except (ValueError, IndexError):
        return "off"
    if tag == "none":
        return "off"
    if tag.startswith("persona__"):
        return tag[len("persona__"):]
    return "off"


def infer_run_index(run_dir: Path) -> int:
    name = run_dir.name
    if name.startswith("run") and name[3:].isdigit():
        return int(name[3:])
    for part in run_dir.parts:
        if part.startswith("run") and part[3:].isdigit():
            return int(part[3:])
    return 1


def discover_scenario_runs(outputs_root: Path, scenarios: list[str] | None = None) -> list[Path]:
    """Return run directories that contain result.json under outputs/<scenario>/..."""
    outputs_root = Path(outputs_root)
    if not outputs_root.is_dir():
        return []

    if scenarios is None:
        scenarios = sorted(
            p.name
            for p in outputs_root.iterdir()
            if p.is_dir() and p.name not in ANALYSIS_SKIP_DIRS and not p.name.startswith(".")
        )

    runs: list[Path] = []
    for scenario in scenarios:
        scenario_root = outputs_root / scenario
        if not scenario_root.is_dir():
            continue
        for result_path in sorted(scenario_root.rglob("result.json")):
            runs.append(result_path.parent)
    return runs


def common_run_meta(run_dir: Path, scenario: str | None = None) -> dict[str, Any]:
    run_dir = Path(run_dir)
    result_path = run_dir / "result.json"
    condition_path = run_dir / "condition.json"
    result = load_json(result_path) if result_path.exists() else {}
    condition = load_json(condition_path) if condition_path.exists() else {}

    scenario = (
        scenario
        or result.get("scenario")
        or condition.get("scenario")
        or _infer_scenario_from_path(run_dir)
    )
    model_name = (
        result.get("model_name")
        or condition.get("model_name")
        or infer_model_from_path(run_dir, scenario)
    )
    persona_enabled = result.get("persona_enabled")
    if persona_enabled is None:
        persona_enabled = condition.get("persona_enabled")
    persona_id = result.get("persona_id")
    if persona_id is None:
        persona_id = condition.get("persona_id")
    if persona_id is None:
        persona_id = infer_persona_from_path(run_dir, scenario)

    persona_id = normalize_persona_id(persona_id)
    persona_label = result.get("persona_label") or condition.get("persona_label")
    persona_group = (
        result.get("persona_discounting_group")
        or condition.get("persona_discounting_group")
    )
    if persona_id == "off":
        persona_group = "off"
        persona_label = persona_label or "off"
    elif not persona_group:
        persona_group = ""

    return {
        "scenario": scenario,
        "model_name": model_name,
        "model_family": model_family_from_name(model_name or ""),
        "persona_enabled": bool(persona_enabled) if persona_enabled is not None else (
            persona_id != "off"
        ),
        "persona_id": persona_id,
        "persona_label": persona_label or persona_id,
        "persona_discounting_group": persona_group or ("off" if persona_id == "off" else ""),
        "run_index": infer_run_index(run_dir),
        "output_dir": str(run_dir),
        "status": result.get("status"),
        "evaluation": result.get("evaluation"),
    }


def _infer_scenario_from_path(run_dir: Path) -> str:
    # .../outputs/<scenario>/<model_safe>/...
    parts = list(run_dir.parts)
    if "outputs" in parts:
        i = parts.index("outputs")
        if i + 1 < len(parts):
            return parts[i + 1]
    return run_dir.parts[-3] if len(run_dir.parts) >= 3 else ""


def agent_started_from_log(log_text: str) -> bool:
    cleaned = strip_compose_prefixes(log_text)
    return (
        "Starting local Ollama agent" in cleaned
        or "Running bash command:" in cleaned
        or "STEP " in cleaned
    )


def run_quality_flags(log_text: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    cleaned = strip_compose_prefixes(log_text)
    n_bash = len(events)
    ollama_crash = (
        "APIConnectionError" in cleaned
        or "Connection refused" in cleaned
        or "Failed to initialize Ollama" in cleaned
    )
    reached_max_steps = (
        "Maximum steps reached" in cleaned
        or "Your maximum steps have been reached" in cleaned
        or "STEP 20/20" in cleaned
    )
    early_terminate = "Terminating:" in cleaned
    no_tools_burn = cleaned.count("No tools were called")
    return {
        "n_bash_commands": n_bash,
        "thin_run": n_bash <= 1,
        "ollama_crash": ollama_crash,
        "reached_max_steps": reached_max_steps,
        "early_terminate": early_terminate,
        "no_tools_burn_count": no_tools_burn,
        "completed_agent_loop": "FINAL RESULTS" in cleaned,
    }
