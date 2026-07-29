#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

CHECK_ROOT="$REPOSITORY_ROOT/.profile-build/check"
FIRST_OUTPUT="$CHECK_ROOT/first"
SECOND_OUTPUT="$CHECK_ROOT/second"

cd "$REPOSITORY_ROOT"
rm -rf "$CHECK_ROOT"

uv sync --locked --all-groups
pnpm install --frozen-lockfile --ignore-scripts

uv run ruff format --check \
    src/profile_system \
    tests/python

uv run ruff check \
    src/profile_system \
    tests/python

uv run mypy
uv run pytest

shellcheck \
    scripts/profile_build.sh \
    scripts/profile_check.sh

scripts/profile_build.sh "$FIRST_OUTPUT"
scripts/profile_build.sh "$SECOND_OUTPUT"

FIRST_MANIFEST="$FIRST_OUTPUT/profile-manifest.json"
SECOND_MANIFEST="$SECOND_OUTPUT/profile-manifest.json"

test -s "$FIRST_MANIFEST"
test -s "$SECOND_MANIFEST"

cmp --silent \
    "$FIRST_MANIFEST" \
    "$SECOND_MANIFEST"

python3 -B -m json.tool \
    "$FIRST_MANIFEST" \
    >/dev/null

printf '[PASS] Python formatting, lint and static analysis\n'
printf '[PASS] Behavioral tests and shell validation\n'
printf '[PASS] Deterministic publication manifest\n'
