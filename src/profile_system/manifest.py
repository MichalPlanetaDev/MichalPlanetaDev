from __future__ import annotations

import json

from profile_system import __version__
from profile_system.model import ProfileSnapshot
from profile_system.publication import project_public_profile


def _collection(ids: tuple[str, ...]) -> dict[str, object]:
    return {
        "count": len(ids),
        "ids": list(ids),
    }


def render_profile_manifest(snapshot: ProfileSnapshot) -> str:
    public_profile = project_public_profile(snapshot)
    document = {
        "displayName": public_profile.display_name,
        "environmentId": public_profile.environment_id,
        "generator": {
            "name": "profile-system",
            "version": __version__,
        },
        "identity": {
            "headline": public_profile.identity.headline,
            "role": public_profile.identity.role,
        },
        "profileId": public_profile.profile_id,
        "publicContent": {
            "disciplines": _collection(
                tuple(record.discipline_id for record in public_profile.disciplines)
            ),
            "evidence": _collection(
                tuple(record.evidence_id for record in public_profile.evidence)
            ),
            "links": _collection(
                tuple(record.link_id for record in public_profile.links)
            ),
            "projects": _collection(
                tuple(record.project_id for record in public_profile.projects)
            ),
            "technologies": _collection(
                tuple(record.technology_id for record in public_profile.technologies)
            ),
        },
        "schemaVersion": public_profile.schema_version,
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
