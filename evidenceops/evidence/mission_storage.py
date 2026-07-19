"""Restrictive storage boundary for normalized Apple mission collections."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Final, cast

from evidenceops.domain import JsonValue
from evidenceops.providers.apple import AppleIntuneCollection

PRIVATE_COLLECTION_TYPE: Final = "evidenceops_private_apple_collection"
_PRIVATE_TOP_LEVEL: Final = frozenset(
    {
        "document_type",
        "schema_version",
        "provider",
        "provider_version",
        "collected_at_utc",
        "records",
        "endpoint_statuses",
        "collection_gaps",
        "raw_response_persisted",
        "retention",
    }
)
_PRIVATE_RECORD_FIELDS: Final = frozenset(
    {
        "schema_version",
        "resource_family",
        "source_api_version",
        "source_endpoint_key",
        "required_permission",
        "collected_at_utc",
        "source_object_id",
        "properties",
        "evidence_id",
        "content_fingerprint",
    }
)


def private_collection_document(
    collection: AppleIntuneCollection, *, delete_after_utc: str
) -> dict[str, JsonValue]:
    """Serialize normalized private evidence without raw Graph response content."""
    document: dict[str, JsonValue] = {
        "document_type": PRIVATE_COLLECTION_TYPE,
        "schema_version": collection.schema_version,
        "provider": collection.provider,
        "provider_version": collection.provider_version,
        "collected_at_utc": collection.collected_at_utc,
        "records": cast(JsonValue, list(collection.records)),
        "endpoint_statuses": cast(JsonValue, list(collection.endpoint_statuses)),
        "collection_gaps": cast(JsonValue, list(collection.collection_gaps)),
        "raw_response_persisted": collection.raw_response_persisted,
        "retention": {
            "policy": "operator-managed-private-evidence",
            "delete_after_utc": delete_after_utc,
        },
    }
    validate_private_collection(document)
    return document


def validate_private_collection(value: object) -> dict[str, JsonValue]:
    """Validate the normalized private envelope before storage or publication."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("private Apple collection must be a string-keyed object")
    document = cast(dict[str, JsonValue], value)
    if set(document) != _PRIVATE_TOP_LEVEL:
        raise ValueError("private Apple collection has unexpected or missing fields")
    if document["document_type"] != PRIVATE_COLLECTION_TYPE:
        raise ValueError("private Apple collection document type is invalid")
    if document["raw_response_persisted"] is not False:
        raise ValueError("raw Graph responses must never be persisted")
    records = document["records"]
    if not isinstance(records, list):
        raise ValueError("private Apple records must be an array")
    for record in records:
        if not isinstance(record, dict) or set(record) != _PRIVATE_RECORD_FIELDS:
            raise ValueError("private Apple record has unexpected or missing fields")
        properties = record.get("properties")
        if not isinstance(properties, dict) or not all(isinstance(key, str) for key in properties):
            raise ValueError("private Apple record properties must be an object")
        if any(
            field in properties
            for field in {
                "deviceName",
                "userPrincipalName",
                "emailAddress",
                "serialNumber",
                "imei",
                "meid",
                "udid",
                "wiFiMacAddress",
                "ethernetMacAddress",
                "phoneNumber",
                "azureADDeviceId",
            }
        ):
            raise ValueError("prohibited raw Graph field entered normalized private evidence")
    for field in ("endpoint_statuses", "collection_gaps"):
        if not isinstance(document[field], list):
            raise ValueError(f"private Apple field {field} must be an array")
    retention = document["retention"]
    if not isinstance(retention, dict) or set(retention) != {"policy", "delete_after_utc"}:
        raise ValueError("private Apple retention policy is invalid")
    return document


def collection_from_private_document(value: object) -> AppleIntuneCollection:
    """Rehydrate only a validated normalized collection; raw exports are unsupported."""
    document = validate_private_collection(value)
    return AppleIntuneCollection(
        schema_version=cast(str, document["schema_version"]),
        provider=cast(str, document["provider"]),
        provider_version=cast(str, document["provider_version"]),
        collected_at_utc=cast(str, document["collected_at_utc"]),
        records=tuple(cast(list[dict[str, JsonValue]], document["records"])),
        endpoint_statuses=tuple(cast(list[dict[str, JsonValue]], document["endpoint_statuses"])),
        collection_gaps=tuple(cast(list[dict[str, JsonValue]], document["collection_gaps"])),
        raw_response_persisted=False,
    )


def load_private_collection(path: Path) -> dict[str, JsonValue]:
    """Load a normalized private package without logging its contents."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("private Apple collection could not be read as JSON") from exc
    return validate_private_collection(value)


def write_private_collection(
    document: dict[str, JsonValue], *, directory: Path, repository_root: Path
) -> Path:
    """Write normalized private evidence to an ignored owner-only directory."""
    validated = validate_private_collection(document)
    root = repository_root.resolve()
    destination = directory.resolve()
    if not destination.is_relative_to(root):
        raise ValueError("private directory must be inside the selected repository")
    _assert_ignored(destination, root)
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.chmod(0o700)
    collected_at = cast(str, validated["collected_at_utc"])
    output = destination / f"private-apple-{collected_at.replace(':', '')}.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(output, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(validated, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return output


def _assert_ignored(destination: Path, root: Path) -> None:
    executable = shutil.which("git")
    if executable is None:
        raise ValueError("git is required to verify the private evidence boundary")
    probe = (destination / ".evidenceops-private-probe").relative_to(root)
    result = subprocess.run(  # noqa: S603  # nosec B603
        [executable, "check-ignore", "--quiet", "--no-index", "--", str(probe)],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError("selected private directory is not covered by repository ignore rules")
