from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
PROBE_SOURCE = REPOSITORY_ROOT / "profile" / "probes" / "github-svg-capabilities.json"
COMMITTED_PROBE = (
    REPOSITORY_ROOT / "assets" / "generated" / "probes" / "github-svg-capabilities.svg"
)


class ProbeCliTests(unittest.TestCase):
    def run_probe(
        self,
        output_path: Path,
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
                "probe",
                "--source",
                str(PROBE_SOURCE),
                "--output",
                str(output_path),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_probe_command_writes_deterministic_svg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            first_output = temporary_root / "first.svg"
            second_output = temporary_root / "second.svg"

            first_result = self.run_probe(first_output)
            second_result = self.run_probe(second_output)

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

            self.assertEqual(
                first_output.read_bytes(),
                second_output.read_bytes(),
            )
            self.assertEqual(
                COMMITTED_PROBE.read_bytes(),
                first_output.read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
