"""Pinned TMCO Build Week demo baseline derived from mSCP metadata.

Only rule identifiers, titles, expected mobileconfig values, and deterministic
cross-reference identifiers needed by the demo are reproduced. Apple vendor
descriptions are deliberately excluded. The upstream mSCP source is CC BY 4.0;
the pinned source and attribution are recorded in ``NOTICE`` and the approval
record below.
"""

from __future__ import annotations

import hashlib
from typing import Final, cast

from evidenceops.domain import JsonValue, canonical_json

BASELINE_SCHEMA_VERSION: Final = "1.0.0"
MSCP_SOURCE_URL: Final = "https://github.com/usnistgov/macos_security"
MSCP_SOURCE_REVISION: Final = "11b5896e4f12f43410686024f543792742562c91"
MSCP_BASELINE_PATH: Final = "src/mscp/data/baselines/macos/cis_lvl1_macos_26.0.yaml"
SOURCE_ARTIFACT_SHA256: Final = "af9ef14ca568f17d3663e6e508c1f75971596fe43c6f185af27ca43451c240d2"

# Complete ordered inventory from the pinned mSCP macOS 26 CIS Level 1 profile.
# Ordering is significant and included in the extracted-inventory fingerprint.
BASELINE_RULES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "Auditing",
        (
            "audit_acls_files_configure",
            "audit_acls_folders_configure",
            "audit_auditd_enabled",
            "audit_control_acls_configure",
            "audit_control_group_configure",
            "audit_control_mode_configure",
            "audit_control_owner_configure",
            "audit_files_group_configure",
            "audit_files_mode_configure",
            "audit_files_owner_configure",
            "audit_folder_group_configure",
            "audit_folder_owner_configure",
            "audit_folders_mode_configure",
            "audit_retention_configure",
        ),
    ),
    (
        "Operating System",
        (
            "os_airdrop_disable",
            "os_anti_virus_installed",
            "os_authenticated_root_enable",
            "os_config_data_install_enforce",
            "os_external_apfs_hfs_volumes_encrypted",
            "os_gatekeeper_enable",
            "os_guest_folder_removed",
            "os_home_folders_secure",
            "os_httpd_disable",
            "os_install_log_retention_configure",
            "os_internal_apfs_volumes_encrypted",
            "os_mail_summary_disable",
            "os_mobile_file_integrity_enable",
            "os_nfsd_disable",
            "os_notes_transcription_disable",
            "os_notes_transcription_summary_disable",
            "os_on_device_dictation_enforce",
            "os_password_hint_remove",
            "os_power_nap_disable",
            "os_root_disable",
            "os_safari_advertising_privacy_protection_enable",
            "os_safari_open_safe_downloads_disable",
            "os_safari_prevent_cross_site_tracking_enable",
            "os_safari_show_full_website_address_enable",
            "os_safari_show_status_bar_enabled",
            "os_safari_warn_fraudulent_website_enable",
            "os_sip_enable",
            "os_software_update_app_update_enforce",
            "os_software_update_deferral",
            "os_sudo_log_enforce",
            "os_sudo_timeout_configure",
            "os_sudoers_timestamp_type_configure",
            "os_system_wide_applications_configure",
            "os_terminal_secure_keyboard_enable",
            "os_time_server_enabled",
            "os_unlock_active_user_session_disable",
            "os_world_writable_system_folder_configure",
            "os_writing_tools_disable",
        ),
    ),
    (
        "Password Policy",
        (
            "pwpolicy_account_lockout_enforce",
            "pwpolicy_account_lockout_timeout_enforce",
            "pwpolicy_history_enforce",
            "pwpolicy_max_lifetime_enforce",
            "pwpolicy_minimum_length_enforce",
        ),
    ),
    (
        "System Settings",
        (
            "system_settings_airplay_receiver_disable",
            "system_settings_automatic_login_disable",
            "system_settings_bluetooth_sharing_disable",
            "system_settings_critical_update_install_enforce",
            "system_settings_diagnostics_reports_disable",
            "system_settings_external_intelligence_disable",
            "system_settings_external_intelligence_sign_in_disable",
            "system_settings_filevault_enforce",
            "system_settings_firewall_enable",
            "system_settings_firewall_stealth_mode_enable",
            "system_settings_guest_access_smb_disable",
            "system_settings_guest_account_disable",
            "system_settings_hot_corners_secure",
            "system_settings_improve_assistive_voice_disable",
            "system_settings_improve_search_disable",
            "system_settings_improve_siri_dictation_disable",
            "system_settings_install_macos_updates_enforce",
            "system_settings_internet_sharing_disable",
            "system_settings_location_services_menu_enforce",
            "system_settings_loginwindow_loginwindowtext_enable",
            "system_settings_loginwindow_prompt_username_password_enforce",
            "system_settings_password_hints_disable",
            "system_settings_personalized_advertising_disable",
            "system_settings_printer_sharing_disable",
            "system_settings_rae_disable",
            "system_settings_remote_management_disable",
            "system_settings_screen_sharing_disable",
            "system_settings_screensaver_ask_for_password_delay_enforce",
            "system_settings_screensaver_password_enforce",
            "system_settings_screensaver_timeout_enforce",
            "system_settings_siri_disable",
            "system_settings_smbd_disable",
            "system_settings_software_update_download_enforce",
            "system_settings_softwareupdate_current",
            "system_settings_ssh_disable",
            "system_settings_system_wide_preferences_configure",
            "system_settings_time_machine_encrypted_configure",
            "system_settings_time_server_configure",
            "system_settings_time_server_enforce",
            "system_settings_wake_network_access_disable",
        ),
    ),
    ("Supplemental", ("supplemental_cis_manual",)),
)


