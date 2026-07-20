# Contribution Log

## Work location

The Phase 0 implementation occurred in the primary Codex thread. No supporting Codex thread or
subagent produced repository content during this phase.

## Milestones

| Date | Milestone | Primary contributor | Commit |
| --- | --- | --- | --- |
| 2026-07-18 | Secure project, evidence engine, and sanitizer foundation | Human-directed Codex implementation | `a5dbe3703e530297cfda165e69338791a419d403` |
| 2026-07-18 | Synthetic documentation and demo site | Human-directed Codex implementation | `b0a283b3848a523f80fd6501273872725d44161d` |
| 2026-07-18 | GitHub governance, CI, and historical Pages automation (later retired) | Human-directed Codex implementation | `0a2dbc3906ae6274e2f9d4a79d2ce620ae417368` |
| 2026-07-18 | Validation evidence record | Human-directed Codex implementation | This document's follow-up commit |

## Commands and checks

The primary thread recorded and directly inspected environment commands including `pwd`, `uname
-a`, Git/GitHub CLI/Python versions, Git identity, GitHub authentication, actor identity,
organization membership and policy, repository conflicts, repository settings, and local
permissions.

Implementation validation commands and their final results are recorded here after the clean run:

```text
python -m ruff format --check .
  PASS — 18 Python files already formatted
python -m ruff check .
  PASS — all checks passed
python -m mypy
  PASS — no issues in 18 source files
python -m pytest
  PASS — 13 tests; 91.03% coverage
python -m bandit -r evidenceops scripts -c pyproject.toml
  PASS — no issues identified
python scripts/check_secrets.py
  PASS — secret scan passed
mkdocs build --strict
  PASS — site built; upstream Material/MkDocs 2.0 warning recorded in the decision log
python scripts/check_public_artifacts.py site
  PASS — public artifact scan passed
python -m pip_audit -r requirements-dev.txt
  PASS — no known vulnerabilities found
```

The dependency installation began in a newly created `.venv` using Python 3.14.6 and the exact
direct pins, after which the resolved transitive environment was captured in
`requirements-dev.txt`. CI independently installs that lock on Python 3.12.

## Pre-Build-Week material

No source history, code, tenant exports, or licensed baseline content from another repository was
incorporated in Phase 0. A previously referenced visual asset was not present with established
usage rights, so the site uses text and original CSS only.

## Rejected design choices

- Importing code or history from an existing endpoint-management repository
- Live Graph collection in a public workflow
- Any Microsoft Graph or Intune write operation
- Stored client secrets or committed pseudonymization keys
- Unclassified field pass-through
- Model-authored compliance verdicts
- A custom domain before separate access and rollback verification

## Phase 1 work

Phase 1 also occurred entirely in this primary Codex thread. It reimplemented the minimum concepts
behind the existing provider-neutral contract and imported no code, history, tenant configuration,
or proprietary material from `intune-apple-gitops` or any other repository.

