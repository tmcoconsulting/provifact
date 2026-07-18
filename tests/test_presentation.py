from evidenceops.domain import DriftFinding, DriftStatus
from evidenceops.presentation import build_summary


def _finding(status: DriftStatus, suffix: str) -> DriftFinding:
    return DriftFinding(
        provider="synthetic",
        platform="macOS",
        control_id=f"SYN-{suffix}",
        subject_ref=f"subject-{suffix}",
        status=status,
        fingerprint=suffix * 64,
    )


def test_summary_is_deterministic_and_labeled() -> None:
    summary = build_summary(
        [
            _finding(DriftStatus.COMPLIANT, "a"),
            _finding(DriftStatus.DRIFTED, "b"),
        ]
    )

    assert summary == {
        "total": 2,
        "compliant": 1,
        "drifted": 1,
        "source_type": "deterministic",
    }
