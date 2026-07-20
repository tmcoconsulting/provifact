"""Reviewed Microsoft Intune mappings for the pinned macOS demo baseline.

The registry is deliberately separate from the baseline desired state.  A baseline
rule is not evaluable merely because it has an expected value: at least one exact
provider identifier must also have been reviewed.  Identifiers are normalized only
for case; display names and substrings are never part of a match.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from evidenceops.domain import JsonValue

PROVIDER_MAPPING_REGISTRY_VERSION: Final = "microsoft-intune-macos-v1.1.0"
PROVIDER_MAPPING_REVIEW_SOURCE: Final = (
    "https://github.com/microsoft/intune-my-macs/blob/main/INTUNE-MY-MACS-DOCUMENTATION.md"
)


class MappingReviewStatus(StrEnum):
    """Closed review states; only REVIEWED mappings may drive a finding."""

    REVIEWED = "reviewed"
    NOT_REVIEWED = "not reviewed"


class ValueTransform(StrEnum):
    """Closed deterministic transforms for provider values."""

    IDENTITY = "identity"
    FILEVAULT_ENABLE_CHOICE = "filevault enable choice"


class AssignmentRequirement(StrEnum):
    """Assignment evidence required by a reviewed mapping."""

    AT_LEAST_ONE = "at least one assignment"
    NOT_REQUIRED = "assignment not required"


class UnsupportedProviderValueError(ValueError):
    """The provider identifier is known but its value cannot be evaluated safely."""


@dataclass(frozen=True, slots=True)
class ProviderAlias:
    """One exact provider definition ID and its deterministic value transform."""

    definition_id: str
    transform: ValueTransform = ValueTransform.IDENTITY


@dataclass(frozen=True, slots=True)
class ProviderRuleMapping:
    """Reviewed join from one baseline rule to an Intune resource vocabulary."""

    rule_id: str
    setting_key: str
    resource_family: str
    aliases: tuple[ProviderAlias, ...]
    expected_value: JsonValue
    assignment_requirement: AssignmentRequirement
    review_status: MappingReviewStatus
    review_source: str


# The four reviewed identifiers below are exported by Microsoft's public Intune
# macOS reference implementation.  Stealth mode remains explicitly unreviewed:
# Microsoft documents the setting in the product UI, but the exact Graph
# settingDefinitionId has not been independently established for this project.
_MAPPINGS: Final = {
    "system_settings_filevault_enforce": ProviderRuleMapping(
        rule_id="system_settings_filevault_enforce",
        setting_key="macos.security.filevault.enabled",
        resource_family="settings_catalog_settings",
        aliases=(
            ProviderAlias(
                "com.apple.mcx.filevault2_enable",
                ValueTransform.FILEVAULT_ENABLE_CHOICE,
            ),
        ),
        expected_value=True,
        assignment_requirement=AssignmentRequirement.AT_LEAST_ONE,
        review_status=MappingReviewStatus.REVIEWED,
        review_source=PROVIDER_MAPPING_REVIEW_SOURCE,
    ),
    "system_settings_firewall_enable": ProviderRuleMapping(
        rule_id="system_settings_firewall_enable",
        setting_key="macos.security.firewall.enabled",
        resource_family="settings_catalog_settings",
        aliases=(ProviderAlias("com.apple.security.firewall_EnableFirewall"),),
        expected_value=True,
        assignment_requirement=AssignmentRequirement.AT_LEAST_ONE,
        review_status=MappingReviewStatus.REVIEWED,
        review_source=PROVIDER_MAPPING_REVIEW_SOURCE,
    ),
    "system_settings_firewall_stealth_mode_enable": ProviderRuleMapping(
        rule_id="system_settings_firewall_stealth_mode_enable",
        setting_key="macos.security.firewall.stealth_mode",
        resource_family="settings_catalog_settings",
        aliases=(),
        expected_value=True,
        assignment_requirement=AssignmentRequirement.AT_LEAST_ONE,
        review_status=MappingReviewStatus.NOT_REVIEWED,
        review_source=PROVIDER_MAPPING_REVIEW_SOURCE,
    ),
    "system_settings_screensaver_password_enforce": ProviderRuleMapping(
        rule_id="system_settings_screensaver_password_enforce",
        setting_key="macos.screen_lock.require_password",
        resource_family="settings_catalog_settings",
        aliases=(ProviderAlias("com.apple.screensaver_askForPassword"),),
        expected_value=True,
        assignment_requirement=AssignmentRequirement.AT_LEAST_ONE,
        review_status=MappingReviewStatus.REVIEWED,
        review_source=PROVIDER_MAPPING_REVIEW_SOURCE,
    ),
    "system_settings_screensaver_timeout_enforce": ProviderRuleMapping(
        rule_id="system_settings_screensaver_timeout_enforce",
        setting_key="macos.screen_lock.max_idle_seconds",
        resource_family="settings_catalog_settings",
        aliases=(ProviderAlias("com.apple.screensaver.user_idleTime"),),
        expected_value=900,
        assignment_requirement=AssignmentRequirement.AT_LEAST_ONE,
        review_status=MappingReviewStatus.REVIEWED,
        review_source=PROVIDER_MAPPING_REVIEW_SOURCE,
    ),
}

INTUNE_PROVIDER_MAPPINGS: Final = MappingProxyType(_MAPPINGS)


def normalize_provider_definition_id(value: str) -> str:
    """Normalize a provider taxonomy identifier without weakening exact matching."""
    if (
        not value
        or value != value.strip()
        or len(value) > 240
        or not value.isascii()
        or not all(character.isalnum() or character in "._:-/" for character in value)
    ):
        raise ValueError("invalid provider setting definition ID")
    return value.casefold()


def matching_alias(mapping: ProviderRuleMapping, definition_id: str) -> ProviderAlias | None:
    """Return the exact normalized alias, never a display-name or substring match."""
    normalized = normalize_provider_definition_id(definition_id)
    for alias in mapping.aliases:
        if normalized == normalize_provider_definition_id(alias.definition_id):
            return alias
    return None


def normalize_provider_value(alias: ProviderAlias, value: JsonValue) -> JsonValue:
    """Apply one reviewed, closed provider-value transform."""
    if alias.transform is ValueTransform.IDENTITY:
        if isinstance(value, (str, bool, int, float)) or value is None:
            return value
        raise UnsupportedProviderValueError("identity mapping received an unsupported value shape")
    if alias.transform is ValueTransform.FILEVAULT_ENABLE_CHOICE:
        # Microsoft's published Intune macOS reference export represents the
        # Settings Catalog FileVault `Enable` choice as the exact provider token
        # below.  Older normalized fixtures used numeric zero for the same closed
        # choice.  No other value is interpreted until it is explicitly reviewed.
        if (type(value) is int and value == 0) or (value == "com.apple.mcx.filevault2_enable_0"):
            return True
        raise UnsupportedProviderValueError("unreviewed FileVault enable choice value")
    raise UnsupportedProviderValueError("unknown provider value transform")


def reviewed_provider_definition_ids() -> frozenset[str]:
    """Return the exact normalized identifier allowlist used by publication."""
    return frozenset(
        normalize_provider_definition_id(alias.definition_id)
        for mapping in INTUNE_PROVIDER_MAPPINGS.values()
        if mapping.review_status is MappingReviewStatus.REVIEWED
        for alias in mapping.aliases
    )


def validate_provider_mapping_registry() -> None:
    """Fail closed if aliases overlap or a reviewed mapping is incomplete."""
    seen: dict[str, str] = {}
    for rule_id, mapping in INTUNE_PROVIDER_MAPPINGS.items():
        if mapping.rule_id != rule_id:
            raise ValueError("provider mapping registry key does not match rule ID")
        if mapping.review_status is MappingReviewStatus.REVIEWED and not mapping.aliases:
            raise ValueError("reviewed provider mapping must contain an exact alias")
        for alias in mapping.aliases:
            normalized = normalize_provider_definition_id(alias.definition_id)
            other = seen.setdefault(normalized, rule_id)
            if other != rule_id:
                raise ValueError("provider definition alias maps to more than one rule")


validate_provider_mapping_registry()
