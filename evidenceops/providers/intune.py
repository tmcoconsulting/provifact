"""Narrow, GET-only Microsoft Intune provider using Microsoft Graph v1.0."""

from __future__ import annotations

import http.client
import json
import random
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from enum import StrEnum
from typing import Final, Protocol, cast
from urllib.parse import urlsplit

from evidenceops.constants import DRIFT_ALGORITHM_VERSION
from evidenceops.domain import EvidenceObject, FreshnessState, JsonValue, make_evidence_object
from evidenceops.providers.auth import TokenProvider
from evidenceops.providers.base import ProviderCollection

GRAPH_HOST: Final = "graph.microsoft.com"
GRAPH_ROOT: Final = f"https://{GRAPH_HOST}"
SOURCE_API_VERSION: Final = "v1.0"
SUPPORTED_API_VERSIONS: Final = frozenset({"v1.0", "beta"})
PROVIDER_VERSION: Final = "1.0.0"
MAX_RESPONSE_BYTES: Final = 4_000_000
MAX_PAGES: Final = 100
SUPPORTED_ODATA_TYPE: Final = "#microsoft.graph.macOSGeneralDeviceConfiguration"
DEVICE_CONFIGURATIONS_PATH: Final = "/v1.0/deviceManagement/deviceConfigurations"


class GraphErrorCategory(StrEnum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    THROTTLED = "throttled"
    TRANSIENT = "transient"
    MALFORMED_RESPONSE = "malformed_response"
    CONFLICT = "conflict"
    TRANSPORT = "transport"


class GraphProviderError(RuntimeError):
    """Structured Graph failure that deliberately excludes response content."""

    def __init__(
        self,
        category: GraphErrorCategory,
        *,
        endpoint: str,
        status_code: int | None = None,
        graph_code: str | None = None,
    ) -> None:
        self.category = category
        self.endpoint = endpoint
        self.status_code = status_code
        self.graph_code = graph_code
        suffix = f" ({status_code})" if status_code is not None else ""
        super().__init__(f"Microsoft Graph {category.value} error at {endpoint}{suffix}")


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class GraphTransport(Protocol):
    """The provider exposes exactly one network operation: GET."""

    def get(self, url: str, *, headers: Mapping[str, str], timeout_seconds: float) -> HttpResponse:
        """Issue one HTTPS GET request."""
        ...


class HttpsGraphTransport:
    """Small standard-library transport restricted to graph.microsoft.com HTTPS."""

    def get(self, url: str, *, headers: Mapping[str, str], timeout_seconds: float) -> HttpResponse:
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or parts.hostname != GRAPH_HOST
            or parts.port not in {None, 443}
            or parts.username is not None
            or parts.password is not None
            or parts.fragment
        ):
            raise GraphProviderError(GraphErrorCategory.TRANSPORT, endpoint="invalid-graph-url")
        target = parts.path or "/"
        if parts.query:
            target = f"{target}?{parts.query}"
        connection = http.client.HTTPSConnection(GRAPH_HOST, timeout=timeout_seconds)
        try:
            connection.request("GET", target, headers=dict(headers))
            response = connection.getresponse()
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise GraphProviderError(GraphErrorCategory.MALFORMED_RESPONSE, endpoint=parts.path)
            return HttpResponse(
                status_code=response.status,
                headers={key.lower(): value for key, value in response.getheaders()},
                body=body,
            )
        except (OSError, http.client.HTTPException) as exc:
            raise GraphProviderError(GraphErrorCategory.TRANSPORT, endpoint=parts.path) from exc
        finally:
            connection.close()


