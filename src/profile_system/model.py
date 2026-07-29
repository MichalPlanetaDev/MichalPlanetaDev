from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from profile_system.content import (
    Discipline,
    Evidence,
    Identity,
    Link,
    ProfileDataError,
    Project,
    Technology,
    parse_disciplines,
    parse_evidence,
    parse_identity,
    parse_links,
    parse_projects,
    parse_technologies,
    require_exact_keys,
    require_identifier_field,
    require_mapping,
    require_non_negative_integer,
    require_text,
)

SUPPORTED_SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    schema_version: int
    profile_id: str
    display_name: str
    environment_id: str
    identity: Identity
    projects: tuple[Project, ...]
    evidence: tuple[Evidence, ...]
    technologies: tuple[Technology, ...]
    disciplines: tuple[Discipline, ...]
    links: tuple[Link, ...]


def _identifier_map(
    records: tuple[object, ...],
    attribute: str,
    collection_name: str,
) -> dict[str, object]:
    mapping: dict[str, object] = {}

    for record in records:
        identifier = getattr(record, attribute)

        if not isinstance(identifier, str):
            raise AssertionError(f"{collection_name} identifier is not a string")

        if identifier in mapping:
            raise ProfileDataError(
                f"Duplicate identifier in {collection_name}: {identifier}"
            )

        mapping[identifier] = record

    return mapping


def _validate_global_identifiers(
    collections: tuple[tuple[str, dict[str, object]], ...],
) -> None:
    owners: dict[str, str] = {}

    for collection_name, mapping in collections:
        for identifier in mapping:
            previous = owners.get(identifier)

            if previous is not None:
                raise ProfileDataError(
                    f"Duplicate global identifier {identifier}: "
                    f"{previous} and {collection_name}"
                )

            owners[identifier] = collection_name


def _require_references(
    identifiers: tuple[str, ...],
    available: dict[str, object],
    context: str,
) -> None:
    for identifier in identifiers:
        if identifier not in available:
            raise ProfileDataError(f"Unresolved reference in {context}: {identifier}")


def _validate_references(snapshot: ProfileSnapshot) -> None:
    project_map = _identifier_map(snapshot.projects, "project_id", "projects")
    evidence_map = _identifier_map(snapshot.evidence, "evidence_id", "evidence")
    technology_map = _identifier_map(
        snapshot.technologies,
        "technology_id",
        "technologies",
    )
    discipline_map = _identifier_map(
        snapshot.disciplines,
        "discipline_id",
        "disciplines",
    )
    link_map = _identifier_map(snapshot.links, "link_id", "links")

    _validate_global_identifiers(
        (
            ("projects", project_map),
            ("evidence", evidence_map),
            ("technologies", technology_map),
            ("disciplines", discipline_map),
            ("links", link_map),
        )
    )

    for project in snapshot.projects:
        context = f"project {project.project_id}"
        _require_references(project.technology_ids, technology_map, context)
        _require_references(project.evidence_ids, evidence_map, context)
        _require_references(project.link_ids, link_map, context)

    for evidence in snapshot.evidence:
        if evidence.link_id is None:
            continue

        if evidence.link_id not in link_map:
            raise ProfileDataError(
                f"Unresolved reference in evidence {evidence.evidence_id}: "
                f"{evidence.link_id}"
            )

        link = link_map[evidence.link_id]

        if evidence.public and isinstance(link, Link) and not link.public:
            raise ProfileDataError(
                f"Public evidence {evidence.evidence_id} references "
                f"nonpublic link {evidence.link_id}"
            )

    for technology in snapshot.technologies:
        context = f"technology {technology.technology_id}"
        _require_references(technology.project_ids, project_map, context)
        _require_references(technology.evidence_ids, evidence_map, context)

    for discipline in snapshot.disciplines:
        context = f"discipline {discipline.discipline_id}"
        _require_references(discipline.project_ids, project_map, context)
        _require_references(discipline.evidence_ids, evidence_map, context)


def load_profile_snapshot(path: Path) -> ProfileSnapshot:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    source = require_mapping(raw, "Profile source")
    require_exact_keys(
        source,
        {
            "schemaVersion",
            "profileId",
            "displayName",
            "environmentId",
            "identity",
            "projects",
            "evidence",
            "technologies",
            "disciplines",
            "links",
        },
        "Profile source",
    )

    schema_version = require_non_negative_integer(
        source,
        "schemaVersion",
        "Profile source",
    )

    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ProfileDataError(f"Unsupported schemaVersion: {schema_version}")

    snapshot = ProfileSnapshot(
        schema_version=schema_version,
        profile_id=require_identifier_field(source, "profileId", "Profile source"),
        display_name=require_text(source, "displayName", "Profile source"),
        environment_id=require_identifier_field(
            source,
            "environmentId",
            "Profile source",
        ),
        identity=parse_identity(source.get("identity")),
        projects=parse_projects(source.get("projects")),
        evidence=parse_evidence(source.get("evidence")),
        technologies=parse_technologies(source.get("technologies")),
        disciplines=parse_disciplines(source.get("disciplines")),
        links=parse_links(source.get("links")),
    )
    _validate_references(snapshot)
    return snapshot


__all__ = [
    "ProfileDataError",
    "ProfileSnapshot",
    "load_profile_snapshot",
]
