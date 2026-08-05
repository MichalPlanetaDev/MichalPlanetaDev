from __future__ import annotations

import errno
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from profile_system.cli import main

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"


class FrontendTokenCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.css_output = self.root / "design-tokens.css"
        self.typescript_output = self.root / "design-tokens.ts"

    def command(self, source: Path = TOKEN_SOURCE) -> list[str]:
        return [
            "frontend-tokens",
            "--source",
            str(source),
            "--css-output",
            str(self.css_output),
            "--typescript-output",
            str(self.typescript_output),
        ]

    def test_frontend_tokens_writes_matching_artifacts(self) -> None:
        exit_code = main(self.command())

        self.assertEqual(0, exit_code)
        css = self.css_output.read_text(encoding="utf-8")
        typescript = self.typescript_output.read_text(encoding="utf-8")
        css_fingerprint = re.search(
            r"/\* fingerprint: ([0-9a-f]{64}) \*/",
            css,
        )
        typescript_fingerprint = re.search(
            r'fingerprint: "([0-9a-f]{64})"',
            typescript,
        )

        self.assertIsNotNone(css_fingerprint)
        self.assertIsNotNone(typescript_fingerprint)
        self.assertEqual(
            css_fingerprint.group(1) if css_fingerprint else "",
            typescript_fingerprint.group(1) if typescript_fingerprint else "",
        )
        self.assertIn("--cr-surface-canvas", css)
        self.assertIn("export const designTokens", typescript)

    def test_invalid_source_preserves_existing_outputs(self) -> None:
        invalid_source = self.root / "invalid.json"
        invalid_source.write_text("{}\n", encoding="utf-8")
        self.css_output.write_text("old css\n", encoding="utf-8")
        self.typescript_output.write_text("old ts\n", encoding="utf-8")

        exit_code = main(self.command(invalid_source))

        self.assertEqual(2, exit_code)
        self.assertEqual(
            "old css\n",
            self.css_output.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "old ts\n",
            self.typescript_output.read_text(encoding="utf-8"),
        )

    def test_identical_output_paths_are_rejected_without_writing(self) -> None:
        exit_code = main(
            [
                "frontend-tokens",
                "--source",
                str(TOKEN_SOURCE),
                "--css-output",
                str(self.css_output),
                "--typescript-output",
                str(self.css_output),
            ]
        )

        self.assertEqual(2, exit_code)
        self.assertFalse(self.css_output.exists())

    def test_second_replacement_failure_restores_both_destinations(self) -> None:
        self.css_output.write_text("old css\n", encoding="utf-8")
        self.typescript_output.write_text("old ts\n", encoding="utf-8")
        original_replace = __import__("os").replace

        def replace_with_second_destination_failure(
            source: str | Path,
            destination: str | Path,
        ) -> None:
            if Path(destination) == self.typescript_output:
                raise OSError(
                    errno.EIO,
                    "simulated TypeScript replacement failure",
                    str(destination),
                )
            original_replace(source, destination)

        with patch(
            "profile_system.cli.os.replace",
            side_effect=replace_with_second_destination_failure,
        ):
            exit_code = main(self.command())

        self.assertEqual(2, exit_code)
        self.assertEqual(
            "old css\n",
            self.css_output.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "old ts\n",
            self.typescript_output.read_text(encoding="utf-8"),
        )
        residue = sorted(
            path.name for path in self.root.iterdir() if path.name.startswith(".")
        )
        self.assertEqual([], residue)


if __name__ == "__main__":
    unittest.main()
