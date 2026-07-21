# Final Build Week Readiness Report

Report date: 2026-07-21

Branch: `codex/final-submission-readiness`

Protected-main starting revision: `91f91a33852c5b0e3105ff9228eda592260a950f`

## Executive decision

**CONDITIONAL GO — not yet submitted.**

Provifact is a materially functional Developer Tools entry with a real protected read-only Intune
slice, deterministic evidence, live sanitized production dashboard, and bounded GPT-5.6 Terra
Assistant. The repository and production security boundaries are credible and independently
inspectable. The original external evaluation's principal demo criticisms—static UI, superficial
AI, no Apple provider, no framework comparison, weak traceability, missing CSP/CodeQL/retry/error
handling—are addressed in the current slice.

Four completion gates remain outside this branch:

1. TJ must review and merge this branch; protected `main` must pass CI.
2. Production evidence must be refreshed through the protected GET-only workflow before it becomes
   stale, and the two-device public aggregate must be reconciled with the expected three-device
   test fleet without guessing private data.
3. TJ must record and publish the under-three-minute public YouTube demonstration.
4. TJ must run `/feedback`, enter that private identifier directly into Devpost, complete the
   required form, submit, and verify green **Submitted** state before 5:00 PM PDT.

This report is not a submission confirmation and does not declare organizational compliance.

## Truth snapshot

### Repository and GitHub

- Public repository: `tmcoconsulting/provifact`, Apache-2.0, default branch `main`.
- Starting worktree was clean and synchronized to remote protected main at `91f91a3`.
- No open pull request existed when this finalization branch was created.
- CI and CodeQL passed on the protected-main starting revision.
- Branch protection requires a strict full CI check, conversation resolution, linear history, and
  CODEOWNERS review; force pushes and deletion are blocked and administrators are enforced.
- GitHub secret scanning, push protection, Dependabot alerts/updates, and CodeQL were enabled; the
  repository audit reported no open alerts.
- Low-severity tradeoffs: CodeQL is not a required status context, signed commits are not required,
  and production-environment administrators can bypass environment protection.

### Production

- Public URL: `https://provifact.tmcoconsulting.com/`.
- Cloudflare Worker and Static Assets serve the site; GitHub Pages remains retired.
- At audit time `/api/status` reported live sanitized tenant data, active OpenAI mode, fixed
  `gpt-5.6-terra`, server-side model availability, no BYOK, and no Intune write capability.
- The public package was current at audit time but reaches its 24-hour freshness limit at
  `2026-07-21T21:28:14Z`, before the submission deadline.
- The public aggregate showed two managed Apple devices—one macOS and one iOS—rather than the
  expected three-device test fleet. No private data was inspected to explain the difference.
- All 32 sitemap routes and 15 sampled authoritative external links returned HTTP success. TLS,
  CSP, HSTS, frame denial, no-sniff, referrer, permissions, COOP, and CORP controls were present.

### Devpost and deadline

- Official deadline: **Tuesday, July 21, 2026 at 5:00 PM PDT** (`2026-07-22T00:00:00Z`).
- Authenticated Devpost data showed the Provifact portfolio project published and associated with
  OpenAI Build Week, but the demo video URL was empty and `submitted_at` was null.
- A coarse relationship field said submitted, but it conflicts with those authoritative fields.
  Treat the entry as draft until My Projects shows green **Submitted**.
- Saved category, repository URL, test instructions, and private `/feedback` field must be checked
  in the authenticated form by TJ.

## Judge-facing product assessment

| Criterion | Evidence | Readiness |
| --- | --- | --- |
| Technological implementation | GET-only Graph provider, OIDC, versioned evidence, exact mappings, fail-closed publication, Cloudflare Worker, fixed-model structured output, verifier, adversarial tests | Strong for a bounded Phase 1 slice |
| Design | Action-first Mission Control, complete inventory/backlog, trace dialog, responsive matrix, provenance, accessible tables, Assistant evidence links | Strong after this branch is deployed |
| Potential impact | Replaces audit reconstruction with an approval-to-evidence chain for regulated endpoint teams | Clear and credible |
| Quality of idea | Deterministic evidence remains authoritative while AI explains only a sanitized verified subset | Differentiated and defensible |

The best demonstration path is: provenance → denominator → one finding trace → baseline planning
row → one verified Assistant answer → no-write/human-review boundary.

## Architecture and portability

The shipped live provider is Microsoft Intune for managed Apple platforms. The domain, observation,
finding, evidence, publication, and narrative-verification contracts are provider-neutral. A Jamf
or Omnissa Workspace ONE integration still requires its own GET-only adapter, authentication,
normalizer, exact provider mappings, fixtures, and contract tests. When it emits the current
observation contract, the deterministic drift, sanitizer, public schema, dashboard, and verifier do
not need a rewrite. This is practical contract portability—not a claim of plug-and-play support.

