"""Read-only provider contracts and the narrow Microsoft Intune adapter."""

from evidenceops.providers.apple import (
    APPLE_COLLECTION_SCHEMA_VERSION,
    APPLE_PROVIDER_VERSION,
    ENDPOINTS,
    AppleIntuneCollection,
    AppleIntuneProvider,
    EndpointSpec,
    assert_get_only_provider,
    endpoint_permissions,
    summarize_devices,
)
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
    "APPLE_COLLECTION_SCHEMA_VERSION",
    "APPLE_PROVIDER_VERSION",
    "ENDPOINTS",
    "AppleIntuneCollection",
    "AppleIntuneProvider",
    "DeviceCodeTokenProvider",
    "EndpointInventoryProvider",
    "EndpointSpec",
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
    "assert_get_only_provider",
    "endpoint_permissions",
    "summarize_devices",
]
