"""Deterministic drift comparison with a stable evidence fingerprint."""

import hashlib
import json
from typing import Final

from evidenceops.domain import ConfigurationObservation, DriftFinding, DriftStatus

_FINGERPRINT_VERSION: Final = "evidenceops-drift-v1"


def evaluate_drift(observation: ConfigurationObservation) -> DriftFinding:
    """Compare desired and observed values without model inference or side effects."""
    status = (
        DriftStatus.COMPLIANT
        if observation.desired == observation.observed
        else DriftStatus.DRIFTED
    )
    canonical = json.dumps(
        {
            "control_id": observation.control_id,
            "desired": observation.desired,
            "observed": observation.observed,
            "platform": observation.platform,
            "provider": observation.provider,
            "subject_ref": observation.subject_ref,
            "version": _FINGERPRINT_VERSION,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return DriftFinding(
        provider=observation.provider,
        platform=observation.platform,
        control_id=observation.control_id,
        subject_ref=observation.subject_ref,
        status=status,
        fingerprint=fingerprint,
    )
