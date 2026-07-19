from __future__ import annotations

from typing import cast

import pytest

from evidenceops.demo import build_synthetic_private_package
from evidenceops.domain import EvidenceObject, EvidenceStatus, JsonValue, make_evidence_object
from evidenceops.evidence import ALGORITHM_VERSION, evaluate_desired_state

RESERVED_FIELDS = frozenset({"schema_version", "object_type", "evidence_id", "content_fingerprint"})


def _with_value(template: EvidenceObject, field: str, value: JsonValue) -> EvidenceObject:
    payload = {key: item for key, item in template.items() if key not in RESERVED_FIELDS}
    payload[field] = value
    return make_evidence_object(cast(str, template["object_type"]), payload)


def _evaluate_maximum(desired_value: JsonValue, observed_value: JsonValue) -> EvidenceObject:
    package = build_synthetic_private_package()
    desired = next(
        item
        for item in cast(list[EvidenceObject], package["desired_state"])
        if item["evaluation_mode"] == "maximum"
    )
    observation = next(
        item
        for item in cast(list[EvidenceObject], package["observations"])
        if item["setting_key"] == desired["setting_key"]
    )
    desired = _with_value(desired, "desired_value", desired_value)
    observation = _with_value(observation, "observed_value", observed_value)
    collection = cast(EvidenceObject, package["collection"])
    return evaluate_desired_state([desired], [observation], collection)[0]


@pytest.mark.parametrize(
    ("desired_value", "observed_value", "expected_status"),
    [
        (900, 600, EvidenceStatus.MATCHES_DESIRED_STATE),
        (900, 900, EvidenceStatus.MATCHES_DESIRED_STATE),
        (900, 901, EvidenceStatus.DIFFERS_FROM_DESIRED_STATE),
    ],
    ids=["below", "equal", "above"],
)
def test_maximum_numeric_boundary(
    desired_value: JsonValue,
    observed_value: JsonValue,
    expected_status: EvidenceStatus,
) -> None:
    finding = _evaluate_maximum(desired_value, observed_value)
    assert finding["status"] == expected_status.value
    assert finding["deterministic_algorithm_version"] == ALGORITHM_VERSION
    assert finding["additional_evidence_required"] == []


def test_maximum_invalid_value_fails_closed() -> None:
    finding = _evaluate_maximum(None, 600)
    assert finding["status"] == EvidenceStatus.NOT_EVALUATED.value
    assert finding["additional_evidence_required"] == [
        "Maximum evaluation requires finite numeric desired and observed values."
    ]


def test_maximum_incomparable_value_fails_closed() -> None:
    finding = _evaluate_maximum(900, "600")
    assert finding["status"] == EvidenceStatus.NOT_EVALUATED.value
    assert finding["additional_evidence_required"] == [
        "Maximum evaluation requires finite numeric desired and observed values."
    ]
