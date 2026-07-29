from __future__ import annotations

import xml.etree.ElementTree as element_tree

from profile_system.probes import (
    ProbeCapability,
    SvgProbeSnapshot,
)

SVG_NAMESPACE = "http://www.w3.org/2000/svg"

element_tree.register_namespace(
    "",
    SVG_NAMESPACE,
)


def _tag(name: str) -> str:
    return f"{{{SVG_NAMESPACE}}}{name}"


def _element(
    parent: element_tree.Element,
    name: str,
    attributes: dict[str, str],
) -> element_tree.Element:
    return element_tree.SubElement(
        parent,
        _tag(name),
        attributes,
    )


def _text(
    parent: element_tree.Element,
    *,
    x: int,
    y: int,
    value: str,
    size: int,
    fill: str,
    weight: str = "500",
    letter_spacing: str = "0",
) -> None:
    node = _element(
        parent,
        "text",
        {
            "x": str(x),
            "y": str(y),
            "fill": fill,
            "font-family": "Inter, Segoe UI, sans-serif",
            "font-size": str(size),
            "font-weight": weight,
            "letter-spacing": letter_spacing,
        },
    )
    node.text = value


def _stop(
    parent: element_tree.Element,
    *,
    offset: str,
    color: str,
    opacity: str = "1",
) -> None:
    _element(
        parent,
        "stop",
        {
            "offset": offset,
            "stop-color": color,
            "stop-opacity": opacity,
        },
    )


def _definitions(
    root: element_tree.Element,
) -> None:
    definitions = _element(
        root,
        "defs",
        {},
    )

    background_gradient = _element(
        definitions,
        "linearGradient",
        {
            "id": "background-gradient",
            "x1": "0",
            "y1": "0",
            "x2": "1",
            "y2": "1",
        },
    )
    _stop(
        background_gradient,
        offset="0%",
        color="#07101d",
    )
    _stop(
        background_gradient,
        offset="52%",
        color="#0b1927",
    )
    _stop(
        background_gradient,
        offset="100%",
        color="#08121b",
    )

    sample_gradient = _element(
        definitions,
        "linearGradient",
        {
            "id": "sample-gradient",
            "x1": "0",
            "y1": "0",
            "x2": "1",
            "y2": "1",
        },
    )
    _stop(
        sample_gradient,
        offset="0%",
        color="#54e3d3",
    )
    _stop(
        sample_gradient,
        offset="100%",
        color="#4f78ff",
    )

    planet_gradient = _element(
        definitions,
        "radialGradient",
        {
            "id": "planet-gradient",
            "cx": "42%",
            "cy": "35%",
            "r": "66%",
        },
    )
    _stop(
        planet_gradient,
        offset="0%",
        color="#c8fff7",
        opacity="0.95",
    )
    _stop(
        planet_gradient,
        offset="45%",
        color="#5ea8ca",
        opacity="0.86",
    )
    _stop(
        planet_gradient,
        offset="100%",
        color="#182d4f",
        opacity="0.42",
    )

    mask_gradient = _element(
        definitions,
        "linearGradient",
        {
            "id": "mask-gradient",
            "x1": "0",
            "y1": "0",
            "x2": "1",
            "y2": "0",
        },
    )
    _stop(
        mask_gradient,
        offset="0%",
        color="#000000",
    )
    _stop(
        mask_gradient,
        offset="50%",
        color="#ffffff",
    )
    _stop(
        mask_gradient,
        offset="100%",
        color="#000000",
    )

    clip_path = _element(
        definitions,
        "clipPath",
        {
            "id": "sample-clip",
        },
    )
    _element(
        clip_path,
        "circle",
        {
            "cx": "0",
            "cy": "0",
            "r": "38",
        },
    )

    mask = _element(
        definitions,
        "mask",
        {
            "id": "sample-mask",
            "maskContentUnits": "objectBoundingBox",
        },
    )
    _element(
        mask,
        "rect",
        {
            "x": "0",
            "y": "0",
            "width": "1",
            "height": "1",
            "fill": "url(#mask-gradient)",
        },
    )

    probe_filter = _element(
        definitions,
        "filter",
        {
            "id": "sample-filter",
            "x": "-50%",
            "y": "-50%",
            "width": "200%",
            "height": "200%",
        },
    )
    _element(
        probe_filter,
        "feGaussianBlur",
        {
            "stdDeviation": "5",
            "result": "blur",
        },
    )
    merge = _element(
        probe_filter,
        "feMerge",
        {},
    )
    _element(
        merge,
        "feMergeNode",
        {
            "in": "blur",
        },
    )
    _element(
        merge,
        "feMergeNode",
        {
            "in": "SourceGraphic",
        },
    )


