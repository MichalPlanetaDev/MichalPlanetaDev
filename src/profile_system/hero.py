from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REQUIRED_LAYER_ORDER = ("scene", "identity", "status")


class HeroDataError(ValueError):
    """Raised when authored identity-hero data violates its contract."""


@dataclass(frozen=True, slots=True)
class HeroViewport:
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class HeroPanel:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class IdentityHeroSnapshot:
    schema_version: int
    hero_id: str
    profile_id: str
    scene_id: str
    theme_id: str
    viewport: HeroViewport
    panel: HeroPanel
    layer_order: tuple[str, ...]


def _mapping(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HeroDataError(f"{context} must contain a JSON object")
    return cast(dict[str, object], value)


def _array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise HeroDataError(f"{context} must contain a JSON array")
    return cast(list[object], value)


def _exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    missing = sorted(expected - set(source))
    unexpected = sorted(set(source) - expected)

    if missing:
        raise HeroDataError(f"{context} is missing fields: {', '.join(missing)}")
    if unexpected:
        raise HeroDataError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def _text(source: dict[str, object], field: str, context: str) -> str:
    value = source.get(field)
    if not isinstance(value, str) or not value.strip():
        raise HeroDataError(f"{context}.{field} must contain a non-empty string")
    return value.strip()


def _integer(source: dict[str, object], field: str, context: str) -> int:
    value = source.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise HeroDataError(f"{context}.{field} must contain an integer")
    return value


def _identifier(value: str, context: str) -> str:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise HeroDataError(f"{context} must use lowercase kebab-case")
    return value


def load_identity_hero(path: Path) -> IdentityHeroSnapshot:
    source = _mapping(
        json.loads(path.read_text(encoding="utf-8")),
        "Identity hero source",
    )
    _exact_keys(
        source,
        {
            "heroId",
            "layerOrder",
            "panel",
            "profileId",
            "sceneId",
            "schemaVersion",
            "themeId",
            "viewport",
        },
        "Identity hero source",
    )

    schema_version = _integer(source, "schemaVersion", "Identity hero source")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise HeroDataError(
            f"Unsupported identity hero schemaVersion: {schema_version}"
        )

    viewport_source = _mapping(
        source.get("viewport"),
        "Identity hero source.viewport",
    )
    _exact_keys(
        viewport_source,
        {"height", "width"},
        "Identity hero source.viewport",
    )
    viewport = HeroViewport(
        width=_integer(viewport_source, "width", "Identity hero source.viewport"),
        height=_integer(
            viewport_source,
            "height",
            "Identity hero source.viewport",
        ),
    )
    if not 960 <= viewport.width <= 1600:
        raise HeroDataError("Identity hero width must be between 960 and 1600")
    if not 600 <= viewport.height <= 1000:
        raise HeroDataError("Identity hero height must be between 600 and 1000")

    panel_source = _mapping(source.get("panel"), "Identity hero source.panel")
    _exact_keys(
        panel_source,
        {"height", "width", "x", "y"},
        "Identity hero source.panel",
    )
    panel = HeroPanel(
        x=_integer(panel_source, "x", "Identity hero source.panel"),
        y=_integer(panel_source, "y", "Identity hero source.panel"),
        width=_integer(panel_source, "width", "Identity hero source.panel"),
        height=_integer(panel_source, "height", "Identity hero source.panel"),
    )
    if panel.width < 420 or panel.height < 240:
        raise HeroDataError("Identity hero panel is below its minimum size")
    if (
        panel.x < 0
        or panel.y < 0
        or panel.x + panel.width > viewport.width
        or panel.y + panel.height > viewport.height
    ):
        raise HeroDataError("Identity hero panel must remain inside the viewport")

    layer_values = _array(
        source.get("layerOrder"),
        "Identity hero source.layerOrder",
    )
    layer_order: list[str] = []
    for index, layer_value in enumerate(layer_values):
        if not isinstance(layer_value, str) or not layer_value:
            raise HeroDataError(
                "Identity hero source.layerOrder"
                f"[{index}] must contain a non-empty string"
            )
        layer_order.append(layer_value)

    if tuple(layer_order) != REQUIRED_LAYER_ORDER:
        raise HeroDataError(
            "Identity hero layerOrder must equal: " + ", ".join(REQUIRED_LAYER_ORDER)
        )

    return IdentityHeroSnapshot(
        schema_version=schema_version,
        hero_id=_identifier(
            _text(source, "heroId", "Identity hero source"),
            "Identity hero source.heroId",
        ),
        profile_id=_identifier(
            _text(source, "profileId", "Identity hero source"),
            "Identity hero source.profileId",
        ),
        scene_id=_identifier(
            _text(source, "sceneId", "Identity hero source"),
            "Identity hero source.sceneId",
        ),
        theme_id=_identifier(
            _text(source, "themeId", "Identity hero source"),
            "Identity hero source.themeId",
        ),
        viewport=viewport,
        panel=panel,
        layer_order=tuple(layer_order),
    )
