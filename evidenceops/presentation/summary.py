"""Small deterministic summary used by the synthetic dashboard shell."""

from collections.abc import Iterable

from evidenceops.domain import DriftFinding, DriftStatus, JsonValue


def build_summary(findings: Iterable[DriftFinding]) -> dict[str, JsonValue]:
    """Count findings without generating or implying an AI narrative."""
    collected = tuple(findings)
    compliant = sum(item.status is DriftStatus.COMPLIANT for item in collected)
    drifted = sum(item.status is DriftStatus.DRIFTED for item in collected)
    return {
        "total": len(collected),
        "compliant": compliant,
        "drifted": drifted,
        "source_type": "deterministic",
    }
