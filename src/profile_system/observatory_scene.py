from __future__ import annotations

import math
import random
import xml.etree.ElementTree as element_tree

from profile_system.design_tokens import DesignTokenSnapshot, NumericToken
from profile_system.scene import ObservatorySceneSnapshot
from profile_system.svg_kernel import GradientStop, SvgDocument, SvgKernelError


def _color(tokens: DesignTokenSnapshot, token_id: str) -> str:
    for token in tokens.colors:
        if token.token_id == token_id:
            return token.value
    raise SvgKernelError(f"Missing color token: {token_id}")


def _numeric(records: tuple[NumericToken, ...], token_id: str) -> int | float:
    for token in records:
        if token.token_id == token_id:
            return token.value
    raise SvgKernelError(f"Missing numeric token: {token_id}")


def _font_stack(tokens: DesignTokenSnapshot) -> str:
    return ", ".join(tokens.font_stack)


def _point_from_angle(
    x: float,
    y: float,
    length: float,
    angle: float,
) -> tuple[float, float]:
    radians = math.radians(angle)
    return (
        x + math.cos(radians) * length,
        y + math.sin(radians) * length,
    )


def _text(
    document: SvgDocument,
    parent: element_tree.Element,
    *,
    x: int,
    y: int,
    value: str,
    fill: str,
    size: int | float,
    weight: int | float,
    family: str,
    tracking: int | float = 0,
    anchor: str | None = None,
) -> None:
    attributes: dict[str, str | int | float] = {
        "fill": fill,
        "font-family": family,
        "font-size": size,
        "font-weight": weight,
        "letter-spacing": tracking,
        "x": x,
        "y": y,
    }
    if anchor is not None:
        attributes["text-anchor"] = anchor
    document.element(parent, "text", attributes, text=value)


