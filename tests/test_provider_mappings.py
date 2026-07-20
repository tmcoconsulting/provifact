from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from evidenceops.baselines import (
    INTUNE_PROVIDER_MAPPINGS,
    MappingReviewStatus,
    UnsupportedProviderValueError,
    matching_alias,
    normalize_provider_definition_id,
    normalize_provider_value,
    validate_provider_mapping_registry,
)
from evidenceops.domain import JsonValue
from evidenceops.providers import apple as apple_module
from evidenceops.providers.apple import ENDPOINTS

FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "synthetic"
    / "intune-settings-catalog.real-shaped.json"
)


def _fixture() -> dict[str, JsonValue]:
    return cast(dict[str, JsonValue], json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_registry_contains_only_exact_reviewed_provider_aliases() -> None:
    validate_provider_mapping_registry()
    filevault = INTUNE_PROVIDER_MAPPINGS["system_settings_filevault_enforce"]
    assert filevault.review_status is MappingReviewStatus.REVIEWED
    alias = matching_alias(filevault, "COM.APPLE.MCX.FILEVAULT2_ENABLE")
    assert alias is not None
    assert normalize_provider_value(alias, 0) is True
    assert normalize_provider_value(alias, "com.apple.mcx.filevault2_enable_0") is True
    assert matching_alias(filevault, "prefix.com.apple.mcx.filevault2_enable") is None
    assert matching_alias(filevault, "com.apple.mcx.filevault2_enable.suffix") is None
    with pytest.raises(UnsupportedProviderValueError, match="unreviewed"):
        normalize_provider_value(alias, 1)
    with pytest.raises(UnsupportedProviderValueError, match="unreviewed"):
        normalize_provider_value(alias, "com.apple.mcx.filevault2_enable_1")

    stealth = INTUNE_PROVIDER_MAPPINGS["system_settings_firewall_stealth_mode_enable"]
    assert stealth.review_status is MappingReviewStatus.NOT_REVIEWED
    assert stealth.aliases == ()


@pytest.mark.parametrize(
    "value",
    [" com.apple.setting", "com.apple.setting ", "unsafe@example.invalid", "é.setting"],
)
def test_provider_identifier_normalization_rejects_unsafe_or_inexact_values(value: str) -> None:
    with pytest.raises(ValueError, match="provider setting"):
        normalize_provider_definition_id(value)


def test_real_shaped_fixture_uses_graph_shapes_and_not_semantic_keys() -> None:
    fixture = _fixture()
    assert fixture["fixture_notice"] == "SYNTHETIC_TEST_DATA_ONLY"
    policies = cast(list[dict[str, JsonValue]], fixture["policies"])
    definitions: set[str] = set()
    settings_spec = next(spec for spec in ENDPOINTS if spec.key == "settings-catalog")
    for entry in policies:
        policy = apple_module._normalize_item(
            settings_spec,
            cast(dict[str, JsonValue], entry["policy"]),
            "2026-07-20T00:00:00Z",
        )
        assert policy is not None
        for setting in cast(list[dict[str, JsonValue]], entry["settings"]):
            record = apple_module._normalize_expansion(
                policy, "settings", setting, "2026-07-20T00:00:00Z"
            )
            properties = cast(dict[str, JsonValue], record["properties"])
            definitions.add(cast(str, properties["setting_definition_id"]))
            assert properties["normalization_state"] == "normalized"
    assert "macos.security.filevault.enabled" not in definitions
    assert "com.apple.mcx.filevault2_enable" in definitions
    assert "com.apple.security.firewall_EnableFirewall" in definitions
    assert "com.apple.screensaver_askForPassword" in definitions
    assert "com.apple.screensaver.user_idleTime" in definitions


def test_unknown_provider_definition_does_not_match_display_name_or_substring() -> None:
    fixture = _fixture()
    firewall_entry = cast(list[dict[str, JsonValue]], fixture["policies"])[1]
    policy = cast(dict[str, JsonValue], firewall_entry["policy"])
    # A tenant-controlled display name that happens to contain the semantic key
    # must have no influence on the exact provider join.
    policy["displayName"] = "Synthetic macos.security.firewall.enabled"
    mapping = INTUNE_PROVIDER_MAPPINGS["system_settings_firewall_enable"]
    assert matching_alias(mapping, "custom.firewall.enabled") is None
