from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
COLOR_PATTERN = re.compile(r"#[0-9a-f]{6}")

PALETTE_GROUPS = {
    "background": ("void", "deep", "panel", "panel-raised"),
    "text": ("primary", "secondary", "muted"),
    "accent": ("signal", "orbit", "warning", "critical", "success"),
    "border": ("subtle", "strong"),
}
TYPE_SIZE_IDS = ("display", "title", "heading", "body", "label", "micro")
TYPE_WEIGHT_IDS = ("regular", "medium", "semibold", "bold")
TRACKING_IDS = ("display", "heading", "label")
RADIUS_IDS = ("small", "medium", "large", "pill")
STROKE_IDS = ("hairline", "emphasis")
OPACITY_IDS = ("subtle", "muted", "secondary", "strong")
LAYOUT_IDS = ("canvasWidth", "safeInset", "columns", "gutter", "sectionGap")
EFFECT_IDS = ("glowBlur", "glowOpacity")


class DesignTokenError(ValueError):
    """Raised when authored visual tokens violate their contract."""


@dataclass(frozen=True, slots=True)
class ColorToken:
    token_id: str
    value: str


@dataclass(frozen=True, slots=True)
class NumericToken:
    token_id: str
    value: int | float


@dataclass(frozen=True, slots=True)
class ContrastPair:
    foreground: str
    background: str
    minimum: float
    actual: float


@dataclass(frozen=True, slots=True)
class DesignTokenSnapshot:
    schema_version: int
    theme_id: str
    colors: tuple[ColorToken, ...]
    font_stack: tuple[str, ...]
    type_sizes: tuple[NumericToken, ...]
    type_weights: tuple[NumericToken, ...]
    tracking: tuple[NumericToken, ...]
    spacing_unit: int
    spacing_steps: tuple[int, ...]
    radii: tuple[NumericToken, ...]
    strokes: tuple[NumericToken, ...]
    opacity: tuple[NumericToken, ...]
    layout: tuple[NumericToken, ...]
    effects: tuple[NumericToken, ...]
    motion: str
    density: str
    corner_language: str
    contrast_pairs: tuple[ContrastPair, ...]


