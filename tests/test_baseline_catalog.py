from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from evidenceops.baselines.mscp import (
    EXTRACTED_INVENTORY_SHA256,
    MSCP_SOURCE_REVISION,
)
from evidenceops.domain import JsonValue, canonical_json
from scripts.build_baseline_catalog import build_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPOSITORY_ROOT / "docs" / "assets" / "data" / "baseline-catalog.json"


def _catalog() -> dict[str, JsonValue]:
    value = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_committed_baseline_catalog_is_pinned_and_fingerprint_verified() -> None:
    catalog = _catalog()
    fingerprint = catalog.pop("catalog_fingerprint")
    assert (
        fingerprint
        == "sha256:" + hashlib.sha256(canonical_json(catalog).encode("utf-8")).hexdigest()
    )
    source = catalog["source"]
    assert isinstance(source, dict)
    assert source["revision"] == MSCP_SOURCE_REVISION
    assert source["license"] == "CC-BY-4.0; Apple vendor descriptions excluded"
    assert catalog["metadata_fallback_rule_ids"] == []


def test_catalog_builder_rejects_an_archive_outside_the_pinned_revision(tmp_path: Path) -> None:
    archive_path = tmp_path / "wrong-source.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        payload = b"profile: []\n"
        member = tarfile.TarInfo(
            "macos_security-unreviewed/src/mscp/data/baselines/macos/test.yaml"
        )
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    with pytest.raises(ValueError, match="pinned mSCP revision"):
        build_catalog(archive_path)


def test_reference_profiles_and_tmco_approval_are_exact_membership_sets() -> None:
    catalog = _catalog()
    profiles_value = catalog["profiles"]
    rules_value = catalog["rules"]
    assert isinstance(profiles_value, list)
    assert isinstance(rules_value, list)
    profiles = {
        item["profile_id"]: item
        for item in profiles_value
        if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
    }
    assert set(profiles) == {
        "tmco_approved",
        "cis_lvl1",
        "cis_lvl2",
        "cis_controls_v8",
        "disa_stig",
        "nist_800_171",
        "nist_800_53_low",
        "nist_800_53_moderate",
        "nist_800_53_high",
        "cmmc_level_1",
        "cmmc_level_2",
        "cnssi_1253_low",
        "cnssi_1253_moderate",
        "cnssi_1253_high",
        "hicp",
        "nllmap_base",
        "nllmap_plus",
    }
    tmco = profiles["tmco_approved"]
    cis_level_1 = profiles["cis_lvl1"]
    assert tmco["source_sha256"] == EXTRACTED_INVENTORY_SHA256
    assert tmco["source_profile_id"] == "cis_lvl1"
    assert tmco["rule_count"] == 98
    assert tmco["rule_ids"] == cis_level_1["rule_ids"]
    assert profiles["cis_lvl2"]["rule_count"] == 117
    assert profiles["disa_stig"]["rule_count"] == 160
    assert profiles["cmmc_level_2"]["rule_count"] == 215
    assert len(rules_value) == 309


def test_filevault_membership_is_visible_without_importing_benchmark_prose() -> None:
    catalog = _catalog()
    rules_value = catalog["rules"]
    assert isinstance(rules_value, list)
    filevault = next(
        item
        for item in rules_value
        if isinstance(item, dict) and item.get("rule_id") == "system_settings_filevault_enforce"
    )
    assert filevault["title"] == "Enforce FileVault"
    memberships = filevault["profile_ids"]
    assert isinstance(memberships, list)
    assert {"tmco_approved", "cis_lvl1", "cis_lvl2", "disa_stig", "cmmc_level_2"} <= set(
        memberships
    )
    assert set(filevault) == {"profile_ids", "rule_id", "section", "title"}


def test_catalog_rule_ids_match_the_normalized_mission_baseline_exactly() -> None:
    catalog = _catalog()
    profiles_value = catalog["profiles"]
    assert isinstance(profiles_value, list)
    tmco = next(
        item
        for item in profiles_value
        if isinstance(item, dict) and item.get("profile_id") == "tmco_approved"
    )
    rule_ids = tmco["rule_ids"]
    assert isinstance(rule_ids, list)
    assert "os_safari_prevent_cross-site_tracking_enable" not in rule_ids
    assert "os_safari_prevent_cross_site_tracking_enable" in rule_ids

    mission = json.loads(
        (REPOSITORY_ROOT / "docs/assets/data/mission-control.json").read_text(encoding="utf-8")
    )
    assert {item["rule_id"] for item in mission["requirements"]} == set(rule_ids)


def test_matrix_loads_the_catalog_and_never_claims_reference_compliance() -> None:
    script = (REPOSITORY_ROOT / "docs/assets/javascripts/settings-matrix.js").read_text(
        encoding="utf-8"
    )
    page = (REPOSITORY_ROOT / "docs/settings-matrix.md").read_text(encoding="utf-8")
    fingerprint = _catalog()["catalog_fingerprint"]
    assert isinstance(fingerprint, str)
    assert f'const CATALOG_FINGERPRINT =\n    "{fingerprint}"' in script
    assert (
        'const CATALOG_URL =\n    "/assets/data/baseline-catalog.json?v='
        f'{fingerprint.removeprefix("sha256:")}"' in script
    )
    assert "value.catalog_fingerprint !== CATALOG_FINGERPRINT" in script
    assert "catalog_fingerprint" in script
    assert "missionRuleIds.size !== tmco.rule_ids.length" in script
    assert "tmco.rule_ids.every((ruleId) => missionRuleIds.has(ruleId))" in script
    assert "reference_only" in script
    assert "Not in TMCO Consulting approved baseline" in script
    assert "Sixteen pinned public mSCP reference profiles are loaded" in page
    assert "not a certification or organizational verdict" in page.lower()
    assert "NOT LOADED" not in script
