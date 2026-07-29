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

    def test_identical_input_produces_identical_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source = temporary_root / "profile.json"
            first_output = temporary_root / "first"
            second_output = temporary_root / "second"

            source.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "profileId": "michal-planeta",
                        "displayName": "Michał Płaneta",
                        "environmentId": "planetary-observatory",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            first_result = self.run_build(source, first_output)
            second_result = self.run_build(source, second_output)

            self.assertEqual(
                0,
                first_result.returncode,
                first_result.stderr,
            )
            self.assertEqual(
                0,
                second_result.returncode,
                second_result.stderr,
            )

            first_manifest = (first_output / "profile-manifest.json").read_bytes()
            second_manifest = (second_output / "profile-manifest.json").read_bytes()

            self.assertEqual(first_manifest, second_manifest)

            expected_document = {
                "displayName": "Michał Płaneta",
                "environmentId": "planetary-observatory",
                "generator": {
                    "name": "profile-system",
                    "version": "0.1.0",
                },
                "profileId": "michal-planeta",
                "schemaVersion": 1,
            }

            self.assertEqual(
                json.dumps(
                    expected_document,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                first_manifest.decode("utf-8"),
            )

    def test_unsupported_schema_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source = temporary_root / "profile.json"
            output_directory = temporary_root / "output"

            source.write_text(
                json.dumps(
                    {
                        "schemaVersion": 2,
                        "profileId": "michal-planeta",
                        "displayName": "Michał Płaneta",
                        "environmentId": "planetary-observatory",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_build(
                source,
                output_directory,
            )

            self.assertEqual(
                2,
                result.returncode,
                "Unsupported schema version was accepted",
            )
            self.assertIn(
                "Unsupported schemaVersion: 2",
                result.stderr,
            )
            self.assertFalse((output_directory / "profile-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
