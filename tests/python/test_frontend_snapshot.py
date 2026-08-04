from __future__ import annotations

import json
from pathlib import Path

from profile_system.frontend_snapshot import render_frontend_snapshot
from profile_system.model import load_profile_snapshot


def test_frontend_snapshot_is_stable_and_excludes_nonpublic_records(
    tmp_path: Path,
) -> None:
    source = json.loads(Path("profile/profile.json").read_text(encoding="utf-8"))
    source["projects"].append(
        {
            "id": "private-contract-probe",
            "name": "Private contract probe",
            "summary": "Must not enter the frontend snapshot.",
            "status": "active",
            "public": False,
            "featured": False,
            "priority": 999,
            "technologyIds": [],
            "evidenceIds": [],
            "linkIds": [],
        }
    )

    source_path = tmp_path / "profile.json"
    source_path.write_text(
        json.dumps(source, ensure_ascii=False),
        encoding="utf-8",
    )

    snapshot = load_profile_snapshot(source_path)
    first = render_frontend_snapshot(snapshot)
    second = render_frontend_snapshot(snapshot)
    document = json.loads(first)

    assert first == second
    assert first.endswith("\n")
    assert document["schemaVersion"] == 1
    assert document["sourceSchemaVersion"] == 2
    assert "private-contract-probe" not in {
        project["id"] for project in document["projects"]
    }

    for collection_name in (
        "projects",
        "evidence",
        "technologies",
        "disciplines",
        "links",
    ):
        assert all("public" not in record for record in document[collection_name])


def test_frontend_snapshot_references_only_projected_records() -> None:
    snapshot = load_profile_snapshot(Path("profile/profile.json"))
    document = json.loads(render_frontend_snapshot(snapshot))

    project_ids = {project["id"] for project in document["projects"]}
    evidence_ids = {evidence["id"] for evidence in document["evidence"]}
    technology_ids = {technology["id"] for technology in document["technologies"]}
    link_ids = {link["id"] for link in document["links"]}

    for project in document["projects"]:
        assert set(project["technologyIds"]) <= technology_ids
        assert set(project["evidenceIds"]) <= evidence_ids
        assert set(project["linkIds"]) <= link_ids

    for technology in document["technologies"]:
        assert set(technology["projectIds"]) <= project_ids
        assert set(technology["evidenceIds"]) <= evidence_ids
