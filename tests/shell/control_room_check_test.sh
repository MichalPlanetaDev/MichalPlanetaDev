#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd
)"
TEMPORARY_ROOT="$(mktemp -d)"
FIXTURE="$TEMPORARY_ROOT/repository"
FAKE_BIN="$TEMPORARY_ROOT/bin"
MARKER_ROOT="$TEMPORARY_ROOT/markers"
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

mkdir -p "$FIXTURE" "$FAKE_BIN" "$MARKER_ROOT"

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

mkdir -p "$FIXTURE/apps/control-room/src/generated"
printf 'stale design token fixture\n' \
    >"$FIXTURE/apps/control-room/src/generated/design-tokens.css"

cat >"$FIXTURE/scripts/profile_check.sh" <<'PROFILE_CHECK_STUB'
#!/usr/bin/env bash
set -Eeuo pipefail
exit 0
PROFILE_CHECK_STUB
chmod +x "$FIXTURE/scripts/profile_check.sh"

cat >"$FIXTURE/tests/shell/control_room_data_test.sh" <<'DATA_MARKER'
#!/usr/bin/env bash
set -Eeuo pipefail
: "${CONTROL_ROOM_SHELL_TEST_MARKER_ROOT:?}"
touch "$CONTROL_ROOM_SHELL_TEST_MARKER_ROOT/data-test-ran"
DATA_MARKER

cat >"$FIXTURE/tests/shell/control_room_check_test.sh" <<'CHECK_MARKER'
#!/usr/bin/env bash
set -Eeuo pipefail
: "${CONTROL_ROOM_SHELL_TEST_MARKER_ROOT:?}"
touch "$CONTROL_ROOM_SHELL_TEST_MARKER_ROOT/check-test-ran"
CHECK_MARKER

chmod +x \
    "$FIXTURE/tests/shell/control_room_data_test.sh" \
    "$FIXTURE/tests/shell/control_room_check_test.sh"

cat >"$FAKE_BIN/pnpm" <<'PNPM_STUB'
#!/usr/bin/env bash
set -Eeuo pipefail
exit 0
PNPM_STUB
chmod +x "$FAKE_BIN/pnpm"

set +e
CONTROL_ROOM_SHELL_TEST_MARKER_ROOT="$MARKER_ROOT" \
UV_LINK_MODE=copy \
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

test -f "$MARKER_ROOT/data-test-ran" ||
    fail "control_room_check.sh did not run the data-generation shell test"

test -f "$MARKER_ROOT/check-test-ran" ||
    fail "control_room_check.sh did not run the stale-output shell test"