def _mapping(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DesignTokenError(f"{context} must contain a JSON object")

    return cast(dict[str, object], value)


def _array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise DesignTokenError(f"{context} must contain a JSON array")

    return cast(list[object], value)


def _exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    missing = sorted(expected - set(source))
    unexpected = sorted(set(source) - expected)

    if missing:
        raise DesignTokenError(f"{context} is missing fields: {', '.join(missing)}")

    if unexpected:
        raise DesignTokenError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def _text(source: dict[str, object], field: str, context: str) -> str:
    value = source.get(field)

    if not isinstance(value, str) or not value.strip():
        raise DesignTokenError(f"{context}.{field} must contain a non-empty string")

    return value.strip()


def _integer(source: dict[str, object], field: str, context: str) -> int:
    value = source.get(field)

    if isinstance(value, bool) or not isinstance(value, int):
        raise DesignTokenError(f"{context}.{field} must contain an integer")

    return value


def _number(source: dict[str, object], field: str, context: str) -> float:
    value = source.get(field)

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DesignTokenError(f"{context}.{field} must contain a number")

    return float(value)


def _numeric_group(
    value: object,
    identifiers: tuple[str, ...],
    context: str,
) -> tuple[NumericToken, ...]:
    source = _mapping(value, context)
    _exact_keys(source, set(identifiers), context)

    records: list[NumericToken] = []

    for identifier in identifiers:
        raw = source.get(identifier)

        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise DesignTokenError(f"{context}.{identifier} must contain a number")

        records.append(NumericToken(identifier, raw))

    return tuple(records)


def _strictly(values: tuple[float, ...], *, descending: bool, context: str) -> None:
    pairs = zip(values, values[1:], strict=False)
    valid = (
        all(left > right for left, right in pairs)
        if descending
        else all(left < right for left, right in pairs)
    )

    if not valid:
        direction = "descending" if descending else "increasing"
        raise DesignTokenError(f"{context} must be strictly {direction}")


def _channel(value: int) -> float:
    normalized = value / 255
    return (
        normalized / 12.92
        if normalized <= 0.04045
        else ((normalized + 0.055) / 1.055) ** 2.4
    )


def _luminance(color: str) -> float:
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def _contrast(foreground: str, background: str) -> float:
    first = _luminance(foreground)
    second = _luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def load_design_token_snapshot(path: Path) -> DesignTokenSnapshot:
    source = _mapping(
        json.loads(path.read_text(encoding="utf-8")),
        "Design token source",
    )
    _exact_keys(
        source,
        {
            "schemaVersion",
            "themeId",
            "palette",
            "typography",
            "spacing",
            "radii",
            "strokes",
            "opacity",
            "layout",
            "effects",
            "rules",
        },
        "Design token source",
    )

    schema_version = _integer(source, "schemaVersion", "Design token source")

    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise DesignTokenError(
            f"Unsupported design token schemaVersion: {schema_version}"
        )

    theme_id = _text(source, "themeId", "Design token source")

    if IDENTIFIER_PATTERN.fullmatch(theme_id) is None:
        raise DesignTokenError(
            "Design token source.themeId must use lowercase kebab-case"
        )

    palette = _mapping(source.get("palette"), "Design token source.palette")
    _exact_keys(palette, set(PALETTE_GROUPS), "Design token source.palette")
    colors: list[ColorToken] = []

    for group_id, token_ids in PALETTE_GROUPS.items():
        group = _mapping(
            palette.get(group_id),
            f"Design token source.palette.{group_id}",
        )
        _exact_keys(
            group,
            set(token_ids),
            f"Design token source.palette.{group_id}",
        )

        for token_id in token_ids:
            value = _text(
                group,
                token_id,
                f"Design token source.palette.{group_id}",
            )

            if COLOR_PATTERN.fullmatch(value) is None:
                raise DesignTokenError(
                    f"palette.{group_id}.{token_id} must use lowercase six-digit hex"
                )

            colors.append(ColorToken(f"{group_id}.{token_id}", value))

    typography = _mapping(
        source.get("typography"),
        "Design token source.typography",
    )
    _exact_keys(
        typography,
        {"fontStack", "sizes", "weights", "tracking"},
        "Design token source.typography",
    )

    font_values = _array(
        typography.get("fontStack"),
        "Design token source.typography.fontStack",
    )
    font_stack: list[str] = []

    for index, font_value in enumerate(font_values):
        if not isinstance(font_value, str) or not font_value.strip():
            raise DesignTokenError(
                "Design token source.typography.fontStack"
                f"[{index}] must contain a non-empty string"
            )
        font_stack.append(font_value.strip())

    if not font_stack or len(font_stack) != len(set(font_stack)):
        raise DesignTokenError("Typography fontStack must contain unique values")

    type_sizes = _numeric_group(
        typography.get("sizes"),
        TYPE_SIZE_IDS,
        "Design token source.typography.sizes",
    )
    type_weights = _numeric_group(
        typography.get("weights"),
        TYPE_WEIGHT_IDS,
        "Design token source.typography.weights",
    )
    tracking = _numeric_group(
        typography.get("tracking"),
        TRACKING_IDS,
        "Design token source.typography.tracking",
    )

    _strictly(
        tuple(float(record.value) for record in type_sizes),
        descending=True,
        context="Typography sizes",
    )
    _strictly(
        tuple(float(record.value) for record in type_weights),
        descending=False,
        context="Typography weights",
    )

    spacing = _mapping(source.get("spacing"), "Design token source.spacing")
    _exact_keys(spacing, {"unit", "steps"}, "Design token source.spacing")
    spacing_unit = _integer(spacing, "unit", "Design token source.spacing")

    if spacing_unit <= 0:
        raise DesignTokenError("Spacing unit must be positive")

    step_values = _array(spacing.get("steps"), "Design token source.spacing.steps")
    spacing_steps: list[int] = []

    for index, step_value in enumerate(step_values):
        if (
            isinstance(step_value, bool)
            or not isinstance(step_value, int)
            or step_value <= 0
        ):
            raise DesignTokenError(
                f"Design token source.spacing.steps[{index}] must be a positive integer"
            )
        spacing_steps.append(step_value)

    _strictly(
        tuple(float(value) for value in spacing_steps),
        descending=False,
        context="Spacing steps",
    )

    if spacing_steps[0] != spacing_unit or any(
        value % spacing_unit != 0 for value in spacing_steps
    ):
        raise DesignTokenError("Spacing steps must start at and align to the unit")

    radii = _numeric_group(source.get("radii"), RADIUS_IDS, "Design token source.radii")
    strokes = _numeric_group(
        source.get("strokes"),
        STROKE_IDS,
        "Design token source.strokes",
    )
    opacity = _numeric_group(
        source.get("opacity"),
        OPACITY_IDS,
        "Design token source.opacity",
    )
    layout = _numeric_group(
        source.get("layout"),
        LAYOUT_IDS,
        "Design token source.layout",
    )
    effects = _numeric_group(
        source.get("effects"),
        EFFECT_IDS,
        "Design token source.effects",
    )

    if any(float(record.value) <= 0 for record in radii + strokes):
        raise DesignTokenError("Radii and strokes must be positive")

    opacity_values = tuple(float(record.value) for record in opacity)
    _strictly(opacity_values, descending=False, context="Opacity values")

    if any(value <= 0 or value > 1 for value in opacity_values):
        raise DesignTokenError(
            "Opacity values must be greater than zero and at most one"
        )

    layout_values = {record.token_id: int(record.value) for record in layout}

    if not 960 <= layout_values["canvasWidth"] <= 1600:
        raise DesignTokenError("Layout canvasWidth must be between 960 and 1600")
    if layout_values["columns"] != 12:
        raise DesignTokenError("Layout columns must equal 12")
    if layout_values["safeInset"] * 2 >= layout_values["canvasWidth"]:
        raise DesignTokenError("Layout safeInset leaves no usable canvas width")

    effect_values = {record.token_id: float(record.value) for record in effects}

    if not 0 <= effect_values["glowBlur"] <= 32:
        raise DesignTokenError("effects.glowBlur must be between zero and 32")
    if not 0 <= effect_values["glowOpacity"] <= 1:
        raise DesignTokenError("effects.glowOpacity must be between zero and one")

    rules = _mapping(source.get("rules"), "Design token source.rules")
    _exact_keys(
        rules,
        {"motion", "density", "cornerLanguage", "contrastPairs"},
        "Design token source.rules",
    )
    motion = _text(rules, "motion", "Design token source.rules")
    density = _text(rules, "density", "Design token source.rules")
    corner_language = _text(rules, "cornerLanguage", "Design token source.rules")

    if motion != "static-github":
        raise DesignTokenError(f"Unsupported motion policy: {motion}")
    if density != "editorial":
        raise DesignTokenError(f"Unsupported density policy: {density}")
    if corner_language != "soft-technical":
        raise DesignTokenError(f"Unsupported corner language: {corner_language}")

    color_values = {record.token_id: record.value for record in colors}
    pair_values = _array(
        rules.get("contrastPairs"),
        "Design token source.rules.contrastPairs",
    )
    contrast_pairs: list[ContrastPair] = []
    seen_pairs: set[tuple[str, str]] = set()

    for index, pair_value in enumerate(pair_values):
        context = f"Design token source.rules.contrastPairs[{index}]"
        pair = _mapping(pair_value, context)
        _exact_keys(pair, {"foreground", "background", "minimum"}, context)
        foreground = _text(pair, "foreground", context)
        background = _text(pair, "background", context)
        minimum = _number(pair, "minimum", context)

        for color_id in (foreground, background):
            if color_id not in color_values:
                raise DesignTokenError(f"Unknown contrast color: {color_id}")

        pair_id = (foreground, background)

        if pair_id in seen_pairs:
            raise DesignTokenError(
                f"Duplicate contrast pair: {foreground} on {background}"
            )

        seen_pairs.add(pair_id)
        actual = _contrast(color_values[foreground], color_values[background])

        if minimum <= 1 or minimum > 21:
            raise DesignTokenError(f"{context}.minimum must be between one and 21")
        if actual < minimum:
            raise DesignTokenError(
                f"Contrast {foreground} on {background} does not meet minimum "
                f"{minimum:.1f}; actual {actual:.3f}"
            )

        contrast_pairs.append(
            ContrastPair(
                foreground=foreground,
                background=background,
                minimum=minimum,
                actual=actual,
            )
        )

    if not contrast_pairs:
        raise DesignTokenError("At least one contrast pair is required")

    return DesignTokenSnapshot(
        schema_version=schema_version,
        theme_id=theme_id,
        colors=tuple(colors),
        font_stack=tuple(font_stack),
        type_sizes=type_sizes,
        type_weights=type_weights,
        tracking=tracking,
        spacing_unit=spacing_unit,
        spacing_steps=tuple(spacing_steps),
        radii=radii,
        strokes=strokes,
        opacity=opacity,
        layout=layout,
        effects=effects,
        motion=motion,
        density=density,
        corner_language=corner_language,
        contrast_pairs=tuple(contrast_pairs),
    )
