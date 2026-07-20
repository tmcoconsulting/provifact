# Build Week Vertical-Slice Validation

> **Historical checkpoint.** This record preserves the 2026-07-19 slice. Final provider mappings,
> runtime mode, current snapshot, and deployment state are reported by current product documentation
> and the deployed API.

**Date:** 2026-07-19

**Branches:** `codex/build-week-demo-slice`, `codex/live-publication-handoff`, and
`codex/phase1-finalization`

**Data modes:** tracked synthetic fixture; deployed reviewed live sanitized projection

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
- `b966cd0` — reviewed sanitized-publication handoff squash merge
- `aa9c8fa` — routine deployment isolated from custom-domain management; review required
- `3e4954d` — reviewed routine-deployment isolation squash merge
- `18b94c3` — Bot-Fight-safe active-version proof; review required

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
- Machine-readable TMCO Consulting demo approval anchored to baseline milestone commit
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

- Exact project: Provifact.
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

TJ reviewed that follow-up through `f21636066d7348f3ff8f86bffa4ae01485de5bba`; PR #3 was
squash-merged as `0f6f3b4fc8897528a5d66383802f578e87dbfd4e`. The one authorized retry,
protected-main run `29701160503`, then completed Entra OIDC authentication, the expanded GET-only
collection, fail-closed Mission publication, the complete public-artifact scan, aggregate summary,
and cleanup. The run succeeded with zero retained artifacts. No tenant names, identifiers,
configuration values, raw Graph responses, or pseudonym key are included in this validation
record.

## Sanitized-publication handoff checkpoint

The unreviewed follow-up keeps the default audit non-retaining and adds a second explicit input for
preparing one scanned public package. The package receives one-day retention, a run-ID-bound name,
and no private sibling files. The deployment workflow downloads only that exact artifact from this
repository, then repeats schema/fingerprint validation, strict nested field classification, secret
and public-content scanning, full site build, Worker validation, deployment, and runtime mode
verification. Both workflows remain trusted-main and `production`-environment only; deployment is
still disabled while `CLOUDFLARE_DEPLOY_ENABLED=false`.

Validation on the pending branch:

```text
temporary Python 3.14 virtual environment + requirements-dev.txt + project wheel
  PASS — exact lock installed independently

.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy
  PASS — 55 files formatted; lint clean; no issues in 55 typed files

.venv/bin/python -m pytest
  PASS — 201 passed, 1 credential-gated live test skipped, 91.16% branch coverage

.venv/bin/python -m bandit -r evidenceops scripts -c pyproject.toml
.venv/bin/python scripts/check_secrets.py
.venv/bin/python -m pip_audit -r requirements-dev.txt
  PASS — no findings, prohibited credentials, or known Python vulnerabilities

npm ci --ignore-scripts --no-audit --no-fund
npm audit --audit-level=moderate
npm run validate:worker
  PASS — exact lock, 0 vulnerabilities, 43 Worker tests, generated bindings, and all three dry-runs

.venv/bin/python -m evidenceops rebuild-static-demo (twice)
.venv/bin/mkdocs build --strict
.venv/bin/python scripts/check_public_artifacts.py site
git diff --check
  PASS — identical generated-data hashes, 81-file static site, public scan, and patch whitespace
```

The only skipped test is the local credential-gated Intune test. No feature-branch Graph request,
OpenAI request, Cloudflare deployment, or production mutation occurred while validating this
checkpoint.

## Reviewed live-publication evidence

PR #4 was separately reviewed and squash-merged as
`b966cd0a5b20580b046c6ed3bb31057f7682bda7`. Protected-main run `29702128497` then acquired the
environment-scoped OIDC identity, used only the allowlisted Graph `GET` paths, built and scanned the
public Mission projection, and uploaded exactly one public file with one-day retention. The private
normalized package, Graph responses, access token, and pseudonym key were never uploaded and were
removed by the always-run cleanup step.

The public artifact was downloaded to an isolated temporary directory and passed the strict Mission
schema, canonical fingerprint, nested field classification, shared credential scan, and public
content scan before deployment. Only aggregate public values are recorded here:

- 98 baseline rules;
- 5 rules in the deterministic alignment denominator;
- 0 aligned and 5 drifted observations;
- 13 policy objects evaluated;
- 5 declared collection gaps;
- 94 unmapped objects; and
- no retained raw/private evidence.

