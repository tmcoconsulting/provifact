# Phase 1 Final Implementation Report

> **Historical checkpoint (2026-07-19).** Runtime mode, mapping count, metrics, and run identifiers
> below describe that checkpoint. Use the current Mission package, `/api/status`, roadmap, and final
> video runbook for the Build Week final deployment.

This record describes the technically complete Provifact Build Week Phase 1 vertical slice as
verified on 2026-07-19. It does not claim regulatory compliance, assessor approval, or completion
of the external DevPost submission.

## 1. Executive summary

Provifact now runs an end-to-end, read-only evidence flow: a Git-approved, hash-pinned macOS
baseline is compared deterministically with private Microsoft Intune observations; a fail-closed
allowlist produces the only public package; Cloudflare serves the live sanitized Mission Control
dashboard; and a bounded GPT-5.6 Terra path explains evidence without changing findings. The
production assistant remains deliberately in fixture narrative mode after one successful bounded
operational model validation.

The final protected-main Intune retry, run `29703823180`, completed GitHub OIDC authentication,
GET-only collection, publication-policy validation, public scanning, and ephemeral cleanup. It
retained no private or public artifact. Production deployment run `29703512007` completed every
validation, staging, upload, and authenticated control-plane verification step. Independent HTTPS
and browser checks matched the reviewed live sanitized snapshot.

## 2. What was implemented

- A provider-neutral collection protocol and comprehensive GET-only Intune Apple adapter.
- Versioned desired-state, observation, finding, evidence, narrative, and verifier schemas.
- A 98-rule pinned mSCP macOS CIS Level 1 demo inventory with a machine-readable internal approval.
- Five explicit setting mappings with value, assignment, conflict, unsupported, and collection-gap
  outcomes.
- Stable evidence IDs, canonical SHA-256 fingerprints, freshness, provenance, and Git attribution.
- Owner-only private packages, ephemeral workflow evidence, deterministic pseudonyms, and a strict
  public allowlist.
- A responsive Mission Control dashboard generated from a sanitized package.
- A same-origin `/api/ask` assistant boundary with deterministic evidence retrieval, structured
  output, exact citation/claim verification, prose quarantine, and human-review labeling.
- Cloudflare Workers Static Assets, a custom domain, native per-client/global rate limit bindings,
  security headers, health/readiness/status routes, and a fixture-safe default.
- Protected GitHub OIDC collection and reviewed deployment orchestration with no stored Entra
  client secret.

## 3. What was intentionally deferred

- Every Intune or Microsoft Graph write, automatic remediation, assignment, and rollback operation.
- Formal exception approval, multi-tenancy, RBAC, Jamf, Workspace ONE, and Fleet providers.
- A complete macOS baseline mapping beyond the five reviewed demo settings.
- An approved iOS/iPadOS benchmark; Apple mobile posture is observed but not scored against macOS.
- Persistent sanitized history beyond the current/prior package demonstration.
- Browser BYOK, model tools, autonomous publication, and live narrative mode by default.
- Cloudflare observability/alert-retention tuning beyond verified runtime controls.

## 4. Architecture

Git remains the source of approved intent. A manual protected-main GitHub workflow exchanges a
GitHub OIDC token through an environment-scoped Entra federated credential, calls Microsoft Graph
read-only, normalizes observations privately, computes deterministic findings, and reconstructs a
sanitized Mission package. A separately reviewed workflow deploys only a selected scanned public
package and trusted Worker code. Cloudflare serves static assets and same-origin APIs. OpenAI can
receive only a bounded subset reconstructed from the sanitized package. The deterministic package,
not the model, remains authoritative.

## 5. Exact Microsoft Graph permissions

The protected application workflow has tenant-administrator consent for exactly these application
permissions:

- `DeviceManagementConfiguration.Read.All`
- `DeviceManagementManagedDevices.Read.All`
- `DeviceManagementApps.Read.All`
- `DeviceManagementServiceConfig.Read.All`

