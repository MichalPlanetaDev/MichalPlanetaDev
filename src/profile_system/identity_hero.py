from __future__ import annotations

import re
import textwrap
import xml.etree.ElementTree as element_tree
from collections.abc import Mapping

from profile_system.design_tokens import DesignTokenSnapshot, NumericToken
from profile_system.hero import HeroDataError, IdentityHeroSnapshot
from profile_system.model import ProfileSnapshot
from profile_system.observatory_scene import render_observatory_scene
from profile_system.scene import ObservatorySceneSnapshot
from profile_system.svg_kernel import SVG_NAMESPACE

REFERENCE_PATTERN = re.compile(r"url\(#([a-z0-9-]+)\)")
FORBIDDEN_ELEMENTS = frozenset(
    {
        "animate",
        "animateMotion",
        "animateTransform",
        "foreignObject",
        "image",
        "script",
        "set",
    }
)


def _tag(name: str) -> str:
    return f"{{{SVG_NAMESPACE}}}{name}"


def _color(tokens: DesignTokenSnapshot, token_id: str) -> str:
    for token in tokens.colors:
        if token.token_id == token_id:
            return token.value
    raise HeroDataError(f"Missing hero color token: {token_id}")


def _numeric(records: tuple[NumericToken, ...], token_id: str) -> int | float:
    for token in records:
        if token.token_id == token_id:
            return token.value
    raise HeroDataError(f"Missing hero numeric token: {token_id}")


def _scalar(value: str | int | float) -> str:
    if isinstance(value, float):
        return format(value, ".6g")
    return str(value)


def _element(
    parent: element_tree.Element,
    name: str,
    attributes: Mapping[str, str | int | float],
    *,
    text: str | None = None,
) -> element_tree.Element:
    node = element_tree.SubElement(
        parent,
        _tag(name),
        {key: _scalar(value) for key, value in sorted(attributes.items())},
    )
    if text is not None:
        node.text = text
    return node


def _text(
    parent: element_tree.Element,
    *,
    identifier: str,
    x: int,
    y: int,
    value: str,
    fill: str,
    size: int | float,
    weight: int | float,
    family: str,
    tracking: int | float = 0,
) -> element_tree.Element:
    return _element(
        parent,
        "text",
        {
            "fill": fill,
            "font-family": family,
            "font-size": size,
            "font-weight": weight,
            "id": identifier,
            "letter-spacing": tracking,
            "x": x,
            "y": y,
        },
        text=value,
    )