def _flat_inventory() -> list[dict[str, JsonValue]]:
    return [
        {"ordinal": ordinal, "section": section, "rule_id": rule_id}
        for ordinal, (section, rule_id) in enumerate(
            ((section, rule_id) for section, rules in BASELINE_RULES for rule_id in rules),
            start=1,
        )
    ]


EXTRACTED_INVENTORY_SHA256: Final = hashlib.sha256(
    canonical_json(cast(JsonValue, _flat_inventory())).encode("utf-8")
).hexdigest()

# Exact, human-reviewed mappings used by the synthetic vertical slice. The
# crosswalk identifiers are copied from the pinned rule metadata, not generated
# by a language model. The complete 98-rule inventory remains visible; only these
# three rules currently have deterministic provider mappings.
DEMO_RULE_MAPPINGS: Final[dict[str, dict[str, JsonValue]]] = {
    "system_settings_filevault_enforce": {
        "title": "Enforce FileVault",
        "setting_key": "macos.security.filevault.enabled",
        "expected_value": True,
        "severity": "high",
        "payload_type": "com.apple.MCX",
        "payload_key": "dontAllowFDEDisable",
        "cis_benchmark": ["2.6.6 (level 1)"],
        "nist_800_53r5": ["SC-28", "SC-28(1)"],
        "nist_800_171r3": ["03.13.08"],
        "stig": ["APPL-26-005020"],
        "cmmc": ["SC.L2-3.13.16"],
    },
    "system_settings_firewall_enable": {
        "title": "Enable macOS Application Firewall",
        "setting_key": "macos.security.firewall.enabled",
        "expected_value": True,
        "severity": "high",
        "payload_type": "com.apple.security.firewall",
        "payload_key": "EnableFirewall",
        "cis_benchmark": ["2.2.1 (level 1)"],
        "nist_800_53r5": ["AC-4", "CM-7", "CM-7(1)", "SC-7", "SC-7(12)"],
        "nist_800_171r3": ["03.01.03", "03.04.06", "03.13.01"],
        "stig": ["APPL-26-005050"],
        "cmmc": ["AC.L2-3.1.3", "CM.L2-3.4.6", "CM.L2-3.4.7", "SC.L1-3.13.1"],
    },
    "system_settings_firewall_stealth_mode_enable": {
        "title": "Enable Firewall Stealth Mode",
        "setting_key": "macos.security.firewall.stealth_mode",
        "expected_value": True,
        "severity": "medium",
        "payload_type": "com.apple.security.firewall",
        "payload_key": "EnableStealthMode",
        "cis_benchmark": ["2.2.2 (level 1)"],
        "nist_800_53r5": ["CM-7", "CM-7(1)", "SC-7", "SC-7(16)"],
        "nist_800_171r3": ["03.04.06", "03.13.01"],
        "stig": [],
        "cmmc": ["CM.L2-3.4.6", "CM.L2-3.4.7", "SC.L1-3.13.1"],
    },
    "system_settings_screensaver_password_enforce": {
        "title": "Enforce Screen Saver Password",
        "setting_key": "macos.screen_lock.require_password",
        "expected_value": True,
        "severity": "medium",
        "payload_type": "com.apple.screensaver",
        "payload_key": "askForPassword",
        "cis_benchmark": ["2.11.2 (level 1)"],
        "nist_800_53r5": ["AC-11"],
        "nist_800_171r3": ["03.01.10", "03.05.01"],
        "stig": ["APPL-26-000002"],
        "cmmc": ["AC.L2-3.1.10"],
    },
    "system_settings_screensaver_timeout_enforce": {
        "title": "Enforce Screen Saver Timeout",
        "setting_key": "macos.screen_lock.max_idle_seconds",
        "expected_value": 900,
        "evaluation_mode": "maximum",
        "severity": "low",
        "payload_type": "com.apple.screensaver",
        "payload_key": "idleTime",
        "cis_benchmark": ["2.11.1 (level 1)"],
        "nist_800_53r5": ["AC-11", "IA-11"],
        "nist_800_171r3": ["03.01.10", "03.05.01"],
        "stig": ["APPL-26-000070"],
        "cmmc": ["AC.L2-3.1.10"],
    },
}

