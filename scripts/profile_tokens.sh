#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

OUTPUT_PATH="${1:-$REPOSITORY_ROOT/assets/generated/contracts/visual-grammar.json}"

cd "$REPOSITORY_ROOT"

exec uv run profile-system tokens \
    --source "$REPOSITORY_ROOT/profile/design-tokens.json" \
    --output "$OUTPUT_PATH"
