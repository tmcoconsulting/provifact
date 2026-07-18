"""Small, provider-neutral domain objects used by the deterministic evidence engine."""

from dataclasses import dataclass
from enum import StrEnum

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class DriftStatus(StrEnum):
    """Deterministic comparison result."""

    COMPLIANT = "compliant"
    DRIFTED = "drifted"


@dataclass(frozen=True, slots=True)
class ConfigurationObservation:
    """A normalized desired/observed configuration pair from any read-only provider."""

    provider: str
    platform: str
    control_id: str
    subject_ref: str
    desired: JsonValue
    observed: JsonValue


@dataclass(frozen=True, slots=True)
class DriftFinding:
    """A reproducible drift result suitable for later evidence packaging."""

    provider: str
    platform: str
    control_id: str
    subject_ref: str
    status: DriftStatus
    fingerprint: str
