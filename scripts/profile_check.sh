#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPOSITORY_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

CHECK_ROOT="$REPOSITORY_ROOT/.profile-build/check"

FIRST_OUTPUT="$CHECK_ROOT/manifest-first"
SECOND_OUTPUT="$CHECK_ROOT/manifest-second"

FIRST_PROBE="$CHECK_ROOT/probe-first.svg"
SECOND_PROBE="$CHECK_ROOT/probe-second.svg"

COMMITTED_PROBE="$(
    printf '%s\n' \
        "$REPOSITORY_ROOT/assets/generated/probes/github-svg-capabilities.svg"
)"

cd "$REPOSITORY_ROOT"

rm -rf "$CHECK_ROOT"
mkdir -p "$CHECK_ROOT"

uv sync \
    --locked \
    --all-groups

pnpm install \
    --frozen-lockfile \
    --ignore-scripts

uv run ruff format \
    --check \
    src/profile_system \
    tests/python

uv run ruff check \
    src/profile_system \
    tests/python

uv run mypy

uv run pytest

shellcheck \
    scripts/profile_build.sh \
    scripts/profile_check.sh \
    scripts/profile_probe.sh

scripts/profile_build.sh \
    "$FIRST_OUTPUT"

scripts/profile_build.sh \
    "$SECOND_OUTPUT"

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

scripts/profile_probe.sh \
    "$FIRST_PROBE"

scripts/profile_probe.sh \
    "$SECOND_PROBE"

test -s "$FIRST_PROBE"
test -s "$SECOND_PROBE"
test -s "$COMMITTED_PROBE"

cmp --silent \
    "$FIRST_PROBE" \
    "$SECOND_PROBE"

cmp --silent \
    "$FIRST_PROBE" \
    "$COMMITTED_PROBE"

xmllint \
    --noout \
    "$FIRST_PROBE"

xmllint \
    --noout \
    "$COMMITTED_PROBE"

python3 -B - \
    "$FIRST_PROBE" <<'PYTHON_SVG_POLICY'
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path

path = Path(sys.argv[1])
root = element_tree.parse(path).getroot()

forbidden_elements = {
    "animate",
    "animateMotion",
    "animateTransform",
    "foreignObject",
    "image",
    "script",
    "set",
}

required_elements = {
    "clipPath",
    "filter",
    "linearGradient",
    "mask",
    "radialGradient",
}

element_names: set[str] = set()
identifiers: list[str] = []
references: set[str] = set()

for element in root.iter():
    element_name = element.tag.rsplit("}", 1)[-1]
    element_names.add(element_name)

    if element_name in forbidden_elements:
        raise SystemExit(
            f"Forbidden SVG element: {element_name}"
        )

    identifier = element.attrib.get("id")

    if identifier is not None:
        identifiers.append(identifier)

    for attribute_name, value in element.attrib.items():
        local_name = attribute_name.rsplit("}", 1)[-1]

        if local_name.lower().startswith("on"):
            raise SystemExit(
                f"Forbidden SVG event attribute: {local_name}"
            )

        if local_name == "href" and value.startswith(
            (
                "http:",
                "https:",
                "//",
                "data:",
            )
        ):
            raise SystemExit(
                f"Forbidden SVG external reference: {value}"
            )

        references.update(
            re.findall(
                r"url\(#([a-z0-9-]+)\)",
                value,
            )
        )

if len(identifiers) != len(set(identifiers)):
    raise SystemExit(
        "SVG contains duplicate identifiers"
    )

if not references.issubset(set(identifiers)):
    unresolved = sorted(
        references - set(identifiers)
    )
    raise SystemExit(
        "SVG contains unresolved references: "
        + ", ".join(unresolved)
    )

if not required_elements.issubset(element_names):
    missing = sorted(
        required_elements - element_names
    )
    raise SystemExit(
        "SVG probe is missing capability elements: "
        + ", ".join(missing)
    )

capability_count = sum(
    identifier.startswith("capability-")
    for identifier in identifiers
)

if capability_count != 9:
    raise SystemExit(
        "SVG probe must contain exactly nine capability groups"
    )
PYTHON_SVG_POLICY

printf '[PASS] Python formatting, lint and static analysis\n'
printf '[PASS] Behavioral tests and shell validation\n'
printf '[PASS] Deterministic publication manifest\n'
printf '[PASS] Deterministic static SVG probe and safety policy\n'
