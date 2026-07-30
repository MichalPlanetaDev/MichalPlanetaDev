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

FIRST_TOKENS="$CHECK_ROOT/tokens-first.json"
SECOND_TOKENS="$CHECK_ROOT/tokens-second.json"
COMMITTED_TOKENS="$(
    printf '%s\n' \
        "$REPOSITORY_ROOT/assets/generated/contracts/visual-grammar.json"
)"

FIRST_KERNEL="$CHECK_ROOT/kernel-first.svg"
SECOND_KERNEL="$CHECK_ROOT/kernel-second.svg"
COMMITTED_KERNEL="$(
    printf '%s\n' \
        "$REPOSITORY_ROOT/assets/generated/kernel/svg-renderer-kernel.svg"
)"

FIRST_SCENE="$CHECK_ROOT/scene-first.svg"
SECOND_SCENE="$CHECK_ROOT/scene-second.svg"
COMMITTED_SCENE="$(
    printf '%s\n' \
        "$REPOSITORY_ROOT/assets/generated/scenes/planetary-observatory.svg"
)"

FIRST_HERO="$CHECK_ROOT/hero-first.svg"
SECOND_HERO="$CHECK_ROOT/hero-second.svg"
COMMITTED_HERO="$(
    printf '%s\n' \
        "$REPOSITORY_ROOT/assets/generated/hero/identity-observatory.svg"
)"

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
    scripts/profile_hero.sh \
    scripts/profile_kernel.sh \
    scripts/profile_probe.sh \
    scripts/profile_scene.sh \
    scripts/profile_tokens.sh

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

scripts/profile_tokens.sh \
    "$FIRST_TOKENS"

scripts/profile_tokens.sh \
    "$SECOND_TOKENS"

test -s "$FIRST_TOKENS"
test -s "$SECOND_TOKENS"
test -s "$COMMITTED_TOKENS"

cmp --silent \
    "$FIRST_TOKENS" \
    "$SECOND_TOKENS"

cmp --silent \
    "$FIRST_TOKENS" \
    "$COMMITTED_TOKENS"

python3 -B -m json.tool \
    "$FIRST_TOKENS" \
    >/dev/null

scripts/profile_kernel.sh \
    "$FIRST_KERNEL"

scripts/profile_kernel.sh \
    "$SECOND_KERNEL"

test -s "$FIRST_KERNEL"
test -s "$SECOND_KERNEL"
test -s "$COMMITTED_KERNEL"

cmp --silent \
    "$FIRST_KERNEL" \
    "$SECOND_KERNEL"

cmp --silent \
    "$FIRST_KERNEL" \
    "$COMMITTED_KERNEL"

xmllint \
    --noout \
    "$FIRST_KERNEL"

xmllint \
    --noout \
    "$COMMITTED_KERNEL"

python3 -B - \
    "$FIRST_KERNEL" <<'PYTHON_KERNEL_POLICY'
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
required_identifiers = {
    "renderer-kernel-title",
    "renderer-kernel-description",
    "layer-background",
    "layer-grid",
    "layer-interface",
    "layer-primitives",
    "layer-typography",
    "layer-footer",
}
identifiers: list[str] = []
references: set[str] = set()

if root.attrib.get("role") != "img":
    raise SystemExit("Renderer kernel root must use role=img")

labelled_by = set(root.attrib.get("aria-labelledby", "").split())

if not {
    "renderer-kernel-title",
    "renderer-kernel-description",
}.issubset(labelled_by):
    raise SystemExit("Renderer kernel is missing accessible labelling")

if root.attrib.get("viewBox") != "0 0 1200 520":
    raise SystemExit("Renderer kernel viewBox differs from its contract")