def _role_lines(value: str) -> tuple[str, ...]:
    lines = textwrap.wrap(
        value,
        width=58,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(lines) <= 2:
        return tuple(lines)
    return (lines[0], " ".join(lines[1:]))


def _validate_composition(root: element_tree.Element) -> None:
    identifiers: list[str] = []
    references: set[str] = set()

    for node in root.iter():
        name = node.tag.rsplit("}", 1)[-1]
        if name in FORBIDDEN_ELEMENTS:
            raise HeroDataError(f"Forbidden identity hero element: {name}")

        identifier = node.attrib.get("id")
        if identifier is not None:
            identifiers.append(identifier)

        for attribute_name, value in node.attrib.items():
            local_name = attribute_name.rsplit("}", 1)[-1]
            if local_name.lower().startswith("on"):
                raise HeroDataError(
                    f"Forbidden identity hero event attribute: {local_name}"
                )
            if local_name == "href":
                raise HeroDataError("Identity hero must not contain href")
            references.update(REFERENCE_PATTERN.findall(value))

    identifier_set = set(identifiers)
    if len(identifiers) != len(identifier_set):
        raise HeroDataError("Identity hero contains duplicate identifiers")
    if not references.issubset(identifier_set):
        unresolved = sorted(references - identifier_set)
        raise HeroDataError(
            "Identity hero contains unresolved references: " + ", ".join(unresolved)
        )

    required = {
        "hero-identity",
        "hero-identity-panel",
        "hero-identity-headline",
        "hero-identity-name",
        "hero-identity-motto",
        "hero-status",
    }
    if not required.issubset(identifier_set):
        missing = sorted(required - identifier_set)
        raise HeroDataError(
            "Identity hero is missing required identifiers: " + ", ".join(missing)
        )


def render_identity_hero(
    profile: ProfileSnapshot,
    scene: ObservatorySceneSnapshot,
    tokens: DesignTokenSnapshot,
    hero: IdentityHeroSnapshot,
) -> str:
    if hero.profile_id != profile.profile_id:
        raise HeroDataError("Identity hero profileId does not match the profile")
    if hero.scene_id != scene.scene_id:
        raise HeroDataError("Identity hero sceneId does not match the scene")
    if profile.environment_id != scene.scene_id:
        raise HeroDataError("Profile environmentId does not match the scene")
    if hero.theme_id != scene.theme_id or hero.theme_id != tokens.theme_id:
        raise HeroDataError("Identity hero themeId does not match its dependencies")
    if (
        hero.viewport.width != scene.viewport.width
        or hero.viewport.height != scene.viewport.height
    ):
        raise HeroDataError("Identity hero viewport does not match the scene")

    root = element_tree.fromstring(render_observatory_scene(scene, tokens))
    title = root.find(_tag("title"))
    description = root.find(_tag("desc"))
    if title is None or description is None:
        raise HeroDataError("Base observatory scene lacks accessible metadata")

    title.text = f"{profile.display_name} — {profile.identity.headline}"
    description.text = (
        f"Identity hero for {profile.display_name}. "
        f"{profile.identity.role} {profile.identity.motto}"
    )

    panel_color = _color(tokens, "background.panel")
    raised_color = _color(tokens, "background.panel-raised")
    text_primary = _color(tokens, "text.primary")
    text_secondary = _color(tokens, "text.secondary")
    text_muted = _color(tokens, "text.muted")
    signal = _color(tokens, "accent.signal")
    orbit = _color(tokens, "accent.orbit")
    border_subtle = _color(tokens, "border.subtle")
    border_strong = _color(tokens, "border.strong")
    font_family = ", ".join(tokens.font_stack)

    display_size = min(float(_numeric(tokens.type_sizes, "display")), 52.0)
    body_size = _numeric(tokens.type_sizes, "body")
    label_size = _numeric(tokens.type_sizes, "label")
    micro_size = _numeric(tokens.type_sizes, "micro")
    regular_weight = _numeric(tokens.type_weights, "regular")
    medium_weight = _numeric(tokens.type_weights, "medium")
    semibold_weight = _numeric(tokens.type_weights, "semibold")
    bold_weight = _numeric(tokens.type_weights, "bold")
    label_tracking = _numeric(tokens.tracking, "label")
    large_radius = _numeric(tokens.radii, "large")

    children = list(root)
    foreground = next(
        (node for node in children if node.attrib.get("id") == "scene-foreground"),
        None,
    )
    if foreground is None:
        raise HeroDataError("Base observatory scene lacks its foreground layer")
    insertion_index = children.index(foreground)

    panel = hero.panel
    identity = element_tree.Element(
        _tag("g"),
        {"data-layer": "identity", "id": "hero-identity"},
    )
    _element(
        identity,
        "rect",
        {
            "fill": panel_color,
            "fill-opacity": 0.9,
            "height": panel.height,
            "id": "hero-identity-panel",
            "rx": large_radius,
            "stroke": border_strong,
            "stroke-opacity": 0.86,
            "stroke-width": 1,
            "width": panel.width,
            "x": panel.x,
            "y": panel.y,
        },
    )
    _element(
        identity,
        "rect",
        {
            "fill": raised_color,
            "height": 42,
            "opacity": 0.72,
            "rx": large_radius,
            "width": panel.width,
            "x": panel.x,
            "y": panel.y,
        },
    )
    _element(
        identity,
        "line",
        {
            "filter": "url(#scene-signal-glow)",
            "stroke": signal,
            "stroke-linecap": "round",
            "stroke-width": 2,
            "x1": panel.x + 24,
            "x2": panel.x + 172,
            "y1": panel.y,
            "y2": panel.y,
        },
    )
    _text(
        identity,
        identifier="hero-identity-headline",
        x=panel.x + 28,
        y=panel.y + 27,
        value=profile.identity.headline,
        fill=signal,
        size=micro_size,
        weight=semibold_weight,
        family=font_family,
        tracking=label_tracking,
    )
    _text(
        identity,
        identifier="hero-identity-name",
        x=panel.x + 28,
        y=panel.y + 102,
        value=profile.display_name.upper(),
        fill=text_primary,
        size=display_size,
        weight=bold_weight,
        family=font_family,
        tracking=-1.2,
    )

    for index, line in enumerate(_role_lines(profile.identity.role), start=1):
        _text(
            identity,
            identifier=f"hero-identity-role-{index}",
            x=panel.x + 30,
            y=panel.y + 145 + (index - 1) * 24,
            value=line,
            fill=text_secondary,
            size=body_size,
            weight=regular_weight,
            family=font_family,
        )

    _element(
        identity,
        "line",
        {
            "stroke": border_subtle,
            "stroke-width": 1,
            "x1": panel.x + 28,
            "x2": panel.x + panel.width - 28,
            "y1": panel.y + 208,
            "y2": panel.y + 208,
        },
    )
    _text(
        identity,
        identifier="hero-identity-motto",
        x=panel.x + 30,
        y=panel.y + 241,
        value=profile.identity.motto,
        fill=text_muted,
        size=label_size,
        weight=medium_weight,
        family=font_family,
    )
    _text(
        identity,
        identifier="hero-identity-node",
        x=panel.x + 30,
        y=panel.y + 270,
        value=f"PROFILE NODE // {profile.profile_id.upper()}",
        fill=orbit,
        size=micro_size,
        weight=semibold_weight,
        family=font_family,
        tracking=label_tracking,
    )

    status = element_tree.Element(
        _tag("g"),
        {"data-layer": "status", "id": "hero-status"},
    )
    status_y = scene.horizon_y - 28
    _element(
        status,
        "rect",
        {
            "fill": panel_color,
            "height": 34,
            "opacity": 0.84,
            "rx": 17,
            "stroke": border_subtle,
            "stroke-width": 1,
            "width": 512,
            "x": 344,
            "y": status_y,
        },
    )
    _text(
        status,
        identifier="hero-status-left",
        x=370,
        y=status_y + 22,
        value="RENDERING / SYSTEMS / AUTOMATION / TECHNICAL DESIGN",
        fill=text_secondary,
        size=micro_size,
        weight=medium_weight,
        family=font_family,
        tracking=label_tracking,
    )
    _text(
        status,
        identifier="hero-status-right",
        x=758,
        y=status_y + 22,
        value="ONLINE",
        fill=signal,
        size=micro_size,
        weight=semibold_weight,
        family=font_family,
        tracking=label_tracking,
    )

    root.insert(insertion_index, identity)
    root.insert(insertion_index + 1, status)
    _validate_composition(root)
    element_tree.indent(root, space="  ")
    return (
        element_tree.tostring(
            root,
            encoding="unicode",
            short_empty_elements=True,
        )
        + "\n"
    )
