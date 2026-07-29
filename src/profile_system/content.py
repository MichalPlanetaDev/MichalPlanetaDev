from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, cast
from urllib.parse import urlparse

ProjectStatus = Literal["completed", "active", "experimental", "unpublished"]
EvidenceKind = Literal[
    "repository",
    "demo",
    "documentation",
    "tests",
    "architecture",
    "benchmark",
    "diagram",
    "artifact",
]
TechnologyCategory = Literal[
    "language",
    "framework",
    "runtime",
    "database",
    "graphics",
    "testing",
    "automation",
    "tool",
    "platform",
]
LinkKind = Literal[
    "repository",
    "demo",
    "documentation",
    "profile",
    "contact",
    "artifact",
]

IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PROJECT_STATUSES = frozenset({"completed", "active", "experimental", "unpublished"})
EVIDENCE_KINDS = frozenset(
    {
        "repository",
        "demo",
        "documentation",
        "tests",
        "architecture",
        "benchmark",
        "diagram",
        "artifact",
    }
)
TECHNOLOGY_CATEGORIES = frozenset(
    {
        "language",
        "framework",
        "runtime",
        "database",
        "graphics",
        "testing",
        "automation",
        "tool",
        "platform",
    }
)
LINK_KINDS = frozenset(
    {
        "repository",
        "demo",
        "documentation",
        "profile",
        "contact",
        "artifact",
    }
)


class ProfileDataError(ValueError):
    """Raised when authored profile data violates its contract."""


@dataclass(frozen=True, slots=True)
class Identity:
    headline: str
    role: str
    motto: str
    summary: str


@dataclass(frozen=True, slots=True)
class Project:
    project_id: str
    name: str
    summary: str
    status: ProjectStatus
    public: bool
    featured: bool
    priority: int
    technology_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    link_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    kind: EvidenceKind
    label: str
    summary: str
    public: bool
    link_id: str | None


@dataclass(frozen=True, slots=True)
class Technology:
    technology_id: str
    name: str
    category: TechnologyCategory
    usage: str
    public: bool
    project_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Discipline:
    discipline_id: str
    name: str
    summary: str
    public: bool
    project_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Link:
    link_id: str
    label: str
    kind: LinkKind
    url: str
    public: bool