The active Build Week baseline is selected by the machine-readable TMCO Consulting, LLC approval
record. Its exact source revision and hashes are pinned. Desired values and exact Intune mappings
remain in a reviewed Python table; extracting that organization-owned layer into a data-only
override is an accepted Phase 1 limitation, documented in the baseline runbook.

## External evaluation reconciliation

The 2026-07-19 external evaluation report supplied by the operator was read in full. Its findings describe an earlier
checkpoint; none of its numerical scores are treated as current evidence.

| Earlier finding / recommendation | Current disposition |
| --- | --- |
| No Apple/MDM provider; only two settings | Addressed: comprehensive managed-Apple Intune resource families, four exact evaluated mappings, 98-rule inventory, GET-only contract tests |
| Static, generic dashboard | Addressed: responsive Mission Control, filtering, findings, drilldowns, coverage, history, evidence health, and Assistant |
| No framework/control linking | Addressed within safe scope: exact reference identifiers and a 17-profile catalog (one approved company target plus 16 public technical profiles); formal framework score/compliance verdict intentionally rejected |
| Partial traceability | Addressed for public-safe data: desired/observed, assignment summary, provider definition, evidence IDs, Git/fingerprint/algorithm provenance; private tenant identities intentionally excluded |
| AI is a static formatter | Addressed: site-wide bounded natural-language evidence Assistant with intent selection, structured output, exact typed claims/references, prose quarantine, and insufficient-evidence behavior |
| No scheduled operation | Accepted deferral: manual protected workflow is safer for the Build Week tenant; cadence is not called continuous without qualification |
| Missing storage/history | Partially addressed with exact current/prior sanitized snapshots; persistent D1/KV/R2 history deferred pending authentication, retention, and residency design |
| No multi-tenancy/RBAC/UI authentication | Accepted enterprise deferral; public demo contains sanitized data and API has same-origin, global/client rate limits, bounds, and no BYOK |
| Weak error handling / no Graph retry | Addressed: bounded retry, jitter, `Retry-After`, timeouts, pagination, structured status classes, fail-closed shapes, and generic public errors |
| No rollback/remediation | Rejected by design: Provifact is read-only; Git revert restores intent history but cannot and must not change Intune |
| Production fixture-only | Addressed: production uses a reviewed live sanitized package and fixed OpenAI mode with no synthetic fallback; local/preview remain fixture-safe |
| Missing Apple/provider/framework tests | Addressed: provider contracts, mappings, catalog fingerprints, mission schemas, sanitizer, verifier, browser contracts, and workflow security tests |
| Documentation/code divergence | Substantially addressed; current docs and dated historical records are distinguished, with final operator/source/submission documents added here |
| Naming/identifier inconsistency | Addressed publicly through Provifact naming and stable pseudonymous evidence IDs; legacy `evidenceops` runtime identifiers remain documented compatibility contracts |
| Dependency/release weakness | Dependencies and actions are immutable-pinned and audited; semantic releases/tags remain a post-submission open-source maturity task |
| Secret rotation / static Azure credentials | Addressed by Entra OIDC with no client secret and a project-scoped OpenAI key stored only as a Worker secret; formal rotation cadence remains operational work |
| No UI authorization | Accepted demo limitation; authenticated private dashboards are deferred |
| Missing exception workflow | Accepted deferral; automatic exceptions and AI risk acceptance remain prohibited |
| Cloudflare AI not used | Rejected: OpenAI GPT-5.6 is a Build Week requirement and fixed-model policy; adding a fallback would complicate authority and cost controls |
| Missing severity/prioritization | Addressed: deterministic severity and priority queue are visible without turning them into compliance verdicts |
| Development overhead | Improved with exact credential-free commands and a public judge path; container packaging is deferred |
| Missing CodeQL/CSP/security headers | Addressed; low-severity inline CSP allowance remains due to Material for MkDocs |
| Missing architecture diagrams / Devpost materials | Addressed in architecture and the final recording, YouTube, Devpost, source-ledger, and readiness package |
| Caching, analytics, WAF, SIEM, HA, database, exports, SSO | Accepted enterprise deferrals; adding them for the submission would expand data retention and attack surface without strengthening the core proof |
| Automatic scheduling, notification, approvals, device search, long-term history | Postponed until access control, retention, and private evidence governance are designed |
| BYOK | Rejected for Phase 1 because browser storage, exfiltration, logging, cost, and abuse boundaries are not justified |

## Security and privacy judgment

- Provider source and workflows enforce GET-only operations. No apply, assignment, remediation,
  profile creation/deletion, exception grant, or rollback operation exists.