class GraphClient:
    """Bounded, paginated, retry-aware Microsoft Graph GET-only reader.

    Callers must select ``v1.0`` or ``beta`` in every path. Beta use is therefore
    visible at the provider endpoint catalog rather than becoming a silent fallback.
    """

    def __init__(
        self,
        *,
        token_provider: TokenProvider,
        transport: GraphTransport | None = None,
        timeout_seconds: float = 20.0,
        max_attempts: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
        jitter: Callable[[float], float] | None = None,
    ) -> None:
        if timeout_seconds <= 0 or max_attempts < 1:
            raise ValueError("timeout_seconds and max_attempts must be positive")
        self._token_provider = token_provider
        self._transport = transport or HttpsGraphTransport()
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._sleeper = sleeper
        self._jitter = jitter or (lambda maximum: random.SystemRandom().uniform(0, maximum))

    def get_collection(self, path: str) -> list[dict[str, JsonValue]]:
        """Read every page while treating nextLink as an opaque same-host URL."""
        api_version = _path_api_version(path)
        if api_version is None:
            raise ValueError("Graph path must explicitly use v1.0 or beta")
        next_url: str | None = f"{GRAPH_ROOT}{path}"
        seen: set[str] = set()
        values: list[dict[str, JsonValue]] = []
        while next_url is not None:
            if next_url in seen or len(seen) >= MAX_PAGES:
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE, endpoint=urlsplit(next_url).path
                )
            seen.add(next_url)
            page = self._get_json(next_url)
            raw_values = page.get("value")
            if not isinstance(raw_values, list):
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE, endpoint=urlsplit(next_url).path
                )
            for item in raw_values:
                if not isinstance(item, dict) or not all(isinstance(key, str) for key in item):
                    raise GraphProviderError(
                        GraphErrorCategory.MALFORMED_RESPONSE, endpoint=urlsplit(next_url).path
                    )
                values.append(item)
            candidate = page.get("@odata.nextLink")
            if candidate is None:
                next_url = None
            elif isinstance(candidate, str) and _is_graph_url(candidate, api_version):
                next_url = candidate
            else:
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE, endpoint=urlsplit(next_url).path
                )
        return values

    def get_object(self, path: str) -> dict[str, JsonValue]:
        """Read one Graph object using the same bounded GET-only transport."""
        if _path_api_version(path) is None:
            raise ValueError("Graph path must explicitly use v1.0 or beta")
        return self._get_json(f"{GRAPH_ROOT}{path}")

    def _get_json(self, url: str) -> dict[str, JsonValue]:
        endpoint = urlsplit(url).path
        for attempt in range(self._max_attempts):
            token = self._token_provider.get_token()
            response = self._transport.get(
                url,
                headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
                timeout_seconds=self._timeout_seconds,
            )
            if response.status_code == 200:
                try:
                    decoded = json.loads(response.body)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise GraphProviderError(
                        GraphErrorCategory.MALFORMED_RESPONSE, endpoint=endpoint
                    ) from exc
                if not isinstance(decoded, dict) or not all(
                    isinstance(key, str) for key in decoded
                ):
                    raise GraphProviderError(
                        GraphErrorCategory.MALFORMED_RESPONSE, endpoint=endpoint
                    )
                return cast(dict[str, JsonValue], decoded)
            category = _error_category(response.status_code)
            if category not in {GraphErrorCategory.THROTTLED, GraphErrorCategory.TRANSIENT}:
                raise GraphProviderError(
                    category,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    graph_code=_safe_graph_error_code(response.body),
                )
            if attempt + 1 >= self._max_attempts:
                raise GraphProviderError(
                    category,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    graph_code=_safe_graph_error_code(response.body),
                )
            delay = _retry_delay(
                response.headers.get("retry-after"),
                attempt,
                jitter=self._jitter,
            )
            self._sleeper(delay)
        raise AssertionError("bounded retry loop exhausted unexpectedly")


class IntuneProvider:
    """Collect only the macOS general device-configuration slice needed by Phase 1."""

    name = "microsoft-intune"
    version = PROVIDER_VERSION
    source_api_version = SOURCE_API_VERSION

    def __init__(self, client: GraphClient) -> None:
        self._client = client

    def collect(self, *, desired_state_git_commit_sha: str | None) -> ProviderCollection:
        """Read and normalize configuration; no raw response is returned or persisted."""
        collected_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        provider = make_evidence_object(
            "provider_metadata",
            {
                "provider": self.name,
                "provider_version": self.version,
                "source_api_version": self.source_api_version,
            },
        )
        collection = make_evidence_object(
            "collection_metadata",
            {
                "collection_timestamp_utc": collected_at,
                "provider_evidence_id": provider["evidence_id"],
                "desired_state_git_commit_sha": desired_state_git_commit_sha,
                "deterministic_algorithm_version": DRIFT_ALGORITHM_VERSION,
                "freshness": {
                    "as_of_utc": collected_at,
                    "max_age_seconds": 86400,
                    "state": FreshnessState.CURRENT.value,
                },
            },
        )
        policies = self._client.get_collection(DEVICE_CONFIGURATIONS_PATH)
        observations: list[EvidenceObject] = []
        source_objects: list[JsonValue] = []
        unsupported_types: dict[str, int] = {}
        supported_policy_count = 0
        for policy in policies:
            odata_type = policy.get("@odata.type")
            if not isinstance(odata_type, str):
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE,
                    endpoint=DEVICE_CONFIGURATIONS_PATH,
                )
            if odata_type != SUPPORTED_ODATA_TYPE:
                unsupported_types[odata_type] = unsupported_types.get(odata_type, 0) + 1
                continue
            supported_policy_count += 1
            normalized, source_trace = self._normalize_policy(policy, provider, collection)
            observations.extend(normalized)
            source_objects.append(source_trace)
        return ProviderCollection(
            provider=provider,
            collection=collection,
            observations=tuple(observations),
            private_trace={
                "source_endpoint": DEVICE_CONFIGURATIONS_PATH,
                "supported_policy_count": supported_policy_count,
                "unsupported_policy_types": cast(
                    JsonValue,
                    [
                        {"policy_type": policy_type, "count": count}
                        for policy_type, count in sorted(unsupported_types.items())
                    ],
                ),
                "source_objects": source_objects,
                "raw_response_persisted": False,
            },
        )

    def _normalize_policy(
        self,
        policy: dict[str, JsonValue],
        provider: EvidenceObject,
        collection: EvidenceObject,
    ) -> tuple[list[EvidenceObject], dict[str, JsonValue]]:
        policy_id = policy.get("id")
        modified = policy.get("lastModifiedDateTime")
        if not isinstance(policy_id, str) or not policy_id or not isinstance(modified, str):
            raise GraphProviderError(
                GraphErrorCategory.MALFORMED_RESPONSE, endpoint=DEVICE_CONFIGURATIONS_PATH
            )
        assignments_path = f"{DEVICE_CONFIGURATIONS_PATH}/{policy_id}/assignments"
        assignments = self._client.get_collection(assignments_path)
        target_types: set[str] = set()
        for assignment in assignments:
            target = assignment.get("target")
            if not isinstance(target, dict):
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE, endpoint=assignments_path
                )
            target_type = target.get("@odata.type")
            if not isinstance(target_type, str) or not target_type:
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE, endpoint=assignments_path
                )
            target_types.add(target_type.removeprefix("#microsoft.graph."))

        settings: tuple[
            tuple[str, str, type[bool] | type[int], Callable[[bool | int], JsonValue]], ...
        ] = (
            (
                "passwordRequired",
                "macos.screen_lock.require_password",
                bool,
                lambda value: value,
            ),
            (
                "passwordMinutesOfInactivityBeforeScreenTimeout",
                "macos.screen_lock.max_idle_seconds",
                int,
                lambda value: value * 60,
            ),
        )
        result: list[EvidenceObject] = []
        for source_field, setting_key, expected_type, transform in settings:
            if source_field not in policy or policy[source_field] is None:
                continue
            value = policy[source_field]
            if type(value) is not expected_type:
                raise GraphProviderError(
                    GraphErrorCategory.MALFORMED_RESPONSE, endpoint=DEVICE_CONFIGURATIONS_PATH
                )
            result.append(
                make_evidence_object(
                    "normalized_configuration_observation",
                    {
                        "collection_evidence_id": collection["evidence_id"],
                        "provider_evidence_id": provider["evidence_id"],
                        "platform": "macOS",
                        "setting_key": setting_key,
                        "observed_value": transform(value),
                        "observation_state": "observed",
                        "source_modified_at_utc": _normalize_graph_timestamp(modified),
                        "freshness": collection["freshness"],
                    },
                )
            )
        return result, {
            "source_object_id": policy_id,
            "source_odata_type": SUPPORTED_ODATA_TYPE,
            "observation_evidence_ids": cast(JsonValue, [item["evidence_id"] for item in result]),
            "assignment_count": len(assignments),
            "assignment_target_types": cast(JsonValue, sorted(target_types)),
        }


