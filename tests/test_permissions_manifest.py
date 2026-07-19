from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from evidenceops.domain import JsonValue
from evidenceops.providers import ENDPOINTS, endpoint_permissions

ROOT = Path(__file__).parents[1]


def test_permission_manifest_is_exactly_read_only_and_matches_provider() -> None:
    manifest = cast(
        dict[str, JsonValue],
        json.loads(
            (ROOT / "manifests/microsoft-graph-permissions.v1.json").read_text(encoding="utf-8")
        ),
    )
    assert manifest["source_api_versions"] == ["v1.0", "beta"]
    assert cast(list[dict[str, JsonValue]], manifest["beta_dependencies"]) == [
        {
            "resource_family": "settings_catalog",
            "path": "/deviceManagement/configurationPolicies",
            "reason": (
                "The Intune Settings Catalog configurationPolicy resource is documented only "
                "on Microsoft Graph beta at the pinned implementation date. The adapter "
                "isolates and attributes this schema explicitly."
            ),
        }
    ]
    profiles = cast(dict[str, JsonValue], manifest["profiles"])
    expected_ids = {
        "local_attended": {
            "DeviceManagementApps.Read.All": "4edf5f54-4666-44af-9de9-0144fb4b6e8c",
            "DeviceManagementConfiguration.Read.All": "f1493658-876a-4c87-8fa7-edb559b3476a",
            "DeviceManagementManagedDevices.Read.All": "314874da-47d6-4978-88dc-cf0d37f0bb82",
            "DeviceManagementServiceConfig.Read.All": "8696daa5-bce5-4b2e-83f9-51b6defc4e1e",
        },
        "private_automation": {
            "DeviceManagementApps.Read.All": "7a6ee1e7-141e-4cec-ae74-d9db155731ff",
            "DeviceManagementConfiguration.Read.All": "dc377aa6-52d8-4e23-b271-2a7ae04cedf3",
            "DeviceManagementManagedDevices.Read.All": "2f51be20-0bb4-4fed-bf7b-db946066c75e",
            "DeviceManagementServiceConfig.Read.All": "06a5fe6d-c49d-46a7-b082-56b1b14103c7",
        },
    }
    for profile_name, permission_ids in expected_ids.items():
        profile = cast(dict[str, JsonValue], profiles[profile_name])
        permissions = cast(list[dict[str, JsonValue]], profile["permissions"])
        assert {
            cast(str, permission["name"]): cast(str, permission["permission_id"])
            for permission in permissions
        } == permission_ids
        assert all(permission["admin_consent_required"] is True for permission in permissions)
    endpoints = cast(list[dict[str, JsonValue]], manifest["endpoints"])
    assert {endpoint["method"] for endpoint in endpoints} == {"GET"}
    assert {cast(str, endpoint["permission"]) for endpoint in endpoints} == set(
        endpoint_permissions()
    )
    for spec in ENDPOINTS:
        documented = [
            endpoint
            for endpoint in endpoints
            if spec.key in cast(list[str], endpoint["provider_keys"])
        ]
        assert documented
        assert {endpoint["api_version"] for endpoint in documented} == {spec.api_version}
        assert {endpoint["permission"] for endpoint in documented} == {spec.permission}
        assert any(
            spec.path.removeprefix(f"/{spec.api_version}")
            .split("?", maxsplit=1)[0]
            .startswith(cast(str, endpoint["path"]).split("{", maxsplit=1)[0])
            for endpoint in documented
        )
    active_contract = json.dumps({"profiles": profiles, "endpoints": endpoints})
    assert "ReadWrite" not in active_contract
    assert '"method": "POST"' not in active_contract


def test_configuration_template_contains_names_only() -> None:
    lines = [
        line
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert lines
    assert all(line.endswith("=") and line.count("=") == 1 for line in lines)