def _render_sample(
    parent: element_tree.Element,
    capability: ProbeCapability,
    *,
    x: int,
    y: int,
) -> None:
    center_x = x + 46
    center_y = y + 46

    _element(
        parent,
        "rect",
        {
            "x": str(x),
            "y": str(y),
            "width": "92",
            "height": "92",
            "rx": "16",
            "fill": "#0a1725",
            "stroke": "#244258",
            "stroke-width": "1",
        },
    )

    if capability.kind == "solid-geometry":
        _element(
            parent,
            "rect",
            {
                "x": str(x + 19),
                "y": str(y + 22),
                "width": "54",
                "height": "48",
                "rx": "9",
                "fill": "#50d8ca",
            },
        )
        _element(
            parent,
            "circle",
            {
                "cx": str(x + 64),
                "cy": str(y + 30),
                "r": "9",
                "fill": "#d6fff8",
            },
        )
        return

    if capability.kind == "path-geometry":
        _element(
            parent,
            "path",
            {
                "d": (
                    f"M {x + 15} {y + 65} "
                    f"L {x + 34} {y + 25} "
                    f"L {x + 51} {y + 55} "
                    f"L {x + 75} {y + 20}"
                ),
                "fill": "none",
                "stroke": "#70e8da",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
                "stroke-width": "6",
            },
        )
        return

    if capability.kind == "linear-gradient":
        _element(
            parent,
            "rect",
            {
                "x": str(x + 16),
                "y": str(y + 20),
                "width": "60",
                "height": "52",
                "rx": "12",
                "fill": "url(#sample-gradient)",
            },
        )
        return

    if capability.kind == "radial-gradient":
        _element(
            parent,
            "circle",
            {
                "cx": str(center_x),
                "cy": str(center_y),
                "r": "31",
                "fill": "url(#planet-gradient)",
            },
        )
        return

    if capability.kind == "clip-path":
        clipped_group = _element(
            parent,
            "g",
            {
                "clip-path": "url(#sample-clip)",
                "transform": (f"translate({center_x} {center_y})"),
            },
        )
        _element(
            clipped_group,
            "circle",
            {
                "cx": "-22",
                "cy": "0",
                "r": "31",
                "fill": "#4f78ff",
            },
        )
        _element(
            clipped_group,
            "circle",
            {
                "cx": "22",
                "cy": "0",
                "r": "31",
                "fill": "#54e3d3",
            },
        )
        return

    if capability.kind == "mask":
        _element(
            parent,
            "rect",
            {
                "x": str(x + 13),
                "y": str(y + 24),
                "width": "66",
                "height": "44",
                "rx": "12",
                "fill": "#65eadc",
                "mask": "url(#sample-mask)",
            },
        )
        return

    if capability.kind == "filter":
        _element(
            parent,
            "circle",
            {
                "cx": str(center_x),
                "cy": str(center_y),
                "r": "25",
                "fill": "#6ce9dd",
                "filter": "url(#sample-filter)",
            },
        )
        return

    if capability.kind == "text":
        _text(
            parent,
            x=x + 18,
            y=y + 55,
            value="Aa",
            size=34,
            fill="#d7fff8",
            weight="650",
            letter_spacing="1",
        )
        return

    if capability.kind == "opacity":
        _element(
            parent,
            "circle",
            {
                "cx": str(x + 35),
                "cy": str(center_y),
                "r": "25",
                "fill": "#4f78ff",
                "opacity": "0.72",
            },
        )
        _element(
            parent,
            "circle",
            {
                "cx": str(x + 57),
                "cy": str(center_y),
                "r": "25",
                "fill": "#54e3d3",
                "opacity": "0.62",
            },
        )
        return

    raise ValueError(f"Unsupported rendered capability kind: {capability.kind}")