- Private normalized evidence is owner-only/ephemeral; raw Graph responses are not public artifacts.
- Publication reconstructs an allowlisted package, rejects unknown fields, pseudonymizes only when
  correlation is needed, fingerprints content, and uses shared credential/identity scans.
- The OpenAI path receives only bounded sanitized evidence. It uses `store: false`, no tools, fixed
  model, time/output limits, and server-side credentials.
- Typed claims and evidence references must match deterministic evidence. Free prose is always
  generated, quarantined, and subject to human review.
- This branch fixes session restoration so the generated label, limitations, and review questions
  cannot disappear after a page navigation/reload.
- Apache-2.0 project licensing and the mSCP CC BY 4.0 attribution in `NOTICE` are present. Restricted
  benchmark prose and Apple-authored descriptions are excluded.

## Final validation

The starting remote main had green CI and CodeQL. The final branch was reproduced from an empty
temporary Python virtual environment on Python 3.14.6 (the project supports Python 3.12 or later).

| Command or gate | Result |
| --- | --- |
| `python -m pip install -r requirements-dev.txt` | Pass in a new temporary virtual environment; every resolved dependency came from the exact-pinned requirements file |
| `python -m pip install --no-build-isolation --no-deps .` / `python -m pip check` | Pass; wheel built and no broken requirements found |
| `python -m ruff format --check .` | Pass; 65 files already formatted |
| `python -m ruff check .` | Pass |
| `python -m mypy` | Pass; no issues in 65 source files |
| `python -m pytest -q` | Pass; 245 passed, 1 opt-in live-tenant test skipped, 90.03% branch coverage |
| `python -m bandit -r evidenceops scripts -c pyproject.toml` | Pass; 6,756 lines scanned, no findings |
| `python scripts/check_company_name.py` | Pass |
| `python scripts/check_secrets.py` | Pass |
| `python -m pip_audit -r requirements-dev.txt` | Pass; no known vulnerabilities |
| `npm ci --ignore-scripts --no-audit --no-fund` | Pass; clean install from `package-lock.json` |
| `npm audit --audit-level=moderate` | Pass; zero vulnerabilities |
| `npm run validate:worker` | Pass; Prettier, Oxlint, strict TypeScript, 57 Worker tests, generated bindings, and default/preview/production Wrangler dry-runs |
| Two isolated `python -m provifact run-mission-demo` runs plus recursive comparison | Pass; byte-identical outputs, with both outputs passing the public-artifact scan |
| `python -m provifact rebuild-static-demo` plus tracked-data diff | Pass; no tracked synthetic-data change |
| `mkdocs build --strict` | Pass; 174 static assets accepted by the Worker dry-run |
| `python scripts/check_public_artifacts.py site` | Pass |
| `git diff --check` | Pass |

The skipped live-tenant test, production refresh/deployment, paid model call, video upload, and
Devpost submission require protected-main or human-controlled external actions and were not run by
this non-deploying readiness branch. On pushed implementation head
`c3a15c97a4606a327102892252e4bd4fedb85ad2`, required CI run `29867933390` and CodeQL run
`29867933414` passed. This audit-only record commit must receive the same final checks.

## Readiness checklist

### Automated / repository

- [x] Public repository, license, source, and credential-free test path exist.
- [x] Current architecture, safety boundary, Build Week collaboration, and runtime GPT-5.6 role are
      documented.
- [x] External requirements and technical sources are linked in the source ledger.
- [x] Approved-baseline and protected-refresh runbooks exist.
- [x] Final recording, YouTube, Devpost, site-audit, and public-safe changelog materials exist.
- [x] Final local validation passes after all branch edits.
- [x] Required CI and both CodeQL language analyses passed on the pushed implementation head.
- [ ] TJ reviews and merges the branch.

### Production / human

- [ ] Protected audit refresh completes from reviewed `main` before the evidence becomes stale.
- [ ] Expected device aggregate is privately reconciled or accurately documented.
- [ ] Exact sanitized audit artifact is deployed and production reverified.
- [ ] Final Assistant response succeeds and remains correctly labeled after reload.
- [ ] Video is recorded, privacy-reviewed, under three minutes, uploaded Public, and tested signed
      out.
- [ ] Devpost category, repository, public test path, required answers, and YouTube URL are saved.
- [ ] `/feedback` is run in the primary task and the returned ID is entered privately in Devpost.
- [ ] Devpost shows green **Submitted** before the deadline.

## Shortest safe operator path

1. Review and merge the final readiness pull request after green checks.
2. Use [Protected Demo Refresh](../operations/demo-refresh.md) to run one trusted-main GET-only audit,
   investigate the device aggregate privately, and deploy the exact scanned package.
