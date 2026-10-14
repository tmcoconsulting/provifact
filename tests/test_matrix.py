from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from evidenceops.domain import JsonValue, fingerprint
from evidenceops.evidence.matrix import build_public_matrix, validate_public_matrix
from evidenceops.evidence.mission import build_public_mission_snapshot
from evidenceops.mission_demo import MISSION_PSEUDONYM_KEY, _collection, build_mission_demo
from scripts.build_public_matrix import write_matrix


def test_canonical_matrix_preserves_evidence_and_independent_baseline_identity() -> None:
    mission = build_mission_demo()
    matrix = build_public_matrix(mission)
    assert validate_public_matrix(matrix, mission) == matrix
    rows = cast(list[dict[str, JsonValue]], matrix["rows"])
    assert len(rows) == 98
    assert {row["baseline_profile_id"] for row in rows} == {"tmco_approved"}
    assert all(row["policy_precedence"] == "unknown" for row in rows)
    assert all(
        row["benchmark_version"]
        == cast(dict[str, JsonValue], mission["baseline"])["benchmark_version"]
        for row in rows
    )
    requirements = [cast(dict[str, JsonValue], row["requirement"]) for row in rows]
    assert requirements == mission["requirements"]
    assert sum(item["evaluation_included"] is True for item in requirements) == 4
    assert {item["outcome"] for item in requirements} >= {
        "Aligned",
        "Value drift",
        "Conflicting policy",
        "Assignment drift",
    }
    conflicted = next(
        row
        for row in rows
        if cast(dict[str, JsonValue], row["requirement"])["outcome"] == "Conflicting policy"
    )
    assert (
        len(
            cast(
                list[JsonValue],
                cast(dict[str, JsonValue], conflicted["requirement"])["parent_resource_refs"],
            )
        )
        == 2
    )
    assert "will not choose" in cast(str, conflicted["change_guidance"])
    # Level 2 membership is independently loaded; it never becomes an evaluated profile here.
    catalog = json.loads(
        (Path(__file__).parents[1] / "docs/assets/data/baseline-catalog.json").read_text()
    )
    level2 = next(profile for profile in catalog["profiles"] if profile["profile_id"] == "cis_lvl2")
    assert level2["rule_count"] == 117
    assert (
        level2["source_sha256"]
        != next(profile for profile in catalog["profiles"] if profile["profile_id"] == "cis_lvl1")[
            "source_sha256"
        ]
    )


@pytest.mark.parametrize("kind", ["missing_setting", "missing_parent", "unavailable"])
def test_matrix_distinguishes_missing_policy_from_unavailable_evidence(kind: str) -> None:
    collection = _collection(previous=False)
    setting = next(
        record
        for record in collection.records
        if cast(dict[str, JsonValue], record["properties"]).get("setting_definition_id")
        == "com.apple.mcx.filevault2_enable"
    )
    parent_id = cast(dict[str, JsonValue], setting["properties"])["parent_evidence_id"]
    if kind == "missing_setting":
        collection = replace(
            collection,
            records=tuple(record for record in collection.records if record is not setting),
        )
    elif kind == "missing_parent":
        collection = replace(
            collection,
            records=tuple(
                record for record in collection.records if record["evidence_id"] != parent_id
            ),
        )
    else:
        collection = replace(
            collection,
            collection_gaps=(
                {
                    "gap_id": "gap-" + "b" * 24,
                    "source_endpoint_key": "settings_catalog:assignments",
                    "resource_family": "settings_catalog",
                    "source_api_version": "beta",
                    "required_permission": "DeviceManagementConfiguration.Read.All",
                    "reason": "permission_denied",
                    "http_status": 403,
                },
            ),
        )
    mission = build_public_mission_snapshot(
        collection, pseudonym_key=MISSION_PSEUDONYM_KEY, synthetic=False, source_git_commit="a" * 40
    )
    row = next(
        row
        for row in cast(list[dict[str, JsonValue]], build_public_matrix(mission)["rows"])
        if cast(dict[str, JsonValue], row["requirement"])["rule_id"]
        == "system_settings_filevault_enforce"
    )
    requirement = cast(dict[str, JsonValue], row["requirement"])
    assert requirement["outcome"] == (
        "Missing from tenant" if kind == "missing_setting" else "Collection gap"
    )
    assert requirement["additional_evidence_required"] is True


@pytest.mark.parametrize("field", ["parent_policy_ref", "change_guidance", "baseline_profile_id"])
def test_matrix_rejects_private_or_forged_claims_even_with_recomputed_fingerprint(
    field: str,
) -> None:
    mission = build_mission_demo()
    matrix = copy.deepcopy(build_public_matrix(mission))
    cast(list[dict[str, JsonValue]], matrix["rows"])[0][field] = "forged"
    matrix["content_fingerprint"] = fingerprint(
        {key: value for key, value in matrix.items() if key != "content_fingerprint"}
    )
    with pytest.raises(ValueError, match="canonical Mission projection"):
        validate_public_matrix(matrix, mission)


def test_matrix_writer_requires_public_input_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "mission.json"
    output = tmp_path / "matrix.json"
    mission = build_mission_demo()
    source.write_text(json.dumps(mission))
    write_matrix(source, output)
    validate_public_matrix(json.loads(output.read_text()), mission)
    with pytest.raises(ValueError, match="must not replace"):
        write_matrix(source, source)
    output.unlink()
    output.symlink_to(source)
    with pytest.raises(ValueError, match="symlink"):
        write_matrix(source, output)
    output.unlink()
    output.with_suffix(".json.tmp").write_text("preserve")
    with pytest.raises(ValueError, match="already exists"):
        write_matrix(source, output)
    assert json.loads(source.read_text()) == mission
    source.write_text('{"document_type":"evidenceops_private_apple_collection"}')
    with pytest.raises(ValueError, match="top-level"):
        write_matrix(source, output)
