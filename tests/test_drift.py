from evidenceops.domain import ConfigurationObservation, DriftStatus
from evidenceops.evidence import evaluate_drift


def test_equal_values_are_compliant_and_stable() -> None:
    observation = ConfigurationObservation(
        provider="synthetic",
        platform="macOS",
        control_id="SYN-MAC-001",
        subject_ref="device-safe-001",
        desired={"enabled": True, "timeout": 300},
        observed={"timeout": 300, "enabled": True},
    )

    first = evaluate_drift(observation)
    second = evaluate_drift(observation)

    assert first.status is DriftStatus.COMPLIANT
    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64


def test_different_values_are_drifted() -> None:
    observation = ConfigurationObservation(
        provider="synthetic",
        platform="macOS",
        control_id="SYN-MAC-002",
        subject_ref="device-safe-002",
        desired=True,
        observed=False,
    )

    assert evaluate_drift(observation).status is DriftStatus.DRIFTED