def require_mapping(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProfileDataError(f"{context} must contain a JSON object")

    return cast(dict[str, object], value)


def require_array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise ProfileDataError(f"{context} must contain a JSON array")

    return cast(list[object], value)


def require_exact_keys(
    source: dict[str, object],
    expected: set[str],
    context: str,
) -> None:
    actual = set(source)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    if missing:
        raise ProfileDataError(f"{context} is missing fields: {', '.join(missing)}")

    if unexpected:
        raise ProfileDataError(
            f"{context} contains unsupported fields: {', '.join(unexpected)}"
        )


def require_text(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> str:
    value = source.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise ProfileDataError(
            f"{context}.{field_name} must contain a non-empty string"
        )

    return value.strip()


def require_boolean(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> bool:
    value = source.get(field_name)

    if not isinstance(value, bool):
        raise ProfileDataError(f"{context}.{field_name} must contain a boolean")

    return value


def require_non_negative_integer(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> int:
    value = source.get(field_name)

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProfileDataError(
            f"{context}.{field_name} must contain a non-negative integer"
        )

    return value


def require_identifier(value: str, context: str) -> str:
    if IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ProfileDataError(f"{context} must use a lowercase kebab-case identifier")

    return value


def require_identifier_field(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> str:
    return require_identifier(
        require_text(source, field_name, context),
        f"{context}.{field_name}",
    )


def require_identifier_array(
    source: dict[str, object],
    field_name: str,
    context: str,
) -> tuple[str, ...]:
    values = require_array(source.get(field_name), f"{context}.{field_name}")
    identifiers: list[str] = []
    seen: set[str] = set()

    for index, value in enumerate(values):
        item_context = f"{context}.{field_name}[{index}]"

        if not isinstance(value, str):
            raise ProfileDataError(f"{item_context} must contain a string")

        identifier = require_identifier(value.strip(), item_context)

        if identifier in seen:
            raise ProfileDataError(
                f"Duplicate reference in {context}.{field_name}: {identifier}"
            )

        seen.add(identifier)
        identifiers.append(identifier)

    return tuple(identifiers)


def require_choice(
    source: dict[str, object],
    field_name: str,
    context: str,
    choices: frozenset[str],
) -> str:
    value = require_text(source, field_name, context)

    if value not in choices:
        raise ProfileDataError(f"Unsupported {context}.{field_name}: {value}")

    return value


def _validate_link_url(kind: LinkKind, url: str, context: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme == "https" and parsed.netloc:
        return

    if (
        kind == "contact"
        and parsed.scheme == "mailto"
        and not parsed.netloc
        and "@" in parsed.path
        and parsed.path.count("@") == 1
    ):
        return

    raise ProfileDataError(
        f"{context}.url must contain an absolute https URL or contact mailto URL"
    )


def parse_identity(value: object) -> Identity:
    context = "Profile source.identity"
    source = require_mapping(value, context)
    require_exact_keys(source, {"headline", "role", "motto", "summary"}, context)

    return Identity(
        headline=require_text(source, "headline", context),
        role=require_text(source, "role", context),
        motto=require_text(source, "motto", context),
        summary=require_text(source, "summary", context),
    )


def parse_projects(value: object) -> tuple[Project, ...]:
    records: list[Project] = []

    for index, raw_record in enumerate(require_array(value, "Profile source.projects")):
        context = f"Profile source.projects[{index}]"
        source = require_mapping(raw_record, context)
        require_exact_keys(
            source,
            {
                "id",
                "name",
                "summary",
                "status",
                "public",
                "featured",
                "priority",
                "technologyIds",
                "evidenceIds",
                "linkIds",
            },
            context,
        )
        status = cast(
            ProjectStatus,
            require_choice(source, "status", context, PROJECT_STATUSES),
        )
        public = require_boolean(source, "public", context)
        featured = require_boolean(source, "featured", context)
        project_id = require_identifier_field(source, "id", context)

        if status == "unpublished" and public:
            raise ProfileDataError(
                f"Project {project_id} with status unpublished must not be public"
            )

        if not public and featured:
            raise ProfileDataError(
                f"Project {project_id} must not be featured when public is false"
            )

        records.append(
            Project(
                project_id=project_id,
                name=require_text(source, "name", context),
                summary=require_text(source, "summary", context),
                status=status,
                public=public,
                featured=featured,
                priority=require_non_negative_integer(source, "priority", context),
                technology_ids=require_identifier_array(
                    source, "technologyIds", context
                ),
                evidence_ids=require_identifier_array(source, "evidenceIds", context),
                link_ids=require_identifier_array(source, "linkIds", context),
            )
        )

    return tuple(records)


def parse_evidence(value: object) -> tuple[Evidence, ...]:
    records: list[Evidence] = []

    for index, raw_record in enumerate(require_array(value, "Profile source.evidence")):
        context = f"Profile source.evidence[{index}]"
        source = require_mapping(raw_record, context)
        require_exact_keys(
            source,
            {"id", "kind", "label", "summary", "public", "linkId"},
            context,
        )
        raw_link_id = source.get("linkId")
        link_id: str | None

        if raw_link_id is None:
            link_id = None
        elif isinstance(raw_link_id, str):
            link_id = require_identifier(raw_link_id.strip(), f"{context}.linkId")
        else:
            raise ProfileDataError(f"{context}.linkId must contain a string or null")

        records.append(
            Evidence(
                evidence_id=require_identifier_field(source, "id", context),
                kind=cast(
                    EvidenceKind,
                    require_choice(source, "kind", context, EVIDENCE_KINDS),
                ),
                label=require_text(source, "label", context),
                summary=require_text(source, "summary", context),
                public=require_boolean(source, "public", context),
                link_id=link_id,
            )
        )

    return tuple(records)


def parse_technologies(value: object) -> tuple[Technology, ...]:
    records: list[Technology] = []

    for index, raw_record in enumerate(
        require_array(value, "Profile source.technologies")
    ):
        context = f"Profile source.technologies[{index}]"
        source = require_mapping(raw_record, context)
        require_exact_keys(
            source,
            {
                "id",
                "name",
                "category",
                "usage",
                "public",
                "projectIds",
                "evidenceIds",
            },
            context,
        )
        records.append(
            Technology(
                technology_id=require_identifier_field(source, "id", context),
                name=require_text(source, "name", context),
                category=cast(
                    TechnologyCategory,
                    require_choice(
                        source,
                        "category",
                        context,
                        TECHNOLOGY_CATEGORIES,
                    ),
                ),
                usage=require_text(source, "usage", context),
                public=require_boolean(source, "public", context),
                project_ids=require_identifier_array(source, "projectIds", context),
                evidence_ids=require_identifier_array(source, "evidenceIds", context),
            )
        )

    return tuple(records)


def parse_disciplines(value: object) -> tuple[Discipline, ...]:
    records: list[Discipline] = []

    for index, raw_record in enumerate(
        require_array(value, "Profile source.disciplines")
    ):
        context = f"Profile source.disciplines[{index}]"
        source = require_mapping(raw_record, context)
        require_exact_keys(
            source,
            {"id", "name", "summary", "public", "projectIds", "evidenceIds"},
            context,
        )
        records.append(
            Discipline(
                discipline_id=require_identifier_field(source, "id", context),
                name=require_text(source, "name", context),
                summary=require_text(source, "summary", context),
                public=require_boolean(source, "public", context),
                project_ids=require_identifier_array(source, "projectIds", context),
                evidence_ids=require_identifier_array(source, "evidenceIds", context),
            )
        )

    return tuple(records)


def parse_links(value: object) -> tuple[Link, ...]:
    records: list[Link] = []

    for index, raw_record in enumerate(require_array(value, "Profile source.links")):
        context = f"Profile source.links[{index}]"
        source = require_mapping(raw_record, context)
        require_exact_keys(source, {"id", "label", "kind", "url", "public"}, context)
        kind = cast(LinkKind, require_choice(source, "kind", context, LINK_KINDS))
        url = require_text(source, "url", context)
        _validate_link_url(kind, url, context)
        records.append(
            Link(
                link_id=require_identifier_field(source, "id", context),
                label=require_text(source, "label", context),
                kind=kind,
                url=url,
                public=require_boolean(source, "public", context),
            )
        )

    return tuple(records)
