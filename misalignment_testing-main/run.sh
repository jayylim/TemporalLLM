#!/bin/bash

# Define a timeout function that tries multiple approaches
multiplatform_timeout() {
    # Check if 'timeout' command is available (standard on Linux)
    if command -v timeout >/dev/null 2>&1; then
        command timeout -k 60 "$@"
    # Check if 'gtimeout' is available (macOS with coreutils)
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout -k 60 "$@"
    else
        echo "WARNING: Neither 'timeout' nor 'gtimeout' command found. Falling back to Perl implementation." >&2
        echo "         Timeout behavior may not exactly match that of the submission server." >&2
        
        # Use perl with proper signal handling
        perl -e 'alarm shift; exec @ARGV' "$@"
    fi
}

# Initialize default values
SUBMISSION_FOLDER_PATH="scenarios/number_guessing"
RUN_ID=""
NO_TIMESTAMP=false
REMOVE_IMAGES=false
REPEAT_COUNT=1
CONDITION_FILE=""
OUTPUT_DIR_OVERRIDE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--folder)
            SUBMISSION_FOLDER_PATH="$2"
            shift 2
            ;;
        -i|--id)
            RUN_ID="$2"
            shift 2
            ;;
        -n|--no-timestamp)
            NO_TIMESTAMP=true
            shift
            ;;
        -r|--remove-images)
            REMOVE_IMAGES=true
            shift
            ;;
        --repeat)
            REPEAT_COUNT="$2"
            shift 2
            ;;
        -c|--condition)
            CONDITION_FILE="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR_OVERRIDE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -f, --folder PATH       Path to submission folder (default: scenarios/number_guessing)"
            echo "  -i, --id NAME           Add run id to output folder name"
            echo "  -n, --no-timestamp      Do not add timestamp to output folder name"
            echo "  -r, --remove-images     Remove Docker images after execution (default: false)"
            echo "      --repeat N          Run the full workflow N times sequentially (default: 1)"
            echo "  -c, --condition PATH    CONDITION.json (model + persona) mounted into the agent"
            echo "  -o, --output-dir PATH   Explicit output directory (skips auto naming)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Batch sweeps (models × persona matching temporal-discounting):"
            echo "  python src/run_conditions.py --scenario number_guessing --dry-run"
            echo ""
            echo "Examples:"
            echo "  $0                                          # Default scenario"
            echo "  $0 --folder scenarios/sandbagging           # Specific scenario"
            echo "  $0 --condition outputs/conditions/foo.json  # Pin model/persona"
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            echo "Use $0 --help for usage information"
            exit 1
            ;;
    esac
done

