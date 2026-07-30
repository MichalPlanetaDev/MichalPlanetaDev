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


class HeroCliTests(unittest.TestCase):
    def run_hero(
        self,
        hero_source: Path,
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
                "hero",
                "--profile",
                "profile/profile.json",
                "--hero",
                str(hero_source),
                "--scene",
                "profile/scenes/planetary-observatory.json",
                "--tokens",
                "profile/design-tokens.json",
                "--output",
                str(output),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_generates_identical_hero_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.svg"
            second = root / "second.svg"
            hero_source = REPOSITORY_ROOT / "profile" / "hero.json"

            first_result = self.run_hero(hero_source, first)
            second_result = self.run_hero(hero_source, second)

            self.assertEqual(0, first_result.returncode, first_result.stderr)
            self.assertEqual(0, second_result.returncode, second_result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_cli_rejects_profile_identifier_mismatch_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = json.loads(
                (REPOSITORY_ROOT / "profile" / "hero.json").read_text(encoding="utf-8")
            )
            source["profileId"] = "different-profile"
            hero_source = root / "hero.json"
            output = root / "hero.svg"
            hero_source.write_text(json.dumps(source), encoding="utf-8")

            result = self.run_hero(hero_source, output)

            self.assertEqual(2, result.returncode)
            self.assertIn("profileId does not match", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
