from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from profile_system.cli import main
from profile_system.model import load_profile_snapshot
from profile_system.readme import load_readme_composition
from profile_system.readme_composer import render_profile_readme

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSITION_PATH = REPOSITORY_ROOT / "profile" / "readme.json"
PROFILE_PATH = REPOSITORY_ROOT / "profile" / "profile.json"


def test_readme_cli_writes_the_deterministic_document(tmp_path: Path) -> None:
    output = tmp_path / "README.md"

    result = main(
        [
            "readme",
            "--composition",
            str(COMPOSITION_PATH),
            "--profile",
            str(PROFILE_PATH),
            "--output",
            str(output),
        ]
    )

    expected = render_profile_readme(
        load_readme_composition(COMPOSITION_PATH),
        load_profile_snapshot(PROFILE_PATH),
    )
    assert result == 0
    assert output.read_text(encoding="utf-8") == expected


def test_readme_cli_reports_invalid_composition(
    tmp_path: Path,
    capsys: Any,
) -> None:
    invalid = tmp_path / "readme.json"
    output = tmp_path / "README.md"
    invalid.write_text(
        json.dumps({"schemaVersion": 999}) + "\n",
        encoding="utf-8",
    )

    result = main(
        [
            "readme",
            "--composition",
            str(invalid),
            "--profile",
            str(PROFILE_PATH),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "profile-system:" in captured.err
    assert not output.exists()
