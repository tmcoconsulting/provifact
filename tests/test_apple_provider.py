from __future__ import annotations

import inspect
from datetime import UTC, datetime
from typing import cast

import pytest

from evidenceops.domain import JsonValue
from evidenceops.evidence import build_public_mission_snapshot
from evidenceops.providers import (
    ENDPOINTS,
    AppleIntuneProvider,
    GraphErrorCategory,
    GraphProviderError,
    assert_get_only_provider,
    endpoint_permissions,
    summarize_devices,
)
from evidenceops.providers import apple as apple_module

NOW = datetime(2026, 7, 19, 15, 0, tzinfo=UTC)


class FakeReader:
    def __init__(
        self,
        collections: dict[str, list[dict[str, JsonValue]]] | None = None,
        objects: dict[str, dict[str, JsonValue]] | None = None,
        failures: dict[str, GraphProviderError] | None = None,
    ) -> None:
        self.collections = collections or {}
        self.objects = objects or {}
        self.failures = failures or {}
        self.calls: list[str] = []

    def get_collection(self, path: str) -> list[dict[str, JsonValue]]:
        self.calls.append(path)
        if path in self.failures:
            raise self.failures[path]
        return self.collections.get(path, [])

    def get_object(self, path: str) -> dict[str, JsonValue]:
        self.calls.append(path)
        if path in self.failures:
            raise self.failures[path]
        return self.objects.get(path, {})


def _catalog() -> tuple[FakeReader, dict[str, str]]:
    paths = {spec.key: spec.path for spec in ENDPOINTS}
    settings_id = "synthetic-settings-policy"
    config_id = "synthetic-config-policy"
    compliance_id = "synthetic-compliance-policy"
    app_id = "synthetic-app"
    app_config_id = "synthetic-app-config"
    collections: dict[str, list[dict[str, JsonValue]]] = {
        paths["managed-devices"]: [
            {
                "id": "private-device-source-id",
                "operatingSystem": "iOS",
                "osVersion": "26.0",
                "managedDeviceOwnerType": "company",
                "managementState": "managed",
                "complianceState": "compliant",
                "isSupervised": True,
                "isEncrypted": True,
                "jailBroken": "false",
                "lastSyncDateTime": "2026-07-19T14:00:00Z",
                "model": "iPad Pro",
                "manufacturer": "Apple",
                "managementAgent": "mdm",
                "deviceRegistrationState": "registered",
                "enrollmentProfileName": "private profile name",
                "deviceCategoryDisplayName": "private category name",
            }
        ],
        paths["device-configurations"]: [
            {
                "id": config_id,
                "@odata.type": "#microsoft.graph.macOSGeneralDeviceConfiguration",
                "displayName": "Private macOS configuration name",
                "lastModifiedDateTime": "2026-07-19T14:00:00Z",
            },
            {
                "id": "windows-policy",
                "@odata.type": "#microsoft.graph.windows10GeneralConfiguration",
            },
        ],
        paths["settings-catalog"]: [
            {
                "id": settings_id,
                "@odata.type": "#microsoft.graph.deviceManagementConfigurationPolicy",
                "platforms": "macOS",
                "displayName": "Private Settings Catalog name",
            }
        ],
        paths["compliance-policies"]: [
            {
                "id": compliance_id,
                "@odata.type": "#microsoft.graph.macOSCompliancePolicy",
                "displayName": "Private compliance name",
            }
        ],
        paths["mobile-apps"]: [
            {
                "id": app_id,
                "@odata.type": "#microsoft.graph.iosStoreApp",
                "displayName": "Private app name",
                "bundleId": "com.example.synthetic",
            }
        ],
        paths["app-configurations"]: [
            {
                "id": app_config_id,
                "@odata.type": "#microsoft.graph.iosMobileAppConfiguration",
            }
        ],
        paths["app-protection-policies"]: [],
        paths["enrollment-configurations"]: [
            {
                "id": "enrollment",
                "@odata.type": "#microsoft.graph.deviceEnrollmentLimitConfiguration",
            }
        ],
        paths["device-categories"]: [
            {"id": "category", "@odata.type": "#microsoft.graph.deviceCategory"}
        ],
        paths["ade-tokens"]: [
            {
                "id": "ade-token",
                "@odata.type": "#microsoft.graph.depOnboardingSetting",
                "tokenState": "active",
                "lastSyncDateTime": "2026-07-19T14:00:00Z",
            }
        ],
        paths["vpp-tokens"]: [
            {
                "id": "vpp-token",
                "@odata.type": "#microsoft.graph.vppToken",
                "state": "valid",
            }
        ],
        f"/v1.0/deviceManagement/deviceConfigurations/{config_id}/assignments": [
            {
                "id": "config-assignment",
                "target": {"@odata.type": "#microsoft.graph.allDevicesAssignmentTarget"},
            }
        ],
        f"/beta/deviceManagement/configurationPolicies/{settings_id}/settings": [
            {
                "id": "setting",
                "settingInstance": {
                    "settingDefinitionId": "com.apple.mcx.filevault2_enable",
                    "choiceSettingValue": {"value": 0},
                },
            }
        ],
        f"/beta/deviceManagement/configurationPolicies/{settings_id}/assignments": [
            {
                "id": "settings-assignment",
                "intent": "required",
                "target": {
                    "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                    "groupId": "private-group-source-id",
                    "deviceAndAppManagementAssignmentFilterType": "none",
                },
            }
        ],
        f"/v1.0/deviceManagement/deviceCompliancePolicies/{compliance_id}/assignments": [],
        (
            f"/v1.0/deviceManagement/deviceCompliancePolicies/{compliance_id}"
            "/scheduledActionsForRule"
        ): [{"id": "action", "ruleName": "passwordRequired", "scheduledActionConfigurations": []}],
        f"/v1.0/deviceAppManagement/mobileApps/{app_id}/assignments": [],
        f"/v1.0/deviceAppManagement/mobileAppConfigurations/{app_config_id}/assignments": [],
    }
    reader = FakeReader(
        collections=collections,
        objects={
            paths["apns-certificate"]: {
                "@odata.type": "#microsoft.graph.applePushNotificationCertificate",
                "expirationDateTime": "2027-07-19T00:00:00Z",
            }
        },
    )
    return reader, paths


