from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
EXPECTED_COPYRIGHT_NOTICE = "Copyright © 2026 Michał Planeta. All rights reserved."
EXPECTED_SOURCE_REVIEW_NOTICE = (
    "Source review is permitted; reuse requires prior written permission."
)
EXPECTED_LICENSE_PATH = PurePosixPath("LICENSE")


class ReadmeDataError(ValueError):
    """Raised when authored README composition data violates its contract."""


@dataclass(frozen=True, slots=True)
class ReadmeCompositionSnapshot:
    schema_version: int
    composition_id: str
    profile_id: str
    theme_id: str
    hero_asset: PurePosixPath
    sections_asset: PurePosixPath
    asset_width_percent: int
    text_fallback_title: str
    license_path: PurePosixPath
    copyright_notice: str
    source_review_notice: str


def _mapping(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ReadmeDataError(f"{context} must contain a JSON object")
    return cast(dict[str, object], value)


def _exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    missing = sorted(expected - set(source))
    unexpected = sorted(set(source) - expected)

    if missing:
        raise ReadmeDataError(f"{context} is missing fields: {', '.join(missing)}")
    if unexpected:
        raise ReadmeDataError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def _text(source: dict[str, object], field: str, context: str) -> str:
    value = source.get(field)

    if not isinstance(value, str) or not value.strip():
        raise ReadmeDataError(f"{context}.{field} must contain a non-empty string")
    return value.strip()


def _integer(source: dict[str, object], field: str, context: str) -> int:
    value = source.get(field)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ReadmeDataError(f"{context}.{field} must contain an integer")
    return value


def _identifier(value: str, context: str) -> str:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ReadmeDataError(f"{context} must use lowercase kebab-case")
    return value


def _repository_path(value: str, context: str) -> PurePosixPath:
    if "\\" in value or "://" in value:
        raise ReadmeDataError(f"{context} must contain a repository-relative path")

    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise ReadmeDataError(f"{context} must contain a repository-relative path")

    return path


def load_readme_composition(path: Path) -> ReadmeCompositionSnapshot:
    source = _mapping(
        json.loads(path.read_text(encoding="utf-8")),
        "README composition source",
    )
    _exact_keys(
        source,
        {
            "assetWidthPercent",
            "compositionId",
            "copyrightNotice",
            "heroAsset",
            "licensePath",
            "profileId",
            "schemaVersion",
            "sectionsAsset",
            "sourceReviewNotice",
            "textFallbackTitle",
            "themeId",
        },
        "README composition source",
    )

    schema_version = _integer(
        source,
        "schemaVersion",
        "README composition source",
    )
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ReadmeDataError(
            f"Unsupported README composition schemaVersion: {schema_version}"
        )

    hero_asset = _repository_path(
        _text(source, "heroAsset", "README composition source"),
        "README composition source.heroAsset",
    )
    sections_asset = _repository_path(
        _text(source, "sectionsAsset", "README composition source"),
        "README composition source.sectionsAsset",
    )
    if hero_asset.suffix != ".svg" or sections_asset.suffix != ".svg":
        raise ReadmeDataError("README composition assets must contain SVG paths")
    if hero_asset == sections_asset:
        raise ReadmeDataError("README composition assets must be distinct")

    asset_width_percent = _integer(
        source,
        "assetWidthPercent",
        "README composition source",
    )
    if not 60 <= asset_width_percent <= 100:
        raise ReadmeDataError(
            "README composition assetWidthPercent must be between 60 and 100"
        )

    license_path = _repository_path(
        _text(source, "licensePath", "README composition source"),
        "README composition source.licensePath",
    )
    if license_path != EXPECTED_LICENSE_PATH:
        raise ReadmeDataError("README composition licensePath must equal LICENSE")

    copyright_notice = _text(
        source,
        "copyrightNotice",
        "README composition source",
    )
    if copyright_notice != EXPECTED_COPYRIGHT_NOTICE:
        raise ReadmeDataError(
            "README composition copyrightNotice differs from repository policy"
        )

    source_review_notice = _text(
        source,
        "sourceReviewNotice",
        "README composition source",
    )
    if source_review_notice != EXPECTED_SOURCE_REVIEW_NOTICE:
        raise ReadmeDataError(
            "README composition sourceReviewNotice differs from repository policy"
        )

    return ReadmeCompositionSnapshot(
        schema_version=schema_version,
        composition_id=_identifier(
            _text(source, "compositionId", "README composition source"),
            "README composition source.compositionId",
        ),
        profile_id=_identifier(
            _text(source, "profileId", "README composition source"),
            "README composition source.profileId",
        ),
        theme_id=_identifier(
            _text(source, "themeId", "README composition source"),
            "README composition source.themeId",
        ),
        hero_asset=hero_asset,
        sections_asset=sections_asset,
        asset_width_percent=asset_width_percent,
        text_fallback_title=_text(
            source,
            "textFallbackTitle",
            "README composition source",
        ),
        license_path=license_path,
        copyright_notice=copyright_notice,
        source_review_notice=source_review_notice,
    )