Deployment run `29702213181` repeated all validation and successfully uploaded and activated the
reviewed Worker and assets. Wrangler then attempted to inspect the already-provisioned custom-domain
route because it was still declarative in the production configuration. The intentionally narrow
account token has only Workers Scripts write access, so that unnecessary post-upload inspection was
denied. This was a safe partial failure: the domain and DNS were not changed, and production status
independently matched the selected live sanitized snapshot.

The production dashboard, Mission asset, `/api/status`, fixture assistant, TLS, CSP, HSTS, frame,
MIME, referrer, permissions, cache, and cross-origin headers were revalidated. The assistant made
no model call, verified its typed claims, quarantined generated prose, and retained human review.
The temporary repository-level deployment flag used to start the diagnostic run was deleted;
`CLOUDFLARE_DEPLOY_ENABLED` remains `false` in the protected environment.

Commit `aa9c8fa` removes custom-domain/route management from routine uploads, requires explicit
manual deployment confirmation, limits the Cloudflare secret to the deploy step, and verifies the
exact expected snapshot after deployment. Its complete credential-free local matrix passed: 201
Python tests with one credential-gated live test skipped and 91.16% branch coverage; 43 Worker
tests; Ruff, Mypy, Bandit, both dependency audits, repository/public scans, strict MkDocs, generated
bindings, deterministic rebuild comparison, all Wrangler dry-runs, and `git diff --check`.

PR #5 was reviewed and squash-merged by TJ as
`3e4954dfe50ddaaa06e5f38114abe26591fe10ea`. Protected-main deployment run `29702968021` passed
the reviewed-window gate, complete validation, exact artifact download, repeated publication scans,
snapshot pinning, and Worker upload. The environment flag was immediately restored and re-read as
`false`. The final custom-domain curl received HTTP 403 at the exact activation timestamp.
Cloudflare Security Analytics classified the corresponding request as a Bot Fight Mode managed
challenge. An independent network then returned HTTP 200 for `/`, `/api/status`, and the exact
reviewed live sanitized snapshot with the expected security headers. No route, DNS, secret, Graph,
or Intune state changed during diagnosis.

The control-plane proof adds a snapshot-bound Worker version message and rejects an absent message,
wrong or partial active version, non-Wrangler source, invalid trigger, malformed UTC timestamp, or
unexpected rollout. The workflow re-reads both versions and deployments inside the single
secret-bearing step; Cloudflare metadata remains ephemeral and is neither logged nor uploaded.
Local validation passed with 208 Python tests, one credential-gated local live test skipped, 91.16%
branch coverage, 43 Worker tests, both dependency audits, Ruff, Mypy, Bandit, repository/public
scans, deterministic rebuild, strict MkDocs, generated bindings, and all Wrangler dry-runs.

## Final protected-main verification

TJ reviewed and merged the Bot-Fight-safe proof as
`f1dd37be822c07677621907168fc372c6ccc0ae0`. Protected deployment run `29703512007` then passed the
reviewed-window gate, complete public validation, exact artifact selection, revalidation, staging,
Worker upload, and authenticated active-version proof. The expected snapshot-bound version was the
sole active deployment at 100% traffic. `CLOUDFLARE_DEPLOY_ENABLED` was restored and independently
re-read as `false`.

Independent HTTPS checks passed for the root, dashboard, live demo, Mission package, status,
health, and readiness routes. The runtime matched `LIVE SANITIZED TENANT DATA`, fixture narrative
mode, and snapshot `mission-d8351dbdfbf9dcc6b46259d5`. TLS, CSP, HSTS, frame, MIME, referrer,
permissions, cache, and cross-origin headers passed. The downloaded Mission package passed the
public-artifact scan and reported only allowlisted aggregates.

TJ then authorized one further protected-main audit retry. Run `29703823180` passed locked
installation, pre-auth contracts, OIDC, GET-only collection, publication-policy validation, public
scanning, and ephemeral cleanup. `prepare_publication=false`, so artifact upload was intentionally
skipped and neither private nor public evidence was retained by the retry.

The bounded model response, protected expanded Intune audit, reviewed live publication, corrected
deployment, and independent production checks are complete. Phase 1 is technically complete. The
remaining `/feedback`, media, DevPost, and submission actions require the operator and are recorded
in the [final implementation report](final-implementation-report.md).