def test_comprehensive_provider_collects_every_family_and_normalizes_joins() -> None:
    reader, paths = _catalog()
    result = AppleIntuneProvider(reader, max_concurrency=2, now=lambda: NOW).collect()
    assert result.schema_version == "2.0.0"
    assert result.collected_at_utc == "2026-07-19T15:00:00Z"
    assert result.raw_response_persisted is False
    assert {item["key"] for item in result.endpoint_statuses}.issuperset(paths)
    assert len(reader.calls) > len(ENDPOINTS)
    assert all(path.startswith(("/v1.0/", "/beta/")) for path in reader.calls)
    families = {record["resource_family"] for record in result.records}
    assert {
        "managed_devices",
        "configuration_profiles",
        "settings_catalog",
        "settings_catalog_settings",
        "settings_catalog_assignments",
        "compliance_policies_scheduled_actions",
        "applications",
        "apple_push_notification_service",
    }.issubset(families)
    settings = next(
        item for item in result.records if item["resource_family"] == "settings_catalog_settings"
    )
    setting_properties = cast(dict[str, JsonValue], settings["properties"])
    assert setting_properties["setting_definition_id"] == "com.apple.mcx.filevault2_enable"
    assert setting_properties["normalized_value"] == 0
    assert setting_properties["normalization_state"] == "normalized"
    assignment = next(
        item for item in result.records if item["resource_family"] == "settings_catalog_assignments"
    )
    assignment_properties = cast(dict[str, JsonValue], assignment["properties"])
    assert assignment_properties["private_target_id"] == "private-group-source-id"
    summary = summarize_devices(result.records)
    assert summary["total"] == 1
    assert summary["by_platform"] == {"iPadOS": 1}
    assert not any(
        gap["source_endpoint_key"] == "settings-catalog"
        and gap["reason"] == "unsupported_resource_type"
        for gap in result.collection_gaps
    )


def test_missing_odata_type_uses_public_safe_unknown_taxonomy() -> None:
    reader, paths = _catalog()
    reader.objects[paths["apns-certificate"]].pop("@odata.type")

    collection = AppleIntuneProvider(reader, max_concurrency=1, now=lambda: NOW).collect()
    apns = next(
        item
        for item in collection.records
        if item["resource_family"] == "apple_push_notification_service"
    )
    assert cast(dict[str, JsonValue], apns["properties"])["odata_type"] == "unknown"

    public = build_public_mission_snapshot(
        collection,
        pseudonym_key=b"public-safe-test-pseudonym-key!!",
        synthetic=False,
        source_git_commit="a" * 40,
    )
    resources = cast(list[dict[str, JsonValue]], public["resources"])
    public_apns = next(
        item for item in resources if item["resource_family"] == "apple_push_notification_service"
    )
    assert public_apns["resource_type"] == "unknown"


