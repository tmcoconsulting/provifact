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
- `c328e4b` — green responsive-head validation record
- `3cd611d` — assistant, audit-reporting, and device-code review fixes
- `0220b2c` — fail-closed duplicate public-artifact filename detection

TJ reviewed PR #2 through `0220b2cf19a5dd019f1d18f90a2e45acc99242df`. PR #2 was squash-merged
through protected `main` as `7d7f8bca0ac7b652e515a360755b534af99c0b46`. The follow-up live
publication fix described below is a separate human-review gate.

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
- One bounded synthetic request reached fixed `gpt-5.6-terra`, returned HTTP success, accepted two
  deterministic typed claims with none rejected, and kept generated prose quarantined. Production
  was immediately returned to fixture mode.

### Microsoft Entra

- Existing GitHub production-environment federated credential remains present; no client secret
  exists.
- Application permissions independently re-read as granted: configuration read, managed-device
  read, managed-app read, and service-configuration read.
- Eight pre-existing delegated permissions remain unchanged; the application-only workflow does
  not use them.
- The protected post-merge audit acquired an application token through OIDC and completed GET-only
  collection. Publication failed closed before producing public evidence, and cleanup completed.
  No Intune write occurred.

### Cloudflare and GitHub

- Production Worker secret name `OPENAI_API_KEY` is present.
- Protected GitHub environment secret name `CLOUDFLARE_API_TOKEN` is present; its value was not
  retrieved. `CLOUDFLARE_DEPLOY_ENABLED` remains `false`.
- PR #2 passed required CI and CodeQL, was reviewed by TJ, and was squash-merged through protected
  `main`.
- The reviewed static/Worker revision is deployed at the production custom domain in explicit
  fixture mode.
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

## Post-merge operational validation

The production fixture deployment returned HTTPS success for the dashboard, status, and readiness
routes with the expected CSP, HSTS, frame, MIME, referrer, permissions, and cross-origin headers.
The one authorized Terra request used only the tracked synthetic snapshot. Structured output
parsed, deterministic typed-claim verification passed, generated prose remained quarantined, and
human review remained required. The Worker was then redeployed from its reviewed configuration and
independently reported `fixture` mode.

Protected-main audit run `29700668896` proved GitHub environment-scoped OIDC, Entra token exchange,
and GET-only collection. The private normalized package was written only to the ephemeral ignored
directory. Public construction then rejected a domain-shaped value, emitted no public package, and
the always-run cleanup step succeeded. The failure was traced to the closed Graph-type fallback:
an absent `@odata.type` normalized as `microsoft.graph.unknown`, which the public domain detector
correctly refused. The follow-up changes that fallback to the non-domain taxonomy value `unknown`
and adds an end-to-end regression test. The domain detector is not relaxed.

## Outstanding gates

1. TJ reviews and merges the narrow live-publication normalization follow-up.
2. Rerun the protected-main audit once. Accept completion only if publication, public scanning,
   sanitized aggregate reporting, and ephemeral cleanup all succeed.
3. Keep the Cloudflare deployment workflow disabled until the environment token's least-privilege
   scope is independently verified.
4. Run `/feedback` in the primary Codex task and preserve the Session ID privately.

Phase 1 must not be called technically complete until the bounded model response and the protected
post-merge expanded Intune audit both succeed.
