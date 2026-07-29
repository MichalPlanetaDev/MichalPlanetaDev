#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

OUTPUT_PATH="${1:-$REPOSITORY_ROOT/assets/generated/probes/github-svg-capabilities.svg}"

cd "$REPOSITORY_ROOT"

exec uv run profile-system probe \
    --source \
    "$REPOSITORY_ROOT/profile/probes/github-svg-capabilities.json" \
    --output \
    "$OUTPUT_PATH"
