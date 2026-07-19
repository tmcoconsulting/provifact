"""Deterministic fixture narrative for credential-free CI and static demos."""

from __future__ import annotations

from typing import cast

from evidenceops.domain import (
    EvidenceObject,
    JsonValue,
    make_evidence_object,
    validate_evidence_object,
)


def build_offline_narrative(package: EvidenceObject) -> EvidenceObject:
    """Build clearly labeled fixture analysis without invoking a model."""
    public = validate_evidence_object(package)
    if public["object_type"] != "sanitized_public_evidence_package":
        raise ValueError("offline narrative requires a sanitized public package")
    findings = cast(list[EvidenceObject], public["findings"])
    explanations: list[dict[str, JsonValue]] = []
    for finding in findings:
        status = cast(str, finding["status"])
        references = [
            cast(str, finding["evidence_id"]),
            cast(str, finding["desired_state_evidence_id"]),
            *cast(list[str], finding["observation_evidence_ids"]),
        ]
        explanations.append(
            {
                "finding_evidence_id": finding["evidence_id"],
                "deterministic_status": status,
                "deterministic_claim": {
                    "claim_code": "finding_status",
                    "claim_value": status,
                },
                "change_or_drift_explanation": (
                    f"The deterministic engine reported '{status}' for this reviewed record."
                ),
                "technical_impact": (
                    "This result describes collected configuration evidence only; operational "
                    "impact and applicability require human review."
                ),
                "evidence_references": cast(JsonValue, references),
            }
        )
    return make_evidence_object(
        "generated_narrative",
        {
            "ai_generated_analysis": True,
            "human_review_required": True,
            "model": "deterministic-offline-fixture-not-a-model-call",
            "source_package_evidence_id": public["evidence_id"],
            "executive_summary": (
                "Fixture analysis summarizes deterministic results without changing them; human "
                "review is required before any audit or operational use."
            ),
            "drift_explanations": cast(JsonValue, explanations),
            "limitations": [
                "This is a synthetic fixture narrative, not a live GPT-5.6 response.",
                "Configuration evidence does not establish organizational compliance.",
            ],
            "additional_evidence_required": [
                "A human assessor must determine scope, applicability, and corroborating evidence."
            ],
            "suggested_human_review_questions": [
                "Does the evidence scope match the systems and assessment period under review?",
                "Are the desired values approved and applicable to the target population?",
            ],
        },
    )
