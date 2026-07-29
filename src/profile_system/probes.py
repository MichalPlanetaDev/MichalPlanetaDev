from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_CAPABILITY_KINDS = frozenset(
    {
        "clip-path",
        "filter",
        "linear-gradient",
        "mask",
        "opacity",
        "path-geometry",
        "radial-gradient",
        "solid-geometry",
        "text",
    }
)
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class ProbeDataError(ValueError):
    """Raised when authored SVG probe data violates its contract."""


@dataclass(frozen=True, slots=True)
class ProbeViewport:
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ProbeCapability:
    capability_id: str
    label: str
    kind: str


@dataclass(frozen=True, slots=True)
class SvgProbeSnapshot:
    schema_version: int
    probe_id: str
    title: str
    viewport: ProbeViewport
    capabilities: tuple[ProbeCapability, ...]


def _require_mapping(
    value: object,
    context: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProbeDataError(f"{context} must contain a JSON object")

    return cast(
        dict[str, object],
        value,
    )


def _require_array(
    value: object,
    context: str,
) -> list[object]:
    if not isinstance(value, list):
        raise ProbeDataError(f"{context} must contain a JSON array")

    return cast(
        list[object],
        value,
    )


def _require_exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    missing = sorted(expected - set(source))
    unexpected = sorted(set(source) - expected)

    if missing:
        raise ProbeDataError(f"{context} is missing fields: {', '.join(missing)}")

    if unexpected:
        raise ProbeDataError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def _require_text(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> str:
    value = source.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise ProbeDataError(f"{context}.{field_name} must contain a non-empty string")

    return value.strip()


def _require_integer(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> int:
    value = source.get(field_name)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ProbeDataError(f"{context}.{field_name} must contain an integer")

    return value


def _require_identifier(
    value: str,
    context: str,
) -> str:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ProbeDataError(f"{context} must use lowercase kebab-case identifiers")

    return value


def load_svg_probe_snapshot(
    path: Path,
) -> SvgProbeSnapshot:
    source = _require_mapping(
        json.loads(path.read_text(encoding="utf-8")),
        "Probe source",
    )

    _require_exact_keys(
        source,
        {
            "capabilities",
            "probeId",
            "schemaVersion",
            "title",
            "viewport",
        },
        "Probe source",
    )

    schema_version = _require_integer(
        source,
        "schemaVersion",
        "Probe source",
    )

    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ProbeDataError(f"Unsupported probe schemaVersion: {schema_version}")

    viewport_source = _require_mapping(
        source.get("viewport"),
        "Probe source.viewport",
    )

    _require_exact_keys(
        viewport_source,
        {
            "height",
            "width",
        },
        "Probe source.viewport",
    )

    viewport = ProbeViewport(
        width=_require_integer(
            viewport_source,
            "width",
            "Probe source.viewport",
        ),
        height=_require_integer(
            viewport_source,
            "height",
            "Probe source.viewport",
        ),
    )

    if not 900 <= viewport.width <= 2400:
        raise ProbeDataError("Probe viewport width must be between 900 and 2400")

    if not 540 <= viewport.height <= 1200:
        raise ProbeDataError("Probe viewport height must be between 540 and 1200")

    capability_values = _require_array(
        source.get("capabilities"),
        "Probe source.capabilities",
    )

    if not capability_values:
        raise ProbeDataError("Probe source.capabilities must not be empty")

    if len(capability_values) > 9:
        raise ProbeDataError("Probe source supports at most 9 capabilities")

    capabilities: list[ProbeCapability] = []
    capability_ids: set[str] = set()

    for index, value in enumerate(capability_values):
        context = f"Probe source.capabilities[{index}]"

        capability_source = _require_mapping(
            value,
            context,
        )

        _require_exact_keys(
            capability_source,
            {
                "id",
                "kind",
                "label",
            },
            context,
        )

        capability_id = _require_identifier(
            _require_text(
                capability_source,
                "id",
                context,
            ),
            f"{context}.id",
        )

        if capability_id in capability_ids:
            raise ProbeDataError(f"Duplicate capability id: {capability_id}")

        capability_kind = _require_text(
            capability_source,
            "kind",
            context,
        )

        if capability_kind not in SUPPORTED_CAPABILITY_KINDS:
            raise ProbeDataError(f"Unsupported capability kind: {capability_kind}")

        capability_ids.add(capability_id)

        capabilities.append(
            ProbeCapability(
                capability_id=capability_id,
                label=_require_text(
                    capability_source,
                    "label",
                    context,
                ),
                kind=capability_kind,
            )
        )

    return SvgProbeSnapshot(
        schema_version=schema_version,
        probe_id=_require_identifier(
            _require_text(
                source,
                "probeId",
                "Probe source",
            ),
            "Probe source.probeId",
        ),
        title=_require_text(
            source,
            "title",
            "Probe source",
        ),
        viewport=viewport,
        capabilities=tuple(capabilities),
    )
