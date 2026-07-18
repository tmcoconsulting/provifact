# Decision Log

## 2026-07-18 — Start with an empty public repository

**Decision:** Create `tmcoconsulting/evidenceops` without importing history from an existing Intune
or Apple GitOps repository.

**Why:** It avoids ambiguous licensing, proprietary history, and accidental tenant-data carryover.

## 2026-07-18 — Use Apache License 2.0

**Decision:** License original EvidenceOps work under Apache License 2.0 and identify TMCO
Consulting, LLC in `NOTICE`.

**Why:** The license is OSI-approved, contribution-friendly, and includes an express patent grant.
The [Apache Software Foundation license text](https://www.apache.org/licenses/LICENSE-2.0) is the
authoritative license source. This is a project decision, not legal advice.

## 2026-07-18 — Keep the core dependency-free

**Decision:** The Phase 0 Python package has no runtime dependency. Direct development and docs
tools are exact-pinned in `pyproject.toml`.

**Why:** The evidence engine and sanitizer use the standard library, keeping the trusted computing
base understandable. MkDocs and the Material theme are development/documentation dependencies only.
MkDocs Material uses the [MIT license](https://github.com/squidfunk/mkdocs-material/blob/master/LICENSE),
so its generated static output does not change EvidenceOps' Apache license.

**Known risk:** The pinned Material release prints an upstream warning about planned MkDocs 2.0
incompatibility and licensing concerns. EvidenceOps remains on the pinned MkDocs 1.6.1 line in Phase
0 and will evaluate a documentation-stack change separately rather than silently upgrading.

## 2026-07-18 — Separate deterministic evidence from generated analysis

**Decision:** Drift state and evidence fingerprints are computed without a model. GPT-5.6 narrative
is deferred and will be non-authoritative, labeled, cited, evaluated, and human-approved.

**Why:** Auditors must be able to reproduce evidence independently of a probabilistic narrative.
The current [Codex model guidance](https://learn.chatgpt.com/docs/models) documents GPT-5.6 Sol and
reasoning controls used for the implementation workflow; runtime API design remains a Phase 1
decision.

## 2026-07-18 — Make the provider contract read-only and vendor-neutral

**Decision:** The provider protocol exposes collection only and returns normalized observations.

**Why:** Evidence production does not require mutation authority. This preserves a narrow initial
Intune boundary and avoids tying drift logic to one vendor's object model. Microsoft remains the
authority for [Graph permissions](https://learn.microsoft.com/graph/permissions-reference) and
[Graph API practices](https://learn.microsoft.com/graph/best-practices-concept).

## 2026-07-18 — Fail closed on unknown fields

**Decision:** Every public-artifact field requires an explicit allow, drop, or pseudonymize action.

**Why:** Provider schemas evolve. Automatic pass-through would make an upstream field addition a
possible public disclosure.

## 2026-07-18 — Deploy Pages only after validation

**Decision:** A Pages workflow runs only after the `CI` workflow succeeds for `main`, rebuilds the
site at the validated commit, scans it, and uses GitHub's supported Pages artifact/deploy actions.

**Why:** It keeps publication downstream of tests and the policy gate. GitHub documents
[custom Pages workflows](https://docs.github.com/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
and [deployment protection rules](https://docs.github.com/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment).

## 2026-07-18 — Defer custom domain and live collection

**Decision:** Use the initial GitHub Pages hostname. Do not configure DNS, Graph authentication, or
live collection in Phase 0.

**Why:** Those actions require separately verified authorization, data inventory, permissions, and
rollback planning. GitHub and Microsoft document the future
[Azure OIDC pattern](https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure)
and [workload identity federation](https://learn.microsoft.com/entra/workload-id/workload-identity-federation).

## 2026-07-18 — Use text-only project identity

**Decision:** Use a polished text identity and CSS, with no copied logo, prior thumbnail, or external
brand asset.

**Why:** No corresponding asset with established usage rights was present in the working directory.
TMCO Consulting, LLC is named as the legitimate project sponsor without using an unverified asset.
