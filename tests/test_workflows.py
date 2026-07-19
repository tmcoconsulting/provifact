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
    assert "environment: production" in audit
    assert "if: github.ref == 'refs/heads/main'" in audit
    assert "ref: main" in audit
    assert "DeviceManagementConfiguration.Read.All" not in audit
    assert "--auth environment-token" in audit
    assert "store_private" not in audit
    assert "python -m pytest -o addopts=''" in audit

    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "python -m pytest" in ci
    assert "python -m pytest -o addopts=''" not in ci

    deploy = (WORKFLOWS / "deploy-cloudflare.yml").read_text(encoding="utf-8")
    assert "id-token: write" not in deploy
    assert "environment: production" in deploy
    assert "github.ref == 'refs/heads/main'" in deploy
    assert "CLOUDFLARE_DEPLOY_ENABLED == 'true'" in deploy
    assert "secrets.CLOUDFLARE_API_TOKEN" in deploy
    assert "npm run deploy:production" in deploy
    assert "ref: main" in deploy


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
    production = configuration["env"]["production"]
    assert production["workers_dev"] is False
    assert production["vars"]["EVIDENCEOPS_MODE"] == "fixture"
    assert production["secrets"]["required"] == ["OPENAI_API_KEY"]
    assert production["routes"] == [
        {
            "pattern": "evidenceops.tmcoconsulting.com",
            "custom_domain": True,
        }
    ]


def test_worker_toolchain_is_exact_pinned_and_private() -> None:
    package = json.loads((REPOSITORY_ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["private"] is True
    for version in package["devDependencies"].values():
        assert version[0].isdigit()
        assert not any(marker in version for marker in ("^", "~", "*", ">", "<"))


def test_browser_boundary_does_not_store_or_accept_byok() -> None:
    browser = (REPOSITORY_ROOT / "docs/assets/javascripts/evidenceops-api.js").read_text(
        encoding="utf-8"
    )
    mission_browser = (REPOSITORY_ROOT / "docs/assets/javascripts/mission-control.js").read_text(
        encoding="utf-8"
    )
    router = (REPOSITORY_ROOT / "worker/src/security.ts").read_text(encoding="utf-8")
    for prohibited in ("localStorage", "sessionStorage", "innerHTML", "X-OpenAI-Key"):
        assert prohibited not in browser
    assert 'request.headers.has("X-OpenAI-Key")' in router
    assert 'request.headers.has("Authorization")' in router
    verifier_gate = mission_browser.index('"insufficient_evidence", "typed_claims_verified"')
    answer_render = mission_browser.index('appendLine("Answer", payload.answer.direct_answer)')
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


def test_mission_control_bounds_grid_content_on_narrow_viewports() -> None:
    stylesheet = (REPOSITORY_ROOT / "docs" / "assets" / "stylesheets" / "extra.css").read_text(
        encoding="utf-8"
    )
    assert ".mission-shell > *," in stylesheet
    assert ".mission-summary-grid > *" in stylesheet
    assert "min-width: 0;" in stylesheet
    assert ".mission-table-wrap {\n  overflow-x: auto;" in stylesheet
    mkdocs = (REPOSITORY_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "assets/stylesheets/extra.css?v=20260719-responsive" in mkdocs