def render_observatory_scene(
    scene: ObservatorySceneSnapshot,
    tokens: DesignTokenSnapshot,
) -> str:
    if scene.theme_id != tokens.theme_id:
        raise SvgKernelError(
            "Observatory scene theme does not match the design-token theme"
        )

    width = scene.viewport.width
    height = scene.viewport.height
    planet = scene.planet
    font_family = _font_stack(tokens)

    background_void = _color(tokens, "background.void")
    background_deep = _color(tokens, "background.deep")
    panel = _color(tokens, "background.panel")
    panel_raised = _color(tokens, "background.panel-raised")
    text_primary = _color(tokens, "text.primary")
    text_secondary = _color(tokens, "text.secondary")
    text_muted = _color(tokens, "text.muted")
    signal = _color(tokens, "accent.signal")
    orbit = _color(tokens, "accent.orbit")
    warning = _color(tokens, "accent.warning")
    border_subtle = _color(tokens, "border.subtle")
    border_strong = _color(tokens, "border.strong")

    label_size = _numeric(tokens.type_sizes, "label")
    micro_size = _numeric(tokens.type_sizes, "micro")
    heading_size = _numeric(tokens.type_sizes, "heading")
    regular_weight = _numeric(tokens.type_weights, "regular")
    medium_weight = _numeric(tokens.type_weights, "medium")
    semibold_weight = _numeric(tokens.type_weights, "semibold")
    label_tracking = _numeric(tokens.tracking, "label")
    large_radius = _numeric(tokens.radii, "large")
    medium_radius = _numeric(tokens.radii, "medium")
    glow_blur = _numeric(tokens.effects, "glowBlur")

    document = SvgDocument(
        width=width,
        height=height,
        title=scene.title,
        description=scene.description,
    )

    document.define_linear_gradient(
        "scene-background-gradient",
        stops=(
            GradientStop("0%", background_void),
            GradientStop("58%", background_deep),
            GradientStop("100%", panel),
        ),
        x1="0%",
        y1="0%",
        x2="100%",
        y2="100%",
    )
    document.define_radial_gradient(
        "scene-planet-gradient",
        stops=(
            GradientStop("0%", text_primary, 0.98),
            GradientStop("38%", signal, 0.86),
            GradientStop("72%", orbit, 0.62),
            GradientStop("100%", background_deep, 0.94),
        ),
        cx="34%",
        cy="28%",
        radius="72%",
    )
    document.define_linear_gradient(
        "scene-ring-gradient",
        stops=(
            GradientStop("0%", orbit, 0.16),
            GradientStop("48%", signal, 0.78),
            GradientStop("100%", text_primary, 0.12),
        ),
    )
    document.define_linear_gradient(
        "scene-console-gradient",
        stops=(
            GradientStop("0%", panel_raised, 0.96),
            GradientStop("100%", background_void, 0.98),
        ),
        x1="0%",
        y1="0%",
        x2="0%",
        y2="100%",
    )
    document.define_glow_filter("scene-signal-glow", blur=glow_blur)
    document.define_glow_filter("scene-planet-glow", blur=float(glow_blur) * 1.6)

    background = document.element(
        document.root,
        "g",
        {"data-layer": "background", "id": "scene-background"},
    )
    document.element(
        background,
        "rect",
        {
            "fill": "url(#scene-background-gradient)",
            "height": height,
            "width": width,
            "x": 0,
            "y": 0,
        },
    )
    document.element(
        background,
        "circle",
        {
            "cx": width * 0.18,
            "cy": height * 0.16,
            "fill": orbit,
            "opacity": 0.05,
            "r": width * 0.2,
        },
    )

    stars = document.element(
        document.root,
        "g",
        {"data-layer": "stars", "id": "scene-stars"},
    )
    generator = random.Random(scene.star_seed)
    for _ in range(scene.star_count):
        x = generator.randint(44, width - 44)
        y = generator.randint(28, scene.horizon_y - 72)
        radius = 1 if generator.random() < 0.88 else 2
        opacity = 0.28 + generator.random() * 0.62
        fill = signal if generator.random() < 0.18 else text_primary
        document.element(
            stars,
            "circle",
            {
                "cx": x,
                "cy": y,
                "fill": fill,
                "opacity": opacity,
                "r": radius,
            },
        )

    for shooting_star in scene.shooting_stars:
        end_x, end_y = _point_from_angle(
            shooting_star.x,
            shooting_star.y,
            shooting_star.length,
            shooting_star.angle,
        )
        document.element(
            stars,
            "line",
            {
                "filter": "url(#scene-signal-glow)",
                "opacity": shooting_star.opacity,
                "stroke": signal,
                "stroke-linecap": "round",
                "stroke-width": 2,
                "x1": shooting_star.x,
                "x2": end_x,
                "y1": shooting_star.y,
                "y2": end_y,
            },
        )
        tail_x, tail_y = _point_from_angle(
            shooting_star.x,
            shooting_star.y,
            shooting_star.length * 1.35,
            shooting_star.angle,
        )
        document.element(
            stars,
            "line",
            {
                "opacity": shooting_star.opacity * 0.24,
                "stroke": orbit,
                "stroke-linecap": "round",
                "stroke-width": 1,
                "x1": shooting_star.x,
                "x2": tail_x,
                "y1": shooting_star.y,
                "y2": tail_y,
            },
        )

    window = document.element(
        document.root,
        "g",
        {"data-layer": "window", "id": "scene-window"},
    )
    document.element(
        window,
        "path",
        {
            "d": (
                f"M 72 {scene.horizon_y} L 72 96 "
                f"Q {width // 2} 18 {width - 72} 96 "
                f"L {width - 72} {scene.horizon_y}"
            ),
            "fill": "none",
            "stroke": border_strong,
            "stroke-opacity": 0.88,
            "stroke-width": 2,
        },
    )
    document.element(
        window,
        "path",
        {
            "d": (
                f"M 92 {scene.horizon_y - 10} L 92 112 "
                f"Q {width // 2} 42 {width - 92} 112 "
                f"L {width - 92} {scene.horizon_y - 10}"
            ),
            "fill": "none",
            "stroke": border_subtle,
            "stroke-opacity": 0.72,
            "stroke-width": 1,
        },
    )
    for x in (210, 390, 810, 990):
        document.element(
            window,
            "line",
            {
                "opacity": 0.62,
                "stroke": border_subtle,
                "stroke-width": 1,
                "x1": x,
                "x2": x,
                "y1": 92,
                "y2": scene.horizon_y,
            },
        )

    planet_group = document.element(
        document.root,
        "g",
        {"data-layer": "planet", "id": "scene-planet"},
    )
    rotation = f"rotate({planet.ring_angle} {planet.center_x} {planet.center_y})"
    document.element(
        planet_group,
        "ellipse",
        {
            "cx": planet.center_x,
            "cy": planet.center_y,
            "fill": "none",
            "opacity": 0.64,
            "rx": planet.ring_radius_x,
            "ry": planet.ring_radius_y,
            "stroke": "url(#scene-ring-gradient)",
            "stroke-width": 18,
            "transform": rotation,
        },
    )
    document.element(
        planet_group,
        "circle",
        {
            "cx": planet.center_x,
            "cy": planet.center_y,
            "fill": "url(#scene-planet-gradient)",
            "filter": "url(#scene-planet-glow)",
            "r": planet.radius,
        },
    )
    document.element(
        planet_group,
        "circle",
        {
            "cx": planet.center_x - planet.radius * 0.28,
            "cy": planet.center_y - planet.radius * 0.22,
            "fill": text_primary,
            "opacity": 0.12,
            "r": planet.radius * 0.34,
        },
    )
    front_arc = (
        f"M {planet.center_x - planet.ring_radius_x} {planet.center_y} "
        f"A {planet.ring_radius_x} {planet.ring_radius_y} 0 0 0 "
        f"{planet.center_x + planet.ring_radius_x} {planet.center_y}"
    )
    document.element(
        planet_group,
        "path",
        {
            "d": front_arc,
            "fill": "none",
            "opacity": 0.92,
            "stroke": "url(#scene-ring-gradient)",
            "stroke-linecap": "round",
            "stroke-width": 9,
            "transform": rotation,
        },
    )

    architecture = document.element(
        document.root,
        "g",
        {"data-layer": "architecture", "id": "scene-architecture"},
    )
    document.element(
        architecture,
        "path",
        {
            "d": (
                f"M 0 0 L 166 0 L 112 {height} L 0 {height} Z "
                f"M {width} 0 L {width - 166} 0 L {width - 112} {height} "
                f"L {width} {height} Z"
            ),
            "fill": panel,
            "opacity": 0.94,
        },
    )
    for x, direction in ((84, 1), (width - 84, -1)):
        document.element(
            architecture,
            "line",
            {
                "stroke": signal,
                "stroke-opacity": 0.24,
                "stroke-width": 2,
                "x1": x,
                "x2": x + direction * 34,
                "y1": 132,
                "y2": scene.horizon_y - 28,
            },
        )

    console = document.element(
        document.root,
        "g",
        {"data-layer": "console", "id": "scene-console"},
    )
    document.element(
        console,
        "path",
        {
            "d": (
                f"M 0 {scene.horizon_y - 6} L {width} {scene.horizon_y - 6} "
                f"L {width} {height} L 0 {height} Z"
            ),
            "fill": "url(#scene-console-gradient)",
        },
    )
    document.element(
        console,
        "path",
        {
            "d": (
                f"M 180 {height} L 300 {scene.horizon_y + 40} "
                f"L {width - 300} {scene.horizon_y + 40} "
                f"L {width - 180} {height} Z"
            ),
            "fill": panel_raised,
            "stroke": border_strong,
            "stroke-width": 1,
        },
    )
    document.element(
        console,
        "ellipse",
        {
            "cx": width / 2,
            "cy": scene.horizon_y + 78,
            "fill": orbit,
            "filter": "url(#scene-signal-glow)",
            "opacity": 0.18,
            "rx": 152,
            "ry": 34,
        },
    )
    document.element(
        console,
        "ellipse",
        {
            "cx": width / 2,
            "cy": scene.horizon_y + 78,
            "fill": "none",
            "rx": 152,
            "ry": 34,
            "stroke": signal,
            "stroke-opacity": 0.72,
            "stroke-width": 2,
        },
    )
    for x in range(width // 2 - 112, width // 2 + 113, 56):
        document.element(
            console,
            "line",
            {
                "opacity": 0.3,
                "stroke": signal,
                "stroke-width": 1,
                "x1": x,
                "x2": x,
                "y1": scene.horizon_y + 48,
                "y2": scene.horizon_y + 108,
            },
        )

    atmosphere = document.element(
        document.root,
        "g",
        {
            "data-layer": "atmosphere",
            "id": "scene-atmosphere",
            "opacity": 0.72,
        },
    )
    document.element(
        atmosphere,
        "line",
        {
            "stroke": signal,
            "stroke-opacity": 0.24,
            "stroke-width": 1,
            "x1": 132,
            "x2": width - 132,
            "y1": scene.horizon_y - 6,
            "y2": scene.horizon_y - 6,
        },
    )
    document.element(
        atmosphere,
        "ellipse",
        {
            "cx": width / 2,
            "cy": scene.horizon_y + 70,
            "fill": signal,
            "opacity": 0.05,
            "rx": width * 0.32,
            "ry": 92,
        },
    )

    foreground = document.element(
        document.root,
        "g",
        {"data-layer": "foreground", "id": "scene-foreground"},
    )
    document.element(
        foreground,
        "rect",
        {
            "fill": panel,
            "height": 104,
            "rx": medium_radius,
            "stroke": border_subtle,
            "stroke-width": 1,
            "width": 248,
            "x": 132,
            "y": height - 132,
        },
    )
    _text(
        document,
        foreground,
        x=156,
        y=height - 98,
        value="OBSERVATORY ARRAY",
        fill=signal,
        size=micro_size,
        weight=semibold_weight,
        family=font_family,
        tracking=label_tracking,
    )
    _text(
        document,
        foreground,
        x=156,
        y=height - 64,
        value="PLANETARY WINDOW ONLINE",
        fill=text_primary,
        size=label_size,
        weight=medium_weight,
        family=font_family,
    )
    _text(
        document,
        foreground,
        x=156,
        y=height - 38,
        value=f"SEED {scene.star_seed} // {scene.star_count} STARS",
        fill=text_muted,
        size=micro_size,
        weight=regular_weight,
        family=font_family,
        tracking=label_tracking,
    )

    document.element(
        foreground,
        "rect",
        {
            "fill": panel,
            "height": 104,
            "rx": large_radius,
            "stroke": border_subtle,
            "stroke-width": 1,
            "width": 248,
            "x": width - 380,
            "y": height - 132,
        },
    )
    _text(
        document,
        foreground,
        x=width - 356,
        y=height - 98,
        value="SCENE SYSTEM // M09",
        fill=orbit,
        size=micro_size,
        weight=semibold_weight,
        family=font_family,
        tracking=label_tracking,
    )
    _text(
        document,
        foreground,
        x=width - 356,
        y=height - 64,
        value="STATIC GITHUB SURFACE",
        fill=text_primary,
        size=label_size,
        weight=medium_weight,
        family=font_family,
    )
    _text(
        document,
        foreground,
        x=width - 356,
        y=height - 38,
        value="TOKEN-DRIVEN // DETERMINISTIC",
        fill=text_muted,
        size=micro_size,
        weight=regular_weight,
        family=font_family,
        tracking=label_tracking,
    )

    _text(
        document,
        foreground,
        x=width // 2,
        y=44,
        value="PLANETARY OBSERVATORY",
        fill=text_secondary,
        size=heading_size,
        weight=semibold_weight,
        family=font_family,
        tracking=label_tracking,
        anchor="middle",
    )
    _text(
        document,
        foreground,
        x=width // 2,
        y=68,
        value="DEEP-SPACE ENGINEERING INTERFACE",
        fill=warning,
        size=micro_size,
        weight=medium_weight,
        family=font_family,
        tracking=label_tracking,
        anchor="middle",
    )

    return document.serialize()
