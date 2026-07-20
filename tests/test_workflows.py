import json
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
WORKFLOWS = REPOSITORY_ROOT / ".github" / "workflows"


def test_executable_workflows_have_no_privileged_pages_chain() -> None:
    workflow_files = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    assert [path.name for path in workflow_files] == [
        "ci.yml",
        "codeql.yml",
        "deploy-cloudflare.yml",
        "intune-audit.yml",
    ]
    content = "\n".join(path.read_text(encoding="utf-8") for path in workflow_files)
    for prohibited in (
        "workflow_run:",
        "pages: write",
        "pull_request_target:",
        "github.event.pull_request.head.sha",
        "cloudflare/wrangler-action",
        "actions/deploy-pages",
        "actions/upload-pages-artifact",
        "actions/configure-pages",
    ):
        assert prohibited not in content


def test_executable_workflow_actions_are_immutable_and_least_privilege() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        content = path.read_text(encoding="utf-8")
        assert "contents: read" in content
        for line in content.splitlines():
            if "uses:" not in line:
                continue
            reference = line.split("uses:", maxsplit=1)[1].strip().split()[0]
            assert "@" in reference
            assert len(reference.rsplit("@", maxsplit=1)[1]) == 40

    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "${{ secrets." not in ci
    assert "OPENAI_API_KEY" not in ci
    assert "id-token: write" not in ci
    assert "npm run worker:dry-run:preview" in ci
    assert "npm run worker:dry-run:production" in ci
    assert "npm run test:worker" in ci
    assert "python scripts/check_company_name.py" in ci

    codeql = (WORKFLOWS / "codeql.yml").read_text(encoding="utf-8")
    assert "security-events: write" in codeql
    assert "actions: read" in codeql
    assert "build-mode: none" in codeql
    assert "pull_request_target:" not in codeql
    assert "persist-credentials: false" in codeql