APPROVAL_RECORD: Final[dict[str, JsonValue]] = {
    "schema_version": BASELINE_SCHEMA_VERSION,
    "organization": "TMCO Consulting",
    "baseline_name": "TMCO macOS CIS Level 1 Build Week Demo Baseline",
    "platform": "macOS",
    "benchmark": "CIS Apple macOS 26 Tahoe Benchmark Level 1",
    "benchmark_version": "macOS 26.0 / pinned mSCP profile",
    "mscp_source_revision": MSCP_SOURCE_REVISION,
    "source_url": MSCP_SOURCE_URL,
    "source_path": MSCP_BASELINE_PATH,
    "source_artifact_sha256": SOURCE_ARTIFACT_SHA256,
    "extracted_baseline_sha256": EXTRACTED_INVENTORY_SHA256,
    "approval_status": "internally approved demo baseline",
    "approver": "TMCO Build Week Demo Authority",
    "approval_date": "2026-07-19",
    "approval_rationale": (
        "Provide reproducible technical drift detection for the EvidenceOps Build Week demo."
    ),
    "scope": "macOS technical configuration evidence only",
    "supersedes": None,
    "limitations": [
        "This internal demo approval is not CIS, NIST, DoD, C3PAO, or assessor certification.",
        "Only explicitly mapped settings are automatically evaluated.",
        "iOS and iPadOS are outside this macOS baseline and are not scored against it.",
        "Organizational, procedural, interview, and assessor evidence remain required.",
    ],
    "repository_commit": "3dd8902a609c6be177cdc913c731fbd378f075a4",
    "rule_count": 98,
    "license": "CC-BY-4.0 (upstream mSCP metadata; Apple vendor descriptions excluded)",
}


def verify_approved_baseline(record: dict[str, JsonValue] = APPROVAL_RECORD) -> None:
    """Fail closed if the pinned inventory or approval record changes unexpectedly."""
    inventory = _flat_inventory()
    if len(inventory) != 98 or len({item["rule_id"] for item in inventory}) != 98:
        raise ValueError("pinned mSCP inventory must contain 98 unique rules")
    actual_hash = hashlib.sha256(
        canonical_json(cast(JsonValue, inventory)).encode("utf-8")
    ).hexdigest()
    if actual_hash != EXTRACTED_INVENTORY_SHA256:
        raise ValueError("pinned mSCP extracted-inventory hash mismatch")
    required = {
        "schema_version",
        "organization",
        "baseline_name",
        "platform",
        "benchmark",
        "benchmark_version",
        "mscp_source_revision",
        "source_url",
        "source_path",
        "source_artifact_sha256",
        "extracted_baseline_sha256",
        "approval_status",
        "approver",
        "approval_date",
        "approval_rationale",
        "scope",
        "supersedes",
        "limitations",
        "repository_commit",
        "rule_count",
        "license",
    }
    if set(record) != required:
        raise ValueError("baseline approval record has unexpected or missing fields")
    if record["extracted_baseline_sha256"] != actual_hash or record["rule_count"] != 98:
        raise ValueError("baseline approval record does not match the pinned inventory")
    if record["mscp_source_revision"] != MSCP_SOURCE_REVISION:
        raise ValueError("baseline approval record source revision mismatch")
    if record["approval_status"] != "internally approved demo baseline":
        raise ValueError("baseline approval record status is not approved for the demo")
