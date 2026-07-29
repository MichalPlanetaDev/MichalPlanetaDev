from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"


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
                "priority": 20,
                "technologyIds": ["python"],
                "evidenceIds": ["alpha-tests"],
                "linkIds": ["alpha-repository-link"],
            },
            {
                "id": "internal-project",
                "name": "Internal Project",
                "summary": "Not selected for publication.",
                "status": "experimental",
                "public": False,
                "featured": False,
                "priority": 10,
                "technologyIds": [],
                "evidenceIds": ["internal-notes"],
                "linkIds": [],
            },
        ],
        "evidence": [
            {
                "id": "alpha-tests",
                "kind": "tests",
                "label": "Alpha tests",
                "summary": "Behavioral verification.",
                "public": True,
                "linkId": None,
            },
            {
                "id": "internal-notes",
                "kind": "documentation",
                "label": "Internal notes",
                "summary": "Nonpublic record.",
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
                "projectIds": ["alpha-project", "internal-project"],
                "evidenceIds": ["alpha-tests", "internal-notes"],
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


class BuildCliTests(unittest.TestCase):
    def run_build(
        self,
        source: Path,
        output_directory: Path,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SOURCE_ROOT)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        return subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "profile_system",
                "build",
                "--source",
                str(source),
                "--output-dir",
                str(output_directory),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_identical_input_produces_public_only_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source = temporary_root / "profile.json"
            first_output = temporary_root / "first"
            second_output = temporary_root / "second"
            source.write_text(
                json.dumps(valid_document(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            first_result = self.run_build(source, first_output)
            second_result = self.run_build(source, second_output)

            self.assertEqual(0, first_result.returncode, first_result.stderr)
            self.assertEqual(0, second_result.returncode, second_result.stderr)

            first_manifest = (first_output / "profile-manifest.json").read_bytes()
            second_manifest = (second_output / "profile-manifest.json").read_bytes()
            self.assertEqual(first_manifest, second_manifest)

            document = json.loads(first_manifest)
            self.assertEqual(2, document["schemaVersion"])
            self.assertEqual(
                {"count": 1, "ids": ["alpha-project"]},
                document["publicContent"]["projects"],
            )
            self.assertEqual(
                {"count": 1, "ids": ["python"]},
                document["publicContent"]["technologies"],
            )
            self.assertNotIn("internal-project", first_manifest.decode("utf-8"))
            self.assertNotIn("internal-notes", first_manifest.decode("utf-8"))
            self.assertNotIn(
                "Not selected for publication",
                first_manifest.decode("utf-8"),
            )

    def test_schema_version_one_is_rejected_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source = temporary_root / "profile.json"
            output_directory = temporary_root / "output"
            document = valid_document()
            document["schemaVersion"] = 1
            source.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_build(source, output_directory)

            self.assertEqual(2, result.returncode)
            self.assertIn("Unsupported schemaVersion: 1", result.stderr)
            self.assertFalse((output_directory / "profile-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
