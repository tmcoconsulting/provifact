"""Build the public mSCP profile-membership comparison catalog.

The input is a local tarball of the pinned public NIST mSCP source revision. The
script never downloads data and copies only profile membership, rule IDs,
titles, sections, source fingerprints, and attribution metadata. Apple vendor
descriptions and remediation content are deliberately excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path
from typing import Final

from evidenceops.baselines.mscp import (
    EXTRACTED_INVENTORY_SHA256,
    MSCP_SOURCE_REVISION,
    MSCP_SOURCE_URL,
)
from evidenceops.domain import JsonValue, canonical_json

CATALOG_SCHEMA_VERSION: Final = "1.0.0"
PLATFORM_VERSION: Final = "macOS 26.0"
RULE_SECTION_LABELS: Final[dict[str, str]] = {
    "audit": "Auditing",
    "auth": "Authentication",
    "icloud": "iCloud",
    "os": "Operating System",
    "pwpolicy": "Password Policy",
    "supplemental": "Supplemental",
    "system_settings": "System Settings",
}

PROFILE_SPECS: Final[tuple[tuple[str, str, str, str], ...]] = (
    ("cis_lvl1", "CIS Level 1", "CIS", "cis_lvl1_macos_26.0.yaml"),
    ("cis_lvl2", "CIS Level 2", "CIS", "cis_lvl2_macos_26.0.yaml"),
    ("cis_controls_v8", "CIS Controls v8", "CIS", "cisv8_macos_26.0.yaml"),
    ("disa_stig", "DISA STIG", "DoD", "disa_stig_macos_26.0.yaml"),
    ("nist_800_171", "NIST SP 800-171", "NIST", "800-171_macos_26.0.yaml"),
    ("nist_800_53_low", "NIST SP 800-53 Low", "NIST", "800-53r5_low_macos_26.0.yaml"),
    (
        "nist_800_53_moderate",
        "NIST SP 800-53 Moderate",
        "NIST",
        "800-53r5_moderate_macos_26.0.yaml",
    ),
    ("nist_800_53_high", "NIST SP 800-53 High", "NIST", "800-53r5_high_macos_26.0.yaml"),
    ("cmmc_level_1", "CMMC Level 1", "CMMC", "cmmc_lvl1_macos_26.0.yaml"),
    ("cmmc_level_2", "CMMC Level 2", "CMMC", "cmmc_lvl2_macos_26.0.yaml"),
    ("cnssi_1253_low", "CNSSI 1253 Low", "CNSSI", "cnssi-1253_low_macos_26.0.yaml"),
    (
        "cnssi_1253_moderate",
        "CNSSI 1253 Moderate",
        "CNSSI",
        "cnssi-1253_moderate_macos_26.0.yaml",
    ),
    ("cnssi_1253_high", "CNSSI 1253 High", "CNSSI", "cnssi-1253_high_macos_26.0.yaml"),
    ("hicp", "HHS HICP", "HHS", "hicp_lp_macos_26.0.yaml"),
    ("nllmap_base", "NLLMAP Base", "NLLMAP", "nlmapgov_base_macos_26.0.yaml"),
    ("nllmap_plus", "NLLMAP Plus", "NLLMAP", "nlmapgov_plus_macos_26.0.yaml"),
)

# The pinned upstream profile uses a hyphen in this one rule identifier while
# the approved Provifact baseline and deterministic Mission schema use the
# normalized underscore form. Keep the conversion explicit rather than
# applying a broad punctuation rewrite that could merge unrelated future IDs.
UPSTREAM_RULE_ID_ALIASES: Final[dict[str, str]] = {
    "os_safari_prevent_cross-site_tracking_enable": (
        "os_safari_prevent_cross_site_tracking_enable"
    ),
}


def _canonical_rule_id(rule_id: str) -> str:
    return UPSTREAM_RULE_ID_ALIASES.get(rule_id, rule_id)


def _validate_archive(archive: tarfile.TarFile) -> None:
    expected_root = f"macos_security-{MSCP_SOURCE_REVISION}/"
    names = [member.name for member in archive.getmembers()]
    if not names or any(
        name != expected_root.rstrip("/") and not name.startswith(expected_root) for name in names
    ):
        raise ValueError("source archive does not match the pinned mSCP revision root")


def _member_name(archive: tarfile.TarFile, suffix: str) -> str:
    matches = [member.name for member in archive.getmembers() if member.name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one pinned source member ending in {suffix!r}")
    return matches[0]


def _read_member(archive: tarfile.TarFile, suffix: str) -> bytes:
    member = archive.extractfile(_member_name(archive, suffix))
    if member is None:
        raise ValueError(f"could not read pinned source member {suffix!r}")
    return member.read()


def _yaml_scalar(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1]
    return stripped


def _parse_profile(raw: bytes) -> tuple[list[str], dict[str, int]]:
    section = "Unsectioned"
    rule_ids: list[str] = []
    section_counts: dict[str, int] = {}
    for line in raw.decode("utf-8").splitlines():
        section_match = re.fullmatch(r"  - section:\s*(.+)", line)
        if section_match:
            section = _yaml_scalar(section_match.group(1))
            section_counts.setdefault(section, 0)
            continue
        rule_match = re.fullmatch(r"      - ([a-z0-9_+-]+)", line)
        if rule_match:
            rule_id = _canonical_rule_id(rule_match.group(1))
            if rule_id in rule_ids:
                raise ValueError(f"duplicate rule {rule_id!r} in pinned profile")
            rule_ids.append(rule_id)
            section_counts[section] = section_counts.get(section, 0) + 1
    if not rule_ids:
        raise ValueError("pinned profile contained no rule IDs")
    return rule_ids, section_counts


def _rule_metadata(archive: tarfile.TarFile) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    pattern = re.compile(r"/src/mscp/data/rules/([^/]+)/([^/]+)\.yaml$")
    for member in archive.getmembers():
        match = pattern.search(member.name)
        if match is None or not member.isfile():
            continue
        stream = archive.extractfile(member)
        if stream is None:
            continue
        rule_id = ""
        title = ""
        for line in stream.read().decode("utf-8").splitlines():
            if line.startswith("id: "):
                rule_id = _yaml_scalar(line[4:])
            elif line.startswith("title: "):
                title = _yaml_scalar(line[7:])
            if rule_id and title:
                break
        if rule_id:
            rule_id = _canonical_rule_id(rule_id)
            if rule_id in metadata:
                raise ValueError(f"duplicate canonical rule metadata {rule_id!r}")
            metadata[rule_id] = {
                "title": title or rule_id.replace("_", " ").title(),
                "section": match.group(1),
            }
    return metadata


def _profile(
    profile_id: str,
    label: str,
    family: str,
    source_path: str,
    raw: bytes,
) -> dict[str, JsonValue]:
    rule_ids, section_counts = _parse_profile(raw)
    section_values: list[JsonValue] = [
        {"name": name, "rule_count": count} for name, count in section_counts.items()
    ]
    rule_values: list[JsonValue] = list(rule_ids)
    return {
        "profile_id": profile_id,
        "label": label,
        "family": family,
        "kind": "external technical reference profile",
        "platform": PLATFORM_VERSION,
        "source_path": source_path,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "rule_count": len(rule_ids),
        "sections": section_values,
        "rule_ids": rule_values,
    }


def build_catalog(source_tar: Path) -> dict[str, JsonValue]:
    with tarfile.open(source_tar, "r:gz") as archive:
        _validate_archive(archive)
        profiles: list[dict[str, JsonValue]] = []
        for profile_id, label, family, filename in PROFILE_SPECS:
            source_path = f"src/mscp/data/baselines/macos/{filename}"
            raw = _read_member(archive, f"/{source_path}")
            profiles.append(_profile(profile_id, label, family, source_path, raw))
        metadata = _rule_metadata(archive)

    cis_level_1 = profiles[0]
    tmco_profile: dict[str, JsonValue] = {
        "profile_id": "tmco_approved",
        "label": "TMCO Consulting Approved",
        "family": "TMCO Consulting",
        "kind": "company-approved technical baseline",
        "platform": PLATFORM_VERSION,
        "source_path": "baselines/tmco-macos-cis-level1-demo-approval.json",
        "source_sha256": EXTRACTED_INVENTORY_SHA256,
        "source_profile_id": "cis_lvl1",
        "rule_count": cis_level_1["rule_count"],
        "sections": cis_level_1["sections"],
        "rule_ids": cis_level_1["rule_ids"],
    }
    profiles.insert(0, tmco_profile)

    membership: dict[str, list[str]] = {}
    for profile in profiles:
        profile_id = str(profile["profile_id"])
        rule_ids_value = profile["rule_ids"]
        if not isinstance(rule_ids_value, list):
            raise ValueError(f"profile {profile_id!r} has invalid rule membership")
        for rule_id in rule_ids_value:
            membership.setdefault(str(rule_id), []).append(profile_id)
    missing = sorted(set(membership) - set(metadata))
    rules: list[dict[str, JsonValue]] = []
    for rule_id in sorted(membership):
        item = metadata.get(rule_id)
        profile_ids: list[JsonValue] = list(membership[rule_id])
        rules.append(
            {
                "rule_id": rule_id,
                "title": item["title"] if item else rule_id.replace("_", " ").title(),
                "section": RULE_SECTION_LABELS.get(item["section"], "Catalog")
                if item
                else "Catalog",
                "profile_ids": profile_ids,
            }
        )

    profile_values: list[JsonValue] = list(profiles)
    rule_values: list[JsonValue] = []
    rule_values.extend(rules)
    missing_values: list[JsonValue] = list(missing)
    catalog: dict[str, JsonValue] = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "source": {
            "repository": MSCP_SOURCE_URL,
            "revision": MSCP_SOURCE_REVISION,
            "platform": PLATFORM_VERSION,
            "license": "CC-BY-4.0; Apple vendor descriptions excluded",
            "attribution": "NIST macOS Security Compliance Project (mSCP)",
        },
        "profiles": profile_values,
        "rules": rule_values,
        "metadata_fallback_rule_ids": missing_values,
        "comparison_boundary": (
            "Exact rule-ID membership overlap only. This is not a framework score, "
            "control-satisfaction result, certification, or assessor conclusion."
        ),
    }
    catalog["catalog_fingerprint"] = (
        "sha256:" + hashlib.sha256(canonical_json(catalog).encode("utf-8")).hexdigest()
    )
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-tar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = build_catalog(args.source_tar)
    args.output.write_text(
        json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