def _path_api_version(path: str) -> str | None:
    for version in SUPPORTED_API_VERSIONS:
        if path.startswith(f"/{version}/"):
            return version
    return None


def _is_graph_url(url: str, api_version: str) -> bool:
    parts = urlsplit(url)
    return (
        parts.scheme == "https"
        and parts.hostname == GRAPH_HOST
        and parts.port in {None, 443}
        and parts.username is None
        and parts.password is None
        and not parts.fragment
        and api_version in SUPPORTED_API_VERSIONS
        and parts.path.startswith(f"/{api_version}/")
    )


def _error_category(status_code: int) -> GraphErrorCategory:
    if status_code == 401:
        return GraphErrorCategory.AUTHENTICATION
    if status_code == 403:
        return GraphErrorCategory.AUTHORIZATION
    if status_code == 404:
        return GraphErrorCategory.NOT_FOUND
    if status_code == 409:
        return GraphErrorCategory.CONFLICT
    if status_code == 429:
        return GraphErrorCategory.THROTTLED
    if 500 <= status_code <= 599:
        return GraphErrorCategory.TRANSIENT
    return GraphErrorCategory.MALFORMED_RESPONSE


def _safe_graph_error_code(body: bytes) -> str | None:
    try:
        decoded = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(decoded, dict):
        return None
    error = decoded.get("error")
    if not isinstance(error, dict):
        return None
    code = error.get("code")
    return code if isinstance(code, str) and len(code) <= 100 else None


def _retry_delay(
    retry_after: str | None,
    attempt: int,
    *,
    jitter: Callable[[float], float] = lambda maximum: 0.0,
) -> float:
    if retry_after is not None:
        try:
            seconds = int(retry_after)
        except ValueError:
            try:
                parsed = parsedate_to_datetime(retry_after)
                seconds = max(0, int((parsed - datetime.now(UTC)).total_seconds()))
            except (TypeError, ValueError):
                seconds = 2**attempt
        return float(min(max(seconds, 0), 60))
    base = float(min(2**attempt, 60))
    return min(60.0, base + max(0.0, min(jitter(min(1.0, base / 4)), 1.0)))


def _normalize_graph_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GraphProviderError(
            GraphErrorCategory.MALFORMED_RESPONSE, endpoint=DEVICE_CONFIGURATIONS_PATH
        ) from exc
    if parsed.tzinfo is None:
        raise GraphProviderError(
            GraphErrorCategory.MALFORMED_RESPONSE, endpoint=DEVICE_CONFIGURATIONS_PATH
        )
    return parsed.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