def test_partial_graph_and_schema_failures_become_collection_gaps() -> None:
    reader, paths = _catalog()
    reader.failures[paths["app-protection-policies"]] = GraphProviderError(
        GraphErrorCategory.AUTHORIZATION,
        endpoint="/v1.0/deviceAppManagement/managedAppPolicies",
        status_code=403,
    )
    reader.collections[paths["managed-devices"]].append({"id": "bad-device", "operatingSystem": 7})
    result = AppleIntuneProvider(reader, max_concurrency=1, now=lambda: NOW).collect()
    assert {gap["reason"] for gap in result.collection_gaps}.issuperset(
        {"authorization", "record_schema_change"}
    )
    status = next(
        item for item in result.endpoint_statuses if item["key"] == "app-protection-policies"
    )
    assert status["status"] == "unavailable"


def test_provider_bounds_permissions_and_has_get_only_surface() -> None:
    with pytest.raises(ValueError, match="between 1 and 4"):
        AppleIntuneProvider(FakeReader(), max_concurrency=5)
    assert_get_only_provider()
    assert set(endpoint_permissions()) == {
        "DeviceManagementApps.Read.All",
        "DeviceManagementConfiguration.Read.All",
        "DeviceManagementManagedDevices.Read.All",
        "DeviceManagementServiceConfig.Read.All",
    }
    assert {name for name in dir(apple_module.GraphReader) if not name.startswith("_")} == {
        "get_collection",
        "get_object",
    }
    source = inspect.getsource(apple_module)
    for verb in ("POST", "PATCH", "PUT", "DELETE"):
        assert f'"{verb}"' not in source


@pytest.mark.parametrize(
    "item",
    [
        {"id": "bad", "operatingSystem": "iOS", "isEncrypted": "yes"},
        {"id": "bad", "operatingSystem": "iOS", "lastSyncDateTime": "invalid"},
    ],
)
def test_changed_managed_device_field_shapes_fail_record_closed(
    item: dict[str, JsonValue],
) -> None:
    paths = {spec.key: spec.path for spec in ENDPOINTS}
    reader = FakeReader(collections={paths["managed-devices"]: [item]})
    result = AppleIntuneProvider(reader, max_concurrency=1, now=lambda: NOW).collect()
    assert any(gap["reason"] == "record_schema_change" for gap in result.collection_gaps)


def test_normalizer_rejects_unsafe_enums_types_and_times() -> None:
    assert apple_module._safe_odata_type("microsoft.graph.unknown") == "unknown"
    with pytest.raises(ValueError, match="unsafe enumerated"):
        apple_module._safe_enum("contains spaces")
    with pytest.raises(ValueError, match="unsafe OData"):
        apple_module._safe_odata_type("bad/type")
    with pytest.raises(ValueError, match="unsafe setting"):
        apple_module._safe_setting_value("unsafe@example.invalid")
    with pytest.raises(TypeError, match="non-empty string"):
        apple_module._required_string({}, "id")
    with pytest.raises(TypeError, match="string when present"):
        apple_module._optional_string({"id": 4}, "id")
    with pytest.raises(TypeError, match="boolean"):
        apple_module._optional_bool({"enabled": "true"}, "enabled")
    with pytest.raises(ValueError, match="UTC offset"):
        apple_module._graph_time("2026-07-19T12:00:00")
    with pytest.raises(ValueError, match="invalid Graph timestamp"):
        apple_module._graph_time("invalid")
    with pytest.raises(ValueError, match="timezone-aware"):
        apple_module._utc(datetime(2026, 7, 19, 12, 0))  # noqa: DTZ001


def test_setting_shapes_and_platform_helpers_are_explicit() -> None:
    assert apple_module._extract_setting(
        {
            "settingInstance": {
                "settingDefinitionId": "setting-id",
                "choiceSettingValue": {"value": "enabled"},
            }
        }
    ) == ("setting-id", "enabled", "normalized")
    assert apple_module._extract_setting(
        {"settingInstance": {"settingDefinitionId": "setting-id", "children": [1, 2]}}
    ) == ("setting-id", None, "unsupported_value_shape")
    with pytest.raises(TypeError, match="settingInstance"):
        apple_module._extract_setting({})
    assert apple_module._extract_setting(
        {
            "settingInstance": {
                "settingDefinitionId": "setting-id",
                "simpleSettingValue": {"value": {"unexpected": True}},
            }
        }
    ) == ("setting-id", None, "unsupported_value_shape")
    with pytest.raises(ValueError, match="definition ID"):
        apple_module._extract_setting(
            {
                "settingInstance": {
                    "settingDefinitionId": "unsafe@example.invalid",
                    "simpleSettingValue": {"value": True},
                }
            }
        )
    assert apple_module._device_platform("macOS", None) == "macOS"
    assert apple_module._device_platform("unknown", None) == "other"
    assert apple_module._model_family("Mac Studio") == "mac-studio"
    assert apple_module._model_family("Vision Pro") == "other-apple"
    assert apple_module._model_family(None) == "unknown"


