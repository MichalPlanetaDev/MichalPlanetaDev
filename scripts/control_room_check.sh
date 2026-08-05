#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"
CHECK_ROOT="$REPOSITORY_ROOT/.profile-build/control-room-check"
FIRST_ROOT="$CHECK_ROOT/first"
SECOND_ROOT="$CHECK_ROOT/second"

PROFILE_SOURCE="$REPOSITORY_ROOT/profile/profile.json"
TOKEN_SOURCE="$REPOSITORY_ROOT/profile/design-tokens.json"

COMMITTED_PROFILE="$REPOSITORY_ROOT/apps/control-room/src/generated/public-profile.json"
COMMITTED_TOKEN_CSS="$REPOSITORY_ROOT/apps/control-room/src/generated/design-tokens.css"
COMMITTED_TOKEN_TYPESCRIPT="$REPOSITORY_ROOT/apps/control-room/src/generated/design-tokens.ts"

FIRST_PROFILE="$FIRST_ROOT/public-profile.json"
FIRST_TOKEN_CSS="$FIRST_ROOT/design-tokens.css"
FIRST_TOKEN_TYPESCRIPT="$FIRST_ROOT/design-tokens.ts"

SECOND_PROFILE="$SECOND_ROOT/public-profile.json"
SECOND_TOKEN_CSS="$SECOND_ROOT/design-tokens.css"
SECOND_TOKEN_TYPESCRIPT="$SECOND_ROOT/design-tokens.ts"

assert_current_artifact() {
    local generated_path="$1"
    local committed_path="$2"
    local relative_path

    if cmp --silent "$generated_path" "$committed_path"; then
        return 0
    fi

    relative_path="${committed_path#"$REPOSITORY_ROOT/"}"
    printf '%s is stale\n' "$relative_path" >&2
    return 1
}

generate_contracts() {
    local output_root="$1"

    uv run profile-system frontend \
        --source "$PROFILE_SOURCE" \
        --output "$output_root/public-profile.json"

    uv run profile-system frontend-tokens \
        --source "$TOKEN_SOURCE" \
        --css-output "$output_root/design-tokens.css" \
        --typescript-output "$output_root/design-tokens.ts"
}

cd "$REPOSITORY_ROOT"

rm -rf "$CHECK_ROOT"
mkdir -p "$FIRST_ROOT" "$SECOND_ROOT"

scripts/profile_check.sh

shellcheck \
    scripts/control_room_check.sh \
    scripts/control_room_data.sh

generate_contracts "$FIRST_ROOT"
generate_contracts "$SECOND_ROOT"

test -s "$FIRST_PROFILE"
test -s "$FIRST_TOKEN_CSS"
test -s "$FIRST_TOKEN_TYPESCRIPT"
test -s "$SECOND_PROFILE"
test -s "$SECOND_TOKEN_CSS"
test -s "$SECOND_TOKEN_TYPESCRIPT"
test -s "$COMMITTED_PROFILE"
test -s "$COMMITTED_TOKEN_CSS"
test -s "$COMMITTED_TOKEN_TYPESCRIPT"

assert_current_artifact "$FIRST_PROFILE" "$SECOND_PROFILE"
assert_current_artifact "$FIRST_TOKEN_CSS" "$SECOND_TOKEN_CSS"
assert_current_artifact "$FIRST_TOKEN_TYPESCRIPT" "$SECOND_TOKEN_TYPESCRIPT"

assert_current_artifact "$FIRST_PROFILE" "$COMMITTED_PROFILE"
assert_current_artifact "$FIRST_TOKEN_CSS" "$COMMITTED_TOKEN_CSS"
assert_current_artifact \
    "$FIRST_TOKEN_TYPESCRIPT" \
    "$COMMITTED_TOKEN_TYPESCRIPT"

python3 -B -m json.tool "$FIRST_PROFILE" >/dev/null

pnpm install \
    --frozen-lockfile \
    --ignore-scripts

pnpm --filter @michal-planeta/control-room typecheck
pnpm --filter @michal-planeta/control-room test
pnpm --filter @michal-planeta/control-room build
pnpm --filter @michal-planeta/control-room test:e2e

printf '[PASS] Deterministic public frontend projection\n'
printf '[PASS] Deterministic generated design contracts\n'
printf '[PASS] Strict TypeScript and component contracts\n'
printf '[PASS] Production build and browser acceptance\n'
