#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"
OUTPUT="${1:-$REPOSITORY_ROOT/assets/generated/sections/engineering-sections.svg}"

cd "$REPOSITORY_ROOT"

uv run python -B -m profile_system sections \
    --source profile/sections.json \
    --profile profile/profile.json \
    --tokens profile/design-tokens.json \
    --output "$OUTPUT"
