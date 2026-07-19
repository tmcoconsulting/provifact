# Build Week Vertical-Slice Validation

**Date:** 2026-07-19

**Branch:** `codex/build-week-demo-slice`

**Data mode:** synthetic fixture

**Human review:** required

## Review commits

- `ce4522d` — comprehensive GET-only Apple/Intune collection
- `3dd8902` — pinned mSCP baseline, deterministic Mission Control, and bounded assistant
- `2d57a5f` — operating controls, demonstration package, and validation record
- `b4a042c` — anchored review and contribution records
- `c1fca86` — fail-closed health/readiness contracts and repository-controlled HSTS
- `b071a89` — hardened PR checkpoint validation record
- `1c057c7` — non-executing Python and JavaScript/TypeScript CodeQL analysis
- `b58db77` — preview and CodeQL evidence record
- `73d6b2b` — browser-proven responsive Mission Control containment
- `214f1bf` — responsive desktop/mobile browser evidence record

These commits and this validation-record update remain pending TJ's review in PR #2. No commit in
the PR uses a `Human-Reviewed` trailer.

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
- Separate `/api/health` liveness, fingerprint-validating `/api/ready`, Mission-derived status, and
  repository-controlled HSTS/CSP/API response headers.

## Commands and results

```text
.venv/bin/python -m ruff format --check .
  PASS — 51 files formatted

.venv/bin/python -m ruff check .
  PASS

.venv/bin/python -m mypy
  PASS — no issues in 51 source files

.venv/bin/python -m pytest
  PASS — 188 passed, 1 skipped, 91.13% branch-aware coverage

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
  PASS — 43 workerd contract tests

.venv/bin/python -m evidenceops rebuild-static-demo (twice)
  PASS — complete docs/assets/data SHA-256 lists identical

.venv/bin/mkdocs build --strict
  PASS — 81-file static artifact in a clean temporary output directory

.venv/bin/python scripts/check_public_artifacts.py site
  PASS

npm run worker:dry-run
npm run worker:dry-run:preview
npm run worker:dry-run:production
  PASS — 115 static-asset entries, 88.54 KiB upload / 19.04 KiB gzip, no deployment

git diff --check
  PASS
```

The opt-in live Intune test remains the one skipped Python test. The Worker suite passed after the
assistant, sanitized 429-classification, health/readiness, Mission-status, and security-header code
changed.

GitHub Actions CI run `29699786745` completed successfully for PR #2 head
`214f1bfc7e0d18efab2eb9339892a90e9b8baa70`, including installation from both locks, Python tests,
Worker tests, dependency audits, secret/public scans, strict documentation build, and all Wrangler
dry-runs. CodeQL run `29699786705` completed successfully for both Python and
JavaScript/TypeScript, and GitHub's separate aggregate CodeQL check also passed. The PR remained
mergeable.

The follow-up responsive fix at `73d6b2b` completed the same full local matrix with 188 passing
Python tests, one credential-gated live test skipped, 91.13% branch coverage, and 43 passing Worker
tests. Both exact-lock dependency audits, Bandit, the repository/public scanners, strict docs build,
generated bindings, and all three Wrangler dry-runs passed.

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
- PR #2 is pushed, mergeable, ready for TJ review, and has a successful required CI run.
- The existing production custom domain and fixture deployment were not changed in this milestone.
- The authenticated Cloudflare session was reverified and the scanned fixture assets from PR head
  `1c057c7` were deployed only to the credential-free preview Worker. `/`, `/api/health`,
  `/api/ready`, `/api/status`, and fixture `/api/ask` returned HTTPS success. Readiness verified the
  Mission fingerprint, the API reported synthetic fixture mode, the assistant performed no model
  call, typed claims verified, generated prose remained quarantined, and human review remained
  required. Production, DNS, the custom domain, and secrets were not changed.
- The browser control policy blocked local-loopback visual inspection. Static build, Workerd tests,
  and artifact scans passed at the earlier checkpoint.
- A later authenticated real-browser pass exercised the deployed preview at desktop and mobile
  breakpoints. Desktop rendering, high-severity filtering, the FileVault traceability dialog,
  fixture-assistant readiness, and console-error checks passed. The first 375-pixel mobile pass
  exposed page-level horizontal overflow; `73d6b2b` added grid-child containment and a versioned
  stylesheet reference. After redeploying only the preview, the document and viewport were both
  375 pixels wide with no page-level overflow, while the 1,040-pixel drift table remained contained
  in its 341-pixel horizontal-scroll wrapper. Mobile rendering and both browser consoles then
  passed. Production remained unchanged.

## Outstanding gates

1. TJ reviews every commit and the complete PR #2 diff through the current head.
2. After review, deploy the fixture revision to production and recheck the public custom domain,
   TLS, headers, desktop, and mobile views. Keep the protected deployment workflow disabled until
   the environment token's least-privilege Cloudflare scope is independently verified.
3. Make at most one bounded synthetic `gpt-5.6-terra` request; accept it only if structured output,
   references, typed claims, content scan, and prose quarantine pass. Return production to fixture
   mode afterward.
4. Merge reviewed code through the protected branch, then manually run the trusted-main Intune
   audit. Retain only sanitized counts and delete ephemeral evidence.
5. Run `/feedback` in the primary Codex task and preserve the Session ID privately.

Phase 1 must not be called technically complete until the bounded model response and the protected
post-merge expanded Intune audit both succeed.
