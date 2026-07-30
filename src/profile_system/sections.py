from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REQUIRED_SECTION_ORDER = (
    "projects",
    "stack",
    "evidence",
    "disciplines",
    "connect",
)
EXPECTED_COPYRIGHT_NOTICE = "Copyright © 2026 Michał Planeta. All rights reserved."


class SectionsDataError(ValueError):
    """Raised when authored engineering-section data violates its contract."""


@dataclass(frozen=True, slots=True)
class SectionsViewport:
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class EngineeringSectionsSnapshot:
    schema_version: int
    section_set_id: str
    theme_id: str
    title: str
    description: str
    viewport: SectionsViewport
    section_order: tuple[str, ...]
    maximum_technologies: int
    copyright_notice: str


def _mapping(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SectionsDataError(f"{context} must contain a JSON object")
    return cast(dict[str, object], value)


def _array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise SectionsDataError(f"{context} must contain a JSON array")
    return cast(list[object], value)


def _exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    missing = sorted(expected - set(source))
    unexpected = sorted(set(source) - expected)

    if missing:
        raise SectionsDataError(f"{context} is missing fields: {', '.join(missing)}")
    if unexpected:
        raise SectionsDataError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def _text(source: dict[str, object], field: str, context: str) -> str:
    value = source.get(field)

    if not isinstance(value, str) or not value.strip():
        raise SectionsDataError(f"{context}.{field} must contain a non-empty string")
    return value.strip()


def _integer(source: dict[str, object], field: str, context: str) -> int:
    value = source.get(field)

    if isinstance(value, bool) or not isinstance(value, int):
        raise SectionsDataError(f"{context}.{field} must contain an integer")
    return value


def _identifier(value: str, context: str) -> str:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise SectionsDataError(f"{context} must use lowercase kebab-case")
    return value


def load_engineering_sections(path: Path) -> EngineeringSectionsSnapshot:
    source = _mapping(
        json.loads(path.read_text(encoding="utf-8")),
        "Engineering sections source",
    )
    _exact_keys(
        source,
        {
            "copyrightNotice",
            "description",
            "maximumTechnologies",
            "schemaVersion",
            "sectionOrder",
            "sectionSetId",
            "themeId",
            "title",
            "viewport",
        },
        "Engineering sections source",
    )

    schema_version = _integer(
        source,
        "schemaVersion",
        "Engineering sections source",
    )
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise SectionsDataError(
            f"Unsupported engineering sections schemaVersion: {schema_version}"
        )

    viewport_source = _mapping(
        source.get("viewport"),
        "Engineering sections source.viewport",
    )
    _exact_keys(
        viewport_source,
        {"height", "width"},
        "Engineering sections source.viewport",
    )
    viewport = SectionsViewport(
        width=_integer(
            viewport_source,
            "width",
            "Engineering sections source.viewport",
        ),
        height=_integer(
            viewport_source,
            "height",
            "Engineering sections source.viewport",
        ),
    )

    if viewport.width != 1200:
        raise SectionsDataError("Engineering sections viewport width must equal 1200")
    if not 1600 <= viewport.height <= 2200:
        raise SectionsDataError(
            "Engineering sections viewport height must be between 1600 and 2200"
        )

    order_values = _array(
        source.get("sectionOrder"),
        "Engineering sections source.sectionOrder",
    )
    section_order: list[str] = []

    for index, order_value in enumerate(order_values):
        if not isinstance(order_value, str) or not order_value:
            raise SectionsDataError(
                "Engineering sections source.sectionOrder"
                f"[{index}] must contain a non-empty string"
            )
        section_order.append(order_value)

    if tuple(section_order) != REQUIRED_SECTION_ORDER:
        raise SectionsDataError(
            "Engineering sections sectionOrder must equal: "
            + ", ".join(REQUIRED_SECTION_ORDER)
        )

    maximum_technologies = _integer(
        source,
        "maximumTechnologies",
        "Engineering sections source",
    )
    if not 8 <= maximum_technologies <= 16:
        raise SectionsDataError(
            "Engineering sections maximumTechnologies must be between 8 and 16"
        )

    copyright_notice = _text(
        source,
        "copyrightNotice",
        "Engineering sections source",
    )
    if copyright_notice != EXPECTED_COPYRIGHT_NOTICE:
        raise SectionsDataError(
            "Engineering sections copyrightNotice differs from the repository policy"
        )

    return EngineeringSectionsSnapshot(
        schema_version=schema_version,
        section_set_id=_identifier(
            _text(source, "sectionSetId", "Engineering sections source"),
            "Engineering sections source.sectionSetId",
        ),
        theme_id=_identifier(
            _text(source, "themeId", "Engineering sections source"),
            "Engineering sections source.themeId",
        ),
        title=_text(source, "title", "Engineering sections source"),
        description=_text(source, "description", "Engineering sections source"),
        viewport=viewport,
        section_order=tuple(section_order),
        maximum_technologies=maximum_technologies,
        copyright_notice=copyright_notice,
    )
