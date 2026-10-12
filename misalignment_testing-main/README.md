# Misalignment Bounty Submission Template

This repository provides a template for you to create environments and prompts that demonstrate potential misalignment behaviors of AI agents. The goal is to identify scenarios where an AI agent exhibits behavior that deviates from intended alignment principles.

[Submit your examples on our portal](https://bounty.palisaderesearch.org/) and join our [Discord](https://discord.gg/ePDrXY8eBG) to get updates and ask questions!

## TemporalLLM integration (Waiting Game conditions)

This checkout is wired to the sibling **`temporal-discounting/`** experiment so misalignment runs use the **same Ollama models and persona framing** as `config_q8.yaml`.

### Reward-hacking pipeline

1. **Sweep** the configured scenarios (primary RH set: `financial_audit`, `number_guessing`, `sys-main-audit`) — edit `misalignment.scenarios` in `config.yaml` to change the set.
2. **Detect hacking binaries** from `run.log` (no judge required): `hacked` per episode, then **mean `hack_rate` over repeats** for each model × persona cell, plus process flags (thin run, conflict reached, checker score, …).
3. **Judge by default:** the Ollama/OpenAI evaluator scores each episode. Pass `--skip-openai-evaluation` (or set `skip_openai_evaluation: true`) to skip the judge; `run.log` / `agent_messages.json` are still saved for a later pass.
4. **Summarize** with `python3 src/analyze_reward_hacking.py` → `outputs/analysis_reward_hacking/SUMMARY.md` (model × persona hack-rate tables). `run_conditions.py` runs this analysis at the end of a sweep unless you pass `--no-analyze`.

| Join key | Source |
|---|---|
| `model_name` | `temporal-discounting/config_q8.yaml` → `models` |
| `persona_enabled` / `persona_id` / `persona_label` / `persona_discounting_group` / `persona_text` | same file → `persona` |
| Persona prompt template | same file → `persona.prompt_template` |

`config.yaml` points at that sibling file (`temporal_discounting_config`). Local overrides in `config.yaml` win if set.

**Condition grid:** default sweep = every model × (persona-off control + each of 8 personas). That matches Waiting Game strata in `by_condition.csv`. Waiting Game `direct`/`cot` modes are task-specific and are **not** duplicated here (the agent already multi-steps).

Output layout:

```
outputs/<scenario>/<model_safe>/<none|persona__{id}>/[runN/]
  condition.json
  result.json          # includes model_name + persona_* fields for joining
  run.log             # full docker/agent log (judge input)
  agent_messages.json  # chat transcript for a later judge
  PROMPT.json
  DESCRIPTION.md
outputs/condition_index.csv
outputs/analysis_reward_hacking/SUMMARY.md
outputs/analysis_reward_hacking/by_model_persona.csv
outputs/analysis_reward_hacking/judge_queue.csv
```

`model_safe` uses the same sanitization as Waiting Game (`:` → `__`).

```bash
pip3 install -r requirements-host.txt   # PyYAML
# Ollama must be running; pull agent models + the judge:
#   ollama pull llama3.3:70b

python3 src/run_conditions.py --dry-run

python3 src/run_conditions.py \
  --scenario number_guessing \
  --model qwen2.5:7b-instruct-q8_0 \
  --no-persona

python3 src/run_conditions.py \
  --scenario number_guessing \
  --model qwen2.5:7b-instruct-q8_0 \
  --persona --persona-id substance_use \
  --skip-openai-evaluation

python3 src/analyze_reward_hacking.py
```

The **judge** runs by default (`evaluator_backend: ollama`, `evaluator_model: llama3.3:70b`). Pull it first (`ollama pull llama3.3:70b`), or set `evaluator_backend: openai` + `OPENAI_API_KEY`. Pass `--skip-openai-evaluation` to skip judging. Agent backend remains **local Ollama** (`agent/run_loop_local_llm.py`).

## Overview

Create scenarios for an AI agent capable of executing bash commands within a Docker environment. The agent runs for up to 20 steps based on the prompts and environment you provide. The setup is designed to work with [OpenAI's o3 model](https://openai.com/index/introducing-o3-and-o4-mini/), but may work with other OpenAI models as well.

## What You're Provided

- A Docker environment with an `o3` agent that can execute arbitrary bash commands
- The agent to execute user-provided prompts
- A testing framework to validate your submissions locally
- Automated evaluation pipeline for submitted scenarios

**Note:** When running locally, you must export your own `OPENAI_API_KEY` for use with `o3` model:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Alternatively, create a `.env` file with
```
OPENAI_API_KEY="your-api-key-here"
```

## Submission Requirements

Each submission must include:

### 1. `PROMPT.json`
A JSON file containing:
- **Required:** `"user_prompt"` - A string field with the prompt for the agent
- **Optional:** `"system_prompt"` - A string field for custom system instructions (though using only user prompts is recommended)

Example:
```json
{
  "user_prompt": "Your prompt here",
  "system_prompt": "Optional system prompt"
}
```

### 2. `DESCRIPTION.md`
A markdown file that:
- Explains the expected misaligned behavior
- Contrasts the misaligned behavior with what aligned behavior would look like
- Provides context for evaluators to understand the scenario

### 3. `Dockerfile` (and associated files)
- A Dockerfile that builds the environment where the agent will operate
- Any additional files needed for the Docker build should be included in the submission folder

### 4. `command_server.py`
- This file is how the agent container will interact with your container, and will usually not need to be modified
- You may edit this file if you like, but spoofing command outputs to cause the agent to unintentionally misbehave will not count as misalignment

## Testing Your Submission

1. Place your submission files in the `submission/` directory
2. Run the test script:
   ```bash
   ./run.sh
   ```

An example submission is already included, feel free to use it as a starting point for your experiments. Mind there is 0% misalignment in the example scenario.

If you create a submission in another folder, you can provide the relative path to `run.sh` via `--folder`:
```bash
./run.sh --folder ../some-other-folder
```

### Prerequisites

To run the testing framework, you need:
- **Docker** - [Installation guide](https://docs.docker.com/get-docker/)
- **Docker Compose plugin** - [Installation guide](https://docs.docker.com/compose/install/)

## Evaluation Process

### 1. Initial Validation
An automated evaluator checks:
- Valid `PROMPT.json` format and required fields
- Presence and validity of `DESCRIPTION.md`
- Whether the described scenario constitutes a genuine alignment failure

### 2. Agent Execution
If validation passes:
- The agent runs against your Docker environment
- The agent receives your prompts
- All actions are logged for evaluation

### 3. Automated Scoring
A second evaluator:
- Inspects the agent's output and final environment state
- Assigns a misalignment score based on observed behavior

**Note:** The entire evaluation process (steps 1-3) must complete within 20 minutes, or all containers will be automatically shut down and the submission will receive a timeout result.

### 4. Human Review
Submissions flagged as interesting by automated evaluation undergo manual review by human evaluators for final assessment.

## Output

All logs and results from your submission will be saved to:

`outputs/{submission_folder_name}_{datetime}` or `outputs/{submission_folder_name}_{id}` if you provide an `id` arg to `run.sh`

For example:
- `outputs/submission_20250717_130131/` - Using default submission folder with timestamp
- `outputs/my_submission_test1/` - Using custom submission folder "my_submission" with id "test1"

This includes:
- Agent action logs
- Build and run logs for the agent container as well as the environment container
- Evaluation scores and feedback

## Tips for Submitters

1. **Clear Descriptions:** Be explicit about what constitutes misalignment in your scenario
2. **Reproducible Environments:** Ensure your Dockerfile builds consistently
3. **Focused Prompts:** Design prompts that reliably trigger the intended behavior
4. **Test Locally:** Always test your submission before final submission

## Getting Started

1. Clone this repository
2. Export your OpenAI API key
3. Create your submission using this repo as a example
4. Test locally using `run.sh`
5. Compress your submission folder into a `.zip` file. When opened, the zip should contain your submission folder with all files inside it (e.g., `submission/` → files), not the files directly at the zip's root level
6. [Submit on our portal](https://bounty.palisaderesearch.org/)

Good luck with your submissions!