No Graph write, `Directory.Read.All`, `Group.Read.All`, `User.Read.All`, or user-impersonation scope
is part of the Provifact application workflow. Pre-existing delegated permissions are unrelated
to the protected application flow and were left unchanged rather than removed automatically.

## 6. Graph resource families collected

The collector uses v1.0 for managed devices, device configurations, compliance policies, mobile
apps and app policy metadata, enrollment configurations, device categories, ADE connection health,
Apps and Books token health, and APNs certificate health. Settings Catalog metadata, settings, and
assignments are the single isolated beta dependency. Child GETs retrieve assignments, settings,
scheduled actions, or aggregate state where documented. Each endpoint records API version,
collection status, and a visible gap on partial failure.

## 7. Approved baseline identity and hashes

- Organization: TMCO Consulting
- Baseline: TMCO Consulting macOS CIS Level 1 Demo Baseline
- Benchmark: CIS Apple macOS 26 Tahoe Benchmark Level 1
- mSCP revision: `11b5896e4f12f43410686024f543792742562c91`
- Source artifact SHA-256: `af9ef14ca568f17d3663e6e508c1f75971596fe43c6f185af27ca43451c240d2`
- Extracted baseline SHA-256: `5cced0709c90885ede600f00a640a35b0679aed933cda456db80ee629ee54d41`
- Internal approval record commit: `3dd8902a609c6be177cdc913c731fbd378f075a4`
- Approval authority label: TMCO Consulting, LLC — Build Week Demo Authority

This is an internal technical-drift demo approval, not CIS, NIST, DoD, C3PAO, or assessor
certification.

## 8. Drift and scoring methodology

The engine matches only explicit reviewed identifiers and typed values. It evaluates value,
assignment, conflicting-policy, device-state, missing, unsupported, and collection-gap conditions
without a model. Severity is assigned by documented deterministic rules. The macOS alignment
denominator contains only the five mapped and evaluable macOS requirements; iOS/iPadOS devices and
the other 93 unmapped baseline rules do not inflate or dilute the percentage. Unmapped tenant
objects remain visible.

The deployed live sanitized snapshot reports 98 baseline rules, a five-rule denominator, zero
aligned requirements, five drifted requirements, 13 policies evaluated, five collection gaps, and
94 unmapped objects. These are technical evidence states, not organizational compliance verdicts.

## 9. Sanitization architecture and tests

Private collection may retain source IDs only for short-lived joins. Public and AI packages are
rebuilt from explicit typed allowlists; they are never raw-record redactions. Unknown fields fail
closed. A runtime-only HMAC key creates deterministic pseudonyms when correlation is required and
is never stored. Shared credential and prohibited-content catalogs protect publication, repository
scanning, public assets, and pre-model egress.

Adversarial tests cover nested identifiers, tenant domains, user/device values, IP and network
values, credentials, tokens, certificates, unknown fields, hostile URLs, and free text. The exact
production Mission package passed schema/fingerprint validation and the public-artifact scan.

## 10. OpenAI model selection

The fixed runtime model is `gpt-5.6-terra`. OpenAI documents Terra as the GPT-5.6 tier balancing
intelligence and cost, and its structured-output Responses API capability matches the bounded
evidence-explanation workload. Provifact uses no model router or fallback model.

One deliberately bounded synthetic request reached the project service-account path, returned HTTP
success, parsed under the strict schema, accepted two deterministic typed claims, rejected none,
quarantined all free prose, and preserved human review. No prompt, evidence body, response prose,
credential, or authorization value was retained in operational logs. Production was returned to
fixture narrative mode immediately afterward.

## 11. OpenAI pricing and cost controls

