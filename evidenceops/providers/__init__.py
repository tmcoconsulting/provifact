"""Read-only provider contracts and the narrow Microsoft Intune adapter."""

from evidenceops.providers.auth import (
    DeviceCodeTokenProvider,
    EnvironmentTokenProvider,
    TokenAcquisitionError,
    TokenProvider,
)
from evidenceops.providers.base import (
    EndpointInventoryProvider,
    ProviderCollection,
    VersionedEvidenceProvider,
)
from evidenceops.providers.intune import (
    GraphClient,
    GraphErrorCategory,
    GraphProviderError,
    GraphTransport,
    HttpResponse,
    HttpsGraphTransport,
    IntuneProvider,
)

__all__ = [
    "DeviceCodeTokenProvider",
    "EndpointInventoryProvider",
    "EnvironmentTokenProvider",
    "GraphClient",
    "GraphErrorCategory",
    "GraphProviderError",
    "GraphTransport",
    "HttpResponse",
    "HttpsGraphTransport",
    "IntuneProvider",
    "ProviderCollection",
    "TokenAcquisitionError",
    "TokenProvider",
    "VersionedEvidenceProvider",
]
