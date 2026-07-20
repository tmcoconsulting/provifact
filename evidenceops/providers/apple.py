"""Comprehensive GET-only Apple evidence collector for Microsoft Intune.

The adapter intentionally emits a small vendor-neutral normalized vocabulary.
Source identifiers are retained only in the returned private in-memory collection
for deterministic joins and are removed or pseudonymized by the publication
boundary. Raw Graph responses are never returned, logged, or persisted.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, Protocol, cast

from evidenceops.domain import JsonValue, fingerprint
from evidenceops.providers.intune import GraphErrorCategory, GraphProviderError

APPLE_PROVIDER_VERSION: Final = "2.1.0"
APPLE_COLLECTION_SCHEMA_VERSION: Final = "2.0.0"
MAX_CONCURRENCY: Final = 4
MAX_SETTING_DEPTH: Final = 8
MAX_SETTINGS_PER_RESPONSE_ITEM: Final = 512


class _OutOfScopeRecordError(ValueError):
    """A well-formed provider record for a platform outside the Apple slice."""


class GraphReader(Protocol):
    """The complete network surface available to this provider remains GET-only."""

    def get_collection(self, path: str) -> list[dict[str, JsonValue]]:
        """Read all pages from one Graph collection."""
        ...

    def get_object(self, path: str) -> dict[str, JsonValue]:
        """Read one Graph object."""
        ...


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """One explicitly versioned Graph read surface."""

    key: str
    resource_family: str
    path: str
    permission: str
    response_kind: str = "collection"
    beta_reason: str | None = None

    @property
    def api_version(self) -> str:
        return self.path.split("/", maxsplit=2)[1]


@dataclass(frozen=True, slots=True)
class AppleIntuneCollection:
    """Normalized private collection with graceful per-endpoint gaps."""

    schema_version: str
    provider: str
    provider_version: str
    collected_at_utc: str
    records: tuple[dict[str, JsonValue], ...]
    endpoint_statuses: tuple[dict[str, JsonValue], ...]
    collection_gaps: tuple[dict[str, JsonValue], ...]
    raw_response_persisted: bool


ENDPOINTS: Final[tuple[EndpointSpec, ...]] = (
    EndpointSpec(
        "managed-devices",
        "managed_devices",
        (
            "/v1.0/deviceManagement/managedDevices?"
            "$select=id,operatingSystem,osVersion,managedDeviceOwnerType,managementState,"
            "complianceState,enrollmentProfileName,deviceCategoryDisplayName,isSupervised,"
            "isEncrypted,jailBroken,lastSyncDateTime,model,manufacturer,managementAgent,"
            "deviceRegistrationState"
        ),
        "DeviceManagementManagedDevices.Read.All",
    ),
    EndpointSpec(
        "device-configurations",
        "configuration_profiles",
        "/v1.0/deviceManagement/deviceConfigurations",
        "DeviceManagementConfiguration.Read.All",
    ),
    EndpointSpec(
        "settings-catalog",
        "settings_catalog",
        "/beta/deviceManagement/configurationPolicies",
        "DeviceManagementConfiguration.Read.All",
        beta_reason=(
            "Microsoft Graph exposes the Intune Settings Catalog configurationPolicy resource "
            "only through the beta endpoint at the pinned implementation date."
        ),
    ),
    EndpointSpec(
        "compliance-policies",
        "compliance_policies",
        "/v1.0/deviceManagement/deviceCompliancePolicies",
        "DeviceManagementConfiguration.Read.All",
    ),
    EndpointSpec(
        "mobile-apps",
        "applications",
        "/v1.0/deviceAppManagement/mobileApps",
        "DeviceManagementApps.Read.All",
    ),
    EndpointSpec(
        "app-configurations",
        "app_configuration_policies",
        "/v1.0/deviceAppManagement/mobileAppConfigurations",
        "DeviceManagementApps.Read.All",
    ),
    EndpointSpec(
        "app-protection-policies",
        "app_protection_policies",
        "/v1.0/deviceAppManagement/managedAppPolicies",
        "DeviceManagementApps.Read.All",
    ),
    EndpointSpec(
        "enrollment-configurations",
        "enrollment_configuration",
        "/v1.0/deviceManagement/deviceEnrollmentConfigurations",
        "DeviceManagementServiceConfig.Read.All",
    ),
    EndpointSpec(
        "device-categories",
        "device_categories",
        "/v1.0/deviceManagement/deviceCategories",
        "DeviceManagementServiceConfig.Read.All",
    ),
    EndpointSpec(
        "ade-tokens",
        "apple_automated_device_enrollment",
        "/v1.0/deviceManagement/depOnboardingSettings",
        "DeviceManagementServiceConfig.Read.All",
    ),
    EndpointSpec(
        "vpp-tokens",
        "apple_apps_and_books",
        "/v1.0/deviceAppManagement/vppTokens",
        "DeviceManagementApps.Read.All",
    ),
    EndpointSpec(
        "apns-certificate",
        "apple_push_notification_service",
        "/v1.0/deviceManagement/applePushNotificationCertificate",
        "DeviceManagementServiceConfig.Read.All",
        response_kind="object",
    ),
)


class AppleIntuneProvider:
    """Collect Apple-focused Intune evidence without exposing mutation methods."""

    name = "microsoft-intune-apple"
    version = APPLE_PROVIDER_VERSION

    def __init__(
        self,
        client: GraphReader,
        *,
        max_concurrency: int = MAX_CONCURRENCY,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if max_concurrency < 1 or max_concurrency > MAX_CONCURRENCY:
            raise ValueError(f"max_concurrency must be between 1 and {MAX_CONCURRENCY}")
        self._client = client
        self._max_concurrency = max_concurrency
        self._now = now or (lambda: datetime.now(UTC))

    def collect(self) -> AppleIntuneCollection:
        """Collect each resource family independently and preserve partial failures."""
        collected_at = _utc(self._now())
        records: list[dict[str, JsonValue]] = []
        statuses: list[dict[str, JsonValue]] = []
        gaps: list[dict[str, JsonValue]] = []
        results: dict[str, Sequence[dict[str, JsonValue]] | dict[str, JsonValue]] = {}

        with ThreadPoolExecutor(max_workers=self._max_concurrency) as pool:
            futures: dict[
                Future[Sequence[dict[str, JsonValue]] | dict[str, JsonValue]], EndpointSpec
            ] = {pool.submit(self._read_endpoint, spec): spec for spec in ENDPOINTS}
            for future in as_completed(futures):
                spec = futures[future]
                try:
                    raw = future.result()
                except GraphProviderError as exc:
                    gaps.append(_gap(spec, exc.category.value, exc.status_code))
                    statuses.append(_endpoint_status(spec, "unavailable", 0))
                except (TypeError, ValueError):
                    gaps.append(_gap(spec, "schema_change", None))
                    statuses.append(_endpoint_status(spec, "malformed", 0))
                else:
                    results[spec.key] = raw
                    count = len(raw) if isinstance(raw, list) else 1
                    statuses.append(_endpoint_status(spec, "collected", count))

        for spec in ENDPOINTS:
            if spec.key not in results:
                continue
            raw_result = results[spec.key]
            items = raw_result if isinstance(raw_result, list) else [raw_result]
            for position, item in enumerate(items):
                try:
                    normalized = _normalize_item(spec, item, collected_at)
                except _OutOfScopeRecordError:
                    continue
                except (TypeError, ValueError):
                    gaps.append(_gap(spec, "record_schema_change", None, position=position))
                    continue
                if normalized is None:
                    gaps.append(_gap(spec, "unsupported_resource_type", None, position=position))
                    continue
                records.append(normalized)

        expandable = [record for record in records if _expansion_paths(record)]
        expansions = self._collect_expansions(expandable, gaps, statuses, collected_at)
        records.extend(expansions)
        return AppleIntuneCollection(
            schema_version=APPLE_COLLECTION_SCHEMA_VERSION,
            provider=self.name,
            provider_version=self.version,
            collected_at_utc=collected_at,
            records=tuple(sorted(records, key=_record_sort_key)),
            endpoint_statuses=tuple(sorted(statuses, key=lambda item: cast(str, item["key"]))),
            collection_gaps=tuple(sorted(gaps, key=_gap_sort_key)),
            raw_response_persisted=False,
        )

    def _read_endpoint(
        self, spec: EndpointSpec
    ) -> Sequence[dict[str, JsonValue]] | dict[str, JsonValue]:
        if spec.response_kind == "collection":
            return self._client.get_collection(spec.path)
        return self._client.get_object(spec.path)

    def _collect_expansions(
        self,
        parents: Sequence[dict[str, JsonValue]],
        gaps: list[dict[str, JsonValue]],
        statuses: list[dict[str, JsonValue]],
        collected_at: str,
    ) -> list[dict[str, JsonValue]]:
        tasks: list[tuple[dict[str, JsonValue], str, str]] = []
        for parent in parents:
            for relationship, path in _expansion_paths(parent):
                tasks.append((parent, relationship, path))
        expansions: list[dict[str, JsonValue]] = []
        with ThreadPoolExecutor(max_workers=self._max_concurrency) as pool:
            futures = {
                pool.submit(self._client.get_collection, path): (parent, relationship, path)
                for parent, relationship, path in tasks
            }
            for future in as_completed(futures):
                parent, relationship, path = futures[future]
                key = f"{parent['resource_family']}:{relationship}"
                spec = EndpointSpec(
                    key=key,
                    resource_family=cast(str, parent["resource_family"]),
                    path=path,
                    permission=cast(str, parent["required_permission"]),
                    beta_reason=(
                        "Relationship belongs to the beta Settings Catalog resource."
                        if path.startswith("/beta/")
                        else None
                    ),
                )
                try:
                    items = future.result()
                except GraphProviderError as exc:
                    gaps.append(_gap(spec, exc.category.value, exc.status_code))
                    statuses.append(_endpoint_status(spec, "unavailable", 0))
                    continue
                statuses.append(_endpoint_status(spec, "collected", len(items)))
                for position, item in enumerate(items):
                    try:
                        expansions.extend(
                            _normalize_expansion_records(parent, relationship, item, collected_at)
                        )
                    except (TypeError, ValueError):
                        gaps.append(_gap(spec, "record_schema_change", None, position=position))
        return expansions


def _normalize_item(
    spec: EndpointSpec, item: dict[str, JsonValue], collected_at: str
) -> dict[str, JsonValue] | None:
    if not isinstance(item, dict):
        raise TypeError("Graph item must be an object")
    if spec.resource_family == "managed_devices":
        return _normalize_device(spec, item, collected_at)
    source_id = (
        _optional_string(item, "id")
        if spec.response_kind == "object"
        else _required_string(item, "id")
    )
    odata_type = _optional_string(item, "@odata.type") or "microsoft.graph.unknown"
    platforms = _platforms(item, odata_type)
    if spec.resource_family in {
        "configuration_profiles",
        "settings_catalog",
        "compliance_policies",
    } and not platforms.intersection({"macOS", "iOS", "iPadOS", "iOS/iPadOS"}):
        if platforms != {"unknown"}:
            raise _OutOfScopeRecordError("provider record is outside the Apple collection slice")
        return None
    properties: dict[str, JsonValue] = {
        "odata_type": _safe_odata_type(odata_type),
        "platforms": cast(JsonValue, sorted(platforms)),
        "assignment_count": 0,
    }
    for source, target in (
        ("lastModifiedDateTime", "modified_at_utc"),
        ("createdDateTime", "created_at_utc"),
        ("expirationDateTime", "expires_at_utc"),
        ("lastSyncDateTime", "last_sync_at_utc"),
    ):
        value = _optional_string(item, source)
        if value is not None:
            properties[target] = _graph_time(value)
    for source, target in (
        ("state", "state"),
        ("tokenState", "token_state"),
        ("status", "status"),
        ("roleScopeTagIds", "role_scope_tag_count"),
    ):
        raw_value = item.get(source)
        if isinstance(raw_value, str):
            properties[target] = _safe_enum(raw_value)
        elif isinstance(raw_value, list):
            properties[target] = len(raw_value)
    display_name = _optional_string(item, "displayName")
    if display_name is not None:
        properties["private_display_name"] = display_name
    bundle_id = _optional_string(item, "bundleId")
    if bundle_id is not None:
        properties["bundle_identifier"] = bundle_id
    return _record(
        spec=spec,
        source_id=source_id or f"singleton:{spec.key}",
        collected_at=collected_at,
        properties=properties,
    )


def _normalize_device(
    spec: EndpointSpec, item: dict[str, JsonValue], collected_at: str
) -> dict[str, JsonValue]:
    source_id = _required_string(item, "id")
    operating_system = _required_string(item, "operatingSystem")
    model = _optional_string(item, "model")
    platform = _device_platform(operating_system, model)
    properties: dict[str, JsonValue] = {
        "platforms": [platform],
        "os_version": _optional_string(item, "osVersion") or "unknown",
        "ownership": _safe_enum(_optional_string(item, "managedDeviceOwnerType") or "unknown"),
        "management_state": _safe_enum(_optional_string(item, "managementState") or "unknown"),
        "compliance_state": _safe_enum(_optional_string(item, "complianceState") or "unknown"),
        "supervised": _optional_bool(item, "isSupervised"),
        "encrypted": _optional_bool(item, "isEncrypted"),
        "compromised_state": _safe_enum(_optional_string(item, "jailBroken") or "unknown"),
        "model_family": _model_family(model),
        "manufacturer": _safe_enum(_optional_string(item, "manufacturer") or "unknown"),
        "management_agent": _safe_enum(_optional_string(item, "managementAgent") or "unknown"),
        "registration_state": _safe_enum(
            _optional_string(item, "deviceRegistrationState") or "unknown"
        ),
    }
    last_sync = _optional_string(item, "lastSyncDateTime")
    if last_sync is not None:
        properties["last_sync_at_utc"] = _graph_time(last_sync)
    # Enrollment profile and category names are intentionally not retained; only
    # their presence is useful to public coverage metrics.
    properties["has_enrollment_profile"] = bool(_optional_string(item, "enrollmentProfileName"))
    properties["has_device_category"] = bool(_optional_string(item, "deviceCategoryDisplayName"))
    return _record(spec=spec, source_id=source_id, collected_at=collected_at, properties=properties)


def _record(
    *,
    spec: EndpointSpec,
    source_id: str,
    collected_at: str,
    properties: dict[str, JsonValue],
) -> dict[str, JsonValue]:
    unsigned: dict[str, JsonValue] = {
        "schema_version": APPLE_COLLECTION_SCHEMA_VERSION,
        "resource_family": spec.resource_family,
        "source_api_version": spec.api_version,
        "source_endpoint_key": spec.key,
        "required_permission": spec.permission,
        "collected_at_utc": collected_at,
        "source_object_id": source_id,
        "properties": properties,
    }
    return {
        **unsigned,
        "evidence_id": f"apple-{fingerprint(unsigned)[7:31]}",
        "content_fingerprint": fingerprint(unsigned),
    }


def _expansion_paths(record: dict[str, JsonValue]) -> tuple[tuple[str, str], ...]:
    family = record["resource_family"]
    source_id = cast(str, record["source_object_id"])
    version = cast(str, record["source_api_version"])
    if family == "configuration_profiles":
        return (
            (
                "assignments",
                f"/{version}/deviceManagement/deviceConfigurations/{source_id}/assignments",
            ),
        )
    if family == "settings_catalog":
        root = f"/{version}/deviceManagement/configurationPolicies/{source_id}"
        return (("settings", f"{root}/settings"), ("assignments", f"{root}/assignments"))
    if family == "compliance_policies":
        root = f"/{version}/deviceManagement/deviceCompliancePolicies/{source_id}"
        return (
            ("assignments", f"{root}/assignments"),
            ("scheduled_actions", f"{root}/scheduledActionsForRule"),
        )
    if family in {"applications", "app_configuration_policies"}:
        root_name = "mobileApps" if family == "applications" else "mobileAppConfigurations"
        return (
            ("assignments", f"/{version}/deviceAppManagement/{root_name}/{source_id}/assignments"),
        )
    return ()


def _normalize_expansion(
    parent: dict[str, JsonValue],
    relationship: str,
    item: dict[str, JsonValue],
    collected_at: str,
) -> dict[str, JsonValue]:
    if not isinstance(item, dict):
        raise TypeError("Graph expansion item must be an object")
    parent_id = cast(str, parent["source_object_id"])
    item_id = _optional_string(item, "id") or fingerprint(cast(JsonValue, item))[7:31]
    properties: dict[str, JsonValue] = {
        "parent_evidence_id": parent["evidence_id"],
        "relationship": relationship,
        "platforms": cast(dict[str, JsonValue], parent["properties"])["platforms"],
    }
    if relationship == "assignments":
        target = item.get("target")
        if not isinstance(target, dict):
            raise TypeError("assignment target must be an object")
        target_type = _required_string(target, "@odata.type")
        properties.update(
            {
                "assignment_kind": _safe_odata_type(target_type),
                "assignment_intent": _safe_enum(_optional_string(item, "intent") or "included"),
                "has_filter": bool(
                    _optional_string(target, "deviceAndAppManagementAssignmentFilterId")
                ),
                "filter_type": _safe_enum(
                    _optional_string(target, "deviceAndAppManagementAssignmentFilterType") or "none"
                ),
            }
        )
        group_id = _optional_string(target, "groupId")
        if group_id is not None:
            properties["private_target_id"] = group_id
    elif relationship == "settings":
        setting_definition, setting_value, normalization_state = _extract_setting(item)
        properties["setting_definition_id"] = setting_definition
        properties["normalized_value"] = setting_value
        properties["normalization_state"] = normalization_state
    elif relationship == "scheduled_actions":
        properties["action_type"] = _safe_enum(
            _optional_string(item, "ruleName") or "scheduled_action"
        )
        configurations = item.get("scheduledActionConfigurations")
        properties["configuration_count"] = (
            len(configurations) if isinstance(configurations, list) else 0
        )
    spec = EndpointSpec(
        key=f"{parent['source_endpoint_key']}:{relationship}",
        resource_family=f"{parent['resource_family']}_{relationship}",
        path=f"/{parent['source_api_version']}/expanded",
        permission=cast(str, parent["required_permission"]),
    )
    return _record(
        spec=spec,
        source_id=f"{parent_id}:{item_id}",
        collected_at=collected_at,
        properties=properties,
    )


def _normalize_expansion_records(
    parent: dict[str, JsonValue],
    relationship: str,
    item: dict[str, JsonValue],
    collected_at: str,
) -> list[dict[str, JsonValue]]:
    """Flatten documented nested Settings Catalog instances into evidence records."""
    if relationship != "settings":
        return [_normalize_expansion(parent, relationship, item, collected_at)]
    return [
        _normalize_expansion(parent, relationship, flattened, collected_at)
        for flattened in _flatten_setting_items(item)
    ]


def _flatten_setting_items(item: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """Return scalar leaf instances from one documented Graph setting tree.

    Microsoft Graph represents Settings Catalog groups as parent instances whose
    values contain child instances.  The parent definition identifies a container,
    not the configured setting.  Unknown or empty shapes remain as one unsupported
    leaf so deterministic evaluation still fails closed.
    """
    root_id = _optional_string(item, "id") or fingerprint(cast(JsonValue, item))[7:31]
    root = item.get("settingInstance")
    if not isinstance(root, dict):
        raise TypeError("Settings Catalog entry lacks a settingInstance object")
    leaves: list[tuple[str, dict[str, JsonValue]]] = []

    def visit(instance: dict[str, JsonValue], path: str, depth: int) -> None:
        if depth > MAX_SETTING_DEPTH:
            raise ValueError("Settings Catalog setting nesting exceeds the supported bound")
        _safe_setting_definition_id(_required_string(instance, "settingDefinitionId"))
        direct_value = False
        child_instances: list[dict[str, JsonValue]] = []
        for value_key in ("simpleSettingValue", "choiceSettingValue"):
            value = instance.get(value_key)
            if value is None:
                continue
            if not isinstance(value, dict):
                raise TypeError(f"{value_key} must be an object when present")
            if "value" in value:
                direct_value = True
            children = value.get("children", [])
            child_instances.extend(_setting_children(children, f"{value_key}.children"))
        group_value = instance.get("groupSettingValue")
        if group_value is not None:
            if not isinstance(group_value, dict):
                raise TypeError("groupSettingValue must be an object when present")
            child_instances.extend(
                _setting_children(group_value.get("children", []), "groupSettingValue.children")
            )
        group_collection = instance.get("groupSettingCollectionValue")
        if group_collection is not None:
            if not isinstance(group_collection, list):
                raise TypeError("groupSettingCollectionValue must be an array when present")
            for group_index, group in enumerate(group_collection):
                if not isinstance(group, dict):
                    raise TypeError("groupSettingCollectionValue entries must be objects")
                child_instances.extend(
                    _setting_children(
                        group.get("children", []),
                        f"groupSettingCollectionValue[{group_index}].children",
                    )
                )
        if direct_value or not child_instances:
            leaves.append((path, instance))
            if len(leaves) > MAX_SETTINGS_PER_RESPONSE_ITEM:
                raise ValueError("Settings Catalog response item exceeds the supported leaf bound")
        for child_index, child in enumerate(child_instances):
            visit(child, f"{path}.{child_index}", depth + 1)

    visit(root, "0", 0)
    return [{"id": f"{root_id}:{path}", "settingInstance": instance} for path, instance in leaves]


def _setting_children(value: JsonValue, field: str) -> list[dict[str, JsonValue]]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be an array when present")
    result: list[dict[str, JsonValue]] = []
    for child in value:
        if not isinstance(child, dict):
            raise TypeError(f"{field} entries must be objects")
        result.append(child)
    return result


def _extract_setting(item: dict[str, JsonValue]) -> tuple[str, JsonValue, str]:
    instance = item.get("settingInstance")
    if not isinstance(instance, dict):
        raise TypeError("Settings Catalog entry lacks a settingInstance object")
    definition = _safe_setting_definition_id(_required_string(instance, "settingDefinitionId"))
    value: JsonValue = None
    for key in (
        "simpleSettingValue",
        "choiceSettingValue",
    ):
        candidate = instance.get(key)
        if isinstance(candidate, dict) and "value" in candidate:
            value = candidate["value"]
            break
    if value is None:
        # Retain the known provider taxonomy ID while refusing to invent meaning
        # for an unsupported structured setting. The evaluator can now distinguish
        # this from a setting that was genuinely absent from a complete response.
        return definition, None, "unsupported_value_shape"
    if isinstance(value, str):
        value = _safe_setting_value(value)
    elif not isinstance(value, (bool, int, float)) and value is not None:
        return definition, None, "unsupported_value_shape"
    return definition, value, "normalized"


def summarize_devices(records: Sequence[dict[str, JsonValue]]) -> dict[str, JsonValue]:
    """Return aggregate Apple device posture without identity-bearing rows."""
    devices = [record for record in records if record["resource_family"] == "managed_devices"]
    platform_counts: Counter[str] = Counter()
    compliance_counts: Counter[str] = Counter()
    encrypted_counts: Counter[str] = Counter()
    supervised_counts: Counter[str] = Counter()
    for record in devices:
        properties = cast(dict[str, JsonValue], record["properties"])
        platforms = cast(list[str], properties["platforms"])
        platform_counts[platforms[0]] += 1
        compliance_counts[cast(str, properties["compliance_state"])] += 1
        encrypted_counts[str(properties["encrypted"]).lower()] += 1
        supervised_counts[str(properties["supervised"]).lower()] += 1
    return {
        "total": len(devices),
        "by_platform": dict(sorted(platform_counts.items())),
        "by_compliance_state": dict(sorted(compliance_counts.items())),
        "by_encryption_state": dict(sorted(encrypted_counts.items())),
        "by_supervision_state": dict(sorted(supervised_counts.items())),
    }


def _endpoint_status(spec: EndpointSpec, status: str, count: int) -> dict[str, JsonValue]:
    value: dict[str, JsonValue] = {
        "key": spec.key,
        "resource_family": spec.resource_family,
        "source_api_version": spec.api_version,
        "required_permission": spec.permission,
        "status": status,
        "record_count": count,
    }
    if spec.beta_reason:
        value["beta_reason"] = spec.beta_reason
    return value


def _gap(
    spec: EndpointSpec,
    reason: str,
    status_code: int | None,
    *,
    position: int | None = None,
) -> dict[str, JsonValue]:
    unsigned: dict[str, JsonValue] = {
        "resource_family": spec.resource_family,
        "source_endpoint_key": spec.key,
        "source_api_version": spec.api_version,
        "required_permission": spec.permission,
        "reason": reason,
        "http_status": status_code,
        "record_position": position,
        "additional_evidence_required": True,
    }
    return {**unsigned, "gap_id": f"gap-{fingerprint(unsigned)[7:31]}"}


def _platforms(item: dict[str, JsonValue], odata_type: str) -> set[str]:
    platforms = item.get("platforms")
    result: set[str] = set()
    if isinstance(platforms, str):
        for value in platforms.replace(",", " ").split():
            result.update(_platform_token(value))
    result.update(_platform_token(odata_type))
    return result or {"unknown"}


def _platform_token(value: str) -> set[str]:
    lowered = value.lower()
    result: set[str] = set()
    if "macos" in lowered or "mac_os" in lowered:
        result.add("macOS")
    if "ios" in lowered:
        result.add("iOS/iPadOS")
    if "windows" in lowered:
        result.add("Windows")
    if "android" in lowered or "aosp" in lowered:
        result.add("Android")
    if "linux" in lowered:
        result.add("Linux")
    return result


def _device_platform(operating_system: str, model: str | None) -> str:
    lowered = operating_system.lower()
    if "mac" in lowered:
        return "macOS"
    if "ios" in lowered:
        return "iPadOS" if model and model.lower().startswith("ipad") else "iOS"
    return "other"


def _model_family(model: str | None) -> str:
    if not model:
        return "unknown"
    lowered = model.lower()
    for family in ("macbook", "imac", "mac mini", "mac studio", "ipad", "iphone"):
        if lowered.startswith(family):
            return family.replace(" ", "-")
    return "other-apple"


def _safe_odata_type(value: str) -> str:
    cleaned = value.removeprefix("#")
    cleaned = cleaned.removeprefix("microsoft.graph.")
    if (
        not cleaned
        or len(cleaned) > 160
        or not all(char.isalnum() or char in "._-" for char in cleaned)
    ):
        raise ValueError("unsafe OData type")
    return cleaned


def _safe_enum(value: str) -> str:
    if not value or len(value) > 100 or not all(char.isalnum() or char in "._-" for char in value):
        raise ValueError("unsafe enumerated value")
    return value


def _safe_setting_value(value: str) -> str:
    if (
        not value
        or len(value) > 200
        or not all(char.isalnum() or char in " ._:/-" for char in value)
    ):
        raise ValueError("unsafe setting value")
    return value


def _safe_setting_definition_id(value: str) -> str:
    if (
        not value
        or value != value.strip()
        or len(value) > 240
        or not value.isascii()
        or not all(character.isalnum() or character in "._:-/" for character in value)
    ):
        raise ValueError("unsafe Settings Catalog definition ID")
    return value


def _required_string(value: Mapping[str, JsonValue], field: str) -> str:
    item = value.get(field)
    if not isinstance(item, str) or not item:
        raise TypeError(f"field {field} must be a non-empty string")
    return item


def _optional_string(value: Mapping[str, JsonValue], field: str) -> str | None:
    item = value.get(field)
    if item is None:
        return None
    if not isinstance(item, str):
        raise TypeError(f"field {field} must be a string when present")
    return item or None


def _optional_bool(value: Mapping[str, JsonValue], field: str) -> bool | None:
    item = value.get(field)
    if item is None:
        return None
    if not isinstance(item, bool):
        raise TypeError(f"field {field} must be a boolean when present")
    return item


def _graph_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid Graph timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Graph timestamp must include a UTC offset")
    return _utc(parsed)


def _utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("collection time must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _record_sort_key(item: dict[str, JsonValue]) -> tuple[str, str]:
    return cast(str, item["resource_family"]), cast(str, item["evidence_id"])


def _gap_sort_key(item: dict[str, JsonValue]) -> tuple[str, str, int]:
    return (
        cast(str, item["resource_family"]),
        cast(str, item["reason"]),
        cast(int, item["record_position"] if item["record_position"] is not None else -1),
    )


def endpoint_permissions() -> dict[str, tuple[str, ...]]:
    """Return the exact endpoint catalog grouped by required read permission."""
    grouped: dict[str, list[str]] = {}
    for spec in ENDPOINTS:
        grouped.setdefault(spec.permission, []).append(spec.key)
    return {permission: tuple(keys) for permission, keys in sorted(grouped.items())}


def assert_get_only_provider() -> None:
    """Defensive runtime assertion used by workflow and permission tests."""
    if any(not spec.path.startswith(("/v1.0/", "/beta/")) for spec in ENDPOINTS):
        raise AssertionError("every Graph endpoint must be explicitly versioned")
    if any(spec.permission.endswith(".ReadWrite.All") for spec in ENDPOINTS):
        raise AssertionError("write permission present in Apple endpoint catalog")
    if GraphErrorCategory.CONFLICT.value != "conflict":
        raise AssertionError("Graph error vocabulary changed unexpectedly")
