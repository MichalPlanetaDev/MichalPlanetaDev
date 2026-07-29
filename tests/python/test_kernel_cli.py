from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"


class KernelCliTests(unittest.TestCase):
    def run_kernel(
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
                "kernel",
                "--tokens",
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

    def test_kernel_command_writes_deterministic_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.svg"
            second = root / "second.svg"

            first_result = self.run_kernel(TOKEN_SOURCE, first)
            second_result = self.run_kernel(TOKEN_SOURCE, second)

            self.assertEqual(0, first_result.returncode, first_result.stderr)
            self.assertEqual(0, second_result.returncode, second_result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertTrue(first.read_text(encoding="utf-8").startswith("<svg"))

    def test_invalid_tokens_do_not_leave_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "invalid.json"
            output = root / "kernel.svg"
            source.write_text("{}\n", encoding="utf-8")

            result = self.run_kernel(source, output)

            self.assertEqual(2, result.returncode)
            self.assertIn("is missing fields", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