for element in root.iter():
    element_name = element.tag.rsplit("}", 1)[-1]

    if element_name in forbidden_elements:
        raise SystemExit(f"Forbidden SVG element: {element_name}")

    identifier = element.attrib.get("id")

    if identifier is not None:
        identifiers.append(identifier)

    for attribute_name, value in element.attrib.items():
        local_name = attribute_name.rsplit("}", 1)[-1]

        if local_name.lower().startswith("on"):
            raise SystemExit(
                f"Forbidden SVG event attribute: {local_name}"
            )
        if local_name == "href":
            raise SystemExit("Renderer kernel must not contain href")

        references.update(
            re.findall(
                r"url\(#([a-z0-9-]+)\)",
                value,
            )
        )

identifier_set = set(identifiers)

if len(identifiers) != len(identifier_set):
    raise SystemExit("Renderer kernel contains duplicate identifiers")

if not references.issubset(identifier_set):
    unresolved = sorted(references - identifier_set)
    raise SystemExit(
        "Renderer kernel contains unresolved references: "
        + ", ".join(unresolved)
    )

if not required_identifiers.issubset(identifier_set):
    missing = sorted(required_identifiers - identifier_set)
    raise SystemExit(
        "Renderer kernel is missing required layers: "
        + ", ".join(missing)
    )
PYTHON_KERNEL_POLICY

scripts/profile_scene.sh \
    "$FIRST_SCENE"

scripts/profile_scene.sh \
    "$SECOND_SCENE"

test -s "$FIRST_SCENE"
test -s "$SECOND_SCENE"
test -s "$COMMITTED_SCENE"

cmp --silent \
    "$FIRST_SCENE" \
    "$SECOND_SCENE"

cmp --silent \
    "$FIRST_SCENE" \
    "$COMMITTED_SCENE"

xmllint \
    --noout \
    "$FIRST_SCENE"

xmllint \
    --noout \
    "$COMMITTED_SCENE"

python3 -B - \
    "$FIRST_SCENE" \
    profile/scenes/planetary-observatory.json <<'PYTHON_SCENE_POLICY'
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path

svg_path = Path(sys.argv[1])
source_path = Path(sys.argv[2])
root = element_tree.parse(svg_path).getroot()
source = json.loads(source_path.read_text(encoding="utf-8"))

required_identifiers = {
    "renderer-kernel-title",
    "renderer-kernel-description",
    "scene-background",
    "scene-stars",
    "scene-window",
    "scene-planet",
    "scene-architecture",
    "scene-console",
    "scene-atmosphere",
    "scene-foreground",
}
forbidden_elements = {
    "animate",
    "animateMotion",
    "animateTransform",
    "foreignObject",
    "image",
    "script",
    "set",
}
identifiers: list[str] = []
references: set[str] = set()
star_count = 0

if root.attrib.get("role") != "img":
    raise SystemExit("Observatory scene root must use role=img")
if root.attrib.get("viewBox") != "0 0 1200 720":
    raise SystemExit("Observatory scene viewBox differs from its contract")

for element in root.iter():
    name = element.tag.rsplit("}", 1)[-1]
    if name in forbidden_elements:
        raise SystemExit(f"Forbidden observatory SVG element: {name}")
    identifier = element.attrib.get("id")
    if identifier is not None:
        identifiers.append(identifier)
    if element.get("id") == "scene-stars":
        star_count = sum(
            child.tag.rsplit("}", 1)[-1] == "circle"
            for child in element
        )
    for attribute_name, value in element.attrib.items():
        local_name = attribute_name.rsplit("}", 1)[-1]
        if local_name.lower().startswith("on"):
            raise SystemExit(f"Forbidden SVG event attribute: {local_name}")
        if local_name == "href":
            raise SystemExit("Observatory scene must not contain href")
        references.update(re.findall(r"url\(#([a-z0-9-]+)\)", value))

identifier_set = set(identifiers)
if len(identifiers) != len(identifier_set):
    raise SystemExit("Observatory scene contains duplicate identifiers")
if not required_identifiers.issubset(identifier_set):
    missing = sorted(required_identifiers - identifier_set)
    raise SystemExit("Observatory scene is missing layers: " + ", ".join(missing))
