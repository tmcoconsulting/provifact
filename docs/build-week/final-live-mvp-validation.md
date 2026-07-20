# Final Live MVP Validation and Production Record

**Date:** 2026-07-20

**Branch:** `codex/build-week-final-live-mvp`

**Implementation commit:** `143f694f7183f1a2ce117a3a0867aad316f7a1ae`

**Primary merge:** PR
[#10](https://github.com/tmcoconsulting/evidenceops/pull/10),
`d71da96b6b3770e96b3b7e715a51ca5b602ef852`

**Promotion-safety fix:** PR
[#11](https://github.com/tmcoconsulting/evidenceops/pull/11),
`1662cd1b631bfa3051eac071f442f70a48ca9b68`

**Human review:** final submission review remains TJ Olnhausen's responsibility

## Validated scope

- Exact reviewed Microsoft Intune provider-definition mappings; no display-name or substring join
- Mission schema `2.1.0`, public-safe parent references, and current/prior live snapshot comparison
- Live-artifact-only production workflow with exact audit-run and snapshot provenance
- Action-first Mission Control, compact Settings detail, global provenance, and snapshot refresh
- Site-wide bounded Provifact Assistant with production `gpt-5.6-terra` and local/preview fixture mode
- Official owner-approved TMCO Consulting assets and standalone-company-name content gate
- Preserved GET-only Graph provider, fail-closed publication, deterministic authority, and no BYOK

## Clean environment

A new Python 3.14.6 virtual environment was created outside the repository. Exact locked
dependencies installed from `requirements-dev.txt`; the package installed with
`--no-build-isolation --no-deps`; `pip check` reported no broken requirements. Public CI remains
pinned to Python 3.12.

## Commands and results

```text
python -m ruff format --check .
  PASS — 60 files formatted
python -m ruff check .
  PASS
python -m mypy
  PASS — no issues in 60 source files
python -m pytest
  PASS — 228 passed, 1 skipped, 90.62% branch coverage
python -m bandit -r evidenceops scripts -c pyproject.toml
  PASS — no findings; 6,255 source lines scanned
python scripts/check_company_name.py
  PASS
python scripts/check_secrets.py
  PASS
python -m pip_audit -r requirements-dev.txt
  PASS — no known vulnerabilities
npm ci --ignore-scripts --no-audit --no-fund
  PASS — 89 exact-locked packages installed
npm audit --audit-level=moderate
  PASS — 0 vulnerabilities
npm run validate:worker
  PASS — Prettier, Oxlint, strict TypeScript, 54 Worker tests, generated bindings,
  and root/preview/production Wrangler dry-runs
python -m evidenceops run-mission-demo --output-dir <temporary-a>
python -m evidenceops run-mission-demo --output-dir <temporary-b>
diff -qr <temporary-a> <temporary-b>
  PASS — deterministic outputs identical
python -m evidenceops rebuild-static-demo
  PASS
mkdocs build --strict
  PASS — 128 static assets in the final production dry-run
python scripts/check_public_artifacts.py site
  PASS
npm run worker:dry-run:production
  PASS — production mode openai; model gpt-5.6-terra; no deployment
git diff --check
  PASS
```

The one skipped test is the opt-in live Microsoft Intune integration test. The protected audit may
run only after reviewed code reaches `main`; feature-branch execution is intentionally prohibited.

## Security review facts

- Provider-source inspection found no POST, PUT, PATCH, DELETE, create, update, apply, or remediation
  operation.
- Production deployment has no synthetic builder or optional artifact path.
- Public CI has no Microsoft, OpenAI, or Cloudflare credential.
- The GitHub production deployment window was independently re-read as disabled after validation.
- The staged repository/public scans found no credential, private evidence, or tenant-derived data.
- The tracked Mission package remains explicitly synthetic; production must replace it in-memory in
  the trusted workflow with one reviewed live sanitized artifact before building.

## Post-merge operational verification

The protected-main GET-only audit and Cloudflare deployment were completed only after the primary
PR passed CI and CodeQL and was squash-merged. The first production attempt, run `29757719909`,
stopped before Cloudflare when a Worker test proved dependent on the generated synthetic JSON
module's inferred scalar types. The deployment enable variable was restored to `false`. PR #11
made those assertions promotion-safe; its CI and CodeQL checks passed before merge.

### Live collection and publication

- Audit run [`29757456114`](https://github.com/tmcoconsulting/evidenceops/actions/runs/29757456114)
  passed GitHub OIDC authentication, GET-only collection, fail-closed sanitization, public scanning,
  one-file artifact upload, and ephemeral cleanup.
- Deployment run
  [`29758740795`](https://github.com/tmcoconsulting/evidenceops/actions/runs/29758740795)
  deployed its exact reviewed snapshot `mission-283e1b9be457b76d104a0e8a`.
- One bounded production request reached fixed `gpt-5.6-terra` for that sanitized snapshot. It
  returned HTTP 200; the deterministic verifier accepted four typed claims, rejected none, kept
  generated prose quarantined, and required human review. No retry was made and no narrative prose
  was retained in this record.
- Audit run [`29759424410`](https://github.com/tmcoconsulting/evidenceops/actions/runs/29759424410)
  then revalidated run `29757456114` as its prior public snapshot before OIDC authentication. It
  passed collection, sanitization, comparison, scanning, artifact upload, and cleanup.
- Deployment run
  [`29759572945`](https://github.com/tmcoconsulting/evidenceops/actions/runs/29759572945)
  deployed the exact comparison snapshot `mission-2626272a6ea65343eee5302c`, collected
  `2026-07-20T16:24:36Z`. The snapshot-tagged Cloudflare version serves 100% of production traffic;
  its UUID is retained in the private operator report rather than the public site.

The final package is `LIVE SANITIZED TENANT DATA`, records
`mission-283e1b9be457b76d104a0e8a` as its prior snapshot, and reports zero changed, new, or resolved
findings because no Intune setting was changed between collections. The reviewed denominator is
four settings; all four remain honest collection gaps. Thirteen policies were evaluated, five
collection gaps were recorded overall, and no raw or private evidence was retained. Unknown
provider settings were not described as missing.

### Production checks

The following public URLs returned HTTP 200 with successful TLS verification:

- `https://evidenceops.tmcoconsulting.com/`
- `https://evidenceops.tmcoconsulting.com/evidence-dashboard/`
- `https://evidenceops.tmcoconsulting.com/settings-matrix/`
- `https://evidenceops.tmcoconsulting.com/api/status`
- `https://evidenceops.tmcoconsulting.com/api/ready`
- `https://evidenceops.tmcoconsulting.com/assets/data/mission-control.json`

The final `/api/status` reports `openai`, `gpt-5.6-terra`, model-call availability, live sanitized
data, and exact snapshot `mission-2626272a6ea65343eee5302c`. API GET responses use `no-store` and
include HSTS, a deny-by-default CSP, same-origin isolation, no-sniff, referrer, permissions, and
frame-denial headers. HEAD is rejected by the method allowlist.

Authenticated browser checks verified global provenance, action-first Mission Control, the compact
settings matrix, exact FileVault mapping detail, the published-snapshot refresh control, the
site-wide Assistant drawer, accessible controls, and a 390-by-844 responsive drawer without
page overflow. Browser logs contained no warnings or errors. No private identifier or synthetic
tenant posture was visible.

The production deployment gate was independently re-read as `false` after each deployment. The
Cloudflare secret list exposes only the name `OPENAI_API_KEY` with type `secret_text`; its value was
never retrieved. The provider remains GET-only and no Intune object was changed.

## Remaining manual demonstration step

The live current/prior comparison is operational, and automated tests prove new and resolved drift
representation. A visible resolved live finding still requires TJ to make the separately authorized
manual Intune change. The lowest-risk reviewed path is a dedicated test-Mac Settings Catalog policy
for exact provider ID `com.apple.screensaver.user_idleTime`: collect an assigned value greater than
the approved 900-second maximum as snapshot A, manually set it to 900 seconds or lower, then run
audit B with A's sanitized audit run ID as `prior_sanitized_audit_run_id`. Provifact must remain
read-only throughout and may call the result resolved only after audit B observes it.
