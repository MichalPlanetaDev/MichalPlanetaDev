#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"
OUTPUT="${1:-$REPOSITORY_ROOT/assets/generated/hero/identity-observatory.svg}"

cd "$REPOSITORY_ROOT"

uv run python -B -m profile_system hero \
    --profile profile/profile.json \
    --hero profile/hero.json \
    --scene profile/scenes/planetary-observatory.json \
    --tokens profile/design-tokens.json \
    --output "$OUTPUT"
