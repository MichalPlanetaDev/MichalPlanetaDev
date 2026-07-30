from __future__ import annotations

import textwrap
import xml.etree.ElementTree as element_tree

from profile_system.design_tokens import DesignTokenSnapshot, NumericToken
from profile_system.model import ProfileSnapshot
from profile_system.publication import PublicProfileSnapshot, project_public_profile
from profile_system.sections import EngineeringSectionsSnapshot
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


def _text(
    document: SvgDocument,
    parent: element_tree.Element,
    *,
    x: int | float,
    y: int | float,
    value: str,
    fill: str,
    size: int | float,
    weight: int | float,
    family: str,
    tracking: int | float = 0,
    anchor: str | None = None,
    identifier: str | None = None,
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
    if identifier is not None:
        attributes["id"] = identifier
    document.element(parent, "text", attributes, text=value)


def _wrapped_lines(value: str, width: int, maximum: int) -> tuple[str, ...]:
    wrapped = textwrap.wrap(
        value,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(wrapped) <= maximum:
        return tuple(wrapped)

    selected = wrapped[:maximum]
    selected[-1] = selected[-1].rstrip(" .") + "…"
    return tuple(selected)


def _multiline(
    document: SvgDocument,
    parent: element_tree.Element,
    *,
    x: int | float,
    y: int | float,
    value: str,
    width: int,
    maximum: int,
    line_height: int | float,
    fill: str,
    size: int | float,
    weight: int | float,
    family: str,
) -> None:
    for index, line in enumerate(_wrapped_lines(value, width, maximum)):
        _text(
            document,
            parent,
            x=x,
            y=float(y) + index * float(line_height),
            value=line,
            fill=fill,
            size=size,
            weight=weight,
            family=family,
        )


def _section_frame(
    document: SvgDocument,
    parent: element_tree.Element,
    *,
    identifier: str,
    y: int,
    height: int,
    sequence: str,
    title: str,
    subtitle: str,
    panel: str,
    panel_raised: str,
    border_subtle: str,
    border_strong: str,
    signal: str,
    text_primary: str,
    text_muted: str,
    family: str,
    heading_size: int | float,
    micro_size: int | float,
    semibold_weight: int | float,
    medium_weight: int | float,
    label_tracking: int | float,
) -> element_tree.Element:
    group = document.element(
        parent,
        "g",
        {
            "data-layer": identifier,
            "id": f"sections-{identifier}",
        },
    )
    document.element(
        group,
        "rect",
        {
            "fill": panel,
            "height": height,
            "rx": 22,
            "stroke": border_subtle,
            "stroke-width": 1,
            "width": 1080,
            "x": 60,
            "y": y,
        },
    )
    document.element(
        group,
        "rect",
        {
            "fill": panel_raised,
            "height": 62,
            "opacity": 0.72,
            "rx": 22,
            "width": 1080,
            "x": 60,
            "y": y,
        },
    )
    document.element(
        group,
        "line",
        {
            "stroke": border_strong,
            "stroke-width": 1,
            "x1": 60,
            "x2": 1140,
            "y1": y + 62,
            "y2": y + 62,
        },
    )
    document.element(
        group,
        "line",
        {
            "stroke": signal,
            "stroke-linecap": "round",
            "stroke-width": 2,
            "x1": 60,
            "x2": 184,
            "y1": y,
            "y2": y,
        },
    )
    _text(
        document,
        group,
        x=88,
        y=y + 26,
        value=sequence,
        fill=signal,
        size=micro_size,
        weight=semibold_weight,
        family=family,
        tracking=label_tracking,
    )
    _text(
        document,
        group,
        x=88,
        y=y + 50,
        value=title,
        fill=text_primary,
        size=heading_size,
        weight=semibold_weight,
        family=family,
    )
    _text(
        document,
        group,
        x=1112,
        y=y + 40,
        value=subtitle,
        fill=text_muted,
        size=micro_size,
        weight=medium_weight,
        family=family,
        tracking=label_tracking,
        anchor="end",
    )
    return group


def _project_cards(
    document: SvgDocument,
    parent: element_tree.Element,
    profile: PublicProfileSnapshot,
    *,
    y: int,
    panel_raised: str,
    border_subtle: str,
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    signal: str,
    orbit: str,
    family: str,
    label_size: int | float,
    body_size: int | float,
    micro_size: int | float,
    semibold_weight: int | float,
    medium_weight: int | float,
    regular_weight: int | float,
    label_tracking: int | float,
) -> None:
    projects = profile.projects[:2]

    if len(projects) != 2:
        raise SvgKernelError(
            "Engineering sections require exactly two public project cards"
        )

    for index, project in enumerate(projects):
        x = 88 + index * 528
        document.element(
            parent,
            "rect",
            {
                "fill": panel_raised,
                "height": 214,
                "rx": 14,
                "stroke": border_subtle,
                "stroke-width": 1,
                "width": 496,
                "x": x,
                "y": y,
            },
        )
        accent = signal if index == 0 else orbit
        document.element(
            parent,
            "rect",
            {
                "fill": accent,
                "height": 4,
                "rx": 2,
                "width": 76,
                "x": x + 22,
                "y": y + 20,
            },
        )
        _text(
            document,
            parent,
            x=x + 22,
            y=y + 53,
            value=project.name,
            fill=text_primary,
            size=label_size + 4,
            weight=semibold_weight,
            family=family,
        )
        _text(
            document,
            parent,
            x=x + 474,
            y=y + 52,
            value=project.status.upper(),
            fill=accent,
            size=micro_size,
            weight=semibold_weight,
            family=family,
            tracking=label_tracking,
            anchor="end",
        )
        _multiline(
            document,
            parent,
            x=x + 22,
            y=y + 84,
            value=project.summary,
            width=58,
            maximum=3,
            line_height=20,
            fill=text_secondary,
            size=body_size,
            weight=regular_weight,
            family=family,
        )
        _text(
            document,
            parent,
            x=x + 22,
            y=y + 188,
            value=f"{len(project.technology_ids):02d} TECHNOLOGIES",
            fill=text_muted,
            size=micro_size,
            weight=medium_weight,
            family=family,
            tracking=label_tracking,
        )
        _text(
            document,
            parent,
            x=x + 474,
            y=y + 188,
            value=f"{len(project.evidence_ids):02d} EVIDENCE RECORDS",
            fill=text_muted,
            size=micro_size,
            weight=medium_weight,
            family=family,
            tracking=label_tracking,
            anchor="end",
        )


def _technology_grid(
    document: SvgDocument,
    parent: element_tree.Element,
    profile: PublicProfileSnapshot,
    *,
    y: int,
    maximum: int,
    panel_raised: str,
    border_subtle: str,
    text_primary: str,
    text_muted: str,
    signal: str,
    orbit: str,
    family: str,
    label_size: int | float,
    micro_size: int | float,
    semibold_weight: int | float,
    medium_weight: int | float,
    label_tracking: int | float,
) -> None:
    technologies = profile.technologies[:maximum]

    if not technologies:
        raise SvgKernelError("Engineering sections require public technologies")

    for index, technology in enumerate(technologies):
        column = index % 3
        row = index // 3
        x = 88 + column * 344
        card_y = y + row * 62
        accent = signal if (index + column) % 2 == 0 else orbit
        document.element(
            parent,
            "rect",
            {
                "fill": panel_raised,
                "height": 48,
                "rx": 8,
                "stroke": border_subtle,
                "stroke-width": 1,
                "width": 320,
                "x": x,
                "y": card_y,
            },
        )
        document.element(
            parent,
            "circle",
            {
                "cx": x + 20,
                "cy": card_y + 24,
                "fill": accent,
                "r": 4,
            },
        )
        _text(
            document,
            parent,
            x=x + 36,
            y=card_y + 21,
            value=technology.name,
            fill=text_primary,
            size=label_size,
            weight=semibold_weight,
            family=family,
        )
        _text(
            document,
            parent,
            x=x + 36,
            y=card_y + 37,
            value=technology.category.upper(),
            fill=text_muted,
            size=micro_size,
            weight=medium_weight,
            family=family,
            tracking=label_tracking,
        )


def _evidence_cards(
    document: SvgDocument,
    parent: element_tree.Element,
    profile: PublicProfileSnapshot,
    *,
    y: int,
    panel_raised: str,
    border_subtle: str,
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    signal: str,
    family: str,
    label_size: int | float,
    body_size: int | float,
    micro_size: int | float,
    semibold_weight: int | float,
    regular_weight: int | float,
    label_tracking: int | float,
) -> None:
    evidence = profile.evidence

    if len(evidence) != 5:
        raise SvgKernelError(
            "Engineering sections require exactly five public evidence records"
        )

    for index, record in enumerate(evidence):
        column = index % 2
        row = index // 2
        x = 88 + column * 528
        card_y = y + row * 82
        card_width = 496 if index < 4 else 1024
        if index == 4:
            x = 88
        document.element(
            parent,
            "rect",
            {
                "fill": panel_raised,
                "height": 68,
                "rx": 10,
                "stroke": border_subtle,
                "stroke-width": 1,
                "width": card_width,
                "x": x,
                "y": card_y,
            },
        )
        _text(
            document,
            parent,
            x=x + 18,
            y=card_y + 24,
            value=record.label,
            fill=text_primary,
            size=label_size,
            weight=semibold_weight,
            family=family,
        )
        _text(
            document,
            parent,
            x=x + card_width - 18,
            y=card_y + 23,
            value=record.kind.upper(),
            fill=signal,
            size=micro_size,
            weight=semibold_weight,
            family=family,
            tracking=label_tracking,
            anchor="end",
        )
        summary_width = 55 if card_width < 600 else 120
        _multiline(
            document,
            parent,
            x=x + 18,
            y=card_y + 47,
            value=record.summary,
            width=summary_width,
            maximum=1,
            line_height=16,
            fill=text_secondary,
            size=body_size - 2,
            weight=regular_weight,
            family=family,
        )
        document.element(
            parent,
            "line",
            {
                "stroke": text_muted,
                "stroke-opacity": 0.26,
                "stroke-width": 1,
                "x1": x + 18,
                "x2": x + card_width - 18,
                "y1": card_y + 58,
                "y2": card_y + 58,
            },
        )


def _discipline_cards(
    document: SvgDocument,
    parent: element_tree.Element,
    profile: PublicProfileSnapshot,
    *,
    y: int,
    panel_raised: str,
    border_subtle: str,
    text_primary: str,
    text_secondary: str,
    signal: str,
    orbit: str,
    family: str,
    label_size: int | float,
    body_size: int | float,
    micro_size: int | float,
    semibold_weight: int | float,
    regular_weight: int | float,
    label_tracking: int | float,
) -> None:
    disciplines = profile.disciplines

    if len(disciplines) != 4:
        raise SvgKernelError(
            "Engineering sections require exactly four public disciplines"
        )

    for index, discipline in enumerate(disciplines):
        column = index % 2
        row = index // 2
        x = 88 + column * 528
        card_y = y + row * 112
        accent = signal if index % 2 == 0 else orbit
        document.element(
            parent,
            "rect",
            {
                "fill": panel_raised,
                "height": 98,
                "rx": 12,
                "stroke": border_subtle,
                "stroke-width": 1,
                "width": 496,
                "x": x,
                "y": card_y,
            },
        )
        _text(
            document,
            parent,
            x=x + 18,
            y=card_y + 28,
            value=discipline.name,
            fill=text_primary,
            size=label_size,
            weight=semibold_weight,
            family=family,
        )
        _text(
            document,
            parent,
            x=x + 474,
            y=card_y + 27,
            value=f"{len(discipline.project_ids):02d} PROJECT LINKS",
            fill=accent,
            size=micro_size,
            weight=semibold_weight,
            family=family,
            tracking=label_tracking,
            anchor="end",
        )
        _multiline(
            document,
            parent,
            x=x + 18,
            y=card_y + 54,
            value=discipline.summary,
            width=64,
            maximum=2,
            line_height=17,
            fill=text_secondary,
            size=body_size - 2,
            weight=regular_weight,
            family=family,
        )


def _connect_panel(
    document: SvgDocument,
    parent: element_tree.Element,
    profile: PublicProfileSnapshot,
    *,
    y: int,
    copyright_notice: str,
    panel_raised: str,
    border_subtle: str,
    text_primary: str,
    text_secondary: str,
    text_muted: str,
    signal: str,
    family: str,
    label_size: int | float,
    body_size: int | float,
    micro_size: int | float,
    semibold_weight: int | float,
    medium_weight: int | float,
    label_tracking: int | float,
) -> None:
    links = profile.links

    if len(links) != 2:
        raise SvgKernelError(
            "Engineering sections require exactly two public connection links"
        )

    for index, link in enumerate(links):
        x = 88 + index * 528
        document.element(
            parent,
            "rect",
            {
                "fill": panel_raised,
                "height": 74,
                "rx": 12,
                "stroke": border_subtle,
                "stroke-width": 1,
                "width": 496,
                "x": x,
                "y": y,
            },
        )
        _text(
            document,
            parent,
            x=x + 18,
            y=y + 28,
            value=link.label,
            fill=text_primary,
            size=label_size,
            weight=semibold_weight,
            family=family,
        )
        _text(
            document,
            parent,
            x=x + 474,
            y=y + 27,
            value=link.kind.upper(),
            fill=signal,
            size=micro_size,
            weight=semibold_weight,
            family=family,
            tracking=label_tracking,
            anchor="end",
        )
        _text(
            document,
            parent,
            x=x + 18,
            y=y + 53,
            value=link.url,
            fill=text_secondary,
            size=body_size - 2,
            weight=medium_weight,
            family=family,
        )

    _text(
        document,
        parent,
        x=88,
        y=y + 112,
        value=copyright_notice,
        fill=text_muted,
        size=micro_size,
        weight=medium_weight,
        family=family,
        tracking=label_tracking,
        identifier="sections-copyright",
    )
    _text(
        document,
        parent,
        x=1112,
        y=y + 112,
        value="SOURCE REVIEW PERMITTED // REUSE REQUIRES WRITTEN PERMISSION",
        fill=signal,
        size=micro_size,
        weight=semibold_weight,
        family=family,
        tracking=label_tracking,
        anchor="end",
    )


def render_engineering_sections(
    sections: EngineeringSectionsSnapshot,
    profile: ProfileSnapshot,
    tokens: DesignTokenSnapshot,
) -> str:
    public_profile = project_public_profile(profile)

    if sections.theme_id != tokens.theme_id:
        raise SvgKernelError(
            "Engineering sections theme does not match the design-token theme"
        )
    if profile.environment_id != sections.theme_id:
        raise SvgKernelError(
            "Engineering sections theme does not match the profile environment"
        )
    if len(public_profile.technologies) > sections.maximum_technologies:
        raise SvgKernelError(
            "Public technology count exceeds the engineering-section limit"
        )

    width = sections.viewport.width
    height = sections.viewport.height
    family = _font_stack(tokens)

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

    heading_size = _numeric(tokens.type_sizes, "heading")
    body_size = _numeric(tokens.type_sizes, "body")
    label_size = _numeric(tokens.type_sizes, "label")
    micro_size = _numeric(tokens.type_sizes, "micro")
    regular_weight = _numeric(tokens.type_weights, "regular")
    medium_weight = _numeric(tokens.type_weights, "medium")
    semibold_weight = _numeric(tokens.type_weights, "semibold")
    bold_weight = _numeric(tokens.type_weights, "bold")
    label_tracking = _numeric(tokens.tracking, "label")
    glow_blur = _numeric(tokens.effects, "glowBlur")

    document = SvgDocument(
        width=width,
        height=height,
        title=sections.title,
        description=sections.description,
    )
    document.define_linear_gradient(
        "sections-background-gradient",
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
    document.define_linear_gradient(
        "sections-signal-gradient",
        stops=(
            GradientStop("0%", signal),
            GradientStop("100%", orbit),
        ),
    )
    document.define_glow_filter("sections-signal-glow", blur=glow_blur)

    background = document.element(
        document.root,
        "g",
        {"data-layer": "background", "id": "sections-background"},
    )
    document.element(
        background,
        "rect",
        {
            "fill": "url(#sections-background-gradient)",
            "height": height,
            "width": width,
            "x": 0,
            "y": 0,
        },
    )
    for x in range(60, width, 90):
        document.element(
            background,
            "line",
            {
                "stroke": border_subtle,
                "stroke-opacity": 0.16,
                "stroke-width": 1,
                "x1": x,
                "x2": x,
                "y1": 0,
                "y2": height,
            },
        )
    for y in range(80, height, 80):
        document.element(
            background,
            "line",
            {
                "stroke": border_subtle,
                "stroke-opacity": 0.12,
                "stroke-width": 1,
                "x1": 0,
                "x2": width,
                "y1": y,
                "y2": y,
            },
        )

    header = document.element(
        document.root,
        "g",
        {"data-layer": "header", "id": "sections-header"},
    )
    _text(
        document,
        header,
        x=60,
        y=42,
        value="ENGINEERING SURFACES // M11",
        fill=signal,
        size=micro_size,
        weight=semibold_weight,
        family=family,
        tracking=label_tracking,
    )
    _text(
        document,
        header,
        x=60,
        y=80,
        value="PROJECTS, STACK, EVIDENCE AND DISCIPLINES",
        fill=text_primary,
        size=heading_size + 5,
        weight=bold_weight,
        family=family,
    )
    _text(
        document,
        header,
        x=1140,
        y=76,
        value=f"PUBLIC GRAPH // {public_profile.profile_id.upper()}",
        fill=warning,
        size=micro_size,
        weight=medium_weight,
        family=family,
        tracking=label_tracking,
        anchor="end",
    )

    projects = _section_frame(
        document,
        document.root,
        identifier="projects",
        y=108,
        height=304,
        sequence="01 // SELECTED WORK",
        title="SELECTED PROJECTS",
        subtitle=f"{len(public_profile.projects):02d} PUBLIC PROJECTS",
        panel=panel,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        border_strong=border_strong,
        signal=signal,
        text_primary=text_primary,
        text_muted=text_muted,
        family=family,
        heading_size=heading_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )
    _project_cards(
        document,
        projects,
        public_profile,
        y=180,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        signal=signal,
        orbit=orbit,
        family=family,
        label_size=label_size,
        body_size=body_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        regular_weight=regular_weight,
        label_tracking=label_tracking,
    )

    stack = _section_frame(
        document,
        document.root,
        identifier="stack",
        y=436,
        height=340,
        sequence="02 // WORKING SYSTEM",
        title="TECHNOLOGY STACK",
        subtitle=f"{len(public_profile.technologies):02d} VERIFIED TECHNOLOGIES",
        panel=panel,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        border_strong=border_strong,
        signal=signal,
        text_primary=text_primary,
        text_muted=text_muted,
        family=family,
        heading_size=heading_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )
    _technology_grid(
        document,
        stack,
        public_profile,
        y=512,
        maximum=sections.maximum_technologies,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        text_primary=text_primary,
        text_muted=text_muted,
        signal=signal,
        orbit=orbit,
        family=family,
        label_size=label_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )

    evidence = _section_frame(
        document,
        document.root,
        identifier="evidence",
        y=800,
        height=330,
        sequence="03 // VERIFIABLE OUTPUT",
        title="ENGINEERING EVIDENCE",
        subtitle=f"{len(public_profile.evidence):02d} PUBLIC RECORDS",
        panel=panel,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        border_strong=border_strong,
        signal=signal,
        text_primary=text_primary,
        text_muted=text_muted,
        family=family,
        heading_size=heading_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )
    _evidence_cards(
        document,
        evidence,
        public_profile,
        y=874,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        signal=signal,
        family=family,
        label_size=label_size,
        body_size=body_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        regular_weight=regular_weight,
        label_tracking=label_tracking,
    )

    disciplines = _section_frame(
        document,
        document.root,
        identifier="disciplines",
        y=1154,
        height=320,
        sequence="04 // ENGINEERING RANGE",
        title="CORE DISCIPLINES",
        subtitle=f"{len(public_profile.disciplines):02d} CONNECTED DOMAINS",
        panel=panel,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        border_strong=border_strong,
        signal=signal,
        text_primary=text_primary,
        text_muted=text_muted,
        family=family,
        heading_size=heading_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )
    _discipline_cards(
        document,
        disciplines,
        public_profile,
        y=1228,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        text_primary=text_primary,
        text_secondary=text_secondary,
        signal=signal,
        orbit=orbit,
        family=family,
        label_size=label_size,
        body_size=body_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        regular_weight=regular_weight,
        label_tracking=label_tracking,
    )

    connect = _section_frame(
        document,
        document.root,
        identifier="connect",
        y=1498,
        height=216,
        sequence="05 // PUBLIC ENDPOINTS",
        title="CONNECT",
        subtitle=f"{len(public_profile.links):02d} VERIFIED LINKS",
        panel=panel,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        border_strong=border_strong,
        signal=signal,
        text_primary=text_primary,
        text_muted=text_muted,
        family=family,
        heading_size=heading_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )
    _connect_panel(
        document,
        connect,
        public_profile,
        y=1572,
        copyright_notice=sections.copyright_notice,
        panel_raised=panel_raised,
        border_subtle=border_subtle,
        text_primary=text_primary,
        text_secondary=text_secondary,
        text_muted=text_muted,
        signal=signal,
        family=family,
        label_size=label_size,
        body_size=body_size,
        micro_size=micro_size,
        semibold_weight=semibold_weight,
        medium_weight=medium_weight,
        label_tracking=label_tracking,
    )

    return document.serialize()
