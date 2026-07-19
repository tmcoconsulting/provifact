"""Polished, identity-free Apple environment fixture for Mission Control."""

from __future__ import annotations

from typing import Final, cast

from evidenceops.domain import JsonValue, fingerprint
from evidenceops.evidence.mission import build_public_mission_snapshot
from evidenceops.providers.apple import (
    APPLE_COLLECTION_SCHEMA_VERSION,
    APPLE_PROVIDER_VERSION,
    ENDPOINTS,
    AppleIntuneCollection,
)

MISSION_FIXTURE_NOTICE: Final = "SYNTHETIC_TEST_DATA_ONLY"
MISSION_COLLECTION_TIME: Final = "2026-07-19T15:00:00Z"
MISSION_SYNTHETIC_COMMIT: Final = "synthetic-mission-reviewed-commit"
MISSION_PSEUDONYM_KEY: Final = bytes(range(32))


def build_mission_demo() -> dict[str, JsonValue]:
    """Build current and prior fixture snapshots and return the current artifact."""
    previous = build_public_mission_snapshot(
        _collection(previous=True),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit=MISSION_SYNTHETIC_COMMIT,
    )
    return build_public_mission_snapshot(
        _collection(previous=False),
        pseudonym_key=MISSION_PSEUDONYM_KEY,
        synthetic=True,
        source_git_commit=MISSION_SYNTHETIC_COMMIT,
        previous=previous,
    )


def _collection(*, previous: bool) -> AppleIntuneCollection:
    records: list[dict[str, JsonValue]] = []
    records.extend(_devices())
    policies = {
        "filevault": _base_record(
            "settings_catalog",
            "synthetic-policy-filevault",
            {
                "odata_type": "deviceManagementConfigurationPolicy",
                "platforms": ["macOS"],
                "assignment_count": 1,
                "private_display_name": "Synthetic macOS FileVault Policy",
            },
            api_version="beta",
        ),
        "firewall": _base_record(
            "settings_catalog",
            "synthetic-policy-firewall",
            {
                "odata_type": "deviceManagementConfigurationPolicy",
                "platforms": ["macOS"],
                "assignment_count": 1,
                "private_display_name": "Synthetic macOS Firewall Policy",
            },
            api_version="beta",
        ),
        "stealth": _base_record(
            "settings_catalog",
            "synthetic-policy-stealth",
            {
                "odata_type": "deviceManagementConfigurationPolicy",
                "platforms": ["macOS"],
                "assignment_count": 0,
                "private_display_name": "Synthetic macOS Firewall Stealth Policy",
            },
            api_version="beta",
        ),
        "screen-primary": _base_record(
            "settings_catalog",
            "synthetic-policy-screen-primary",
            {
                "odata_type": "deviceManagementConfigurationPolicy",
                "platforms": ["macOS"],
                "assignment_count": 1,
                "private_display_name": "Synthetic macOS Screen Lock Policy",
            },
            api_version="beta",
        ),
        "screen-conflict": _base_record(
            "settings_catalog",
            "synthetic-policy-screen-conflict",
            {
                "odata_type": "deviceManagementConfigurationPolicy",
                "platforms": ["macOS"],
                "assignment_count": 1,
                "private_display_name": "Synthetic macOS Conflicting Screen Lock Policy",
            },
            api_version="beta",
        ),
    }
    records.extend(policies.values())
    filevault_value = bool(previous)
    firewall_value = bool(previous)
    records.extend(
        [
            _setting(policies["filevault"], "macos.security.filevault.enabled", filevault_value),
            _setting(policies["firewall"], "macos.security.firewall.enabled", firewall_value),
            _setting(policies["stealth"], "macos.security.firewall.stealth_mode", True),
            _setting(policies["screen-primary"], "macos.screen_lock.require_password", True),
            _setting(policies["screen-primary"], "macos.screen_lock.max_idle_seconds", 600),
        ]
    )
    if not previous:
        records.append(
            _setting(
                policies["screen-conflict"],
                "macos.screen_lock.require_password",
                False,
            )
        )
    for key in ("filevault", "firewall", "screen-primary", "screen-conflict"):
        if key == "screen-conflict" and previous:
            continue
        records.append(_assignment(policies[key]))
    records.extend(
        [
            _base_record(
                "configuration_profiles",
                "synthetic-ios-passcode",
                {
                    "odata_type": "iosGeneralDeviceConfiguration",
                    "platforms": ["iOS", "iPadOS"],
                    "assignment_count": 1,
                    "private_display_name": "Synthetic iOS and iPadOS Passcode Policy",
                },
            ),
            _base_record(
                "compliance_policies",
                "synthetic-macos-compliance",
                {
                    "odata_type": "macOSCompliancePolicy",
                    "platforms": ["macOS"],
                    "assignment_count": 1,
                    "private_display_name": "Synthetic macOS Compliance Policy",
                },
            ),
            _base_record(
                "applications",
                "synthetic-ios-app",
                {
                    "odata_type": "iosStoreApp",
                    "platforms": ["iOS", "iPadOS"],
                    "assignment_count": 1,
                    "status": "deploymentFailuresObserved",
                    "private_display_name": "Synthetic Managed Productivity App",
                    "install_failure_count": 1,
                },
            ),
            _base_record(
                "apple_push_notification_service",
                "singleton:apns-certificate",
                {
                    "odata_type": "applePushNotificationCertificate",
                    "platforms": ["macOS", "iOS", "iPadOS"],
                    "assignment_count": 0,
                    "state": "healthy",
                    "expires_at_utc": "2027-06-30T00:00:00Z",
                },
            ),
            _base_record(
                "apple_apps_and_books",
                "synthetic-vpp-token",
                {
                    "odata_type": "vppToken",
                    "platforms": ["macOS", "iOS", "iPadOS"],
                    "assignment_count": 0,
                    "status": "valid",
                },
            ),
        ]
    )
    statuses: tuple[dict[str, JsonValue], ...] = tuple(
        cast(
            dict[str, JsonValue],
            {
                "key": spec.key,
                "resource_family": spec.resource_family,
                "source_api_version": spec.api_version,
                "required_permission": spec.permission,
                "status": "unavailable" if spec.key == "app-protection-policies" else "collected",
                "record_count": 0 if spec.key == "app-protection-policies" else 1,
                **({"beta_reason": spec.beta_reason} if spec.beta_reason else {}),
            },
        )
        for spec in ENDPOINTS
    )
    gap_unsigned: dict[str, JsonValue] = {
        "resource_family": "app_protection_policies",
        "source_endpoint_key": "app-protection-policies",
        "source_api_version": "v1.0",
        "required_permission": "DeviceManagementApps.Read.All",
        "reason": "fixture_permission_gap",
        "http_status": 403,
        "record_position": None,
        "additional_evidence_required": True,
    }
    gap = {**gap_unsigned, "gap_id": f"gap-{fingerprint(gap_unsigned)[7:31]}"}
    return AppleIntuneCollection(
        schema_version=APPLE_COLLECTION_SCHEMA_VERSION,
        provider="synthetic-microsoft-intune-apple",
        provider_version=APPLE_PROVIDER_VERSION,
        collected_at_utc=MISSION_COLLECTION_TIME,
        records=tuple(records),
        endpoint_statuses=statuses,
        collection_gaps=(gap,),
        raw_response_persisted=False,
    )


