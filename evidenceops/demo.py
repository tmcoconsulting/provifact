"""Deterministic synthetic Phase 1 flow used by tests, judges, and static builds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from evidenceops.domain import EvidenceObject, FreshnessState, JsonValue, make_evidence_object
from evidenceops.evidence import ALGORITHM_VERSION, build_private_package

FIXED_COLLECTION_TIME = "2026-07-18T18:00:00Z"
SYNTHETIC_GIT_COMMIT = "synthetic-reviewed-commit"
DEFAULT_DESIRED_FIXTURE = (
    Path(__file__).parents[1] / "fixtures" / "synthetic" / "desired-state.macos-screen-lock.json"
)


def build_synthetic_private_package(
    desired_fixture: Path = DEFAULT_DESIRED_FIXTURE,
) -> EvidenceObject:
    """Run reviewed intent through normalized observation and deterministic drift."""
    provider = make_evidence_object(
        "provider_metadata",
        {
            "provider": "synthetic-intune",
            "provider_version": "1.0.0",
            "source_api_version": "v1.0-fixture",
        },
    )
    collection = make_evidence_object(
        "collection_metadata",
        {
            "collection_timestamp_utc": FIXED_COLLECTION_TIME,
            "provider_evidence_id": provider["evidence_id"],
            "desired_state_git_commit_sha": SYNTHETIC_GIT_COMMIT,
            "deterministic_algorithm_version": ALGORITHM_VERSION,
            "freshness": {
                "as_of_utc": FIXED_COLLECTION_TIME,
                "max_age_seconds": 86400,
                "state": FreshnessState.UNKNOWN.value,
            },
        },
    )
    desired_state = load_desired_state(desired_fixture, git_commit_sha=SYNTHETIC_GIT_COMMIT)
    observations = _synthetic_observations(collection, provider)
    return build_private_package(
        synthetic=True,
        provider=provider,
        collection=collection,
        desired_state=desired_state,
        observations=observations,
        retention={
            "policy": "synthetic-demo-no-private-retention",
            "delete_after_utc": FIXED_COLLECTION_TIME,
        },
        private_trace={"fixture_notice": "SYNTHETIC_TEST_DATA_ONLY"},
    )


def load_desired_state(path: Path, *, git_commit_sha: str | None) -> list[EvidenceObject]:
    """Load reviewed vendor-neutral desired state at an explicit Git revision."""
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or loaded.get("schema_version") != "1.0.0":
        raise ValueError("desired-state fixture must use schema version 1.0.0")
    if loaded.get("fixture_notice") != "SYNTHETIC_TEST_DATA_ONLY":
        raise ValueError("desired-state fixture must be explicitly synthetic")
    records = loaded.get("records")
    if not isinstance(records, list):
        raise ValueError("desired-state fixture records must be an array")
    result: list[EvidenceObject] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("desired-state fixture record must be an object")
        payload = cast(dict[str, JsonValue], record)
        result.append(
            make_evidence_object(
                "desired_state_record",
                {**payload, "desired_state_git_commit_sha": git_commit_sha},
            )
        )
    return result


def _synthetic_observations(
    collection: EvidenceObject, provider: EvidenceObject
) -> list[EvidenceObject]:
    base: dict[str, JsonValue] = {
        "collection_evidence_id": collection["evidence_id"],
        "provider_evidence_id": provider["evidence_id"],
        "platform": "macOS",
        "source_modified_at_utc": FIXED_COLLECTION_TIME,
        "freshness": {
            "as_of_utc": FIXED_COLLECTION_TIME,
            "max_age_seconds": 86400,
            "state": FreshnessState.UNKNOWN.value,
        },
    }
    return [
        make_evidence_object(
            "normalized_configuration_observation",
            {
                **base,
                "setting_key": "macos.screen_lock.require_password",
                "observed_value": True,
                "observation_state": "observed",
            },
        ),
        make_evidence_object(
            "normalized_configuration_observation",
            {
                **base,
                "setting_key": "macos.screen_lock.max_idle_seconds",
                "observed_value": 1800,
                "observation_state": "observed",
            },
        ),
        make_evidence_object(
            "normalized_configuration_observation",
            {
                **base,
                "setting_key": "macos.screen_lock.unsupported_demo_setting",
                "observed_value": None,
                "observation_state": "unsupported",
            },
        ),
    ]