if not references.issubset(identifier_set):
    unresolved = sorted(references - identifier_set)
    raise SystemExit(
        "Observatory scene contains unresolved references: "
        + ", ".join(unresolved)
    )
if star_count != source["starCount"]:
    raise SystemExit("Rendered star count differs from the scene contract")
PYTHON_SCENE_POLICY

scripts/profile_hero.sh \
    "$FIRST_HERO"

scripts/profile_hero.sh \
    "$SECOND_HERO"

test -s "$FIRST_HERO"
test -s "$SECOND_HERO"
test -s "$COMMITTED_HERO"

cmp --silent \
    "$FIRST_HERO" \
    "$SECOND_HERO"

cmp --silent \
    "$FIRST_HERO" \
    "$COMMITTED_HERO"

xmllint \
    --noout \
    "$FIRST_HERO"

xmllint \
    --noout \
    "$COMMITTED_HERO"

python3 -B - \
    "$FIRST_HERO" \
    profile/profile.json <<'PYTHON_HERO_POLICY'
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path

svg_path = Path(sys.argv[1])
profile_path = Path(sys.argv[2])
root = element_tree.parse(svg_path).getroot()
profile = json.loads(profile_path.read_text(encoding="utf-8"))
identity = profile["identity"]

required_identifiers = {
    "renderer-kernel-title",
    "renderer-kernel-description",
    "scene-background",
    "scene-stars",
    "scene-window",
    "scene-planet",
    "scene-architecture",
    "scene-console",
    "scene-atmosphere",
    "scene-foreground",
    "hero-identity",
    "hero-identity-panel",
    "hero-identity-headline",
    "hero-identity-name",
    "hero-identity-motto",
    "hero-status",
}
forbidden_elements = {
    "animate",
    "animateMotion",
    "animateTransform",
    "foreignObject",
    "image",
    "script",
    "set",
}
identifiers: list[str] = []
references: set[str] = set()
texts: list[str] = []

if root.attrib.get("role") != "img":
    raise SystemExit("Identity hero root must use role=img")
if root.attrib.get("viewBox") != "0 0 1200 720":
    raise SystemExit("Identity hero viewBox differs from its contract")

for element in root.iter():
    name = element.tag.rsplit("}", 1)[-1]
    if name in forbidden_elements:
        raise SystemExit(f"Forbidden identity hero element: {name}")
    identifier = element.attrib.get("id")
    if identifier is not None:
        identifiers.append(identifier)
    if element.text:
        texts.append(element.text)
    for attribute_name, value in element.attrib.items():
        local_name = attribute_name.rsplit("}", 1)[-1]
        if local_name.lower().startswith("on"):
            raise SystemExit(f"Forbidden identity hero event: {local_name}")
        if local_name == "href":
            raise SystemExit("Identity hero must not contain href")
        references.update(re.findall(r"url\(#([a-z0-9-]+)\)", value))

identifier_set = set(identifiers)
if len(identifiers) != len(identifier_set):
    raise SystemExit("Identity hero contains duplicate identifiers")
if not required_identifiers.issubset(identifier_set):
    missing = sorted(required_identifiers - identifier_set)
    raise SystemExit("Identity hero is missing layers: " + ", ".join(missing))
if not references.issubset(identifier_set):
    unresolved = sorted(references - identifier_set)
    raise SystemExit(
        "Identity hero contains unresolved references: "
        + ", ".join(unresolved)
    )

content = "\n".join(texts)
for required_text in (
    profile["displayName"].upper(),
    identity["headline"],
    identity["motto"],
):
    if required_text not in content:
        raise SystemExit(f"Identity hero is missing canonical copy: {required_text}")
PYTHON_HERO_POLICY

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
printf '[PASS] Deterministic visual grammar contract\n'
printf '[PASS] Deterministic SVG renderer kernel\n'
printf '[PASS] Deterministic planetary observatory scene\n'
printf '[PASS] Deterministic canonical identity hero\n'
printf '[PASS] Deterministic static SVG probe and safety policy\n'
