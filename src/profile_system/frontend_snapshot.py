from __future__ import annotations

import json

from profile_system import __version__
from profile_system.content import (
    Discipline,
    Evidence,
    Link,
    Project,
    Technology,
)
from profile_system.model import ProfileSnapshot
from profile_system.publication import project_public_profile


def _project_document(project: Project) -> dict[str, object]:
    return {
        "evidenceIds": list(project.evidence_ids),
        "featured": project.featured,
        "id": project.project_id,
        "linkIds": list(project.link_ids),
        "name": project.name,
        "priority": project.priority,
        "status": project.status,
        "summary": project.summary,
        "technologyIds": list(project.technology_ids),
    }


def _evidence_document(evidence: Evidence) -> dict[str, object]:
    return {
        "id": evidence.evidence_id,
        "kind": evidence.kind,
        "label": evidence.label,
        "linkId": evidence.link_id,
        "summary": evidence.summary,
    }


def _technology_document(technology: Technology) -> dict[str, object]:
    return {
        "category": technology.category,
        "evidenceIds": list(technology.evidence_ids),
        "id": technology.technology_id,
        "name": technology.name,
        "projectIds": list(technology.project_ids),
        "usage": technology.usage,
    }


def _discipline_document(discipline: Discipline) -> dict[str, object]:
    return {
        "evidenceIds": list(discipline.evidence_ids),
        "id": discipline.discipline_id,
        "name": discipline.name,
        "projectIds": list(discipline.project_ids),
        "summary": discipline.summary,
    }


def _link_document(link: Link) -> dict[str, object]:
    return {
        "id": link.link_id,
        "kind": link.kind,
        "label": link.label,
        "url": link.url,
    }


def render_frontend_snapshot(snapshot: ProfileSnapshot) -> str:
    public_profile = project_public_profile(snapshot)
    document = {
        "disciplines": [
            _discipline_document(record) for record in public_profile.disciplines
        ],
        "displayName": public_profile.display_name,
        "environmentId": public_profile.environment_id,
        "evidence": [_evidence_document(record) for record in public_profile.evidence],
        "generator": {
            "name": "profile-system",
            "version": __version__,
        },
        "identity": {
            "headline": public_profile.identity.headline,
            "motto": public_profile.identity.motto,
            "role": public_profile.identity.role,
            "summary": public_profile.identity.summary,
        },
        "links": [_link_document(record) for record in public_profile.links],
        "profileId": public_profile.profile_id,
        "projects": [_project_document(record) for record in public_profile.projects],
        "schemaVersion": 1,
        "sourceSchemaVersion": public_profile.schema_version,
        "technologies": [
            _technology_document(record) for record in public_profile.technologies
        ],
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


__all__ = ["render_frontend_snapshot"]