def test_grouped_filevault_setting_children_are_flattened_with_exact_values() -> None:
    paths = {spec.key: spec.path for spec in ENDPOINTS}
    policy_id = "synthetic-grouped-filevault-policy"
    reader = FakeReader(
        collections={
            paths["settings-catalog"]: [
                {
                    "id": policy_id,
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationPolicy",
                    "platforms": "macOS",
                }
            ],
            f"/beta/deviceManagement/configurationPolicies/{policy_id}/settings": [
                {
                    "id": "synthetic-grouped-setting",
                    "settingInstance": {
                        "@odata.type": (
                            "#microsoft.graph."
                            "deviceManagementConfigurationGroupSettingCollectionInstance"
                        ),
                        "settingDefinitionId": (
                            "com.apple.mcx.filevault2_com.apple.mcx.filevault2"
                        ),
                        "groupSettingCollectionValue": [
                            {
                                "children": [
                                    {
                                        "@odata.type": (
                                            "#microsoft.graph."
                                            "deviceManagementConfigurationChoiceSettingInstance"
                                        ),
                                        "settingDefinitionId": ("com.apple.mcx.filevault2_enable"),
                                        "choiceSettingValue": {
                                            "value": "com.apple.mcx.filevault2_enable_0"
                                        },
                                    },
                                    {
                                        "@odata.type": (
                                            "#microsoft.graph."
                                            "deviceManagementConfigurationChoiceSettingInstance"
                                        ),
                                        "settingDefinitionId": ("com.apple.mcx.filevault2_defer"),
                                        "choiceSettingValue": {
                                            "value": "com.apple.mcx.filevault2_defer_true"
                                        },
                                    },
                                ]
                            }
                        ],
                    },
                }
            ],
            f"/beta/deviceManagement/configurationPolicies/{policy_id}/assignments": [],
        }
    )

    result = AppleIntuneProvider(reader, max_concurrency=1, now=lambda: NOW).collect()
    settings = [
        cast(dict[str, JsonValue], record["properties"])
        for record in result.records
        if record["resource_family"] == "settings_catalog_settings"
    ]
    assert {item["setting_definition_id"] for item in settings} == {
        "com.apple.mcx.filevault2_enable",
        "com.apple.mcx.filevault2_defer",
    }
    filevault = next(
        item
        for item in settings
        if item["setting_definition_id"] == "com.apple.mcx.filevault2_enable"
    )
    assert filevault["normalized_value"] == "com.apple.mcx.filevault2_enable_0"
    assert filevault["normalization_state"] == "normalized"
    assert not result.collection_gaps


def test_unknown_nested_setting_shape_remains_fail_closed() -> None:
    flattened = apple_module._flatten_setting_items(
        {
            "id": "synthetic-unknown-setting",
            "settingInstance": {
                "settingDefinitionId": "com.apple.synthetic.unknown-container",
                "futureValueShape": {"value": True},
            },
        }
    )
    assert len(flattened) == 1
    assert apple_module._extract_setting(flattened[0]) == (
        "com.apple.synthetic.unknown-container",
        None,
        "unsupported_value_shape",
    )


def test_known_non_apple_settings_policy_is_filtered_without_collection_gap() -> None:
    paths = {spec.key: spec.path for spec in ENDPOINTS}
    reader = FakeReader(
        collections={
            paths["settings-catalog"]: [
                {
                    "id": "synthetic-windows-policy",
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationPolicy",
                    "platforms": "windows10",
                }
            ]
        }
    )
    result = AppleIntuneProvider(reader, max_concurrency=1, now=lambda: NOW).collect()
    assert not any(record["resource_family"] == "settings_catalog" for record in result.records)
    assert not any(
        gap["source_endpoint_key"] == "settings-catalog" for gap in result.collection_gaps
    )
