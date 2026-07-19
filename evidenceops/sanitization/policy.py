"""Explicit field classification and deterministic pseudonymization.

The sanitizer is deliberately strict: every mapping key must be classified. New provider
fields therefore stop publication until a human decides whether to allow, drop, or
pseudonymize them.
"""

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from evidenceops.domain import JsonValue
from evidenceops.sanitization.credentials import CREDENTIAL_PATTERNS


class SanitizationError(ValueError):
    """Base class for publication-blocking sanitization errors."""


class UnknownFieldError(SanitizationError):
    """Raised when an input field has not been explicitly classified."""


class SensitiveValueError(SanitizationError):
    """Raised when a prohibited value survives field transformation."""


class FieldAction(StrEnum):
    """Allowed transformations for a classified input field."""

    ALLOW = "allow"
    DROP = "drop"
    PSEUDONYMIZE = "pseudonymize"


@dataclass(frozen=True, slots=True)
class SanitizationPolicy:
    """A complete field-action map and pseudonym namespace map."""

    version: str
    actions: dict[str, FieldAction]
    pseudonym_prefixes: dict[str, str]


DEFAULT_POLICY_MANIFEST: Final = Path(__file__).with_name("publication-policy.v1.json")

_PUBLIC_VALUE_CATALOG: Final = Path(__file__).with_name("public-value-patterns.v1.json")


