#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

OUTPUT_PATH="${1:-$REPOSITORY_ROOT/assets/generated/kernel/svg-renderer-kernel.svg}"

cd "$REPOSITORY_ROOT"

exec uv run profile-system kernel \
    --tokens "$REPOSITORY_ROOT/profile/design-tokens.json" \
    --output "$OUTPUT_PATH"
