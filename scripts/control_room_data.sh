#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

OUTPUT="$REPOSITORY_ROOT/apps/control-room/src/generated/public-profile.json"

cd "$REPOSITORY_ROOT"

exec uv run profile-system frontend \
    --source "$REPOSITORY_ROOT/profile/profile.json" \
    --output "$OUTPUT"
