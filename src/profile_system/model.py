from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_SCHEMA_VERSION = 1


class ProfileDataError(ValueError):
    """Raised when authored profile data violates its contract."""


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    schema_version: int
    profile_id: str
    display_name: str
    environment_id: str


def _require_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProfileDataError("Profile source must contain a JSON object")

    return cast(dict[str, object], value)


def _require_string(
    source: dict[str, object],
    field_name: str,
) -> str:
    value = source.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise ProfileDataError(f"{field_name} must contain a non-empty string")

    return value.strip()


def _require_integer(
    source: dict[str, object],
    field_name: str,
) -> int:
    value = source.get(field_name)

    if isinstance(value, bool) or not isinstance(value, int):
        raise ProfileDataError(f"{field_name} must contain an integer")

    return value


def load_profile_snapshot(path: Path) -> ProfileSnapshot:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    source = _require_mapping(raw)

    schema_version = _require_integer(
        source,
        "schemaVersion",
    )

    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ProfileDataError(f"Unsupported schemaVersion: {schema_version}")

    return ProfileSnapshot(
        schema_version=schema_version,
        profile_id=_require_string(
            source,
            "profileId",
        ),
        display_name=_require_string(
            source,
            "displayName",
        ),
        environment_id=_require_string(
            source,
            "environmentId",
        ),
    )
