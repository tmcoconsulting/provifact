from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import cast

import pytest

from evidenceops.demo import FIXED_COLLECTION_TIME, build_synthetic_private_package
from evidenceops.domain import EvidenceObject, JsonValue, make_evidence_object
from evidenceops.evidence import publish_private_package
from evidenceops.narrative import (
    NarrativeGenerationError,
    OpenAINarrativeAdapter,
    build_offline_narrative,
    verify_narrative,
)

TEST_KEY = bytes(range(32))


def _public() -> EvidenceObject:
    return publish_private_package(
        build_synthetic_private_package(),
        pseudonym_key=TEST_KEY,
        published_at_utc=FIXED_COLLECTION_TIME,
    )


def _rebuild(narrative: EvidenceObject, **updates: JsonValue) -> EvidenceObject:
    payload = {
        key: value
        for key, value in narrative.items()
        if key not in {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
    }
    payload.update(updates)
    return make_evidence_object("generated_narrative", payload)


def test_offline_narrative_verifies_typed_claims_but_quarantines_generated_prose() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    result = verify_narrative(narrative, public)
    assert result["accepted"] is False
    assert result["human_review_required"] is True
    assert len(cast(list[str], result["accepted_claims"])) == len(
        cast(list[EvidenceObject], public["findings"])
    )
    assert all("finding_status=" in claim for claim in cast(list[str], result["accepted_claims"]))
    assert all(
        claim.startswith("generated prose quarantined:")
        for claim in cast(list[str], result["rejected_claims"])
    )
    assert "not machine-verifiable" in " ".join(cast(list[str], result["reasons"]))
    assert narrative["model"] == "deterministic-offline-fixture-not-a-model-call"


@pytest.mark.parametrize(
    ("field", "text", "reason"),
    [
        ("executive_summary", "The tenant is compliant.", "compliance or certification"),
        ("executive_summary", "NIST AC-2 is satisfied.", "control or framework"),
        ("executive_summary", "No assessor action is needed.", "human-review language"),
    ],
)
def test_verifier_rejects_unsupported_verdicts_controls_and_missing_review_language(
    field: str, text: str, reason: str
) -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    updates: dict[str, JsonValue] = {field: text}
    if reason == "human-review language":
        updates.update(
            {
                "drift_explanations": cast(
                    JsonValue,
                    [
                        {
                            **item,
                            "technical_impact": "Operational applicability requires assessment.",
                        }
                        for item in cast(
                            list[dict[str, JsonValue]], narrative["drift_explanations"]
                        )
                    ],
                ),
                "limitations": ["Configuration evidence has limited scope."],
                "additional_evidence_required": ["Scoping evidence is required."],
                "suggested_human_review_questions": ["Is the evidence period appropriate?"],
            }
        )
    result = verify_narrative(_rebuild(narrative, **updates), public)
    assert result["accepted"] is False
    assert any(reason in item for item in cast(list[str], result["reasons"]))


def test_verifier_rejects_hallucinated_and_out_of_package_evidence_ids() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    explanations[0]["finding_evidence_id"] = "ev1-000000000000000000000000"
    explanations[0]["evidence_references"] = ["ev1-ffffffffffffffffffffffff"]
    result = verify_narrative(
        _rebuild(narrative, drift_explanations=cast(JsonValue, explanations)), public
    )
    reasons = " ".join(cast(list[str], result["reasons"]))
    assert result["accepted"] is False
    assert "unknown finding explanation IDs" in reasons
    assert "outside supplied package" in reasons


def test_verifier_rejects_typed_and_legacy_status_contradictions() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    explanations[0]["deterministic_status"] = "differs from desired state"
    explanations[0]["change_or_drift_explanation"] = (
        "The observation shows false and differs from desired state."
    )
    result = verify_narrative(
        _rebuild(narrative, drift_explanations=cast(JsonValue, explanations)), public
    )
    reasons = " ".join(cast(list[str], result["reasons"]))
    assert "contradicts the deterministic finding status" in reasons
    assert "typed deterministic claim contradicts the narrative status" in reasons


def test_verifier_rejects_duplicate_finding_ids_and_reports_the_omission() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    omitted_id = cast(str, explanations[-1]["finding_evidence_id"])
    duplicate_id = cast(str, explanations[0]["finding_evidence_id"])
    explanations[-1] = copy.deepcopy(explanations[0])

    result = verify_narrative(
        _rebuild(narrative, drift_explanations=cast(JsonValue, explanations)), public
    )

    reasons = cast(list[str], result["reasons"])
    assert f"duplicate finding explanation IDs: {duplicate_id}" in reasons
    assert f"missing deterministic finding explanations: {omitted_id}" in reasons


def test_verifier_rejects_missing_finding_even_when_no_duplicate_exists() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    omitted_id = cast(str, explanations[-1]["finding_evidence_id"])

    result = verify_narrative(
        _rebuild(narrative, drift_explanations=cast(JsonValue, explanations[:-1])), public
    )

    assert f"missing deterministic finding explanations: {omitted_id}" in cast(
        list[str], result["reasons"]
    )


def test_verifier_rejects_unknown_finding_even_when_all_expected_findings_remain() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    unknown_id = "ev1-000000000000000000000000"
    extra = copy.deepcopy(explanations[0])
    extra["finding_evidence_id"] = unknown_id
    explanations.append(extra)

    result = verify_narrative(
        _rebuild(narrative, drift_explanations=cast(JsonValue, explanations)), public
    )

    assert f"unknown finding explanation IDs: {unknown_id}" in cast(list[str], result["reasons"])


@pytest.mark.parametrize(
    "contradictory_prose",
    [
        "This setting deviates from the approved baseline despite the structured match value.",
        "The observed configuration is out of alignment with reviewed intent.",
        "A material variance exists and the expected state was not achieved.",
    ],
)
def test_unrestricted_evaluative_synonyms_are_never_verified(
    contradictory_prose: str,
) -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    explanations[0]["change_or_drift_explanation"] = contradictory_prose

    result = verify_narrative(
        _rebuild(narrative, drift_explanations=cast(JsonValue, explanations)), public
    )

    assert result["accepted"] is False
    assert contradictory_prose not in cast(list[str], result["accepted_claims"])
    assert "generated prose quarantined: drift_explanations[0].change_or_drift_explanation" in cast(
        list[str], result["rejected_claims"]
    )


def test_legacy_narrative_shape_validates_but_cannot_verify_without_typed_claims() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    explanations = copy.deepcopy(cast(list[dict[str, JsonValue]], narrative["drift_explanations"]))
    for explanation in explanations:
        del explanation["deterministic_claim"]
    legacy = _rebuild(narrative, drift_explanations=cast(JsonValue, explanations))

    result = verify_narrative(legacy, public)

    assert result["accepted"] is False
    assert "typed deterministic claim is missing" in cast(list[str], result["reasons"])


def test_unknown_evaluative_claim_code_is_quarantined_by_schema() -> None:
    public = _public()
    narrative = copy.deepcopy(build_offline_narrative(public))
    explanations = cast(list[dict[str, JsonValue]], narrative["drift_explanations"])
    claim = cast(dict[str, JsonValue], explanations[0]["deterministic_claim"])
    claim["claim_code"] = "assessment_conclusion"

    result = verify_narrative(narrative, public)

    assert result["accepted"] is False
    assert result["rejected_claims"] == ["entire narrative quarantined"]
    assert "claim code is unsupported" in cast(list[str], result["reasons"])[0]


def test_verifier_rejects_evidence_id_invented_inside_narrative_text() -> None:
    public = _public()
    narrative = build_offline_narrative(public)
    unsafe = _rebuild(
        narrative,
        executive_summary=(
            "Human review is required, but ev1-aaaaaaaaaaaaaaaaaaaaaaaa was not supplied."
        ),
    )
    result = verify_narrative(unsafe, public)
    assert result["accepted"] is False
    assert "nonexistent evidence IDs in narrative text" in " ".join(
        cast(list[str], result["reasons"])
    )


def test_verifier_quarantines_unexpected_schema_fields() -> None:
    public = _public()
    narrative = copy.deepcopy(build_offline_narrative(public))
    narrative["unexpected_model_field"] = "must fail closed"
    result = verify_narrative(narrative, public)
    assert result["accepted"] is False
    assert result["rejected_claims"] == ["entire narrative quarantined"]
    assert "unexpected fields" in cast(list[str], result["reasons"])[0]


@dataclass
class RecordingTransport:
    output: dict[str, JsonValue]
    requests: list[dict[str, JsonValue]] = field(default_factory=list)
    seen_keys: list[str] = field(default_factory=list)

    def create(self, *, api_key: str, request: dict[str, JsonValue]) -> dict[str, JsonValue]:
        self.seen_keys.append(api_key)
        self.requests.append(request)
        return {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": json.dumps(self.output)}],
                }
            ]
        }


