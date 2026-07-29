#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

OUTPUT_DIRECTORY="${1:-$REPOSITORY_ROOT/.profile-build/generated}"

cd "$REPOSITORY_ROOT"

exec uv run profile-system build \
    --source "$REPOSITORY_ROOT/profile/profile.json" \
    --output-dir "$OUTPUT_DIRECTORY"