def _capability_card(
    root: element_tree.Element,
    capability: ProbeCapability,
    *,
    x: int,
    y: int,
) -> None:
    group = _element(
        root,
        "g",
        {
            "id": f"capability-{capability.capability_id}",
        },
    )

    _element(
        group,
        "rect",
        {
            "x": str(x),
            "y": str(y),
            "width": "344",
            "height": "128",
            "rx": "19",
            "fill": "#0b1826",
            "stroke": "#233f54",
            "stroke-width": "1",
        },
    )

    _element(
        group,
        "line",
        {
            "x1": str(x + 20),
            "y1": str(y + 1),
            "x2": str(x + 128),
            "y2": str(y + 1),
            "stroke": "#57dfd2",
            "stroke-width": "2",
            "opacity": "0.85",
        },
    )

    _render_sample(
        group,
        capability,
        x=x + 18,
        y=y + 18,
    )

    _text(
        group,
        x=x + 128,
        y=y + 53,
        value=capability.label,
        size=14,
        fill="#d8e9ef",
        weight="650",
        letter_spacing="1.1",
    )

    _text(
        group,
        x=x + 128,
        y=y + 78,
        value=capability.kind.upper(),
        size=10,
        fill="#7193a5",
        weight="500",
        letter_spacing="0.9",
    )

    _element(
        group,
        "circle",
        {
            "cx": str(x + 318),
            "cy": str(y + 23),
            "r": "4",
            "fill": "#62e5d8",
            "opacity": "0.8",
        },
    )


def render_svg_probe(
    snapshot: SvgProbeSnapshot,
) -> str:
    width = snapshot.viewport.width
    height = snapshot.viewport.height

    root = element_tree.Element(
        _tag("svg"),
        {
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
            "role": "img",
            "aria-label": snapshot.title,
        },
    )

    title = _element(
        root,
        "title",
        {},
    )
    title.text = snapshot.title

    _definitions(root)

    _element(
        root,
        "rect",
        {
            "x": "0",
            "y": "0",
            "width": str(width),
            "height": str(height),
            "fill": "url(#background-gradient)",
        },
    )

    _element(
        root,
        "circle",
        {
            "cx": "1080",
            "cy": "48",
            "r": "170",
            "fill": "url(#planet-gradient)",
            "opacity": "0.32",
        },
    )

    _element(
        root,
        "rect",
        {
            "x": "0",
            "y": "0",
            "width": str(width),
            "height": "104",
            "fill": "#081521",
            "mask": "url(#sample-mask)",
            "opacity": "0.58",
        },
    )

    _text(
        root,
        x=60,
        y=50,
        value=snapshot.title.upper(),
        size=20,
        fill="#d7f5f1",
        weight="650",
        letter_spacing="2.2",
    )

    _text(
        root,
        x=60,
        y=78,
        value="DETERMINISTIC / STATIC / REPOSITORY-OWNED",
        size=10,
        fill="#668b9d",
        weight="550",
        letter_spacing="1.4",
    )

    _text(
        root,
        x=1025,
        y=67,
        value="09",
        size=34,
        fill="#75eadf",
        weight="650",
        letter_spacing="2",
    )

    card_width = 344
    card_height = 128
    horizontal_gap = 24
    vertical_gap = 24
    left_margin = 60
    top_margin = 136

    for index, capability in enumerate(snapshot.capabilities):
        column = index % 3
        row = index // 3

        x = left_margin + column * (card_width + horizontal_gap)
        y = top_margin + row * (card_height + vertical_gap)

        _capability_card(
            root,
            capability,
            x=x,
            y=y,
        )

    element_tree.indent(
        root,
        space="  ",
    )

    serialized = element_tree.tostring(
        root,
        encoding="unicode",
        short_empty_elements=True,
    )

    return f'<?xml version="1.0" encoding="UTF-8"?>\n{serialized}\n'
