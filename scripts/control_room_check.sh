#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"
CHECK_ROOT="$REPOSITORY_ROOT/.profile-build/control-room-check"
FIRST_SNAPSHOT="$CHECK_ROOT/public-profile-first.json"
SECOND_SNAPSHOT="$CHECK_ROOT/public-profile-second.json"
COMMITTED_SNAPSHOT="$(
    printf '%s\n' \
        "$REPOSITORY_ROOT/apps/control-room/src/generated/public-profile.json"
)"

cd "$REPOSITORY_ROOT"

rm -rf "$CHECK_ROOT"
mkdir -p "$CHECK_ROOT"

scripts/profile_check.sh

shellcheck \
    scripts/control_room_check.sh \
    scripts/control_room_data.sh

uv run profile-system frontend \
    --source profile/profile.json \
    --output "$FIRST_SNAPSHOT"

uv run profile-system frontend \
    --source profile/profile.json \
    --output "$SECOND_SNAPSHOT"

test -s "$FIRST_SNAPSHOT"
test -s "$SECOND_SNAPSHOT"
test -s "$COMMITTED_SNAPSHOT"

cmp --silent "$FIRST_SNAPSHOT" "$SECOND_SNAPSHOT"
cmp --silent "$FIRST_SNAPSHOT" "$COMMITTED_SNAPSHOT"

python3 -B -m json.tool "$FIRST_SNAPSHOT" >/dev/null

pnpm install \
    --frozen-lockfile \
    --ignore-scripts

pnpm --filter @michal-planeta/control-room typecheck
pnpm --filter @michal-planeta/control-room test
pnpm --filter @michal-planeta/control-room build
pnpm --filter @michal-planeta/control-room test:e2e

printf '[PASS] Deterministic public frontend projection\n'
printf '[PASS] Strict TypeScript and component contracts\n'
printf '[PASS] Production build and browser acceptance\n'
