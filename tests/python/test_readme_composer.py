from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from profile_system.content import Identity, Project
from profile_system.model import load_profile_snapshot
from profile_system.readme import ReadmeDataError, load_readme_composition
from profile_system.readme_composer import render_profile_readme
from profile_system.svg_kernel import SvgKernelError

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSITION_PATH = REPOSITORY_ROOT / "profile" / "readme.json"
PROFILE_PATH = REPOSITORY_ROOT / "profile" / "profile.json"


def _source() -> dict[str, object]:
    value = json.loads(COMPOSITION_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_source(tmp_path: Path, source: dict[str, object]) -> Path:
    path = tmp_path / "readme.json"
    path.write_text(
        json.dumps(source, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def test_composition_contract_loads_the_publication_surface() -> None:
    composition = load_readme_composition(COMPOSITION_PATH)

    assert composition.schema_version == 1
    assert composition.composition_id == "github-profile-readme"
    assert composition.profile_id == "michal-planeta"
    assert composition.theme_id == "planetary-observatory"
    assert composition.hero_asset.as_posix() == (
        "assets/generated/hero/identity-observatory.svg"
    )
    assert composition.sections_asset.as_posix() == (
        "assets/generated/sections/engineering-sections.svg"
    )
    assert composition.asset_width_percent == 100
    assert composition.license_path.as_posix() == "LICENSE"


def test_composition_rejects_unexpected_fields(tmp_path: Path) -> None:
    source = _source()
    source["unsupported"] = True

    with pytest.raises(ReadmeDataError, match="unsupported fields"):
        load_readme_composition(_write_source(tmp_path, source))


def test_composition_rejects_parent_path_traversal(tmp_path: Path) -> None:
    source = _source()
    source["heroAsset"] = "../identity.svg"

    with pytest.raises(ReadmeDataError, match="repository-relative"):
        load_readme_composition(_write_source(tmp_path, source))


def test_composition_rejects_external_asset_paths(tmp_path: Path) -> None:
    source = _source()
    source["sectionsAsset"] = "https://example.com/sections.svg"

    with pytest.raises(ReadmeDataError, match="repository-relative"):
        load_readme_composition(_write_source(tmp_path, source))


def test_composition_rejects_changed_rights_notice(tmp_path: Path) -> None:
    source = _source()
    source["copyrightNotice"] = "Copyright 2026"

    with pytest.raises(ReadmeDataError, match="copyrightNotice"):
        load_readme_composition(_write_source(tmp_path, source))


def test_readme_rendering_is_byte_deterministic() -> None:
    composition = load_readme_composition(COMPOSITION_PATH)
    profile = load_profile_snapshot(PROFILE_PATH)

    first = render_profile_readme(composition, profile)
    second = render_profile_readme(composition, profile)

    assert first == second
    assert first.endswith("\n")


def test_readme_composes_relative_assets_and_canonical_identity() -> None:
    composition = load_readme_composition(COMPOSITION_PATH)
    profile = load_profile_snapshot(PROFILE_PATH)

    document = render_profile_readme(composition, profile)

    assert document.count("<img ") == 2
    assert "./assets/generated/hero/identity-observatory.svg" in document
    assert "./assets/generated/sections/engineering-sections.svg" in document
    assert profile.display_name in document
    assert profile.identity.headline in document
    assert profile.identity.role in document
    assert profile.identity.motto in document
    assert profile.identity.summary in document
    assert 'href="./LICENSE"' in document
    assert "shields.io" not in document


def test_readme_uses_only_the_public_project_projection() -> None:
    composition = load_readme_composition(COMPOSITION_PATH)
    profile = load_profile_snapshot(PROFILE_PATH)
    hidden = Project(
        project_id="private-system",
        name="Private System",
        summary="This project must not enter the public README.",
        status="experimental",
        public=False,
        featured=False,
        priority=999,
        technology_ids=(),
        evidence_ids=(),
        link_ids=(),
    )
    extended = replace(profile, projects=profile.projects + (hidden,))

    document = render_profile_readme(composition, extended)

    assert "Private System" not in document
    assert "This project must not enter the public README." not in document


def test_readme_escapes_canonical_text_before_emitting_html() -> None:
    composition = load_readme_composition(COMPOSITION_PATH)
    profile = load_profile_snapshot(PROFILE_PATH)
    changed_identity = Identity(
        headline=profile.identity.headline,
        role="Systems <Rendering> & Verification",
        motto=profile.identity.motto,
        summary='Architecture "under test" <must remain text>.',
    )
    changed = replace(
        profile,
        display_name="Michał <Planeta>",
        identity=changed_identity,
    )

    document = render_profile_readme(composition, changed)

    assert "Michał &lt;Planeta&gt;" in document
    assert "Systems &lt;Rendering&gt; &amp; Verification" in document
    assert "&lt;must remain text&gt;" in document
    assert "<must remain text>" not in document


def test_readme_rejects_profile_or_theme_mismatch() -> None:
    composition = load_readme_composition(COMPOSITION_PATH)
    profile = load_profile_snapshot(PROFILE_PATH)

    with pytest.raises(SvgKernelError, match="profileId"):
        render_profile_readme(
            replace(composition, profile_id="different-profile"),
            profile,
        )

    with pytest.raises(SvgKernelError, match="themeId"):
        render_profile_readme(
            replace(composition, theme_id="different-theme"),
            profile,
        )
