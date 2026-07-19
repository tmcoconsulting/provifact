#!/usr/bin/env python3
"""Verify that the reviewed Worker version is active at 100 percent traffic."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

SNAPSHOT_MESSAGE: Final = re.compile(r"^evidenceops-snapshot:mission-[0-9a-f]{24}$")


def _read_json(path: Path) -> object:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Cloudflare metadata must be a regular file")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Cloudflare metadata could not be read") from exc


def _object(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be an object")
    return value


def _timestamp(value: object, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} timestamp is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{label} timestamp must be UTC")
    return parsed


def _records(value: object, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty array")
    return [_object(item, label=f"{label} entry") for item in value]


def verify_active_deployment(
    versions_value: object,
    deployments_value: object,
    *,
    expected_message: str,
) -> None:
    """Fail unless the message-bound version is the only active deployment version."""
    if not SNAPSHOT_MESSAGE.fullmatch(expected_message):
        raise ValueError("expected snapshot deployment message is invalid")

    versions = _records(versions_value, label="Cloudflare versions")
    matching_versions: list[tuple[datetime, str]] = []
    for version in versions:
        metadata = _object(version.get("metadata"), label="version metadata")
        annotations = _object(version.get("annotations"), label="version annotations")
        version_id = version.get("id")
        if not isinstance(version_id, str) or not version_id:
            raise ValueError("version ID is invalid")
        created_on = _timestamp(metadata.get("created_on"), label="version")
        if annotations.get("workers/message") != expected_message:
            continue
        if metadata.get("source") != "wrangler":
            raise ValueError("reviewed version source is not Wrangler")
        if annotations.get("workers/triggered_by") != "version_upload":
            raise ValueError("reviewed version trigger is invalid")
        matching_versions.append((created_on, version_id))
    if not matching_versions:
        raise ValueError("reviewed snapshot version is absent")
    reviewed_created_on, reviewed_version_id = max(matching_versions)

    deployments = _records(deployments_value, label="Cloudflare deployments")
    latest_deployment = max(
        deployments,
        key=lambda item: _timestamp(item.get("created_on"), label="deployment"),
    )
    deployed_at = _timestamp(latest_deployment.get("created_on"), label="deployment")
    if deployed_at < reviewed_created_on:
        raise ValueError("active deployment predates the reviewed version")
    if latest_deployment.get("source") != "wrangler":
        raise ValueError("active deployment source is not Wrangler")
    deployment_annotations = _object(
        latest_deployment.get("annotations"), label="deployment annotations"
    )
    if deployment_annotations.get("workers/triggered_by") != "deployment":
        raise ValueError("active deployment trigger is invalid")
    active_versions = _records(
        latest_deployment.get("versions"), label="active deployment versions"
    )
    if len(active_versions) != 1:
        raise ValueError("active deployment is not a single-version rollout")
    active = active_versions[0]
    if active.get("version_id") != reviewed_version_id or active.get("percentage") != 100:
        raise ValueError("reviewed version is not receiving 100 percent of traffic")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("versions", type=Path)
    parser.add_argument("deployments", type=Path)
    parser.add_argument("--expected-message", required=True)
    args = parser.parse_args(argv)
    verify_active_deployment(
        _read_json(args.versions),
        _read_json(args.deployments),
        expected_message=args.expected_message,
    )
    print("active Cloudflare deployment matches the reviewed snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
