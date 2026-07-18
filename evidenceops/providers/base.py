"""Read-only provider boundary for endpoint-management inventory."""

from collections.abc import Sequence
from typing import Protocol

from evidenceops.domain import ConfigurationObservation


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