def _load_public_value_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    try:
        loaded = json.loads(_PUBLIC_VALUE_CATALOG.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("public value pattern catalog could not be loaded") from exc
    if not isinstance(loaded, dict) or set(loaded) != {"catalog_version", "patterns"}:
        raise RuntimeError("public value pattern catalog has unexpected or missing fields")
    patterns = loaded.get("patterns")
    if not isinstance(loaded.get("catalog_version"), str) or not isinstance(patterns, list):
        raise RuntimeError("public value pattern catalog metadata is invalid")
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for entry in patterns:
        if not isinstance(entry, dict) or set(entry) != {"label", "expression", "flags"}:
            raise RuntimeError("public value pattern entry has unexpected or missing fields")
        label = entry.get("label")
        expression = entry.get("expression")
        flags = entry.get("flags")
        if (
            not isinstance(label, str)
            or not label
            or not isinstance(expression, str)
            or not expression
            or flags not in {"", "i"}
        ):
            raise RuntimeError("public value pattern entry is invalid")
        compiled.append((label, re.compile(expression, re.IGNORECASE if flags == "i" else 0)))
    if not compiled:
        raise RuntimeError("public value pattern catalog must not be empty")
    return tuple(compiled)


_PROHIBITED_PUBLIC_VALUE_PATTERNS: Final = _load_public_value_patterns()

# These exact strings are public vendor permission identifiers or approved
# EvidenceOps taxonomy keys, not network domains. Exact membership prevents the
# domain detector from being weakened for arbitrary dotted strings.
_PUBLIC_SAFE_TECHNICAL_VALUES: Final = frozenset(
    {
        "DeviceManagementApps.Read.All",
        "DeviceManagementConfiguration.Read.All",
        "DeviceManagementManagedDevices.Read.All",
        "DeviceManagementServiceConfig.Read.All",
        "macos.screen_lock.max_idle_seconds",
        "macos.screen_lock.require_password",
        "macos.security.filevault.enabled",
        "macos.security.firewall.enabled",
        "macos.security.firewall.stealth_mode",
    }
)


def load_policy_manifest(path: Path = DEFAULT_POLICY_MANIFEST) -> SanitizationPolicy:
    """Load an explicit field-classification manifest or stop publication."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SanitizationError("publication policy manifest could not be loaded") from exc
    if not isinstance(loaded, dict) or set(loaded) != {
        "policy_version",
        "fields",
        "pseudonym_prefixes",
    }:
        raise SanitizationError("publication policy manifest has unexpected or missing fields")
    version = loaded.get("policy_version")
    fields = loaded.get("fields")
    prefixes = loaded.get("pseudonym_prefixes")
    if not isinstance(version, str) or not version:
        raise SanitizationError("publication policy version is invalid")
    if not isinstance(fields, dict) or not all(
        isinstance(field, str) and isinstance(action, str) for field, action in fields.items()
    ):
        raise SanitizationError("publication field classifications are invalid")
    if not isinstance(prefixes, dict) or not all(
        isinstance(field, str) and isinstance(prefix, str) and prefix
        for field, prefix in prefixes.items()
    ):
        raise SanitizationError("publication pseudonym prefixes are invalid")
    try:
        actions = {field: FieldAction(action) for field, action in fields.items()}
    except ValueError as exc:
        raise SanitizationError("publication field action is invalid") from exc
    pseudonymized = {
        field for field, action in actions.items() if action is FieldAction.PSEUDONYMIZE
    }
    if pseudonymized != set(prefixes):
        raise SanitizationError("every pseudonymized field requires exactly one prefix")
    return SanitizationPolicy(
        version=version,
        actions=actions,
        pseudonym_prefixes={field: str(prefix) for field, prefix in prefixes.items()},
    )


DEFAULT_PUBLIC_POLICY: Final = load_policy_manifest()


def sanitize_document(
    document: dict[str, JsonValue],
    *,
    pseudonym_key: bytes,
    policy: SanitizationPolicy = DEFAULT_PUBLIC_POLICY,
) -> dict[str, JsonValue]:
    """Return a public-safe copy or raise before producing an artifact.

    The caller supplies pseudonym key material at runtime. A key shorter than 32 bytes is
    rejected, and EvidenceOps never persists it.
    """
    if len(pseudonym_key) < 32:
        raise SanitizationError("pseudonym_key must contain at least 32 bytes")
    sanitized = _sanitize_mapping(document, policy=policy, pseudonym_key=pseudonym_key)
    assert_public_safe(sanitized)
    return sanitized


def _sanitize_mapping(
    value: dict[str, JsonValue],
    *,
    policy: SanitizationPolicy,
    pseudonym_key: bytes,
) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for field, item in value.items():
        try:
            action = policy.actions[field]
        except KeyError as exc:
            raise UnknownFieldError(f"unclassified field: {field}") from exc

        if action is FieldAction.DROP:
            _validate_nested_classifications(item, policy=policy)
            continue
        if action is FieldAction.PSEUDONYMIZE:
            if not isinstance(item, str) or not item:
                raise SanitizationError(f"field {field} requires a non-empty string")
            prefix = policy.pseudonym_prefixes[field]
            result[field] = _pseudonymize(prefix, item, pseudonym_key)
            continue
        result[field] = _sanitize_allowed_value(
            item,
            policy=policy,
            pseudonym_key=pseudonym_key,
        )
    return result


def _validate_nested_classifications(value: JsonValue, *, policy: SanitizationPolicy) -> None:
    """A dropped parent does not allow unknown nested fields to bypass classification."""
    if isinstance(value, dict):
        for field, item in value.items():
            if field not in policy.actions:
                raise UnknownFieldError(f"unclassified field: {field}")
            _validate_nested_classifications(item, policy=policy)
    elif isinstance(value, list):
        for item in value:
            _validate_nested_classifications(item, policy=policy)


def _sanitize_allowed_value(
    value: JsonValue,
    *,
    policy: SanitizationPolicy,
    pseudonym_key: bytes,
) -> JsonValue:
    if isinstance(value, dict):
        return _sanitize_mapping(value, policy=policy, pseudonym_key=pseudonym_key)
    if isinstance(value, list):
        return [
            _sanitize_allowed_value(item, policy=policy, pseudonym_key=pseudonym_key)
            for item in value
        ]
    return value


def _pseudonymize(prefix: str, value: str, key: bytes) -> str:
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
    return f"{prefix}-{digest}"


def assert_public_safe(value: JsonValue) -> None:
    """Reject sensitive public or external-egress values without transforming input."""
    if isinstance(value, dict):
        for item in value.values():
            assert_public_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_public_safe(item)
        return
    if not isinstance(value, str):
        return
    if value in _PUBLIC_SAFE_TECHNICAL_VALUES:
        return
    for label, pattern in (*CREDENTIAL_PATTERNS, *_PROHIBITED_PUBLIC_VALUE_PATTERNS):
        if pattern.search(value):
            raise SensitiveValueError(f"prohibited {label} survived sanitization")
