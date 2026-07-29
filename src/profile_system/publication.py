from __future__ import annotations

from dataclasses import dataclass, replace

from profile_system.content import (
    Discipline,
    Evidence,
    Identity,
    Link,
    ProfileDataError,
    Project,
    Technology,
)
from profile_system.model import ProfileSnapshot


@dataclass(frozen=True, slots=True)
class PublicProfileSnapshot:
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


def project_public_profile(snapshot: ProfileSnapshot) -> PublicProfileSnapshot:
    public_links = tuple(
        sorted(
            (link for link in snapshot.links if link.public),
            key=lambda item: item.link_id,
        )
    )
    public_link_ids = {link.link_id for link in public_links}

    public_evidence = tuple(
        sorted(
            (record for record in snapshot.evidence if record.public),
            key=lambda item: item.evidence_id,
        )
    )
    public_evidence_ids = {record.evidence_id for record in public_evidence}

    for record in public_evidence:
        if record.link_id is not None and record.link_id not in public_link_ids:
            raise ProfileDataError(
                f"Public evidence {record.evidence_id} depends on nonpublic link "
                f"{record.link_id}"
            )

    public_technology_ids = {
        record.technology_id for record in snapshot.technologies if record.public
    }

    projected_projects: list[Project] = []

    for project in snapshot.projects:
        if not project.public or project.status == "unpublished":
            continue

        technology_ids = tuple(
            identifier
            for identifier in project.technology_ids
            if identifier in public_technology_ids
        )
        evidence_ids = tuple(
            identifier
            for identifier in project.evidence_ids
            if identifier in public_evidence_ids
        )
        link_ids = tuple(
            identifier
            for identifier in project.link_ids
            if identifier in public_link_ids
        )

        if not evidence_ids:
            raise ProfileDataError(
                f"Public project {project.project_id} has no public evidence"
            )

        projected_projects.append(
            replace(
                project,
                technology_ids=technology_ids,
                evidence_ids=evidence_ids,
                link_ids=link_ids,
            )
        )

    public_projects = tuple(
        sorted(projected_projects, key=lambda item: (item.priority, item.project_id))
    )
    public_project_ids = {project.project_id for project in public_projects}

    projected_technologies: list[Technology] = []

    for technology in snapshot.technologies:
        if not technology.public:
            continue

        project_ids = tuple(
            identifier
            for identifier in technology.project_ids
            if identifier in public_project_ids
        )
        evidence_ids = tuple(
            identifier
            for identifier in technology.evidence_ids
            if identifier in public_evidence_ids
        )

        if not project_ids and not evidence_ids:
            raise ProfileDataError(
                f"Public technology {technology.technology_id} has no public dependency"
            )

        projected_technologies.append(
            replace(
                technology,
                project_ids=project_ids,
                evidence_ids=evidence_ids,
            )
        )

    public_technologies = tuple(
        sorted(projected_technologies, key=lambda item: item.technology_id)
    )

    projected_disciplines: list[Discipline] = []

    for discipline in snapshot.disciplines:
        if not discipline.public:
            continue

        project_ids = tuple(
            identifier
            for identifier in discipline.project_ids
            if identifier in public_project_ids
        )
        evidence_ids = tuple(
            identifier
            for identifier in discipline.evidence_ids
            if identifier in public_evidence_ids
        )

        if not project_ids and not evidence_ids:
            raise ProfileDataError(
                f"Public discipline {discipline.discipline_id} has no public dependency"
            )

        projected_disciplines.append(
            replace(
                discipline,
                project_ids=project_ids,
                evidence_ids=evidence_ids,
            )
        )

    public_disciplines = tuple(
        sorted(projected_disciplines, key=lambda item: item.discipline_id)
    )

    return PublicProfileSnapshot(
        schema_version=snapshot.schema_version,
        profile_id=snapshot.profile_id,
        display_name=snapshot.display_name,
        environment_id=snapshot.environment_id,
        identity=snapshot.identity,
        projects=public_projects,
        evidence=public_evidence,
        technologies=public_technologies,
        disciplines=public_disciplines,
        links=public_links,
    )