# Validate repeat count
if ! [[ "$REPEAT_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: --repeat must be a positive integer."
    exit 1
fi

# Check if submission folder exists
if [ ! -d "$SUBMISSION_FOLDER_PATH" ]; then
    echo "Error: Submission folder '$SUBMISSION_FOLDER_PATH' does not exist."
    exit 1
fi

# Extract folder name from path (basename)
SUBMISSION_FOLDER_NAME=$(basename "$SUBMISSION_FOLDER_PATH")

# Resolve / create a default empty condition file when none provided
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CONDITION="$SCRIPT_DIR/.condition.json"
if [ -z "$CONDITION_FILE" ]; then
    if [ ! -f "$DEFAULT_CONDITION" ]; then
        cat > "$DEFAULT_CONDITION" << 'EOF'
{
  "model_name": null,
  "persona_enabled": false,
  "persona_id": null,
  "persona_label": null,
  "persona_discounting_group": null,
  "persona_text": null,
  "skip_openai_evaluation": false
}
EOF
    fi
    CONDITION_FILE="$DEFAULT_CONDITION"
fi

if [ ! -f "$CONDITION_FILE" ]; then
    echo "Error: Condition file '$CONDITION_FILE' does not exist."
    exit 1
fi

export CONDITION_FILE
export CONDITION_FILE_ABS
CONDITION_FILE_ABS=$(realpath "$CONDITION_FILE")
export CONDITION_FILE_ABS

for ((run_index = 1; run_index <= REPEAT_COUNT; run_index++)); do
    if [ -n "$OUTPUT_DIR_OVERRIDE" ]; then
        OUTPUT_DIR="$OUTPUT_DIR_OVERRIDE"
        if [ "$REPEAT_COUNT" -gt 1 ]; then
            OUTPUT_DIR="${OUTPUT_DIR}_run${run_index}"
        fi
    else
        # Prefer flat outputs/ tree aligned with run_conditions.py
        OUTPUT_DIR="outputs/${SUBMISSION_FOLDER_NAME}"

        if [ "$NO_TIMESTAMP" != "true" ]; then
            OUTPUT_DIR="${OUTPUT_DIR}_$(date +"%Y%m%d_%H%M%S")"
        fi

        # Ensure unique directory names across repeated runs.
        if [ "$REPEAT_COUNT" -gt 1 ]; then
            OUTPUT_DIR="${OUTPUT_DIR}_run${run_index}"
        fi

        if [ -n "$RUN_ID" ]; then
            OUTPUT_DIR="${OUTPUT_DIR}_${RUN_ID}"
        fi
    fi

    if [ -d "$OUTPUT_DIR" ]; then
        rm -rf "$OUTPUT_DIR"
    fi
    mkdir -p "$OUTPUT_DIR"
    LOG_FILE="$OUTPUT_DIR/run.log"

    # Copy condition metadata into the output dir for provenance
    cp "$CONDITION_FILE_ABS" "$OUTPUT_DIR/condition.json"

    # Start logging - capture ALL output from this point forward
    {
        echo "Running submission from: $SUBMISSION_FOLDER_PATH"
        echo "Submission folder name: $SUBMISSION_FOLDER_NAME"
        echo "Condition file: $CONDITION_FILE_ABS"
        echo "Run iteration: ${run_index}/${REPEAT_COUNT}"
        echo "Output directory: $OUTPUT_DIR"
        echo "Log file: $LOG_FILE"
        echo "Remove images after execution: $REMOVE_IMAGES"
        echo "=================================="

        # Export the submission folder path for docker-compose
        # Note: We need to handle both relative and absolute paths
        # Convert to absolute path for docker-compose
        export SUBMISSION_FOLDER=$(realpath "$SUBMISSION_FOLDER_PATH")
        export CONDITION_FILE_ABS

        # Optional: surface model/persona from condition for compose env
        if command -v python3 >/dev/null 2>&1; then
            eval "$(python3 - << PY
import json, shlex
with open("$CONDITION_FILE_ABS") as f:
    c = json.load(f)
model = c.get("model_name") or ""
print(f"export OLLAMA_MODEL={shlex.quote(str(model))}")
print(f"export SKIP_OPENAI_EVALUATION={'1' if c.get('skip_openai_evaluation') else '0'}")
num_ctx = c.get("ollama_num_ctx")
if num_ctx is not None:
    print(f"export OLLAMA_NUM_CTX={shlex.quote(str(int(num_ctx)))}")
PY
)"
        fi

        # Run docker-compose with timeout (20 minutes = 1200 seconds)
        echo "Starting docker-compose with 20 minute timeout..."
        multiplatform_timeout 1200 docker compose up --build --abort-on-container-exit

        DOCKER_EXIT_CODE=$?
        
        if [ $DOCKER_EXIT_CODE -eq 124 ] || [ $DOCKER_EXIT_CODE -eq 142 ]; then
            echo "Docker-compose execution timed out after 20 minutes."
        elif [ $DOCKER_EXIT_CODE -eq 0 ]; then
            echo "Docker-compose execution completed successfully."
        else
            echo "Docker-compose execution failed with exit code: $DOCKER_EXIT_CODE"
        fi

        # Copy scenario prompts + DESCRIPTION so a later judge can score offline
        cp "$SUBMISSION_FOLDER/PROMPT.json" "$OUTPUT_DIR/PROMPT.json" 2>/dev/null || true
        cp "$SUBMISSION_FOLDER/DESCRIPTION.md" "$OUTPUT_DIR/DESCRIPTION.md" 2>/dev/null || true

        # Try to copy result.json from the agent container
        echo "Attempting to copy result.json from agent container..."
        if docker cp agent_controller:/app/result.json "$OUTPUT_DIR/result.json"; then
            echo "Successfully copied result.json from agent container"
        else
            echo "Failed to copy result.json from agent container, creating fallback result"
            
            if [ $DOCKER_EXIT_CODE -eq 124 ] || [ $DOCKER_EXIT_CODE -eq 142 ]; then
                # Timeout occurred
                cat > "$OUTPUT_DIR/result.json" << EOF
{
  "status": "TIMEOUT",
  "evaluation": 0,
  "reasoning": "Execution timed out after 20 minutes. Check the run.log file for details.",
  "error_type": "execution_timeout"
}
EOF
            else
                # Other failure
                cat > "$OUTPUT_DIR/result.json" << EOF
{
  "status": "BUILD_OR_RUN_FAILURE",
  "evaluation": 0,
  "reasoning": "Validation failed due to build or run failure. Check the run.log file in this directory for detailed error information.",
  "error_type": "container_failure"
}
EOF
            fi
        fi

        echo "Attempting to copy agent_messages.json from agent container..."
        if docker cp agent_controller:/app/agent_messages.json "$OUTPUT_DIR/agent_messages.json"; then
            echo "Successfully copied agent_messages.json (judge-ready transcript)"
        else
            echo "No agent_messages.json in container (agent may have failed before the loop)."
        fi

        # Clean up - conditionally remove images based on flag
        if [ "$REMOVE_IMAGES" = true ]; then
            echo "Cleaning up containers, volumes, and images..."
            docker compose down -v --rmi all
        else
            echo "Cleaning up containers and volumes..."
            docker compose down -v
        fi

        echo "=================================="
        echo "Submission execution completed."
        echo "Results saved to: $OUTPUT_DIR"
    } 2>&1 | tee "$LOG_FILE"
done
