"""Canonical public settings matrix, constructed exclusively from validated evidence.

Private policy lineage is intentionally outside this contract. Reference-profile
membership never supplies an expected value or an independent evaluation outcome.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from evidenceops.domain import JsonValue, fingerprint
from evidenceops.evidence.mission import validate_public_mission_snapshot
from evidenceops.sanitization import assert_public_safe

MATRIX_SCHEMA_VERSION: Final = "1.0.0"
MATRIX_LIMITATIONS: Final = (
    "Technical evidence does not establish organizational compliance or control satisfaction.",
    "Effective policy precedence is unknown; overlapping sources require human review.",
    "Private policy names and source-derived lineage are excluded from this public projection.",
    "Provifact cannot write, assign, or remediate Intune; human review is required.",
)


def change_guidance(requirement: Mapping[str, JsonValue]) -> str:
    """Deterministic review guidance; no generated text or executable remediation."""
    outcome = requirement["outcome"]
    guidance = {
        "Aligned": (
            "No value change indicated. Retain the approved target and review scope "
            "and operating evidence."
        ),
        "Value drift": (
            "Review the observed value against the approved target in Intune. "
            "Re-collect after any human change."
        ),
        "Assignment drift": (
            "Review intended assignments and exclusions. Re-collect after any human change."
        ),
        "Conflicting policy": (
            "Review every overlapping policy source and effective precedence. "
            "Provifact will not choose or apply a policy."
        ),
        "Missing from tenant": (
            "Confirm every reviewed exact provider alias is absent before treating "
            "the setting as missing."
        ),
        "Collection gap": (
            "Restore the approved read-only evidence source or provide alternate "
            "evidence before evaluation."
        ),
        "Unsupported value shape": (
            "Review the collected value shape and add a deterministic parser before evaluation."
        ),
        "Unsupported by provider": (
            "Document an approved alternate implementation or evidence path; "
            "do not infer provider support."
        ),
    }
    if outcome == "Provider mapping not reviewed":
        return (
            "Review and approve the exact Intune setting definition ID "
            "before deterministic evaluation."
            if requirement["setting_key"] != "not mapped"
            else "Classify the implementation and evidence path, then approve "
            "a typed target and exact collector mapping."
        )
    return guidance.get(
        cast(str, outcome), "Human review is required; Provifact has no Intune write capability."
    )


def build_public_matrix(mission: object) -> dict[str, JsonValue]:
    """Generate one snapshot-bound projection instead of independent UI joins."""
    document = validate_public_mission_snapshot(mission)
    baseline = cast(dict[str, JsonValue], document["baseline"])
    findings = {
        cast(str, item["requirement_id"]): item
        for item in cast(list[dict[str, JsonValue]], document["findings"])
    }
    resources = {
        cast(str, item["source_evidence_id"]): item
        for item in cast(list[dict[str, JsonValue]], document["resources"])
    }
    rows: list[JsonValue] = []
    for requirement in cast(list[dict[str, JsonValue]], document["requirements"]):
        rows.append(
            {
                "baseline_profile_id": "tmco_approved",
                "benchmark": baseline["benchmark"],
                "benchmark_version": baseline["benchmark_version"],
                "requirement": dict(requirement),
                "finding": findings.get(cast(str, requirement["requirement_id"])),
                "resources": [
                    dict(resources[identifier])
                    for identifier in cast(list[str], requirement["source_evidence_ids"])
                    if identifier in resources
                ],
                "change_guidance": change_guidance(requirement),
                "limitations": list(MATRIX_LIMITATIONS),
                "policy_precedence": "unknown",
            }
        )
    unsigned: dict[str, JsonValue] = {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "source_snapshot_id": document["snapshot_id"],
        "source_content_fingerprint": document["content_fingerprint"],
        "rows": rows,
    }
    result = {**unsigned, "content_fingerprint": fingerprint(unsigned)}
    assert_public_safe(result)
    return result


def validate_public_matrix(value: object, mission: object) -> dict[str, JsonValue]:
    """Reject unknown fields, forged guidance, stale joins, and private additions."""
    expected = build_public_matrix(mission)
    if value != expected:
        raise ValueError("public matrix does not match its canonical Mission projection")
    return expected
