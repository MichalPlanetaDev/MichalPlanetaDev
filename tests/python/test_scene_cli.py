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
SCENE_SOURCE = REPOSITORY_ROOT / "profile/scenes/planetary-observatory.json"
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"
COMMITTED_SCENE = REPOSITORY_ROOT / "assets/generated/scenes/planetary-observatory.svg"


class SceneCliTests(unittest.TestCase):
    def run_scene(
        self,
        source: Path,
        output: Path,
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
                "scene",
                "--source",
                str(source),
                "--tokens",
                str(TOKEN_SOURCE),
                "--output",
                str(output),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_scene_command_is_deterministic_and_matches_committed_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.svg"
            second = root / "second.svg"

            first_result = self.run_scene(SCENE_SOURCE, first)
            second_result = self.run_scene(SCENE_SOURCE, second)

            self.assertEqual(0, first_result.returncode, first_result.stderr)
            self.assertEqual(0, second_result.returncode, second_result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(COMMITTED_SCENE.read_bytes(), first.read_bytes())

    def test_invalid_scene_returns_two_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "invalid.json"
            output = root / "scene.svg"
            source.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "sceneId": "planetary-observatory",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_scene(source, output)

            self.assertEqual(2, result.returncode)
            self.assertIn("is missing fields", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
