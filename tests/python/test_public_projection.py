from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from profile_system.manifest import render_profile_manifest
from profile_system.model import ProfileDataError, load_profile_snapshot
from profile_system.publication import project_public_profile


def base_document() -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "profileId": "michal-planeta",
        "displayName": "Michał Planeta",
        "environmentId": "planetary-observatory",
        "identity": {
            "headline": "A — CINEMATIC SYSTEMS ENGINEER",
            "role": "Software engineer.",
            "motto": "Build and verify.",
            "summary": "Repository-grounded engineering profile.",
        },
        "projects": [
            {
                "id": "later-project",
                "name": "Later Project",
                "summary": "Second public project.",
                "status": "active",
                "public": True,
                "featured": False,
                "priority": 20,
                "technologyIds": ["python"],
                "evidenceIds": ["later-tests"],
                "linkIds": [],
            },
            {
                "id": "first-project",
                "name": "First Project",
                "summary": "First public project.",
                "status": "completed",
                "public": True,
                "featured": True,
                "priority": 10,
                "technologyIds": ["python"],
                "evidenceIds": ["first-tests", "private-notes"],
                "linkIds": ["public-link", "private-link"],
            },
            {
                "id": "private-project",
                "name": "Private Project",
                "summary": "Nonpublic project.",
                "status": "experimental",
                "public": False,
                "featured": False,
                "priority": 0,
                "technologyIds": [],
                "evidenceIds": ["private-notes"],
                "linkIds": ["private-link"],
            },
        ],
        "evidence": [
            {
                "id": "first-tests",
                "kind": "tests",
                "label": "First tests",
                "summary": "Public verification.",
                "public": True,
                "linkId": None,
            },
            {
                "id": "later-tests",
                "kind": "tests",
                "label": "Later tests",
                "summary": "Public verification.",
                "public": True,
                "linkId": None,
            },
            {
                "id": "private-notes",
                "kind": "documentation",
                "label": "Private notes",
                "summary": "Nonpublic details.",
                "public": False,
                "linkId": None,
            },
        ],
        "technologies": [
            {
                "id": "python",
                "name": "Python",
                "category": "language",
                "usage": "Validation and generation.",
                "public": True,
                "projectIds": ["first-project", "private-project"],
                "evidenceIds": ["first-tests", "private-notes"],
            }
        ],
        "disciplines": [
            {
                "id": "software-architecture",
                "name": "Software Architecture",
                "summary": "Clear boundaries.",
                "public": True,
                "projectIds": ["first-project", "private-project"],
                "evidenceIds": ["first-tests", "private-notes"],
            }
        ],
        "links": [
            {
                "id": "public-link",
                "label": "Public link",
                "kind": "repository",
                "url": "https://github.com/example/public",
                "public": True,
            },
            {
                "id": "private-link",
                "label": "Private link",
                "kind": "documentation",
                "url": "https://example.com/private",
                "public": False,
            },
        ],
    }


def load_document(document: dict[str, object]):
    with tempfile.TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / "profile.json"
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return load_profile_snapshot(path)


class PublicProjectionTests(unittest.TestCase):
    def test_projection_filters_nonpublic_records_and_references(self) -> None:
        public_profile = project_public_profile(load_document(base_document()))

        self.assertEqual(
            ["first-project", "later-project"],
            [project.project_id for project in public_profile.projects],
        )
        self.assertEqual(
            ("first-tests",),
            public_profile.projects[0].evidence_ids,
        )
        self.assertEqual(
            ("public-link",),
            public_profile.projects[0].link_ids,
        )
        self.assertEqual(
            ("first-project",),
            public_profile.technologies[0].project_ids,
        )
        self.assertEqual(
            ("first-tests",),
            public_profile.technologies[0].evidence_ids,
        )
        self.assertNotIn(
            "private-project",
            {project.project_id for project in public_profile.projects},
        )

    def test_public_project_requires_public_evidence(self) -> None:
        document = base_document()
        document["projects"][0]["public"] = False
        document["projects"][1]["evidenceIds"] = ["private-notes"]

        with self.assertRaisesRegex(
            ProfileDataError,
            "Public project first-project has no public evidence",
        ):
            project_public_profile(load_document(document))

    def test_public_technology_requires_public_dependency(self) -> None:
        document = base_document()
        document["technologies"][0]["projectIds"] = ["private-project"]
        document["technologies"][0]["evidenceIds"] = ["private-notes"]

        with self.assertRaisesRegex(
            ProfileDataError,
            "Public technology python has no public dependency",
        ):
            project_public_profile(load_document(document))

    def test_public_discipline_requires_public_dependency(self) -> None:
        document = base_document()
        document["disciplines"][0]["projectIds"] = ["private-project"]
        document["disciplines"][0]["evidenceIds"] = ["private-notes"]

        with self.assertRaisesRegex(
            ProfileDataError,
            "Public discipline software-architecture has no public dependency",
        ):
            project_public_profile(load_document(document))

    def test_manifest_contains_no_nonpublic_identifier_or_summary(self) -> None:
        manifest = render_profile_manifest(load_document(base_document()))

        self.assertNotIn("private-project", manifest)
        self.assertNotIn("private-notes", manifest)
        self.assertNotIn("Nonpublic details", manifest)
        self.assertIn('"schemaVersion": 2', manifest)


if __name__ == "__main__":
    unittest.main()
