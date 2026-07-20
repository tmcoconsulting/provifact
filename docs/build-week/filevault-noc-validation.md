# FileVault normalization and Mission Control validation

Date: 2026-07-20

Branch: `codex/intune-filevault-noc-dashboard`

Review state: pending human review

## Problem reproduced

The last sanitized production package reported Settings Catalog as incomplete even though an
assigned FileVault policy exists in the private tenant. No tenant policy name, identifier,
assignment target, or configured value is recorded here.

The defect had two independent causes:

1. the adapter treated a Settings Catalog group-collection parent as the configured setting and did
   not walk its documented child instances; and
2. an explicitly known non-Apple policy was counted as an Apple provider failure, which made the
   entire Settings Catalog slice incomplete.

Microsoft's public FileVault reference confirms that `com.apple.mcx.filevault2_enable` is a nested
choice child with the closed `com.apple.mcx.filevault2_enable_0` token. The implementation now
flattens documented, bounded group/choice/simple containers, retains exact child definition IDs,
and filters well-formed known non-Apple policies from the Apple slice. Unknown platforms and value
shapes still fail closed.

## Dashboard boundary

Mission Control is now a full-width operational console showing desired state, observed state,
deterministic findings, evidence counts, freshness, collection flow, blind spots, and the
private-to-public boundary. The STIG selector is a technical cross-reference lens only. It visibly
states that a STIG baseline is not loaded and produces no STIG score, assessment, or compliance
verdict.

## Local validation

```text
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy
  PASS — 60 files formatted; lint clean; no issues in 60 source files

.venv/bin/python -m pytest
  PASS — 232 passed, 1 credential-gated live test skipped, 90.01% branch coverage

.venv/bin/python -m bandit -r evidenceops scripts -c pyproject.toml
.venv/bin/python scripts/check_secrets.py
.venv/bin/python -m pip_audit -r requirements-dev.txt
  PASS — no findings, prohibited credentials, or known Python vulnerabilities

npm ci --ignore-scripts --no-audit --no-fund
npm audit --audit-level=moderate
npm run format:check
npm run lint:worker
npm run typecheck:worker
npm run test:worker
npm run worker:types:check
npm run worker:dry-run
npm run worker:dry-run:preview
npm run worker:dry-run:production
  PASS — exact lock, 0 vulnerabilities, 54 Worker tests, generated bindings, and all dry-runs

.venv/bin/python -m evidenceops run-mission-demo --output-dir <temporary-a>
.venv/bin/python -m evidenceops run-mission-demo --output-dir <temporary-b>
diff -qr <temporary-a> <temporary-b>
.venv/bin/python -m evidenceops rebuild-static-demo
.venv/bin/mkdocs build --strict
.venv/bin/python scripts/check_public_artifacts.py site
git diff --check
  PASS — deterministic outputs identical, strict site build, public scan, and patch whitespace
```

The local dashboard was also exercised in the browser. Its STIG lens, desired/observed table,
navigation, and generated sections rendered without browser console warnings or errors.

## Deferred live verification

No Microsoft Graph request, Intune write, OpenAI request, Cloudflare deployment, or production
mutation was made from this feature branch. After human review and protected merge, one manual
read-only audit must confirm that the nested FileVault setting joins by exact provider definition ID
and that the false Settings Catalog completeness gap is absent. Only sanitized counts and status may
be retained.

## Authoritative sources

- Microsoft Graph
  [`deviceManagementConfigurationSetting`](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfigv2-devicemanagementconfigurationsetting?view=graph-rest-beta)
- Microsoft Graph
  [`deviceManagementConfigurationGroupSettingCollectionInstance`](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfigv2-devicemanagementconfigurationgroupsettingcollectioninstance?view=graph-rest-beta)
- Microsoft's public
  [`intune-my-macs` FileVault policy](https://github.com/microsoft/intune-my-macs/blob/main/macOS/configurations/intune/pol-sec-001-filevault.json)
