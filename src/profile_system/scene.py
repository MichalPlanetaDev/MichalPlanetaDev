from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REQUIRED_LAYER_ORDER = (
    "background",
    "stars",
    "window",
    "planet",
    "architecture",
    "console",
    "atmosphere",
    "foreground",
)


class SceneDataError(ValueError):
    """Raised when authored observatory scene data violates its contract."""


@dataclass(frozen=True, slots=True)
class SceneViewport:
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class PlanetSpec:
    center_x: int
    center_y: int
    radius: int
    ring_radius_x: int
    ring_radius_y: int
    ring_angle: float


@dataclass(frozen=True, slots=True)
class ShootingStarSpec:
    x: int
    y: int
    length: int
    angle: float
    opacity: float


@dataclass(frozen=True, slots=True)
class ObservatorySceneSnapshot:
    schema_version: int
    scene_id: str
    theme_id: str
    title: str
    description: str
    viewport: SceneViewport
    star_seed: int
    star_count: int
    horizon_y: int
    planet: PlanetSpec
    shooting_stars: tuple[ShootingStarSpec, ...]
    layer_order: tuple[str, ...]


def _mapping(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SceneDataError(f"{context} must contain a JSON object")
    return cast(dict[str, object], value)


def _array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise SceneDataError(f"{context} must contain a JSON array")
    return cast(list[object], value)


def _exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    missing = sorted(expected - set(source))
    unexpected = sorted(set(source) - expected)
    if missing:
        raise SceneDataError(f"{context} is missing fields: {', '.join(missing)}")
    if unexpected:
        raise SceneDataError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def _text(source: dict[str, object], field: str, context: str) -> str:
    value = source.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SceneDataError(f"{context}.{field} must contain a non-empty string")
    return value.strip()


def _integer(source: dict[str, object], field: str, context: str) -> int:
    value = source.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise SceneDataError(f"{context}.{field} must contain an integer")
    return value


def _number(source: dict[str, object], field: str, context: str) -> float:
    value = source.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SceneDataError(f"{context}.{field} must contain a number")
    return float(value)


def _identifier(value: str, context: str) -> str:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise SceneDataError(f"{context} must use lowercase kebab-case")
    return value


def load_observatory_scene(path: Path) -> ObservatorySceneSnapshot:
    source = _mapping(
        json.loads(path.read_text(encoding="utf-8")),
        "Observatory scene source",
    )
    _exact_keys(
        source,
        {
            "description",
            "horizonY",
            "layerOrder",
            "planet",
            "sceneId",
            "schemaVersion",
            "shootingStars",
            "starCount",
            "starSeed",
            "themeId",
            "title",
            "viewport",
        },
        "Observatory scene source",
    )

    schema_version = _integer(source, "schemaVersion", "Observatory scene source")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise SceneDataError(
            f"Unsupported observatory scene schemaVersion: {schema_version}"
        )

    scene_id = _identifier(
        _text(source, "sceneId", "Observatory scene source"),
        "Observatory scene source.sceneId",
    )
    theme_id = _identifier(
        _text(source, "themeId", "Observatory scene source"),
        "Observatory scene source.themeId",
    )

    viewport_source = _mapping(
        source.get("viewport"),
        "Observatory scene source.viewport",
    )
    _exact_keys(
        viewport_source,
        {"height", "width"},
        "Observatory scene source.viewport",
    )
    viewport = SceneViewport(
        width=_integer(
            viewport_source,
            "width",
            "Observatory scene source.viewport",
        ),
        height=_integer(
            viewport_source,
            "height",
            "Observatory scene source.viewport",
        ),
    )
    if not 960 <= viewport.width <= 1600:
        raise SceneDataError("Scene viewport width must be between 960 and 1600")
    if not 600 <= viewport.height <= 1000:
        raise SceneDataError("Scene viewport height must be between 600 and 1000")

    star_seed = _integer(source, "starSeed", "Observatory scene source")
    star_count = _integer(source, "starCount", "Observatory scene source")
    horizon_y = _integer(source, "horizonY", "Observatory scene source")

    if not 0 <= star_seed <= 2_147_483_647:
        raise SceneDataError("Scene starSeed must fit a signed 32-bit integer")
    if not 24 <= star_count <= 96:
        raise SceneDataError("Scene starCount must be between 24 and 96")
    if not int(viewport.height * 0.58) <= horizon_y <= int(viewport.height * 0.86):
        raise SceneDataError(
            "Scene horizonY must remain inside the lower viewport band"
        )

    planet_source = _mapping(
        source.get("planet"),
        "Observatory scene source.planet",
    )
    _exact_keys(
        planet_source,
        {
            "centerX",
            "centerY",
            "radius",
            "ringAngle",
            "ringRadiusX",
            "ringRadiusY",
        },
        "Observatory scene source.planet",
    )
    planet = PlanetSpec(
        center_x=_integer(
            planet_source,
            "centerX",
            "Observatory scene source.planet",
        ),
        center_y=_integer(
            planet_source,
            "centerY",
            "Observatory scene source.planet",
        ),
        radius=_integer(
            planet_source,
            "radius",
            "Observatory scene source.planet",
        ),
        ring_radius_x=_integer(
            planet_source,
            "ringRadiusX",
            "Observatory scene source.planet",
        ),
        ring_radius_y=_integer(
            planet_source,
            "ringRadiusY",
            "Observatory scene source.planet",
        ),
        ring_angle=_number(
            planet_source,
            "ringAngle",
            "Observatory scene source.planet",
        ),
    )
    if not 72 <= planet.radius <= 220:
        raise SceneDataError("Scene planet radius must be between 72 and 220")
    if not (
        planet.radius < planet.ring_radius_x <= planet.radius * 2
        and 16 <= planet.ring_radius_y < planet.radius
    ):
        raise SceneDataError("Scene planet ring dimensions are outside the contract")
    if not -35 <= planet.ring_angle <= 35:
        raise SceneDataError("Scene planet ringAngle must be between -35 and 35")
    if not (
        planet.radius <= planet.center_x <= viewport.width - planet.radius
        and planet.radius <= planet.center_y <= horizon_y - planet.radius // 2
    ):
        raise SceneDataError("Scene planet must remain inside the observatory window")

    shooting_values = _array(
        source.get("shootingStars"),
        "Observatory scene source.shootingStars",
    )
    if not 1 <= len(shooting_values) <= 5:
        raise SceneDataError("Scene must define between one and five shooting stars")

    shooting_stars: list[ShootingStarSpec] = []
    for index, raw_star in enumerate(shooting_values):
        context = f"Observatory scene source.shootingStars[{index}]"
        star_source = _mapping(raw_star, context)
        _exact_keys(
            star_source,
            {"angle", "length", "opacity", "x", "y"},
            context,
        )
        star = ShootingStarSpec(
            x=_integer(star_source, "x", context),
            y=_integer(star_source, "y", context),
            length=_integer(star_source, "length", context),
            angle=_number(star_source, "angle", context),
            opacity=_number(star_source, "opacity", context),
        )
        if not 0 <= star.x <= viewport.width or not 0 <= star.y <= horizon_y:
            raise SceneDataError(f"{context} origin must remain inside the sky band")
        if not 24 <= star.length <= 160:
            raise SceneDataError(f"{context}.length must be between 24 and 160")
        if not -45 <= star.angle <= 45:
            raise SceneDataError(f"{context}.angle must be between -45 and 45")
        if not 0.1 <= star.opacity <= 1:
            raise SceneDataError(f"{context}.opacity must be between 0.1 and 1")
        shooting_stars.append(star)

    layer_values = _array(
        source.get("layerOrder"),
        "Observatory scene source.layerOrder",
    )
    layer_order: list[str] = []
    for index, layer_value in enumerate(layer_values):
        if not isinstance(layer_value, str) or not layer_value:
            raise SceneDataError(
                "Observatory scene source.layerOrder"
                f"[{index}] must contain a non-empty string"
            )
        layer_order.append(layer_value)

    if tuple(layer_order) != REQUIRED_LAYER_ORDER:
        raise SceneDataError(
            "Scene layerOrder must equal: " + ", ".join(REQUIRED_LAYER_ORDER)
        )

    return ObservatorySceneSnapshot(
        schema_version=schema_version,
        scene_id=scene_id,
        theme_id=theme_id,
        title=_text(source, "title", "Observatory scene source"),
        description=_text(source, "description", "Observatory scene source"),
        viewport=viewport,
        star_seed=star_seed,
        star_count=star_count,
        horizon_y=horizon_y,
        planet=planet,
        shooting_stars=tuple(shooting_stars),
        layer_order=tuple(layer_order),
    )
