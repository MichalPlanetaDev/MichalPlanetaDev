#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"
OUTPUT="${1:-$REPOSITORY_ROOT/README.md}"

cd "$REPOSITORY_ROOT"

uv run python -B -m profile_system readme \
    --composition profile/readme.json \
    --profile profile/profile.json \
    --output "$OUTPUT"
