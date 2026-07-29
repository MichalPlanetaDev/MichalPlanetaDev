from __future__ import annotations

from profile_system.design_tokens import (
    DesignTokenSnapshot,
    NumericToken,
)
from profile_system.svg_kernel import (
    GradientStop,
    SvgDocument,
)


def _colors(tokens: DesignTokenSnapshot) -> dict[str, str]:
    return {record.token_id: record.value for record in tokens.colors}


def _numbers(records: tuple[NumericToken, ...]) -> dict[str, float]:
    return {record.token_id: float(record.value) for record in records}


def render_kernel_specimen(tokens: DesignTokenSnapshot) -> str:
    colors = _colors(tokens)
    layout = _numbers(tokens.layout)
    radii = _numbers(tokens.radii)
    strokes = _numbers(tokens.strokes)
    opacity = _numbers(tokens.opacity)
    effects = _numbers(tokens.effects)
    type_sizes = _numbers(tokens.type_sizes)
    type_weights = _numbers(tokens.type_weights)
    tracking = _numbers(tokens.tracking)

    width = int(layout["canvasWidth"])
    height = 520
    inset = int(layout["safeInset"])
    medium_radius = int(radii["medium"])
    large_radius = int(radii["large"])
    hairline = int(strokes["hairline"])
    glow_blur = effects["glowBlur"]
    font_family = ", ".join(tokens.font_stack)

    document = SvgDocument(
        width=width,
        height=height,
        title="SVG Renderer Kernel",
        description=(
            "Token-driven static SVG primitives, layer boundaries, "
            "accessible text and local resource references."
        ),
    )

    document.define_linear_gradient(
        "kernel-background-gradient",
        x1="0%",
        y1="0%",
        x2="100%",
        y2="100%",
        stops=(
            GradientStop("0%", colors["background.void"]),
            GradientStop("54%", colors["background.deep"]),
            GradientStop("100%", colors["background.panel"]),
        ),
    )
    document.define_linear_gradient(
        "kernel-signal-gradient",
        stops=(
            GradientStop("0%", colors["accent.signal"]),
            GradientStop("100%", colors["accent.orbit"]),
        ),
    )
    document.define_radial_gradient(
        "kernel-orbit-gradient",
        cx="38%",
        cy="32%",
        radius="68%",
        stops=(
            GradientStop("0%", colors["text.primary"], 0.96),
            GradientStop("44%", colors["accent.signal"], 0.84),
            GradientStop("100%", colors["accent.orbit"], 0.18),
        ),
    )
    document.define_linear_gradient(
        "kernel-mask-gradient",
        stops=(
            GradientStop("0%", "#000000"),
            GradientStop("48%", "#ffffff"),
            GradientStop("100%", "#000000"),
        ),
    )
    document.define_clip_rect(
        "kernel-panel-clip",
        x=198,
        y=72,
        width=386,
        height=92,
        radius=medium_radius,
    )
    document.define_alpha_mask(
        "kernel-fade-mask",
        gradient_id="kernel-mask-gradient",
    )
    document.define_glow_filter(
        "kernel-signal-glow",
        blur=glow_blur,
    )

    background = document.element(
        document.root,
        "g",
        {
            "data-layer": "background",
            "id": "layer-background",
        },
    )
    document.element(
        background,
        "rect",
        {
            "fill": "url(#kernel-background-gradient)",
            "height": height,
            "width": width,
            "x": 0,
            "y": 0,
        },
    )

    grid = document.element(
        document.root,
        "g",
        {
            "data-layer": "grid",
            "id": "layer-grid",
            "opacity": opacity["subtle"],
        },
    )
    usable_width = width - inset * 2
    column_width = usable_width / int(layout["columns"])

    for column in range(int(layout["columns"]) + 1):
        x = inset + column * column_width
        document.element(
            grid,
            "line",
            {
                "stroke": colors["border.subtle"],
                "stroke-width": hairline,
                "x1": x,
                "x2": x,
                "y1": 36,
                "y2": height - 36,
            },
        )

    for y in (92, 164, 236, 308, 380, 452):
        document.element(
            grid,
            "line",
            {
                "stroke": colors["border.subtle"],
                "stroke-width": hairline,
                "x1": inset,
                "x2": width - inset,
                "y1": y,
                "y2": y,
            },
        )

    interface = document.element(
        document.root,
        "g",
        {
            "data-layer": "interface",
            "id": "layer-interface",
        },
    )
    document.element(
        interface,
        "rect",
        {
            "fill": "none",
            "height": height - 72,
            "rx": large_radius,
            "stroke": colors["border.strong"],
            "stroke-opacity": opacity["secondary"],
            "stroke-width": hairline,
            "width": width - inset * 2,
            "x": inset,
            "y": 36,
        },
    )
    document.element(
        interface,
        "line",
        {
            "stroke": "url(#kernel-signal-gradient)",
            "stroke-linecap": "round",
            "stroke-width": int(strokes["emphasis"]),
            "x1": inset,
            "x2": inset + 186,
            "y1": 36,
            "y2": 36,
        },
    )
    document.element(
        interface,
        "text",
        {
            "fill": colors["accent.signal"],
            "font-family": font_family,
            "font-size": int(type_sizes["label"]),
            "font-weight": int(type_weights["semibold"]),
            "letter-spacing": tracking["label"],
            "x": inset,
            "y": 76,
        },
        text="SVG RENDERER KERNEL // M08",
    )
    document.element(
        interface,
        "text",
        {
            "fill": colors["text.primary"],
            "font-family": font_family,
            "font-size": int(type_sizes["title"]),
            "font-weight": int(type_weights["bold"]),
            "letter-spacing": tracking["display"],
            "x": inset,
            "y": 120,
        },
        text="TOKEN-DRIVEN SVG PRIMITIVES",
    )
    document.element(
        interface,
        "text",
        {
            "fill": colors["text.secondary"],
            "font-family": font_family,
            "font-size": int(type_sizes["body"]),
            "font-weight": int(type_weights["regular"]),
            "x": inset,
            "y": 146,
        },
        text=(
            "Deterministic geometry, owned identifiers and validated local references."
        ),
    )

    primitives = document.element(
        document.root,
        "g",
        {
            "data-layer": "primitives",
            "id": "layer-primitives",
            "transform": "translate(60 178)",
        },
    )
    document.element(
        primitives,
        "rect",
        {
            "fill": colors["background.panel"],
            "height": 240,
            "rx": large_radius,
            "stroke": colors["border.subtle"],
            "stroke-width": hairline,
            "width": 640,
            "x": 0,
            "y": 0,
        },
    )
    document.element(
        primitives,
        "text",
        {
            "fill": colors["text.muted"],
            "font-family": font_family,
            "font-size": int(type_sizes["micro"]),
            "font-weight": int(type_weights["semibold"]),
            "letter-spacing": tracking["label"],
            "x": 28,
            "y": 32,
        },
        text="GEOMETRY / CLIPPING / FILTERS",
    )
    document.element(
        primitives,
        "circle",
        {
            "cx": 108,
            "cy": 126,
            "fill": "url(#kernel-orbit-gradient)",
            "filter": "url(#kernel-signal-glow)",
            "r": 54,
        },
    )
    document.element(
        primitives,
        "circle",
        {
            "cx": 108,
            "cy": 126,
            "fill": "none",
            "r": 76,
            "stroke": colors["accent.orbit"],
            "stroke-dasharray": "7 9",
            "stroke-opacity": opacity["secondary"],
            "stroke-width": hairline,
        },
    )
    document.element(
        primitives,
        "path",
        {
            "d": "M 202 162 L 240 82 L 282 142 L 338 68 L 382 134",
            "fill": "none",
            "stroke": "url(#kernel-signal-gradient)",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": int(strokes["emphasis"]),
        },
    )
    clipped = document.element(
        primitives,
        "g",
        {"clip-path": "url(#kernel-panel-clip)"},
    )
    document.element(
        clipped,
        "rect",
        {
            "fill": colors["background.panel-raised"],
            "height": 92,
            "rx": medium_radius,
            "width": 386,
            "x": 198,
            "y": 72,
        },
    )
    document.element(
        clipped,
        "rect",
        {
            "fill": "url(#kernel-signal-gradient)",
            "height": 92,
            "opacity": opacity["muted"],
            "width": 386,
            "x": 198,
            "y": 72,
        },
    )
    document.element(
        primitives,
        "text",
        {
            "fill": colors["text.secondary"],
            "font-family": font_family,
            "font-size": int(type_sizes["label"]),
            "font-weight": int(type_weights["medium"]),
            "x": 198,
            "y": 198,
        },
        text="LOCAL DEFS → URL REFERENCES → STATIC OUTPUT",
    )

    typography = document.element(
        document.root,
        "g",
        {
            "data-layer": "typography",
            "id": "layer-typography",
            "transform": "translate(724 178)",
        },
    )
    document.element(
        typography,
        "rect",
        {
            "fill": colors["background.panel"],
            "height": 240,
            "rx": large_radius,
            "stroke": colors["border.subtle"],
            "stroke-width": hairline,
            "width": 416,
            "x": 0,
            "y": 0,
        },
    )
    document.element(
        typography,
        "text",
        {
            "fill": colors["text.muted"],
            "font-family": font_family,
            "font-size": int(type_sizes["micro"]),
            "font-weight": int(type_weights["semibold"]),
            "letter-spacing": tracking["label"],
            "x": 28,
            "y": 32,
        },
        text="TYPOGRAPHY / TOKENS / LAYERS",
    )
    document.element(
        typography,
        "text",
        {
            "fill": colors["text.primary"],
            "font-family": font_family,
            "font-size": int(type_sizes["heading"]),
            "font-weight": int(type_weights["bold"]),
            "x": 28,
            "y": 74,
        },
        text="Readable by default",
    )
    document.element(
        typography,
        "text",
        {
            "fill": colors["text.secondary"],
            "font-family": font_family,
            "font-size": int(type_sizes["body"]),
            "font-weight": int(type_weights["regular"]),
            "x": 28,
            "y": 104,
        },
        text="No hover-only evidence. No external fonts.",
    )

    swatches = (
        (colors["accent.signal"], "SIGNAL"),
        (colors["accent.orbit"], "ORBIT"),
        (colors["accent.warning"], "WARNING"),
        (colors["accent.success"], "SUCCESS"),
    )

    for index, (color, label) in enumerate(swatches):
        y = 132 + index * 24
        document.element(
            typography,
            "rect",
            {
                "fill": color,
                "height": 10,
                "rx": 5,
                "width": 34,
                "x": 28,
                "y": y,
            },
        )
        document.element(
            typography,
            "text",
            {
                "fill": colors["text.secondary"],
                "font-family": font_family,
                "font-size": int(type_sizes["micro"]),
                "font-weight": int(type_weights["medium"]),
                "letter-spacing": tracking["label"],
                "x": 78,
                "y": y + 9,
            },
            text=label,
        )

    footer = document.element(
        document.root,
        "g",
        {
            "data-layer": "footer",
            "id": "layer-footer",
        },
    )
    document.element(
        footer,
        "line",
        {
            "stroke": colors["border.subtle"],
            "stroke-width": hairline,
            "x1": inset,
            "x2": width - inset,
            "y1": 452,
            "y2": 452,
        },
    )
    document.element(
        footer,
        "text",
        {
            "fill": colors["text.muted"],
            "font-family": font_family,
            "font-size": int(type_sizes["micro"]),
            "font-weight": int(type_weights["medium"]),
            "letter-spacing": tracking["label"],
            "x": inset,
            "y": 482,
        },
        text=("SAFE STATIC SVG • DETERMINISTIC OUTPUT • NO EXTERNAL REFERENCES"),
    )
    document.element(
        footer,
        "text",
        {
            "fill": colors["accent.signal"],
            "font-family": font_family,
            "font-size": int(type_sizes["micro"]),
            "font-weight": int(type_weights["semibold"]),
            "letter-spacing": tracking["label"],
            "text-anchor": "end",
            "x": width - inset,
            "y": 482,
        },
        text="KERNEL STATUS // READY",
    )

    return document.serialize()
