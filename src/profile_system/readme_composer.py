from __future__ import annotations

from html import escape

from profile_system.content import Link, Project
from profile_system.model import ProfileSnapshot
from profile_system.publication import PublicProfileSnapshot, project_public_profile
from profile_system.readme import ReadmeCompositionSnapshot
from profile_system.svg_kernel import SvgKernelError

BEGIN_MARKER = "<!-- profile-system:begin -->"
END_MARKER = "<!-- profile-system:end -->"


def _escaped(value: str) -> str:
    return escape(value, quote=True)


def _asset_source(value: str) -> str:
    return "./" + value


def _project_heading(
    project: Project,
    links: dict[str, Link],
) -> str:
    name = _escaped(project.name)

    for link_id in project.link_ids:
        link = links.get(link_id)
        if link is not None:
            return f'<a href="{_escaped(link.url)}"><strong>{name}</strong></a>'

    return f"<strong>{name}</strong>"


def _render_project_paragraphs(
    profile: PublicProfileSnapshot,
) -> list[str]:
    links = {link.link_id: link for link in profile.links}
    paragraphs: list[str] = []

    for project in profile.projects:
        heading = _project_heading(project, links)
        paragraphs.extend(
            (
                f"<p>{heading}</p>",
                f"<p>{_escaped(project.summary)}</p>",
            )
        )

    return paragraphs


def _render_evidence_paragraphs(
    profile: PublicProfileSnapshot,
) -> list[str]:
    paragraphs: list[str] = []

    for record in profile.evidence:
        paragraphs.append(
            "<p>"
            f"<strong>{_escaped(record.label)}</strong> "
            f"<code>{_escaped(record.kind.upper())}</code><br>"
            f"{_escaped(record.summary)}"
            "</p>"
        )

    return paragraphs


def _render_discipline_paragraphs(
    profile: PublicProfileSnapshot,
) -> list[str]:
    paragraphs: list[str] = []

    for discipline in profile.disciplines:
        paragraphs.append(
            "<p>"
            f"<strong>{_escaped(discipline.name)}</strong><br>"
            f"{_escaped(discipline.summary)}"
            "</p>"
        )

    return paragraphs


def _render_connection_paragraph(profile: PublicProfileSnapshot) -> str:
    anchors = [
        f'<a href="{_escaped(link.url)}">{_escaped(link.label)}</a>'
        for link in profile.links
    ]
    return "<p>" + " &nbsp;·&nbsp; ".join(anchors) + "</p>"


def render_profile_readme(
    composition: ReadmeCompositionSnapshot,
    profile: ProfileSnapshot,
) -> str:
    if composition.profile_id != profile.profile_id:
        raise SvgKernelError(
            "README composition profileId does not match the canonical profile"
        )
    if composition.theme_id != profile.environment_id:
        raise SvgKernelError(
            "README composition themeId does not match the profile environment"
        )

    public_profile = project_public_profile(profile)
    width = composition.asset_width_percent
    hero_source = _asset_source(composition.hero_asset.as_posix())
    sections_source = _asset_source(composition.sections_asset.as_posix())
    license_source = _asset_source(composition.license_path.as_posix())
    technology_names = " ".join(
        f"<code>{_escaped(technology.name)}</code>"
        for technology in public_profile.technologies
    )

    lines = [
        BEGIN_MARKER,
        "",
        '<div align="center">',
        "",
        (
            f'  <img src="{hero_source}" width="{width}%" '
            f'alt="{_escaped(profile.display_name)} — '
            'cinematic systems engineer identity observatory">'
        ),
        "",
        "</div>",
        "",
        "<br>",
        "",
        '<div align="center">',
        "",
        (
            f'  <img src="{sections_source}" width="{width}%" '
            'alt="Selected projects, technologies, engineering evidence, '
            'disciplines and public connection endpoints">'
        ),
        "",
        "</div>",
        "",
        "<br>",
        "",
        "<details>",
        (
            f"<summary><strong>{_escaped(composition.text_fallback_title)}"
            "</strong></summary>"
        ),
        "",
        f"<p><strong>{_escaped(profile.identity.headline)}</strong></p>",
        "",
        f"<p><strong>{_escaped(profile.display_name)}</strong></p>",
        "",
        f"<p>{_escaped(profile.identity.role)}</p>",
        "",
        f"<p>{_escaped(profile.identity.summary)}</p>",
        "",
        f"<p><em>{_escaped(profile.identity.motto)}</em></p>",
        "",
        "<h3>Selected projects</h3>",
        "",
        *_render_project_paragraphs(public_profile),
        "",
        "<h3>Technology evidence</h3>",
        "",
        f"<p>{technology_names}</p>",
        "",
        "<h3>Engineering evidence</h3>",
        "",
        *_render_evidence_paragraphs(public_profile),
        "",
        "<h3>Engineering disciplines</h3>",
        "",
        *_render_discipline_paragraphs(public_profile),
        "",
        "<h3>Connect</h3>",
        "",
        _render_connection_paragraph(public_profile),
        "",
        "</details>",
        "",
        '<p align="center">',
        (
            f"  <sub>{_escaped(composition.copyright_notice)} "
            f"{_escaped(composition.source_review_notice)} "
            f'See <a href="{license_source}">LICENSE</a>.</sub>'
        ),
        "</p>",
        "",
        END_MARKER,
        "",
    ]
    return "\n".join(lines)
