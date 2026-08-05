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

"$FIXTURE/scripts/control_room_data.sh"

test -s \
    "$FIXTURE/apps/control-room/src/generated/public-profile.json" ||
    fail "missing generated public-profile.json"

test -s \
    "$FIXTURE/apps/control-room/src/generated/design-tokens.css" ||
    fail "missing generated design-tokens.css"

test -s \
    "$FIXTURE/apps/control-room/src/generated/design-tokens.ts" ||
    fail "missing generated design-tokens.ts"
