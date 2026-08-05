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
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"


class TokenCliTests(unittest.TestCase):
    def run_tokens(
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
                "tokens",
                "--source",
                str(source),
                "--output",
                str(output),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_identical_input_produces_identical_visual_grammar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_output = root / "first.json"
            second_output = root / "second.json"

            first_result = self.run_tokens(TOKEN_SOURCE, first_output)
            second_result = self.run_tokens(TOKEN_SOURCE, second_output)

            self.assertEqual(0, first_result.returncode, first_result.stderr)
            self.assertEqual(0, second_result.returncode, second_result.stderr)
            self.assertEqual(first_output.read_bytes(), second_output.read_bytes())

            document = json.loads(first_output.read_text(encoding="utf-8"))
            self.assertEqual(2, document["schemaVersion"])
            self.assertEqual("planetary-observatory", document["themeId"])
            self.assertEqual(14, document["groups"]["colors"]["count"])
            self.assertEqual(
                [
                    '"SFMono-Regular"',
                    "Consolas",
                    '"Liberation Mono"',
                    "monospace",
                ],
                document["groups"]["typography"]["monoStack"],
            )
            self.assertEqual(120, document["groups"]["motion"]["duration"]["fast"])
            self.assertEqual(
                "background.void",
                document["semantic"]["surface"]["canvas"]["reference"],
            )
            self.assertEqual("static-github", document["rules"]["motion"])
            self.assertTrue(all(record["passes"] for record in document["contrast"]))

    def test_invalid_source_returns_two_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "invalid.json"
            output = root / "visual-grammar.json"
            source.write_text("{}\n", encoding="utf-8")

            result = self.run_tokens(source, output)

            self.assertEqual(2, result.returncode)
            self.assertIn("missing fields", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