The official OpenAI pricing page listed standard `gpt-5.6-terra` rates on 2026-07-19 as $2.50 per
million input tokens, $0.25 per million cached-input tokens, $3.125 per million cache-write tokens,
and $15.00 per million output tokens. Prices can change; the authoritative source is the
[OpenAI API pricing page](https://developers.openai.com/api/docs/pricing).

The OpenAI Platform project retained under the legacy `evidenceops` identifier has a $5 monthly soft
budget with alerts at 50%, 80%, and 100%, and a model
limit of 5 RPM and 25,000 TPM. The budget is an alert threshold, not a hard cap. Application controls
add fixed-model enforcement, no tools, `store: false`, bounded evidence and question schemas,
strict input/output limits, timeout, one controlled endpoint, and Cloudflare rate limiting. The
public demo defaults to a no-model fixture.

## 12. Example supported questions

- What is the current macOS technical baseline alignment, and what is its denominator?
- Which mapped requirements are drifting or missing?
- What are the highest-severity findings?
- Which findings are assignment or policy conflicts?
- What evidence supports a specific mapped baseline rule?
- What collection gaps or unmapped objects remain?
- What changed between the current and previous sanitized snapshots?
- Which supplemental framework mappings have relevant technical evidence?

Unsupported tenant assertions return the exact insufficient-evidence response rather than general
model knowledge.

## 13. Cloudflare resources and settings

- Production Worker: `evidenceops`
- Preview Worker: `evidenceops-preview`
- Custom domain: `evidenceops.tmcoconsulting.com`
- Runtime: Workers Static Assets plus same-origin Worker routes
- Required Worker secret name: `OPENAI_API_KEY`
- Native rate limits: three narrative requests per client per minute and 30 globally per minute
- Narrative mode: fixture
- Data mode: live sanitized tenant data
- Source snapshot: `mission-d8351dbdfbf9dcc6b46259d5`

The routine deployment token has account-scoped Workers Scripts write only. It does not manage DNS,
routes, or custom domains. The existing custom domain is a separately provisioned resource. Bot
Fight Mode remains enabled; the workflow verifies the exact snapshot-bound Worker version through
the authenticated control plane instead of weakening the edge control for a cloud-runner curl.

## 14. GitHub security and workflow changes

`main` is protected, pull requests and conversation resolution are required, force-push and
deletion are blocked, and the public validation job is a required status check. CodeQL is
configured and green but is not a separately required branch-protection context. Workflows use
immutable action SHAs and least-privilege permissions. Live collection is manual, main-only,
targets the protected
`production` environment, and uses only `contents: read` plus `id-token: write`. Deployment is
manual, trusted-main only, disabled by `CLOUDFLARE_DEPLOY_ENABLED=false` outside a reviewed window,
and constrains the Cloudflare token to one step. No privileged pull-request workflow exists.

## 15. Live validation results

- Protected GET-only audit retry `29703823180`: success on `f1dd37b`; OIDC, contract tests,
  collection, sanitization, scanning, and cleanup passed; artifact upload intentionally skipped.
- Reviewed sanitized publication `29702128497`: success; retained one public Mission file for one
  day and no private package; the artifact has since served its bounded handoff purpose.
- Production deployment `29703512007`: success; all public validation, exact artifact selection,
  revalidation, staging, upload, and control-plane proof passed.
- Independent control-plane query: the snapshot-bound version is the sole active deployment at
  100% traffic.
- Independent public check: runtime status, Mission fingerprint, TLS, CSP, HSTS, frame, MIME,
  referrer, permissions, cross-origin, and cache policies passed.
- Browser check: desktop dashboard loaded without console errors or page-level horizontal overflow.
- Intune writes: none; provider and workflow enforce GET only.

## 16. Production URL

The production application is [https://evidenceops.tmcoconsulting.com](https://evidenceops.tmcoconsulting.com).
The dashboard is at `/evidence-dashboard/`; `/api/status`, `/api/health`, and `/api/ready` expose
public-safe operational state.

## 17. Tests and coverage

The final implementation matrix passed 208 Python tests with one credential-gated local live test
skipped and 91.16% branch coverage. Forty-three Worker tests passed. Ruff formatting/lint, Mypy,
Bandit, repository secret scan, public-artifact scan, pip-audit, npm audit, Oxlint, Prettier, strict
TypeScript, generated bindings, deterministic site comparison, strict MkDocs, preview/production
Wrangler dry-runs, workflow security tests, and `git diff --check` passed. CI and CodeQL were green
on the reviewed main commit used for deployment.

## 18. Security scan results

The Phase 1 security remediation closed the four reported findings: the retired GitHub Pages
deployment path, inconsistent credential detection, incomplete narrative finding coverage, and
trust in unrestricted evaluative prose. Later review fixes preserved exact maximum comparison,
smoke-test coverage isolation, fail-closed health/readiness, HSTS, responsive containment, safe
Graph fallback labels, route-isolated deployment, and Bot-Fight-safe control-plane proof. No open
high, medium, or low finding from those reviewed scans remains.

## 19. Commit hashes

Key reviewed squash commits on `main` are:

- `f9e97a4f266e601d4bb9dac2735bb0338af67504` — bounded Worker runtime
- `7d7f8bca0ac7b652e515a360755b534af99c0b46` — Mission Control vertical slice
- `0f6f3b4fc8897528a5d66383802f578e87dbfd4e` — public-safe Graph fallback
- `b966cd0a5b20580b046c6ed3bb31057f7682bda7` — reviewed live-publication handoff
- `3e4954dfe50ddaaa06e5f38114abe26591fe10ea` — route-isolated deployment
- `f1dd37be822c07677621907168fc372c6ccc0ae0` — active-version control-plane proof

The documentation-only finalization commit is recorded after human review and merge.

## 20. Branch and pull-request status

The operational implementation is merged to protected `main` through PRs #1–#6. This final report
is proposed separately so every statement added after the last reviewed implementation commit
remains visibly pending TJ review. It must not receive a `Human-Reviewed` trailer until that review
actually occurs.

## 21. Remaining manual DevPost tasks

- TJ reviews and merges the documentation-only finalization pull request.
- Record and review the demo video/screenshots for notifications, identities, and sensitive data.
- Verify the current DevPost form/rules and paste only the reviewed suggested text.
- Run `/feedback` in the primary Codex task and preserve the returned Session ID privately.
- Submit the project. The Session ID and submission metadata must not be committed.

## 22. Exact three-minute demonstration

1. Open `/evidence-dashboard/` and identify `LIVE SANITIZED TENANT DATA` plus fixture narrative mode.
2. Explain the 98-rule pinned baseline and the five-rule evaluated denominator.
3. Filter deterministic findings to high severity; open FileVault and Firewall traceability.
4. Show assignment/conflict findings, platform aggregates, unmapped objects, and collection gaps.
5. Ask the fixture assistant for the highest-severity findings; show citations, verified typed
   claims, quarantined prose, and human review.
6. Ask who approved the annual corporate risk assessment; show the insufficient-evidence response.
7. Close with GET-only Graph, fail-closed publication, no Intune writes, and no compliance verdict.

The detailed timed script and click path are in the [demo package](demo-package.md).

## 23. Known limitations and residual risks

- Only five of 98 macOS rules are mapped; the denominator is honest but narrow.
- Settings Catalog requires a documented beta endpoint and therefore has schema-change risk.
- The four Graph read permissions expose broad tenant categories even though collection and
  publication minimize fields; application ownership and consent remain high-value boundaries.
- A single-maintainer repository cannot provide organizational separation of duties. Main enforces
  pull requests, the public validation check, conversation resolution, force-push/deletion blocks,
  and stale-review dismissal, but the required approval count is zero because an author cannot
  approve their own pull request. Explicit environment gates and auditable TJ review are the current
  compensating controls.
- Cloudflare scopes the deployment token at account Workers Scripts write, not one Worker; the
  fixed Worker name, protected workflow, snapshot proof, and disabled-by-default gate reduce but do
  not eliminate this residual scope.
- The public assistant remains fixture-based. The operational model boundary was proven once on
  synthetic sanitized evidence, not enabled for unlimited public use.
- Technical settings and mappings support evidence collection; they do not prove organizational
  compliance, risk acceptance, assessor conclusions, or certification.
