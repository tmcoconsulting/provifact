"""Read-only provider boundary for endpoint-management inventory."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from evidenceops.domain import ConfigurationObservation, EvidenceObject, JsonValue


@dataclass(frozen=True, slots=True)
class ProviderCollection:
    """Vendor-neutral result of one schema-v1 read-only collection."""

    provider: EvidenceObject
    collection: EvidenceObject
    observations: tuple[EvidenceObject, ...]
    private_trace: dict[str, JsonValue]


class EndpointInventoryProvider(Protocol):
    """Collect normalized observations without changing the source system."""

    @property
    def name(self) -> str:
        """Return the stable provider name."""
        ...

    def collect(self) -> Sequence[ConfigurationObservation]:
        """Read and normalize configuration observations.

        Provider implementations must not expose create, update, delete, assign, or sync
        operations through this interface.
        """
        ...


class VersionedEvidenceProvider(Protocol):
    """Additive schema-v1 provider contract used by live and synthetic collectors."""

    @property
    def name(self) -> str:
        """Return the stable provider name."""
        ...

    @property
    def version(self) -> str:
        """Return the adapter version recorded in evidence."""
        ...

    @property
    def source_api_version(self) -> str:
        """Return the provider API version used for collection."""
        ...

    def collect(self, *, desired_state_git_commit_sha: str | None) -> ProviderCollection:
        """Return normalized evidence without exposing mutation operations."""
        ...
