from __future__ import annotations

import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from dataclasses import replace
from pathlib import Path

from profile_system.design_tokens import load_design_token_snapshot
from profile_system.engineering_sections import render_engineering_sections
from profile_system.model import load_profile_snapshot
from profile_system.sections import SectionsDataError, load_engineering_sections
from profile_system.svg_kernel import SvgKernelError

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SECTIONS_SOURCE = REPOSITORY_ROOT / "profile" / "sections.json"
PROFILE_SOURCE = REPOSITORY_ROOT / "profile" / "profile.json"
TOKEN_SOURCE = REPOSITORY_ROOT / "profile" / "design-tokens.json"


class EngineeringSectionsTests(unittest.TestCase):
    def _render(self) -> str:
        return render_engineering_sections(
            load_engineering_sections(SECTIONS_SOURCE),
            load_profile_snapshot(PROFILE_SOURCE),
            load_design_token_snapshot(TOKEN_SOURCE),
        )

    def test_contract_loads_the_approved_surface(self) -> None:
        snapshot = load_engineering_sections(SECTIONS_SOURCE)

        self.assertEqual(1, snapshot.schema_version)
        self.assertEqual("engineering-sections", snapshot.section_set_id)
        self.assertEqual("planetary-observatory", snapshot.theme_id)
        self.assertEqual(
            (1200, 1760),
            (snapshot.viewport.width, snapshot.viewport.height),
        )
        self.assertEqual(
            ("projects", "stack", "evidence", "disciplines", "connect"),
            snapshot.section_order,
        )
        self.assertEqual(11, snapshot.maximum_technologies)

    def test_contract_rejects_unknown_fields(self) -> None:
        source = json.loads(SECTIONS_SOURCE.read_text(encoding="utf-8"))
        source["unexpected"] = True

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sections.json"
            path.write_text(json.dumps(source), encoding="utf-8")

            with self.assertRaisesRegex(
                SectionsDataError,
                "contains unsupported fields: unexpected",
            ):
                load_engineering_sections(path)

    def test_contract_rejects_wrong_section_order(self) -> None:
        source = json.loads(SECTIONS_SOURCE.read_text(encoding="utf-8"))
        source["sectionOrder"] = list(reversed(source["sectionOrder"]))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sections.json"
            path.write_text(json.dumps(source), encoding="utf-8")

            with self.assertRaisesRegex(
                SectionsDataError,
                "sectionOrder must equal",
            ):
                load_engineering_sections(path)

    def test_contract_rejects_changed_copyright_notice(self) -> None:
        source = json.loads(SECTIONS_SOURCE.read_text(encoding="utf-8"))
        source["copyrightNotice"] = "Copyright changed"

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sections.json"
            path.write_text(json.dumps(source), encoding="utf-8")

            with self.assertRaisesRegex(
                SectionsDataError,
                "copyrightNotice differs",
            ):
                load_engineering_sections(path)

    def test_rendering_is_byte_identical(self) -> None:
        self.assertEqual(self._render(), self._render())

    def test_rendering_contains_the_complete_public_graph(self) -> None:
        document = self._render()
        profile = load_profile_snapshot(PROFILE_SOURCE)

        for project in profile.projects:
            if project.public and project.status != "unpublished":
                self.assertIn(project.name, document)
        for evidence in profile.evidence:
            if evidence.public:
                self.assertIn(evidence.label, document)
        for technology in profile.technologies:
            if technology.public:
                self.assertIn(technology.name, document)
        for discipline in profile.disciplines:
            if discipline.public:
                self.assertIn(discipline.name, document)
        for link in profile.links:
            if link.public:
                self.assertIn(link.label, document)

    def test_rendering_excludes_nonpublic_projects(self) -> None:
        profile = load_profile_snapshot(PROFILE_SOURCE)
        hidden_project = replace(
            profile.projects[0],
            project_id="internal-project",
            name="Internal Project",
            public=False,
            featured=False,
            priority=999,
        )
        extended_profile = replace(
            profile,
            projects=profile.projects + (hidden_project,),
        )
        document = render_engineering_sections(
            load_engineering_sections(SECTIONS_SOURCE),
            extended_profile,
            load_design_token_snapshot(TOKEN_SOURCE),
        )

        self.assertNotIn("Internal Project", document)
        self.assertNotIn("internal-project", document)

    def test_rendering_rejects_theme_mismatch(self) -> None:
        sections = replace(
            load_engineering_sections(SECTIONS_SOURCE),
            theme_id="different-theme",
        )

        with self.assertRaisesRegex(SvgKernelError, "theme does not match"):
            render_engineering_sections(
                sections,
                load_profile_snapshot(PROFILE_SOURCE),
                load_design_token_snapshot(TOKEN_SOURCE),
            )

    def test_rendering_rejects_technology_overflow(self) -> None:
        sections = replace(
            load_engineering_sections(SECTIONS_SOURCE),
            maximum_technologies=8,
        )

        with self.assertRaisesRegex(SvgKernelError, "technology count exceeds"):
            render_engineering_sections(
                sections,
                load_profile_snapshot(PROFILE_SOURCE),
                load_design_token_snapshot(TOKEN_SOURCE),
            )

    def test_svg_policy_and_required_layers(self) -> None:
        root = element_tree.fromstring(self._render())
        identifiers: list[str] = []
        references: set[str] = set()
        forbidden = {
            "animate",
            "animateMotion",
            "animateTransform",
            "foreignObject",
            "image",
            "script",
            "set",
        }

        self.assertEqual("img", root.attrib.get("role"))
        self.assertEqual("0 0 1200 1760", root.attrib.get("viewBox"))

        for element in root.iter():
            name = element.tag.rsplit("}", 1)[-1]
            self.assertNotIn(name, forbidden)
            identifier = element.attrib.get("id")
            if identifier is not None:
                identifiers.append(identifier)
            for attribute_name, value in element.attrib.items():
                local_name = attribute_name.rsplit("}", 1)[-1]
                self.assertFalse(local_name.lower().startswith("on"))
                self.assertNotEqual("href", local_name)
                references.update(re.findall(r"url\(#([a-z0-9-]+)\)", value))

        identifier_set = set(identifiers)
        self.assertEqual(len(identifiers), len(identifier_set))
        self.assertTrue(references.issubset(identifier_set))
        self.assertTrue(
            {
                "sections-projects",
                "sections-stack",
                "sections-evidence",
                "sections-disciplines",
                "sections-connect",
                "sections-copyright",
            }.issubset(identifier_set)
        )
