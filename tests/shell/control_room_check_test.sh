#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd
)"
TEMPORARY_ROOT="$(mktemp -d)"
FIXTURE="$TEMPORARY_ROOT/repository"
FAKE_BIN="$TEMPORARY_ROOT/bin"
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

mkdir -p "$FIXTURE" "$FAKE_BIN"

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

printf 'stale design token fixture\n' \
    >"$FIXTURE/apps/control-room/src/generated/design-tokens.css"

cat >"$FAKE_BIN/uv" <<'UV_STUB'
#!/usr/bin/env bash
printf 'unexpected uv invocation\n' >&2
exit 97
UV_STUB

cat >"$FAKE_BIN/python3" <<'PYTHON_STUB'
#!/usr/bin/env bash
printf 'unexpected python3 invocation\n' >&2
exit 98
PYTHON_STUB

chmod +x "$FAKE_BIN/uv" "$FAKE_BIN/python3"

set +e
PATH="$FAKE_BIN:$PATH" \
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

if grep -F "unexpected uv invocation" "$STDERR_FILE" >/dev/null; then
    fail "canonical Control Room gate still invoked uv"
fi

if grep -F "unexpected python3 invocation" "$STDERR_FILE" >/dev/null; then
    fail "canonical Control Room gate still invoked python3"
fi