3. Verify production status, freshness, TLS/headers, Mission Control, Baseline Plan, mobile/keyboard
   behavior, and one bounded Assistant answer.
4. Record with the [shot guide](final-recording-shot-guide.md),
   [script](final-voiceover-script.md), and [checklist](final-recording-checklist.md).
5. Publish using the [YouTube runbook](youtube-publishing-runbook.md); verify the URL signed out.
6. Copy the [Devpost packet](final-devpost-packet.md), complete accurate personal/legal fields, and
   add the video URL.
7. Run `/feedback`; paste the identifier directly into Devpost and nowhere public.
8. Submit and verify green **Submitted** state.

## Decision ownership

TJ Olnhausen is the human product, security, baseline, legal/brand, external-account, review, merge,
recording, and submission decision-maker for TMCO Consulting, LLC. Codex and its supporting agents
performed implementation, evidence collection, and read-only audits. New commits from this branch
require TJ review and must not carry a `Human-Reviewed` trailer until that review occurs.

## Independent gate decision

| Gate | Evidence | Status | Blocking? | Exact owner action |
| --- | --- | --- | --- | --- |
| Repository clean and reviewed | Branch starts at current `origin/main`; public-safe diff and validation complete | NEEDS HUMAN | Yes | Review this pull request, approve, and merge after green checks |
| CI and CodeQL | Protected-main checks were green; required CI and both CodeQL analyses passed on pushed implementation head `c3a15c9` | PASS WITH LIMIT | Yes | Require the final audit-only head checks to remain green before merge |
| Dependency and security scans | Ruff, Mypy, Pytest, Bandit, pip-audit, npm audit, Worker security tests pass | PASS | No | None |
| Deterministic build | Two isolated Mission runs are byte-identical; tracked demo rebuild has no unexplained delta | PASS | No | None |
| Public-artifact and privacy scan | Repository, two demo outputs, and final `site/` scans pass | PASS | No | None |
| Every-page QA | 32 sitemap routes and sampled external sources pass; branch fixes static accessibility/mobile issues | PASS WITH LIMIT | Yes | After deployment, repeat keyboard, 375 px, console, and social-card checks |
| Landing and README clarity | Problem, chain, judge path, limits, GPT/Codex role, current scope, and portability are explicit | PASS | No | None |
| Approved-baseline workflow | Canonical files, source pins, targets, mappings, extensions, comparisons, tests, and approval gates documented | PASS | No | Use the runbook for any policy decision; do not hand-edit evidence |
| Refresh workflow dry-run | Workflow names, actual inputs, exact artifact name, one-day retention, scan, gate, verify, and rollback paths matched to source | PASS WITH LIMIT | Yes | Execute the two protected-main workflows only after merge and artifact review |
| Production snapshot current | Audited package was current but expires before the deadline; device aggregate remains unexplained | NEEDS HUMAN | Yes | Run protected refresh and reconcile aggregate privately before recording |
| Live site and API readiness | HTTPS, routes, status, TLS, and security headers passed on the existing production version | PASS WITH LIMIT | Yes | Verify health, readiness, status, snapshot, headers, and pages after deployment |
| Assistant behavior | Existing fixed Terra runtime is available; branch preserves labels/limitations across session restore | PASS WITH LIMIT | Yes | After deployment, make one bounded question and confirm verified labels/references after reload |
| Demo script and privacy review | Shot guide, natural script, teleprompter cues, contingencies, and frame-level checklist exist | PASS | No | Rehearse with current visible values and complete the privacy checklist |
| YouTube channel and assets | Original SVG/PNG avatar/banner and official-source publishing runbook exist; channel state not verified | NEEDS HUMAN | Yes | Confirm/create the company channel, upload assets, and retain ownership details privately |
| Video under three minutes | No final video exists | NEEDS HUMAN | Yes | Record, trim to less than 3:00, and watch the final export completely |
| Video public and signed-out tested | Devpost video URL is empty | NEEDS HUMAN | Yes | Publish on YouTube and verify the exact URL signed out/incognito |
| Devpost text and required fields | Public-safe packet exists; authenticated record still lacks video and final submission proof | NEEDS HUMAN | Yes | Verify category, links, legal/personal fields, testing answer, and save final text |
| Private `/feedback` identifier | Intentionally absent from Git | NEEDS HUMAN | Yes | Run `/feedback` in the primary task and paste the returned ID directly into Devpost |
| OpenAI Build Week submission | Authenticated `submitted_at` was null at audit time | NEEDS HUMAN | Yes | Submit explicitly and verify green **Submitted** before 5:00 PM PDT |

**CONDITIONAL GO — ONLY THE LISTED HUMAN ACTIONS REMAIN**