def _devices() -> list[dict[str, JsonValue]]:
    return [
        _base_record(
            "managed_devices",
            source_id,
            {
                "platforms": [platform],
                "os_version": version,
                "ownership": "company",
                "management_state": "managed",
                "compliance_state": compliance,
                "supervised": supervised,
                "encrypted": encrypted,
                "compromised_state": "false",
                "model_family": model,
                "manufacturer": "Apple",
                "management_agent": "mdm",
                "registration_state": "registered",
                "last_sync_at_utc": MISSION_COLLECTION_TIME,
                "has_enrollment_profile": True,
                "has_device_category": True,
            },
        )
        for source_id, platform, version, compliance, supervised, encrypted, model in (
            ("synthetic-device-mac", "macOS", "26.0", "noncompliant", False, False, "macbook"),
            ("synthetic-device-phone", "iOS", "26.0", "compliant", True, True, "iphone"),
            ("synthetic-device-tablet", "iPadOS", "26.0", "compliant", True, True, "ipad"),
        )
    ]


def _setting(
    parent: dict[str, JsonValue], definition: str, value: JsonValue
) -> dict[str, JsonValue]:
    return _base_record(
        "settings_catalog_settings",
        f"{parent['source_object_id']}:{definition}:{canonical_marker(value)}",
        {
            "parent_evidence_id": parent["evidence_id"],
            "relationship": "settings",
            "platforms": ["macOS"],
            "setting_definition_id": definition,
            "normalized_value": value,
        },
        api_version="beta",
    )


def _assignment(parent: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return _base_record(
        "settings_catalog_assignments",
        f"{parent['source_object_id']}:assignment",
        {
            "parent_evidence_id": parent["evidence_id"],
            "relationship": "assignments",
            "platforms": ["macOS"],
            "assignment_kind": "allDevicesAssignmentTarget",
            "assignment_intent": "included",
            "has_filter": False,
            "filter_type": "none",
        },
        api_version="beta",
    )


def _base_record(
    family: str,
    source_id: str,
    properties: dict[str, JsonValue],
    *,
    api_version: str = "v1.0",
) -> dict[str, JsonValue]:
    unsigned: dict[str, JsonValue] = {
        "schema_version": APPLE_COLLECTION_SCHEMA_VERSION,
        "resource_family": family,
        "source_api_version": api_version,
        "source_endpoint_key": f"fixture-{family}",
        "required_permission": _fixture_permission(family),
        "collected_at_utc": MISSION_COLLECTION_TIME,
        "source_object_id": source_id,
        "properties": properties,
    }
    digest = fingerprint(unsigned)
    return {
        **unsigned,
        "evidence_id": f"apple-{digest[7:31]}",
        "content_fingerprint": digest,
    }


def _fixture_permission(family: str) -> str:
    if family == "managed_devices":
        return "DeviceManagementManagedDevices.Read.All"
    if family in {"applications", "apple_apps_and_books"}:
        return "DeviceManagementApps.Read.All"
    if family == "apple_push_notification_service":
        return "DeviceManagementServiceConfig.Read.All"
    return "DeviceManagementConfiguration.Read.All"


def canonical_marker(value: JsonValue) -> str:
    """Return a short fixture-only stable marker without an identity value."""
    return fingerprint(value)[7:19]


def fixture_finding_outcomes(snapshot: dict[str, JsonValue]) -> set[str]:
    """Expose fixture outcome coverage for focused tests."""
    findings = cast(list[dict[str, JsonValue]], snapshot["findings"])
    return {cast(str, item["drift_type"]) for item in findings}
