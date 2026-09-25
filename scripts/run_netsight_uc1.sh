#!/usr/bin/env bash
# Uses the cloned NetSight backend without replacing its existing prompt or .env.
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
NETSIGHT_DIR="${1:-$SCRIPT_DIR/../../netsight}"
cd "$NETSIGHT_DIR"
test -f .env || { echo 'NetSight .env is missing.' >&2; exit 1; }
test -f prompts/uc1_system_prompt.md || { echo 'Run controller_uc1.py --prepare first.' >&2; exit 1; }
test -f attachments/operator_request.json || { echo 'Prepare a current operator request first.' >&2; exit 1; }
docker compose run --rm \
  -e PROMPT_FILE=prompts/uc1_system_prompt.md -e OUTPUT_FILE=output/action.json \
  check-prerequisites
docker compose run --rm \
  -e PROMPT_FILE=prompts/uc1_system_prompt.md -e OUTPUT_FILE=output/action.json \
  netsight-agent
