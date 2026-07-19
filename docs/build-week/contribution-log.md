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

Exact Phase 1 commands, results, limitations, and commit hashes are maintained in the
[Phase 1 validation record](phase-1-validation.md).

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
fix preserves the detector and requires separate human review.