| Date | Milestone | Commit |
| --- | --- | --- |
| 2026-07-18 | Schema, deterministic evidence, and synthetic fixture | Recorded after commit |
| 2026-07-18 | GET-only Intune adapter and private/public boundary | Recorded after commit |
| 2026-07-18 | GPT adapter, verifier, CLI, local static demo, and documentation | Recorded after commit |
| 2026-07-18 | Four-finding security remediation and Cloudflare-next decision | `ccec44bd674c761fe3e4b335c56442f6ef7be912` |
| 2026-07-18 | Human-reviewed Cloudflare Worker/static-assets checkpoint | `7683c69f9eaca9f67ec220de5fb9f1a19fe9b3df` |
| 2026-07-18 | Runtime spend/log/egress hardening | `f8994d9` |
| 2026-07-18 | Protected audit and deployment workflow support | `925e0f8` |
| 2026-07-18 | Cloudflare/OpenAI egress fix and safe fixture production guard | `cfd9975` |
| 2026-07-19 | Comprehensive GET-only Apple collector | `ce4522d` |
| 2026-07-19 | Pinned baseline, Mission Control, and bounded assistant | `3dd8902` |
| 2026-07-19 | Controls, demo package, and validation documentation | `2d57a5f` |
| 2026-07-19 | Review-record anchoring | `b4a042c` |
| 2026-07-19 | Fail-closed health/readiness and HSTS hardening | `c1fca86` |
| 2026-07-19 | Hardened PR checkpoint validation record | `b071a89` |
| 2026-07-19 | Non-executing Python and JavaScript/TypeScript CodeQL analysis | `1c057c7` |
| 2026-07-19 | Preview and CodeQL evidence record | `b58db77` |
| 2026-07-19 | Browser-proven responsive Mission Control containment | `73d6b2b` |
| 2026-07-19 | Responsive desktop/mobile browser evidence record | `214f1bf` |
| 2026-07-19 | Reviewed Mission Control slice squash merge | `7d7f8bca0ac7b652e515a360755b534af99c0b46` |
| 2026-07-19 | Reviewed Graph fallback fix squash merge | `0f6f3b4fc8897528a5d66383802f578e87dbfd4e` |
| 2026-07-19 | Reviewed sanitized-publication handoff squash merge | `b966cd0a5b20580b046c6ed3bb31057f7682bda7` |
| 2026-07-19 | Routine deployment isolated from custom-domain management | `aa9c8fa` |
| 2026-07-19 | Reviewed deployment-isolation squash merge | `3e4954dfe50ddaaa06e5f38114abe26591fe10ea` |
| 2026-07-19 | Bot-Fight-safe active Worker version proof | `18b94c3` |
| 2026-07-19 | Reviewed active-version proof squash merge | `f1dd37be822c07677621907168fc372c6ccc0ae0` |
| 2026-07-20 | Consolidated rebrand and live-readiness pull requests | `f3db2c7a38750d8b31938ec43c816cb435492e7d` |
| 2026-07-20 | Full 98-rule implementation plan, cohesive docs shell, and judge path | `cde773cdd0f3820a46cd59205e8b883706f0ae58` |
| 2026-07-20 | Judge-ready product experience squash merge through PR #16 | `48a67aea60e5759f54ed5aee1396f68274b57f3b` |
| 2026-07-20 | Provifact Assistant, profile catalog, social metadata, and public cutover preparation | `9dae1363c0019022062c844a3725e0b537de658c` |
| 2026-07-20 | Exact upstream rule-ID canonicalization and catalog/Mission set guard | `2ca6073` |
| 2026-07-20 | Exact-mapping and cutover-record squash merge through PR #25 | `ffbdd0352e78e8c288cf3f79865552a83def79db` |
| 2026-07-20 | Version-bound catalog cache and final product squash merge through PR #26 | `0dd12dcac2511bdfeed51471baedc2f304741659` |

Exact Phase 1 commands, results, limitations, and commit hashes are maintained in the
[Phase 1 validation record](phase-1-validation.md).

After PR #16 passed CI and both CodeQL languages, protected-main audit run `29772311614` completed
OIDC authentication, GET-only collection, current-versus-prior comparison, sanitization, public
scanning, artifact upload, and ephemeral cleanup. Deployment run `29772466732` selected only that
run's exact reviewed snapshot, reran every public gate, deployed the Cloudflare Worker/static
artifact, and proved the active version through the authenticated control plane. Independent HTTPS
and browser checks matched the reviewed snapshot; the production deployment gate was restored to
false.

The July 20 finalization remained owned by the primary Codex task and used three bounded supporting
agents in the same shared checkout: one implemented exact provider mappings and sanitized snapshot
history; one hardened protected audit/deployment workflows; and one implemented Mission Control and
Provifact Assistant. The primary agent read the governing instructions, integrated and reviewed every
shared change, added TMCO Consulting branding and documentation, ran the complete validation gate,
and retained sole responsibility for Git, PR, merge, live audit, deployment, and production checks.
Implementation commit: `143f694f7183f1a2ce117a3a0867aad316f7a1ae`.

