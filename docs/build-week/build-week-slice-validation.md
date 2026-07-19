# Build Week Vertical-Slice Validation

**Date:** 2026-07-19

**Branch:** `codex/build-week-demo-slice`

**Data mode:** synthetic fixture

**Human review:** required

## Implemented and locally verified

- Comprehensive GET-only Apple/Intune resource-family provider with pagination, bounded
  concurrency, retry/jitter, timeout, per-endpoint status, and partial collection gaps.
- Exact four-permission read-only manifest with one isolated Settings Catalog beta dependency.
- Pinned mSCP revision `11b5896e4f12f43410686024f543792742562c91`.
- Source profile SHA-256
  `af9ef14ca568f17d3663e6e508c1f75971596fe43c6f185af27ca43451c240d2`.
- Extracted 98-rule inventory SHA-256
  `5cced0709c90885ede600f00a640a35b0679aed933cda456db80ee629ee54d41`.
- Machine-readable TMCO demo approval anchored to baseline milestone commit
  `3dd8902a609c6be177cdc913c731fbd378f075a4`.
- Strict private normalized package, allowlisted public Mission package, and public/model scans.
- Deterministic value, maximum, assignment, conflict, missing, gap, unsupported, and human-review
  behavior. Maximum evaluation is inclusive and tested below/equal/above plus invalid/incomparable.
- Dynamic Mission Control package, dashboard, previous/current change summary, and synthetic
  Mac/iPhone/iPad/application/service-health fixture.
- Same-origin `/api/ask` with closed intent classification, bounded server-side evidence
  prefiltering, strict structured output, exact typed claims, reference verification, and prose
  quarantine.

## Commands and results

```text
.venv/bin/python -m ruff format --check .
  PASS — 51 files formatted

.venv/bin/python -m ruff check .
  PASS

.venv/bin/python -m mypy
  PASS — no issues in 51 source files

.venv/bin/python -m pytest
  PASS — 187 passed, 1 skipped, 91.13% branch-aware coverage

.venv/bin/python -m bandit -r evidenceops scripts -c pyproject.toml
  PASS — no findings after classifying one synthetic service-health label

.venv/bin/python scripts/check_secrets.py
  PASS

.venv/bin/python -m pip_audit -r requirements-dev.txt
  PASS — no known vulnerabilities

npm ci --ignore-scripts --no-audit --no-fund
  PASS — 89 exact-lock packages installed

npm audit --audit-level=moderate
  PASS — 0 vulnerabilities

npm run format:check
npm run lint:worker
npm run typecheck:worker
npm run worker:types:check
  PASS

npm run test:worker
  PASS — 41 workerd contract tests

.venv/bin/python -m evidenceops rebuild-static-demo (twice)
  PASS — complete docs/assets/data SHA-256 lists identical

.venv/bin/mkdocs build --strict
  PASS — 81-file static artifact in a clean temporary output directory

.venv/bin/python scripts/check_public_artifacts.py site
  PASS

npm run worker:dry-run
npm run worker:dry-run:preview
npm run worker:dry-run:production
  PASS — 115 static-asset entries, 86.70 KiB upload / 18.77 KiB gzip, no deployment

git diff --check
  PASS
```

The opt-in live Intune test remains the one skipped Python test. The Worker suite was completed
after the assistant and sanitized 429-classification code changed. A later attempt to repeat its
local loopback run after `npm ci` was blocked by the execution environment's usage gate; the locked
dependencies and Worker sources were unchanged, and all non-loopback Worker checks passed again.

## External control-plane verification

### OpenAI

- Exact project: EvidenceOps.
- Dedicated service account: `evidenceops-cloudflare-production`.
- Only active project key belongs to that service account; Cloudflare lists `OPENAI_API_KEY` as an
  encrypted production secret. No value was retrieved or printed.
- Service account is assigned only the custom `evidenceops-responses-runtime` role, which grants
  Responses API model capability and no project administration, key management, files, assistants,
  threads, evals, fine-tuning, or vector stores.
- Allowed model: only `gpt-5.6-terra`.
- Model limits: 5 RPM and 25,000 TPM.
- Monthly project budget: `$5` soft threshold with 50%, 80%, and 100% alerts. It is not a hard cap.
- A bounded live response has not yet been accepted; public production remains fixture mode.

### Microsoft Entra

- Existing GitHub production-environment federated credential remains present; no client secret
  exists.
- Application permissions independently re-read as granted: configuration read, managed-device
  read, managed-app read, and service-configuration read.
- Eight pre-existing delegated permissions remain unchanged; the application-only workflow does
  not use them.
- No Microsoft Graph request or Intune write occurred on this branch.

### Cloudflare and GitHub

- Production Worker secret name `OPENAI_API_KEY` is present.
- Protected GitHub environment secret name `CLOUDFLARE_API_TOKEN` is present; its value was not
  retrieved. `CLOUDFLARE_DEPLOY_ENABLED` remains `false`.
- The existing production custom domain and fixture deployment were not changed in this milestone.
- Local Wrangler dry-runs passed. The interactive Wrangler control-plane login had expired, so the
  new assets could not be previewed or deployed from this session without a fresh operator login.
- The browser control policy blocked local-loopback visual inspection. Static build, Workerd tests,
  and artifact scans passed, but desktop/mobile visual QA of this exact revision remains manual.

## Outstanding gates

1. TJ reviews the new commits and pull-request diff.
2. Refresh the local Wrangler login or validate the protected deployment token, deploy the fixture
   revision, and recheck the public custom domain, TLS, headers, desktop, and mobile views.
3. Make at most one bounded synthetic `gpt-5.6-terra` request; accept it only if structured output,
   references, typed claims, content scan, and prose quarantine pass. Return production to fixture
   mode afterward.
4. Merge reviewed code through the protected branch, then manually run the trusted-main Intune
   audit. Retain only sanitized counts and delete ephemeral evidence.
5. Run `/feedback` in the primary Codex task and preserve the Session ID privately.

Phase 1 must not be called technically complete until the bounded model response and the protected
post-merge expanded Intune audit both succeed.