def test_openai_adapter_sends_only_sanitized_package_and_strict_schema() -> None:
    public = _public()
    fixture = build_offline_narrative(public)
    model_output = {
        key: value
        for key, value in fixture.items()
        if key
        not in {
            "schema_version",
            "object_type",
            "evidence_id",
            "content_fingerprint",
            "ai_generated_analysis",
            "human_review_required",
            "model",
            "source_package_evidence_id",
        }
    }
    transport = RecordingTransport(model_output)
    narrative = OpenAINarrativeAdapter(transport=transport).generate(
        public, api_key="test-secret-never-in-request"
    )
    request = transport.requests[0]
    assert request["store"] is False
    assert "tools" not in request
    assert request["model"] == "gpt-5.6-terra"
    assert "private_trace" not in cast(str, request["input"])
    assert "test-secret-never-in-request" not in json.dumps(request)
    assert transport.seen_keys == ["test-secret-never-in-request"]
    assert narrative["model"] == "gpt-5.6-terra"
    verification = verify_narrative(narrative, public)
    assert verification["accepted"] is False
    assert len(cast(list[str], verification["accepted_claims"])) == len(
        cast(list[EvidenceObject], public["findings"])
    )


def test_openai_adapter_rejects_private_package_and_malformed_output() -> None:
    private = build_synthetic_private_package()
    transport = RecordingTransport({})
    adapter = OpenAINarrativeAdapter(transport=transport)
    with pytest.raises(NarrativeGenerationError, match="only a sanitized"):
        adapter.generate(private, api_key="not-used")
    with pytest.raises(NarrativeGenerationError, match="narrative schema"):
        adapter.generate(_public(), api_key="test-key")


@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
def test_openai_adapter_blocks_every_github_token_family_before_transport(
    prefix: str,
) -> None:
    public = _public()
    references = copy.deepcopy(cast(list[EvidenceObject], public["evidence_references"]))
    reference_payload = {
        key: value
        for key, value in references[0].items()
        if key not in {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
    }
    reference_payload["label"] = prefix + ("A" * 40)
    references[0] = make_evidence_object("evidence_reference", reference_payload)
    public_payload = {
        key: value
        for key, value in public.items()
        if key not in {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
    }
    public_payload["evidence_references"] = cast(JsonValue, references)
    credential_shaped = make_evidence_object("sanitized_public_evidence_package", public_payload)
    transport = RecordingTransport({})

    with pytest.raises(NarrativeGenerationError, match="pre-model credential"):
        OpenAINarrativeAdapter(transport=transport).generate(credential_shaped, api_key="test-key")
    assert transport.requests == []
