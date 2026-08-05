from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

SUPPORTED_SCHEMA_VERSION = 2
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
MOTION_DURATION_IDS = ("fast", "standard")

SEMANTIC_ROLE_KINDS: dict[str, dict[str, str]] = {
    "surface": {
        "canvas": "color",
        "depth": "color",
        "panel": "color",
        "elevated": "color",
    },
    "content": {
        "primary": "color",
        "secondary": "color",
        "muted": "color",
        "inverse": "color",
    },
    "signal": {
        "primary": "color",
        "secondary": "color",
        "warning": "color",
        "critical": "color",
        "success": "color",
    },
    "structure": {
        "subtle": "color",
        "strong": "color",
        "focus": "color",
    },
    "font": {
        "content": "font-stack",
        "technical": "font-stack",
    },
    "typeSize": {
        "display": "length",
        "title": "length",
        "heading": "length",
        "body": "length",
        "label": "length",
        "micro": "length",
    },
    "typeWeight": {
        "regular": "font-weight",
        "medium": "font-weight",
        "semibold": "font-weight",
        "bold": "font-weight",
    },
    "tracking": {
        "display": "tracking",
        "heading": "tracking",
        "label": "tracking",
    },
    "spacing": {
        "xs": "length",
        "sm": "length",
        "md": "length",
        "lg": "length",
        "xl": "length",
        "2xl": "length",
        "3xl": "length",
        "4xl": "length",
        "section": "length",
        "safeInset": "length",
        "gutter": "length",
    },
    "radius": {
        "small": "length",
        "medium": "length",
        "large": "length",
        "pill": "length",
    },
    "stroke": {
        "hairline": "length",
        "emphasis": "length",
    },
    "opacity": {
        "subtle": "opacity",
        "muted": "opacity",
        "secondary": "opacity",
        "strong": "opacity",
    },
    "effect": {
        "glowBlur": "length",
        "glowOpacity": "opacity",
    },
    "layout": {
        "contentWidth": "length",
        "columns": "number",
    },
    "motion": {
        "fast": "duration",
        "standard": "duration",
    },
}

TokenValue = str | int | float | tuple[str, ...]


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
class RawDesignToken:
    token_id: str
    kind: str
    value: TokenValue


@dataclass(frozen=True, slots=True)
class SemanticTokenReference:
    reference: str
    resolved_token_id: str
    kind: str


@dataclass(frozen=True, slots=True)
class SemanticTokenGroup:
    group_id: str
    tokens: Mapping[str, SemanticTokenReference]

    def __getitem__(self, role_id: str) -> SemanticTokenReference:
        return self.tokens[role_id]


@dataclass(frozen=True, slots=True)
class DesignTokenSnapshot:
    schema_version: int
    theme_id: str
    colors: tuple[ColorToken, ...]
    font_stack: tuple[str, ...]
    mono_stack: tuple[str, ...]
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
    motion_durations: tuple[NumericToken, ...]
    raw_tokens: Mapping[str, RawDesignToken]
    semantic_groups: Mapping[str, SemanticTokenGroup]
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


def _font_stack(value: object, context: str) -> tuple[str, ...]:
    values = _array(value, context)
    stack: list[str] = []

    for index, font_value in enumerate(values):
        if not isinstance(font_value, str) or not font_value.strip():
            raise DesignTokenError(
                f"{context}[{index}] must contain a non-empty string"
            )
        stack.append(font_value.strip())

    if not stack or len(stack) != len(set(stack)):
        raise DesignTokenError(f"{context} must contain unique values")

    return tuple(stack)


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


def _raw_token_index(
    *,
    colors: tuple[ColorToken, ...],
    font_stack: tuple[str, ...],
    mono_stack: tuple[str, ...],
    type_sizes: tuple[NumericToken, ...],
    type_weights: tuple[NumericToken, ...],
    tracking: tuple[NumericToken, ...],
    spacing_unit: int,
    spacing_steps: tuple[int, ...],
    radii: tuple[NumericToken, ...],
    strokes: tuple[NumericToken, ...],
    opacity: tuple[NumericToken, ...],
    layout: tuple[NumericToken, ...],
    effects: tuple[NumericToken, ...],
    motion_durations: tuple[NumericToken, ...],
) -> Mapping[str, RawDesignToken]:
    records: dict[str, RawDesignToken] = {}

    def add(token_id: str, kind: str, value: TokenValue) -> None:
        if token_id in records:
            raise DesignTokenError(f"Duplicate raw token path: {token_id}")
        records[token_id] = RawDesignToken(token_id, kind, value)

    for color_token in colors:
        add(color_token.token_id, "color", color_token.value)

    add("typography.fontStack", "font-stack", font_stack)
    add("typography.monoStack", "font-stack", mono_stack)

    for type_size_token in type_sizes:
        add(
            f"typography.sizes.{type_size_token.token_id}",
            "length",
            type_size_token.value,
        )
    for type_weight_token in type_weights:
        add(
            f"typography.weights.{type_weight_token.token_id}",
            "font-weight",
            type_weight_token.value,
        )
    for tracking_token in tracking:
        add(
            f"typography.tracking.{tracking_token.token_id}",
            "tracking",
            tracking_token.value,
        )

    add("spacing.unit", "length", spacing_unit)
    for index, value in enumerate(spacing_steps):
        add(f"spacing.steps.{index}", "length", value)

    for radius_token in radii:
        add(
            f"radii.{radius_token.token_id}",
            "length",
            radius_token.value,
        )
    for stroke_token in strokes:
        add(
            f"strokes.{stroke_token.token_id}",
            "length",
            stroke_token.value,
        )
    for opacity_token in opacity:
        add(
            f"opacity.{opacity_token.token_id}",
            "opacity",
            opacity_token.value,
        )

    for layout_token in layout:
        kind = "number" if layout_token.token_id == "columns" else "length"
        add(
            f"layout.{layout_token.token_id}",
            kind,
            layout_token.value,
        )

    for effect_token in effects:
        kind = "opacity" if effect_token.token_id == "glowOpacity" else "length"
        add(
            f"effects.{effect_token.token_id}",
            kind,
            effect_token.value,
        )

    for duration_token in motion_durations:
        add(
            f"motion.duration.{duration_token.token_id}",
            "duration",
            duration_token.value,
        )

    return MappingProxyType(records)


