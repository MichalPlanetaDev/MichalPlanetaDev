from __future__ import annotations

import json

from profile_system import __version__
from profile_system.model import ProfileSnapshot


def render_profile_manifest(snapshot: ProfileSnapshot) -> str:
    document = {
        "displayName": snapshot.display_name,
        "environmentId": snapshot.environment_id,
        "generator": {
            "name": "profile-system",
            "version": __version__,
        },
        "profileId": snapshot.profile_id,
        "schemaVersion": snapshot.schema_version,
    }

    return (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
