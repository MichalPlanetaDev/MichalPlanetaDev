from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from profile_system.model import ProfileDataError, load_profile_snapshot

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PROFILE = REPOSITORY_ROOT / "profile" / "profile.json"


def valid_document() -> dict[str, object]:
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
                "id": "alpha-project",
                "name": "Alpha Project",
                "summary": "Public project.",
                "status": "active",
                "public": True,
                "featured": True,
                "priority": 10,
                "technologyIds": ["python"],
                "evidenceIds": ["alpha-tests"],
                "linkIds": ["alpha-repository-link"],
            }
        ],
        "evidence": [
            {
                "id": "alpha-tests",
                "kind": "tests",
                "label": "Alpha tests",
                "summary": "Behavioral verification.",
                "public": True,
                "linkId": None,
            }
        ],
        "technologies": [
            {
                "id": "python",
                "name": "Python",
                "category": "language",
                "usage": "Validation and generation.",
                "public": True,
                "projectIds": ["alpha-project"],
                "evidenceIds": ["alpha-tests"],
            }
        ],
        "disciplines": [
            {
                "id": "software-architecture",
                "name": "Software Architecture",
                "summary": "Clear boundaries.",
                "public": True,
                "projectIds": ["alpha-project"],
                "evidenceIds": ["alpha-tests"],
            }
        ],
        "links": [
            {
                "id": "alpha-repository-link",
                "label": "Alpha repository",
                "kind": "repository",
                "url": "https://github.com/example/alpha",
                "public": True,
            }
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


class ProfileContentTests(unittest.TestCase):
    def test_repository_profile_loads_schema_two_content(self) -> None:
        snapshot = load_profile_snapshot(REPOSITORY_PROFILE)

        self.assertEqual(2, snapshot.schema_version)
        self.assertEqual("michal-planeta", snapshot.profile_id)
        self.assertEqual(2, len(snapshot.projects))
        self.assertGreaterEqual(len(snapshot.technologies), 10)
        self.assertEqual(4, len(snapshot.disciplines))

    def test_unknown_top_level_field_is_rejected(self) -> None:
        document = valid_document()
        document["unexpected"] = True

        with self.assertRaisesRegex(
            ProfileDataError,
            "Profile source contains unsupported fields: unexpected",
        ):
            load_document(document)

    def test_duplicate_identifier_within_collection_is_rejected(self) -> None:
        document = valid_document()
        project = copy.deepcopy(document["projects"][0])
        document["projects"].append(project)

        with self.assertRaisesRegex(
            ProfileDataError,
            "Duplicate identifier in projects: alpha-project",
        ):
            load_document(document)

    def test_duplicate_identifier_across_collections_is_rejected(self) -> None:
        document = valid_document()
        document["technologies"][0]["id"] = "alpha-project"
        document["projects"][0]["technologyIds"] = ["alpha-project"]

        with self.assertRaisesRegex(
            ProfileDataError,
            "Duplicate global identifier alpha-project",
        ):
            load_document(document)

    def test_duplicate_reference_is_rejected(self) -> None:
        document = valid_document()
        document["projects"][0]["evidenceIds"] = ["alpha-tests", "alpha-tests"]

        with self.assertRaisesRegex(
            ProfileDataError,
            r"Duplicate reference in Profile source.projects\[0\].evidenceIds",
        ):
            load_document(document)

    def test_unresolved_reference_is_rejected(self) -> None:
        document = valid_document()
        document["projects"][0]["technologyIds"] = ["missing-technology"]

        with self.assertRaisesRegex(
            ProfileDataError,
            "Unresolved reference in project alpha-project: missing-technology",
        ):
            load_document(document)

    def test_unpublished_project_cannot_be_public(self) -> None:
        document = valid_document()
        document["projects"][0]["status"] = "unpublished"

        with self.assertRaisesRegex(
            ProfileDataError,
            "Project alpha-project with status unpublished must not be public",
        ):
            load_document(document)

    def test_nonpublic_project_cannot_be_featured(self) -> None:
        document = valid_document()
        document["projects"][0]["public"] = False

        with self.assertRaisesRegex(
            ProfileDataError,
            "Project alpha-project must not be featured when public is false",
        ):
            load_document(document)

    def test_invalid_link_url_is_rejected(self) -> None:
        document = valid_document()
        document["links"][0]["url"] = "http://example.com/alpha"

        with self.assertRaisesRegex(
            ProfileDataError,
            "must contain an absolute https URL or contact mailto URL",
        ):
            load_document(document)


if __name__ == "__main__":
    unittest.main()