The integrated cockpit was squash-merged through PR #10 as
`d71da96b6b3770e96b3b7e715a51ca5b602ef852`. A generated-artifact-dependent Worker test stopped the
first protected deployment before Cloudflare; the production gate was closed, the focused fix
passed CI and CodeQL in PR #11, and it was squash-merged as
`1662cd1b631bfa3051eac071f442f70a48ca9b68`. Protected audit runs `29757456114` and `29759424410`
then completed GET-only OIDC collection, sanitization, scanning, current/prior comparison, and
ephemeral cleanup. Deployment runs `29758740795` and `29759572945` published only their exact
reviewed snapshots. One bounded production `gpt-5.6-terra` call passed deterministic verification;
its prose and input were not retained in the repository record.

The follow-on Cloudflare runtime and deployment were completed in this same primary thread on
`codex/cloudflare-worker-runtime` with no supporting-agent contribution. No Graph access or real
tenant data occurred. Cloudflare resources, the custom domain, a project-scoped OpenAI key/Worker
secret, GitHub environment controls, and bounded synthetic external validation are recorded in the
[Worker validation record](cloudflare-worker-validation.md).

The same thread later configured the exact Entra production-environment federation and required
Graph application consent without making a tenant request or creating a client secret. It also
added bounded, code-aware OpenAI 429 classification while keeping upstream bodies and messages out
of responses and logs. Those changes were reviewed and merged through PR #1.

The July 19 vertical slice was implemented in the same primary Codex task. Codex added the GET-only
resource-family collector, baseline verification, deterministic Mission schema, synthetic package,
dashboard, assistant boundary, tests, and documentation. TJ retains human review, external
approval, merge, and public-submission authority. No Intune write or raw tenant export was added.
The same task then deployed the scanned fixture revision to the credential-free Cloudflare preview,
validated its health/readiness/status/assistant boundaries, and added CodeQL without executing
repository code. Production and live-tenant state were left unchanged pending human review.
An authenticated desktop/mobile browser pass then found and remediated a narrow-screen overflow in
the preview. The table remains locally scrollable, the page itself fits the mobile viewport, and a
regression guard preserves the required grid containment and versioned stylesheet reference.
TJ subsequently reviewed the final PR #2 head and merged it through protected `main`. The primary
task deployed the reviewed fixture to production, accepted one bounded Terra response only after
typed-claim verification and prose quarantine, and restored fixture mode. A protected-main OIDC
audit completed private GET-only collection but correctly failed public publication on a
domain-shaped fallback value; cleanup removed the ephemeral evidence. The follow-up normalization
fix preserved the detector, was separately reviewed and merged, and the authorized retry completed
OIDC collection, sanitization, public scanning, aggregate reporting, and cleanup. The next review
boundary was a one-day scanned-public-package handoff; it retained no private package and did not
weaken the fixture-safe deployment default. After separate review and merge, a protected run
created exactly one scanned public artifact and the selected package was revalidated and deployed.
Production now reports live sanitized evidence and fixture narrative mode. A later review boundary
removed the already-provisioned custom domain from routine Wrangler uploads so the narrow
deployment token needs no zone-route permission. After TJ reviewed and merged that boundary, the
protected upload succeeded but a cloud-runner curl was managed-challenged by Bot Fight Mode. The
follow-up preserves the edge control and proves the snapshot-bound Worker version is the only active
100%-traffic deployment through Cloudflare's authenticated control plane. TJ reviewed and merged
that proof. Protected deployment `29703512007` passed validation, exact public-package selection,
upload, and control-plane proof; independent production checks matched the live sanitized snapshot.
TJ then authorized one further protected-main audit retry. Run `29703823180` passed OIDC, GET-only
collection, sanitization, scanning, and cleanup with artifact retention disabled. The earlier
documentation-only final report is retained as a dated checkpoint; the current Mission
package, roadmap, judge guide, and latest validation record supersede its mutable runtime counts.

After the public repository rename, protected-main audit `29780265224` proved the new immutable
`github-provifact-production` trust, completed GET-only collection, published only the scanned
sanitized package, and removed ephemeral evidence. The old repository-name federated credential
was deleted after this proof. Deployment `29780852414` validated and promoted exact snapshot
`mission-c62d533f8d58f76cef9afb1a` to the new Cloudflare custom domain; the old hostname was retained
as rollback and the deployment gate returned to `false`. A single bounded production Terra answer
passed typed-claim/reference verification while its prose remained quarantined and was not stored
in the repository.
