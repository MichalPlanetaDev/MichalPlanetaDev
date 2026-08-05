#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd
)"
TEMPORARY_ROOT="$(mktemp -d)"
FIXTURE="$TEMPORARY_ROOT/repository"

cleanup() {
    rm -rf "$TEMPORARY_ROOT"
}

fail() {
    printf '%s\n' "$1" >&2
    exit 1
}

trap cleanup EXIT

mkdir -p "$FIXTURE"

tar \
    --exclude='./.git' \
    --exclude='./.mypy_cache' \
    --exclude='./.profile-build' \
    --exclude='./.pytest_cache' \
    --exclude='./.ruff_cache' \
    --exclude='./.venv' \
    --exclude='./node_modules' \
    --exclude='./apps/control-room/.next' \
    --exclude='./apps/control-room/node_modules' \
    --exclude='./apps/control-room/playwright-report' \
    --exclude='./apps/control-room/test-results' \
    --exclude='./apps/control-room/tsconfig.tsbuildinfo' \
    -C "$REPOSITORY_ROOT" \
    -cf - \
    . |
    tar -C "$FIXTURE" -xf -

PROFILE_OUTPUT="$FIXTURE/apps/control-room/src/generated/public-profile.json"
TOKEN_CSS_OUTPUT="$FIXTURE/apps/control-room/src/generated/design-tokens.css"
TOKEN_TYPESCRIPT_OUTPUT="$FIXTURE/apps/control-room/src/generated/design-tokens.ts"

rm -f \
    "$PROFILE_OUTPUT" \
    "$TOKEN_CSS_OUTPUT" \
    "$TOKEN_TYPESCRIPT_OUTPUT"

for output in \
    "$PROFILE_OUTPUT" \
    "$TOKEN_CSS_OUTPUT" \
    "$TOKEN_TYPESCRIPT_OUTPUT"
do
    if [ -e "$output" ]; then
        fail "fixture output was not removed before generation: $output"
    fi
done

UV_LINK_MODE=copy "$FIXTURE/scripts/control_room_data.sh"

test -s "$PROFILE_OUTPUT" ||
    fail "missing generated public-profile.json"

test -s "$TOKEN_CSS_OUTPUT" ||
    fail "missing generated design-tokens.css"

test -s "$TOKEN_TYPESCRIPT_OUTPUT" ||
    fail "missing generated design-tokens.ts"
