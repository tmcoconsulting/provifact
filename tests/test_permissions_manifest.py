from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from evidenceops.domain import JsonValue
from evidenceops.providers.intune import DEVICE_CONFIGURATIONS_PATH, SOURCE_API_VERSION

ROOT = Path(__file__).parents[1]


def test_permission_manifest_is_exactly_read_only_and_matches_provider() -> None:
    manifest = cast(
        dict[str, JsonValue],
        json.loads(
            (ROOT / "manifests/microsoft-graph-permissions.v1.json").read_text(encoding="utf-8")
        ),
    )
    assert manifest["source_api_version"] == SOURCE_API_VERSION
    profiles = cast(dict[str, JsonValue], manifest["profiles"])
    expected_ids = {
        "local_attended": "f1493658-876a-4c87-8fa7-edb559b3476a",
        "private_automation": "dc377aa6-52d8-4e23-b271-2a7ae04cedf3",
    }
    for profile_name, permission_id in expected_ids.items():
        profile = cast(dict[str, JsonValue], profiles[profile_name])
        permissions = cast(list[dict[str, JsonValue]], profile["permissions"])
        assert permissions == [
            {
                "name": "DeviceManagementConfiguration.Read.All",
                "permission_id": permission_id,
                "admin_consent_required": True,
            }
        ]
    endpoints = cast(list[dict[str, JsonValue]], manifest["endpoints"])
    assert {endpoint["method"] for endpoint in endpoints} == {"GET"}
    assert endpoints[0]["path"] == DEVICE_CONFIGURATIONS_PATH.removeprefix("/v1.0")
    assert all(
        endpoint["permission"] == "DeviceManagementConfiguration.Read.All" for endpoint in endpoints
    )


def test_configuration_template_contains_names_only() -> None:
    lines = [
        line
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert lines
    assert all(line.endswith("=") and line.count("=") == 1 for line in lines)
