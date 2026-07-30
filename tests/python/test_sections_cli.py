from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from profile_system.cli import main

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SECTIONS_SOURCE = REPOSITORY_ROOT / "profile" / "sections.json"
PROFILE_SOURCE = REPOSITORY_ROOT / "profile" / "profile.json"
TOKEN_SOURCE = REPOSITORY_ROOT / "profile" / "design-tokens.json"


class SectionsCliTests(unittest.TestCase):
    def test_sections_command_writes_the_expected_svg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "engineering-sections.svg"
            exit_code = main(
                [
                    "sections",
                    "--source",
                    str(SECTIONS_SOURCE),
                    "--profile",
                    str(PROFILE_SOURCE),
                    "--tokens",
                    str(TOKEN_SOURCE),
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(0, exit_code)
            document = output.read_text(encoding="utf-8")
            self.assertIn('viewBox="0 0 1200 1760"', document)
            self.assertIn("sections-projects", document)
            self.assertIn("Copyright © 2026 Michał Planeta", document)

    def test_invalid_sections_source_returns_two_without_output(self) -> None:
        source = json.loads(SECTIONS_SOURCE.read_text(encoding="utf-8"))
        source["sectionOrder"] = ["connect"]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid_source = root / "invalid-sections.json"
            output = root / "engineering-sections.svg"
            invalid_source.write_text(json.dumps(source), encoding="utf-8")
            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                exit_code = main(
                    [
                        "sections",
                        "--source",
                        str(invalid_source),
                        "--profile",
                        str(PROFILE_SOURCE),
                        "--tokens",
                        str(TOKEN_SOURCE),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(2, exit_code)
            self.assertFalse(output.exists())
            self.assertIn("sectionOrder must equal", errors.getvalue())
