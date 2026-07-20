"""Pinned TMCO Consulting Build Week demo baseline derived from mSCP metadata.

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

# Human-readable titles copied from the rule metadata at the pinned mSCP source
# revision above. Product-like dotted tokens are expanded to public-safe words so
# they cannot resemble a tenant domain to the fail-closed publication scanner.
# Keeping the complete title catalog beside the ordered inventory prevents the
# public implementation plan from presenting machine identifiers as if they were
# usable control objectives. No Apple descriptions or remediation scripts are
# reproduced.
BASELINE_RULE_TITLES: Final[dict[str, str]] = {
    "audit_acls_files_configure": "Configure Audit Log Files to Not Contain Access Control Lists",
    "audit_acls_folders_configure": (
        "Configure Audit Log Folder to Not Contain Access Control Lists"
    ),
    "audit_auditd_enabled": "Enable Security Auditing",
    "audit_control_acls_configure": "Configure Audit_Control to Not Contain Access Control Lists",
    "audit_control_group_configure": "Configure Audit_Control Group to Wheel",
    "audit_control_mode_configure": "Configure Audit_Control Owner to Mode 440 or Less Permissive",
    "audit_control_owner_configure": "Configure Audit_Control Owner to Root",
    "audit_files_group_configure": "Configure Audit Log Files Group to Wheel",
    "audit_files_mode_configure": "Configure Audit Log Files to Mode 440 or Less Permissive",
    "audit_files_owner_configure": "Configure Audit Log Files to be Owned by Root",
    "audit_folder_group_configure": "Configure Audit Log Folders Group to Wheel",
    "audit_folder_owner_configure": "Configure Audit Log Folders to be Owned by Root",
    "audit_folders_mode_configure": "Configure Audit Log Folders to Mode 700 or Less Permissive",
    "audit_retention_configure": "Configure Audit Retention to $ODV",
    "os_airdrop_disable": "Disable AirDrop",
    "os_anti_virus_installed": "Must Use an Approved Antivirus Program",
    "os_authenticated_root_enable": "Enable Authenticated Root",
    "os_config_data_install_enforce": (
        "Enforce Installation of XProtect Remediator and Gatekeeper Updates Automatically"
    ),
    "os_external_apfs_hfs_volumes_encrypted": (
        "Ensure All APFS and HFS+ External User Storage Volumes Are Encrypted"
    ),
    "os_gatekeeper_enable": "Enable Gatekeeper",
    "os_guest_folder_removed": "Remove Guest Folder if Present",
    "os_home_folders_secure": "Secure User's Home Folders",
    "os_httpd_disable": "Disable the Built-in Web Server",
    "os_install_log_retention_configure": "Configure Install Log Retention to $ODV",
    "os_internal_apfs_volumes_encrypted": (
        "Ensure All Internal User Storage APFS Volumes Are Encrypted"
    ),
    "os_mail_summary_disable": "Disable Apple Intelligence Mail Summary",
    "os_mobile_file_integrity_enable": "Enable Apple Mobile File Integrity",
    "os_nfsd_disable": "Disable Network File System Service",
    "os_notes_transcription_disable": "Disable Apple Intelligence Notes Transcription",
    "os_notes_transcription_summary_disable": (
        "Disable Apple Intelligence Notes Transcription Summary"
    ),
    "os_on_device_dictation_enforce": "Enforce On Device Dictation",
    # Public benchmark title; no credential material is embedded here.
    "os_password_hint_remove": "Remove Password Hint From User Accounts",  # nosec B105
    "os_power_nap_disable": "Disable Power Nap",
    "os_root_disable": "Disable Root Login",
    "os_safari_advertising_privacy_protection_enable": (
        "Ensure Advertising Privacy Protection in Safari Is Enabled"
    ),
    "os_safari_open_safe_downloads_disable": ("Disable Automatic Opening of Safe Files in Safari"),
    "os_safari_prevent_cross_site_tracking_enable": (
        "Ensure Prevent Cross-site Tracking in Safari Is Enabled"
    ),
    "os_safari_show_full_website_address_enable": (
        "Ensure Show Full Website Address in Safari Is Enabled"
    ),
    "os_safari_show_status_bar_enabled": "Ensure Show Safari shows the Status Bar is Enabled",
    "os_safari_warn_fraudulent_website_enable": (
        "Ensure Warn When Visiting A Fraudulent Website in Safari Is Enabled"
    ),
    "os_sip_enable": "Ensure System Integrity Protection is Enabled",
    "os_software_update_app_update_enforce": (
        "Enforce Software Update App Update Updates Automatically"
    ),
    "os_software_update_deferral": (
        "Ensure Software Update Deferment Is Less Than or Equal to $ODV Days"
    ),
    "os_sudo_log_enforce": "Configure Sudo To Log Events",
    "os_sudo_timeout_configure": "Configure Sudo Timeout Period to $ODV",
    "os_sudoers_timestamp_type_configure": "Configure Sudoers Timestamp Type",
    "os_system_wide_applications_configure": (
        "Ensure Appropriate Permissions Are Enabled for System Wide Applications"
    ),
    "os_terminal_secure_keyboard_enable": "Ensure Secure Keyboard Entry in Terminal Is Enabled",
    "os_time_server_enabled": "Enable Time Synchronization Daemon",
    "os_unlock_active_user_session_disable": (
        "Disable Login to Other User's Active and Locked Sessions"
    ),
    "os_world_writable_system_folder_configure": (
        "Ensure No World Writable Files Exist in the System Folder"
    ),
    "os_writing_tools_disable": "Disable Apple Intelligence Writing Tools",
    "pwpolicy_account_lockout_enforce": "Limit Consecutive Failed Login Attempts to $ODV",
    "pwpolicy_account_lockout_timeout_enforce": "Set Account Lockout Time to $ODV Minutes",
    "pwpolicy_history_enforce": "Prohibit Password Reuse for a Minimum of $ODV Generations",
    "pwpolicy_max_lifetime_enforce": "Restrict Maximum Password Lifetime to $ODV Days",
    "pwpolicy_minimum_length_enforce": "Require a Minimum Password Length of $ODV Characters",
    "system_settings_airplay_receiver_disable": "Disable Airplay Receiver",
    "system_settings_automatic_login_disable": (
        "Disable Unattended or Automatic Logon to the System"
    ),
    "system_settings_bluetooth_sharing_disable": "Disable Bluetooth Sharing",
    "system_settings_critical_update_install_enforce": (
        "Enforce Critical Security Updates to be Installed"
    ),
    "system_settings_diagnostics_reports_disable": (
        "Disable Sending Diagnostic and Usage Data to Apple"
    ),
    "system_settings_external_intelligence_disable": "Disable External Intelligence Integrations",
    "system_settings_external_intelligence_sign_in_disable": (
        "Disable External Intelligence Integration Sign In"
    ),
    "system_settings_filevault_enforce": "Enforce FileVault",
    "system_settings_firewall_enable": "Enable macOS Application Firewall",
    "system_settings_firewall_stealth_mode_enable": "Enable Firewall Stealth Mode",
    "system_settings_guest_access_smb_disable": "Disable Guest Access to Shared SMB Folders",
    "system_settings_guest_account_disable": "Disable the Guest Account",
    "system_settings_hot_corners_secure": "Secure Hot Corners",
    "system_settings_improve_assistive_voice_disable": (
        "Disable Sending Audio Recordings and Transcripts to Apple"
    ),
    "system_settings_improve_search_disable": "Disable Improve Search Information to Apple",
    "system_settings_improve_siri_dictation_disable": (
        "Disable Improve Siri and Dictation Information to Apple"
    ),
    "system_settings_install_macos_updates_enforce": (
        "Enforce macOS Updates are Automatically Installed"
    ),
    "system_settings_internet_sharing_disable": "Disable Internet Sharing",
    "system_settings_location_services_menu_enforce": (
        "Ensure Location Services Is In the Menu Bar"
    ),
    "system_settings_loginwindow_loginwindowtext_enable": (
        "Configure Login Window to Show A Custom Message"
    ),
    "system_settings_loginwindow_prompt_username_password_enforce": (  # nosec B105
        "Configure Login Window to Prompt for Username and Password"
    ),
    # Public benchmark title; no credential material is embedded here.
    "system_settings_password_hints_disable": "Disable Password Hints",  # nosec B105
    "system_settings_personalized_advertising_disable": "Disable Personalized Advertising",
    "system_settings_printer_sharing_disable": "Disable Printer Sharing",
    "system_settings_rae_disable": "Disable Remote Apple Events",
    "system_settings_remote_management_disable": "Disable Remote Management",
    "system_settings_screen_sharing_disable": "Disable Screen Sharing and Apple Remote Desktop",
    "system_settings_screensaver_ask_for_password_delay_enforce": (  # nosec B105
        "Enforce Session Lock After Screen Saver is Started"
    ),
    "system_settings_screensaver_password_enforce": (  # nosec B105
        "Enforce Screen Saver Password"
    ),
    "system_settings_screensaver_timeout_enforce": "Enforce Screen Saver Timeout",
    "system_settings_siri_disable": "Disable Siri",
    "system_settings_smbd_disable": "Disable Server Message Block Sharing",
    "system_settings_software_update_download_enforce": (
        "Enforce Software Update Downloads Updates Automatically"
    ),
    "system_settings_softwareupdate_current": "Ensure Software Update is Updated and Current",
    "system_settings_ssh_disable": "Disable SSH Server for Remote Access Sessions",
    "system_settings_system_wide_preferences_configure": (
        "Require Administrator Password to Modify System-Wide Preferences"
    ),
    "system_settings_time_machine_encrypted_configure": (
        "Ensure Time Machine Volumes are Encrypted"
    ),
    "system_settings_time_server_configure": "Configure macOS to Use an Authorized Time Server",
    "system_settings_time_server_enforce": "Enforce macOS Time Synchronization",
    "system_settings_wake_network_access_disable": "Ensure Wake for Network Access Is Disabled",
    "supplemental_cis_manual": "CIS Manual Recommendations",
}


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
# by a language model. The complete 98-rule inventory remains visible; four of
# these five desired settings currently have deterministic provider mappings.
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
    "baseline_name": "TMCO Consulting macOS CIS Level 1 Demo Baseline",
    "platform": "macOS",
    "benchmark": "CIS Apple macOS 26 Tahoe Benchmark Level 1",
    "benchmark_version": "macOS 26.0 / pinned mSCP profile",
    "mscp_source_revision": MSCP_SOURCE_REVISION,
    "source_url": MSCP_SOURCE_URL,
    "source_path": MSCP_BASELINE_PATH,
    "source_artifact_sha256": SOURCE_ARTIFACT_SHA256,
    "extracted_baseline_sha256": EXTRACTED_INVENTORY_SHA256,
    "approval_status": "internally approved demo baseline",
    "approver": "TMCO Consulting, LLC — Build Week Demo Authority",
    "approval_date": "2026-07-19",
    "approval_rationale": (
        "Provide reproducible technical drift detection for the Provifact Build Week demo."
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
    inventory_rule_ids = {cast(str, item["rule_id"]) for item in inventory}
    if set(BASELINE_RULE_TITLES) != inventory_rule_ids:
        raise ValueError("pinned mSCP title catalog must exactly cover the approved inventory")
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
