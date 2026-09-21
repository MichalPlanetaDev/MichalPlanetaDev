#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd
)"
TEMPORARY_ROOT="$(mktemp -d)"
FIXTURE="$TEMPORARY_ROOT/repository"
STDOUT_FILE="$TEMPORARY_ROOT/stdout"
STDERR_FILE="$TEMPORARY_ROOT/stderr"

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
    --exclude='./.profile-build' \
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

printf 'stale design token fixture\n' \
    >"$FIXTURE/apps/control-room/src/generated/design-tokens.css"

set +e
"$FIXTURE/scripts/control_room_check.sh" \
    >"$STDOUT_FILE" \
    2>"$STDERR_FILE"
status=$?
set -e

if [ "$status" -eq 0 ]; then
    fail "control_room_check.sh accepted stale design token artifact"
fi

grep -F \
    "apps/control-room/src/generated/design-tokens.css is stale" \
    "$STDERR_FILE" \
    >/dev/null ||
    fail "stale design token diagnostic did not identify the CSS artifact"