def test_privileged_workflows_are_main_only_and_environment_protected() -> None:
    audit = (WORKFLOWS / "intune-audit.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in audit
    assert "pull_request:" not in audit
    assert "push:" not in audit
    assert "id-token: write" in audit
    assert "actions: read" in audit
    assert "environment: production" in audit
    assert "if: github.ref == 'refs/heads/main'" in audit
    assert "ref: ${{ github.sha }}" in audit
    assert "DeviceManagementConfiguration.Read.All" not in audit
    assert "--auth environment-token" in audit
    assert "store_private" not in audit
    assert "python -m pytest -o addopts=''" in audit
    assert "if: inputs.prepare_publication" in audit
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in audit
    assert "path: build/live-public/mission-control.json" in audit
    assert "retention-days: 1" in audit
    assert "path: artifacts/private" not in audit

    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "python -m pytest" in ci
    assert "python -m pytest -o addopts=''" not in ci

    deploy = (WORKFLOWS / "deploy-cloudflare.yml").read_text(encoding="utf-8")
    assert "id-token: write" not in deploy
    assert "push:" not in deploy
    assert "environment: production" in deploy
    assert "github.ref == 'refs/heads/main'" in deploy
    assert "inputs.confirm_production_deploy" in deploy
    assert 'if [ "$CLOUDFLARE_DEPLOY_ENABLED" != "true" ]' in deploy
    assert "secrets.CLOUDFLARE_API_TOKEN" in deploy
    assert deploy.count("secrets.CLOUDFLARE_API_TOKEN") == 1
    assert "npm run deploy:production" in deploy
    assert "ref: ${{ github.sha }}" in deploy
    assert "actions: read" in deploy
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in deploy
    assert "run-id: ${{ inputs.sanitized_audit_run_id }}" in deploy
    assert "expected_source_snapshot_id:" in deploy
    assert "EXPECTED_SOURCE_SNAPSHOT_ID: ${{ inputs.expected_source_snapshot_id }}" in deploy
    assert "python scripts/promote_live_mission.py" in deploy
    assert 'actual_snapshot_id="$(jq -r' in deploy
    assert 'if [ "$actual_snapshot_id" != "$EXPECTED_SOURCE_SNAPSHOT_ID" ]' in deploy
    assert 'deployment_message="evidenceops-snapshot:$EXPECTED_SOURCE_SNAPSHOT_ID"' in deploy
    assert 'npm run deploy:production -- --message "$deployment_message"' in deploy
    assert "npx wrangler versions list --env production --json" in deploy
    assert "npx wrangler deployments list --env production --json" in deploy
    assert "python scripts/verify_cloudflare_deployment.py" in deploy
    assert "provifact.tmcoconsulting.com/api/status" not in deploy
    assert "curl " not in deploy
    assert "python scripts/check_public_artifacts.py build/publication-handoff" in deploy


def test_production_deployment_requires_exact_reviewed_live_artifact() -> None:
    deploy = (WORKFLOWS / "deploy-cloudflare.yml").read_text(encoding="utf-8")
    promoter = (REPOSITORY_ROOT / "scripts" / "promote_live_mission.py").read_text(encoding="utf-8")
    selector = deploy.index("sanitized_audit_run_id:")
    expected = deploy.index("expected_source_snapshot_id:")
    permissions = deploy.index("permissions:")
    assert "required: true" in deploy[selector:expected]
    assert "required: true" in deploy[expected:permissions]
    assert "inputs.sanitized_audit_run_id != ''" not in deploy
    assert "rebuild-static-demo" not in deploy
    assert "SYNTHETIC DEMO DATA" not in deploy
    for trusted_run_property in (
        '.name == "Read-only Intune audit"',
        '.path == ".github/workflows/intune-audit.yml"',
        '.event == "workflow_dispatch"',
        '.head_branch == "main"',
        '.status == "completed"',
        '.conclusion == "success"',
    ):
        assert trusted_run_property in deploy
    assert 'if [[ ! "$SANITIZED_AUDIT_RUN_ID" =~ ^[0-9]{1,20}$ ]]' in deploy
    assert 'if [[ ! "$EXPECTED_SOURCE_SNAPSHOT_ID" =~ ^mission-[0-9a-f]{24}$ ]]' in deploy
    assert (
        "python scripts/promote_live_mission.py build/publication-handoff/mission-control.json"
        in deploy
    )
    assert 'mission["data_mode"] != "LIVE SANITIZED TENANT DATA"' in promoter
    assert "publication handoff must contain live sanitized tenant data" in promoter
    assert "find build/publication-handoff -mindepth 1 -print" in deploy
    assert deploy.index("Verify reviewed audit run provenance") < deploy.index(
        "Download reviewed sanitized Mission package"
    )
    assert deploy.index("python scripts/promote_live_mission.py") < deploy.index(
        "npm run validate:worker"
    )
    assert 'if [ "$snapshot_id" != "$EXPECTED_SOURCE_SNAPSHOT_ID" ]' in deploy
    assert "python scripts/verify_cloudflare_deployment.py" in deploy


def test_live_publication_handoff_cannot_retain_or_publish_private_evidence() -> None:
    audit = (WORKFLOWS / "intune-audit.yml").read_text(encoding="utf-8")
    deploy = (WORKFLOWS / "deploy-cloudflare.yml").read_text(encoding="utf-8")
    combined = audit + deploy
    assert "prepare_publication:" in audit
    assert "default: false" in audit
    assert "evidenceops-sanitized-mission-${{ github.run_id }}" in audit
    assert "include-hidden-files: false" in audit
    assert "compression-level: 0" in audit
    assert "overwrite: false" in audit
    assert "sanitized_audit_run_id:" in deploy
    assert "repository: ${{ github.repository }}" in deploy
    assert 'gh api "/repos/$GITHUB_REPOSITORY/actions/runs/' in deploy
    assert "evidenceops-sanitized-mission-${{ inputs.sanitized_audit_run_id }}" in deploy
    assert "find artifacts/private -type f -delete" in audit
    assert "find build/live-public -type f -delete" in audit
    for prohibited in (
        "upload-artifact@v",
        "download-artifact@v",
        "path: artifacts/private",
        "path: artifacts/raw",
        "retention-days: 90",
    ):
        assert prohibited not in combined


def test_prior_live_publication_is_validated_and_never_private() -> None:
    audit = (WORKFLOWS / "intune-audit.yml").read_text(encoding="utf-8")
    assert "prior_sanitized_audit_run_id:" in audit
    assert "PRIOR_SANITIZED_AUDIT_RUN_ID: ${{ inputs.prior_sanitized_audit_run_id }}" in audit
    assert 'if [[ ! "$PRIOR_SANITIZED_AUDIT_RUN_ID" =~ ^[0-9]{1,20}$ ]]' in audit
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in audit
    assert "evidenceops-sanitized-mission-${{ inputs.prior_sanitized_audit_run_id }}" in audit
    assert "run-id: ${{ inputs.prior_sanitized_audit_run_id }}" in audit
    assert "path: build/previous-public" in audit
    assert "find build/previous-public -mindepth 1 -print" in audit
    assert "python scripts/check_public_artifacts.py build/previous-public" in audit
    assert '--destination "$RUNNER_TEMP/evidenceops-previous-public.json"' in audit
    assert 'publication_args+=(--previous-public "$PREVIOUS_PUBLIC_PATH")' in audit
    assert "find build/previous-public -type f -delete" in audit
    assert "evidenceops-previous-public.json' -delete" in audit
    assert "previous-private" not in audit
    assert "prior-private" not in audit
    for trusted_run_property in (
        '.name == "Read-only Intune audit"',
        '.path == ".github/workflows/intune-audit.yml"',
        '.event == "workflow_dispatch"',
        '.head_branch == "main"',
        '.status == "completed"',
        '.conclusion == "success"',
    ):
        assert trusted_run_property in audit
    assert audit.index("Verify prior audit run provenance") < audit.index(
        "Download prior sanitized Mission package"
    )
    assert audit.index("Revalidate prior live Mission package") < audit.index(
        "Authenticate to Microsoft Entra through GitHub OIDC"
    )


def test_worker_static_assets_and_modes_are_explicit() -> None:
    source = (REPOSITORY_ROOT / "wrangler.jsonc").read_text(encoding="utf-8")
    configuration = json.loads(re.sub(r",(?=\s*[}\]])", "", source))
    assert configuration["assets"] == {
        "directory": "./site",
        "binding": "ASSETS",
        "html_handling": "auto-trailing-slash",
        "not_found_handling": "404-page",
        "run_worker_first": ["/api/*"],
    }
    assert configuration["workers_dev"] is False
    assert configuration["vars"]["EVIDENCEOPS_MODE"] == "fixture"
    assert configuration["env"]["preview"]["vars"]["EVIDENCEOPS_MODE"] == "fixture"
    production = configuration["env"]["production"]
    assert production["workers_dev"] is False
    assert production["vars"]["EVIDENCEOPS_MODE"] == "openai"
    assert production["secrets"]["required"] == ["OPENAI_API_KEY"]
    assert "routes" not in production
    assert "route" not in production


def test_worker_toolchain_is_exact_pinned_and_private() -> None:
    package = json.loads((REPOSITORY_ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["private"] is True
    for version in package["devDependencies"].values():
        assert version[0].isdigit()
        assert not any(marker in version for marker in ("^", "~", "*", ">", "<"))


def test_browser_boundary_uses_session_only_history_and_does_not_accept_byok() -> None:
    browser = (REPOSITORY_ROOT / "docs/assets/javascripts/provifact-api.js").read_text(
        encoding="utf-8"
    )
    assistant_browser = (
        REPOSITORY_ROOT / "docs/assets/javascripts/assistant-evidence-context.js"
    ).read_text(encoding="utf-8")
    router = (REPOSITORY_ROOT / "worker/src/security.ts").read_text(encoding="utf-8")
    for prohibited in ("localStorage", "sessionStorage", "innerHTML", "X-OpenAI-Key"):
        assert prohibited not in browser
    for prohibited in ("localStorage", "innerHTML", "X-OpenAI-Key", "Authorization"):
        assert prohibited not in assistant_browser
    assert 'const HISTORY_KEY = "provifact-assistant-history-v1"' in assistant_browser
    assert "sessionStorage.getItem(HISTORY_KEY)" in assistant_browser
    assert "sessionStorage.setItem(" in assistant_browser
    assert 'request.headers.has("X-OpenAI-Key")' in router
    assert 'request.headers.has("Authorization")' in router
    verifier_gate = assistant_browser.index('"typed_claims_verified", "insufficient_evidence"')
    answer_render = assistant_browser.index("payload.answer.direct_answer,")
    assert verifier_gate < answer_render


def test_static_asset_headers_set_core_browser_controls() -> None:
    headers = (REPOSITORY_ROOT / "docs/_headers").read_text(encoding="utf-8")
    for expected in (
        "Content-Security-Policy:",
        "frame-ancestors 'none'",
        "Permissions-Policy:",
        "Referrer-Policy: no-referrer",
        "Strict-Transport-Security: max-age=31536000",
        "X-Content-Type-Options: nosniff",
        "X-Frame-Options: DENY",
    ):
        assert expected in headers
    mission_rule = headers.index("/assets/data/mission-control.json")
    asset_rule = headers.index("/assets/*")
    assert "! Cache-Control" in headers[mission_rule:asset_rule]
    assert "Cache-Control: no-store" in headers[mission_rule:asset_rule]
    api_rule = headers.index("/api/*")
    assert "Cache-Control: no-store" in headers[api_rule:mission_rule]
    worker_security = (REPOSITORY_ROOT / "worker" / "src" / "security.ts").read_text(
        encoding="utf-8"
    )
    assert 'headers.set("Cache-Control", "no-store")' in worker_security


def test_mission_control_bounds_grid_content_on_narrow_viewports() -> None:
    stylesheet = (REPOSITORY_ROOT / "docs" / "assets" / "stylesheets" / "extra.css").read_text(
        encoding="utf-8"
    )
    assert ".mission-shell > *," in stylesheet
    assert ".mission-summary-grid > *" in stylesheet
    assert "min-width: 0;" in stylesheet
    assert ".mission-table-wrap {\n  overflow-x: auto;" in stylesheet
    mkdocs = (REPOSITORY_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "assets/stylesheets/extra.css?v=20260720-provifact2" in mkdocs
    assert "assets/javascripts/mission-control.js?v=20260720-provifact2" in mkdocs
    assert "assets/javascripts/assistant-evidence-context.js?v=20260720-provifact2" in mkdocs


def test_mission_control_links_to_loaded_reference_profile_comparisons() -> None:
    dashboard = (REPOSITORY_ROOT / "docs" / "evidence-dashboard.md").read_text(encoding="utf-8")
    script = (REPOSITORY_ROOT / "docs" / "assets" / "javascripts" / "mission-control.js").read_text(
        encoding="utf-8"
    )
    stylesheet = (REPOSITORY_ROOT / "docs" / "assets" / "stylesheets" / "extra.css").read_text(
        encoding="utf-8"
    )
    for required in (
        "data-baseline-view",
        "Compare with DISA STIG →",
        "Compare with CIS Level 2 →",
        "data-collection-pipeline",
        "data-posture-rows",
        "data-planning-groups",
        "TMCO Consulting Approved · full implementation plan",
        "TMCO Consulting Approved · evaluated rules only",
        "No Intune writes",
    ):
        assert required in dashboard
    assert '"disa_stig"' in script
    assert '"cis_lvl2"' in script
    assert '"APPROVED"' in script
    assert "/settings-matrix/?profile=" in script
    assert "exact provider mappings" in script
    assert 'if (lens === "active") return true' in script
    assert 'return "Implementation planning required"' in script
    assert 'return "Provider mapping review required"' in script
    assert 'const synthetic = mission.data_mode.startsWith("SYNTHETIC")' in script
    assert "reproducible fixed-time fixture" in script
    assert "body:has(.mission-shell) .md-header" in stylesheet
    assert ".mission-commandbar" in stylesheet
    assert ".mission-rail" in stylesheet


def test_operational_frontend_is_compact_and_keyboard_accessible() -> None:
    matrix = (REPOSITORY_ROOT / "docs" / "assets" / "javascripts" / "settings-matrix.js").read_text(
        encoding="utf-8"
    )
    matrix_css = (
        REPOSITORY_ROOT / "docs" / "assets" / "stylesheets" / "settings-matrix.css"
    ).read_text(encoding="utf-8")
    assistant = (
        REPOSITORY_ROOT / "docs" / "assets" / "javascripts" / "assistant-evidence-context.js"
    ).read_text(encoding="utf-8")
    assistant_css = (
        REPOSITORY_ROOT / "docs" / "assets" / "stylesheets" / "assistant-evidence-context.css"
    ).read_text(encoding="utf-8")
    for heading in (
        '"Setting"',
        '"Observed → target"',
        '"State"',
        '"Assignment"',
        '"Frameworks"',
        '"Action"',
    ):
        assert heading in matrix
    assert "table-layout: fixed" in matrix_css
    assert "min-width: 0" in matrix_css
    assert "dialog.showModal()" in matrix
    assert 'launcher.setAttribute("aria-haspopup", "dialog")' in assistant
    assert "if (!dialog.open) dialog.showModal()" in assistant
    assert "input.focus()" in assistant
    assert "launcher.focus()" in assistant
    assert "validateAssistantPayload" in assistant
    assert "canonicalJson" in assistant
    assert "typed_claims_rejected.length !== 0" in assistant
    assert "Ask the evidence, not the tenant" in assistant
    assert "grid-template-areas:" in assistant_css
    assert '"suggestions"' in assistant_css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in assistant_css
    assert "scroll-snap-type: x proximity" in assistant_css
    assert "@media (max-width: 52rem)" in assistant_css
    assert "@media (max-width: 35rem)" in assistant_css


def test_public_brand_uses_original_mark_and_provifact_assistant() -> None:
    mkdocs = (REPOSITORY_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    dashboard = (REPOSITORY_ROOT / "docs" / "evidence-dashboard.md").read_text(encoding="utf-8")
    assistant = (
        REPOSITORY_ROOT / "docs" / "assets" / "javascripts" / "assistant-evidence-context.js"
    ).read_text(encoding="utf-8")
    logo = REPOSITORY_ROOT / "docs" / "assets" / "images" / "provifact-mark.svg"

    assert "logo: assets/images/provifact-mark.svg" in mkdocs
    assert "favicon: assets/images/provifact-mark.svg" in mkdocs
    assert 'class="mission-brand-mark"' in dashboard
    assert "PV</span>" not in dashboard
    assert "Ask Provifact Assistant" in dashboard
    assert "Provifact Assistant" in assistant
    assert "Copilot" not in assistant
    assert logo.is_file()


def test_baseline_plan_shows_all_rules_by_default_without_false_findings() -> None:
    page = (REPOSITORY_ROOT / "docs" / "settings-matrix.md").read_text(encoding="utf-8")
    matrix = (REPOSITORY_ROOT / "docs" / "assets" / "javascripts" / "settings-matrix.js").read_text(
        encoding="utf-8"
    )
    assert "data-matrix-mapped-only>" in page
    assert "data-matrix-mapped-only checked" not in page
    assert "Limit to deterministically evaluated rules" in page
    assert "TMCO Consulting-approved rules" in matrix
    assert "Implementation backlog" in matrix
    assert "Provider mapping review required" in matrix
    assert "Implementation planning required" in matrix
    assert "mappedOnly.checked = false" in matrix
    assert "Target pending approved mapping" in matrix
    assert "a backlog state—not a failed control" in page


def test_public_navigation_prioritizes_judge_path_and_current_evidence() -> None:
    mkdocs = (REPOSITORY_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    judge = (REPOSITORY_ROOT / "docs" / "judge-guide.md").read_text(encoding="utf-8")
    assert "- Mission Control: evidence-dashboard.md" in mkdocs
    assert "- Baseline Plan: settings-matrix.md" in mkdocs
    assert "- Judge Guide: judge-guide.md" in mkdocs
    assert "Current Judge-Readiness Validation: build-week/judge-readiness-validation.md" in mkdocs
    assert "Final Implementation Report: build-week/final-implementation-report.md" not in mkdocs
    assert "Phase 1 Validation: build-week/phase-1-validation.md" not in mkdocs
    assert "Worker Validation: build-week/cloudflare-worker-validation.md" not in mkdocs
    assert "a backlog state" in judge or "not mislabeled as a failed control" in judge
    assert "not a statement of any competition's judging rules" in judge
