#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

PROFILE_SOURCE="$REPOSITORY_ROOT/profile/profile.json"
TOKEN_SOURCE="$REPOSITORY_ROOT/profile/design-tokens.json"

PROFILE_OUTPUT="$REPOSITORY_ROOT/apps/control-room/src/generated/public-profile.json"
TOKEN_CSS_OUTPUT="$REPOSITORY_ROOT/apps/control-room/src/generated/design-tokens.css"
TOKEN_TYPESCRIPT_OUTPUT="$REPOSITORY_ROOT/apps/control-room/src/generated/design-tokens.ts"

cd "$REPOSITORY_ROOT"

uv run profile-system frontend \
    --source "$PROFILE_SOURCE" \
    --output "$PROFILE_OUTPUT"

uv run profile-system frontend-tokens \
    --source "$TOKEN_SOURCE" \
    --css-output "$TOKEN_CSS_OUTPUT" \
    --typescript-output "$TOKEN_TYPESCRIPT_OUTPUT"