def _semantic_groups(
    value: object,
    raw_tokens: Mapping[str, RawDesignToken],
) -> Mapping[str, SemanticTokenGroup]:
    semantic = _mapping(value, "Design token source.semantic")
    _exact_keys(
        semantic,
        set(SEMANTIC_ROLE_KINDS),
        "Design token source.semantic",
    )

    authored: dict[str, tuple[str, str]] = {}

    for group_id, role_kinds in SEMANTIC_ROLE_KINDS.items():
        context = f"Design token source.semantic.{group_id}"
        group = _mapping(semantic.get(group_id), context)
        _exact_keys(group, set(role_kinds), context)

        for role_id, required_kind in role_kinds.items():
            reference = _text(group, role_id, context)
            authored[f"semantic.{group_id}.{role_id}"] = (
                reference,
                required_kind,
            )

    resolved_cache: dict[str, RawDesignToken] = {}

    def resolve(path: str, stack: tuple[str, ...]) -> RawDesignToken:
        raw = raw_tokens.get(path)
        if raw is not None:
            return raw

        cached = resolved_cache.get(path)
        if cached is not None:
            return cached

        authored_entry = authored.get(path)
        if authored_entry is None:
            origin = stack[0]
            raise DesignTokenError(f"{origin} references unknown token {path}")

        if path in stack:
            cycle_start = stack.index(path)
            cycle = (*stack[cycle_start:], path)
            raise DesignTokenError(f"Semantic reference cycle: {' -> '.join(cycle)}")

        reference, required_kind = authored_entry
        target = resolve(reference, (*stack, path))

        if target.kind != required_kind:
            raise DesignTokenError(
                f"{path} requires a {required_kind} token; "
                f"{reference} resolves to {target.kind}"
            )

        resolved_cache[path] = target
        return target

    groups: dict[str, SemanticTokenGroup] = {}

    for group_id, role_kinds in SEMANTIC_ROLE_KINDS.items():
        references: dict[str, SemanticTokenReference] = {}

        for role_id in role_kinds:
            path = f"semantic.{group_id}.{role_id}"
            reference, required_kind = authored[path]
            target = resolve(path, ())
            references[role_id] = SemanticTokenReference(
                reference=reference,
                resolved_token_id=target.token_id,
                kind=required_kind,
            )

        groups[group_id] = SemanticTokenGroup(
            group_id=group_id,
            tokens=MappingProxyType(references),
        )

    return MappingProxyType(groups)


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
            "motion",
            "semantic",
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
        {"fontStack", "monoStack", "sizes", "weights", "tracking"},
        "Design token source.typography",
    )

    font_stack = _font_stack(
        typography.get("fontStack"),
        "Design token source.typography.fontStack",
    )
    mono_stack = _font_stack(
        typography.get("monoStack"),
        "Design token source.typography.monoStack",
    )

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

    motion_source = _mapping(source.get("motion"), "Design token source.motion")
    _exact_keys(motion_source, {"duration"}, "Design token source.motion")
    motion_durations = _numeric_group(
        motion_source.get("duration"),
        MOTION_DURATION_IDS,
        "Design token source.motion.duration",
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

    duration_values = tuple(float(record.value) for record in motion_durations)
    _strictly(
        duration_values,
        descending=False,
        context="Motion durations",
    )

    if any(value <= 0 or value > 1000 for value in duration_values):
        raise DesignTokenError(
            "Motion durations must be greater than zero and at most 1000 milliseconds"
        )

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

    raw_tokens = _raw_token_index(
        colors=tuple(colors),
        font_stack=font_stack,
        mono_stack=mono_stack,
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
        motion_durations=motion_durations,
    )
    semantic_groups = _semantic_groups(source.get("semantic"), raw_tokens)

    return DesignTokenSnapshot(
        schema_version=schema_version,
        theme_id=theme_id,
        colors=tuple(colors),
        font_stack=font_stack,
        mono_stack=mono_stack,
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
        motion_durations=motion_durations,
        raw_tokens=raw_tokens,
        semantic_groups=semantic_groups,
        motion=motion,
        density=density,
        corner_language=corner_language,
        contrast_pairs=tuple(contrast_pairs),
    )
