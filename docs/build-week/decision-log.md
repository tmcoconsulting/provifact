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

**Status:** Superseded during Phase 1 security remediation; the workflow was removed.

**Decision:** A Pages workflow runs only after the `CI` workflow succeeds for `main`, rebuilds the
site at the validated commit, scans it, and uses GitHub's supported Pages artifact/deploy actions.

**Why:** It keeps publication downstream of tests and the policy gate. GitHub documents
[custom Pages workflows](https://docs.github.com/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
and [deployment protection rules](https://docs.github.com/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment).

## 2026-07-18 — Defer custom domain and live collection

**Status:** Superseded for hosting. Live collection remains deferred; the selected future hostname
is now part of the Cloudflare Workers milestone below.

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

## 2026-07-18 — Bound Phase 1 to Graph v1.0 legacy configuration

**Decision:** Read only `deviceConfigurations` and their `assignments`; normalize two fields from
`macOSGeneralDeviceConfiguration`. Do not use `/beta` Settings Catalog or managed-device inventory.

**Why:** Microsoft documents the [configuration list](https://learn.microsoft.com/graph/api/intune-deviceconfig-deviceconfiguration-list?view=graph-rest-1.0),
[assignment list](https://learn.microsoft.com/graph/api/intune-deviceconfig-deviceconfigurationassignment-list?view=graph-rest-1.0),
and [macOS resource](https://learn.microsoft.com/graph/api/resources/intune-deviceconfig-macosgeneraldeviceconfiguration?view=graph-rest-1.0)
in v1.0. A supported v1.0 Settings Catalog contract was not established. Device counts would add a
permission without contributing to this narrow drift proof.

## 2026-07-18 — Request one Graph read permission

**Decision:** Use only delegated/application `DeviceManagementConfiguration.Read.All`, with its
documented administrator consent requirement. Do not request its write counterpart,
`Directory.Read.All`, or managed-device read scope.

**Why:** It is the least privileged permission Microsoft lists for both implemented endpoints. The
IDs and rationale are machine-readable in `manifests/microsoft-graph-permissions.v1.json` and
traceable to the [Microsoft permissions reference](https://learn.microsoft.com/graph/permissions-reference#devicemanagementconfigurationreadall).

## 2026-07-18 — Normalize instead of storing raw Graph exports

**Decision:** Retain source policy IDs only in a restrictive private package; never persist full
Graph responses. Publication is a distinct, key-requiring, fail-closed command.

**Why:** Configuration read permission is broad even when code uses a narrow slice. Data
minimization reduces disclosure, retention, and future schema-change risk.

## 2026-07-18 — Constrain GPT with structure and verification

**Decision:** Send only a validated public package (maximum 64 KiB) to the OpenAI Responses API,
with no tools, `store: false`, strict `json_schema`, and the configured Build Week model
`gpt-5.6-terra`. Treat the returned object as untrusted.

**Why:** OpenAI documents [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
and the [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create).
Structure narrows output shape; a separate deterministic verifier enforces evidence/status/claim
rules and keeps human review authoritative.

## 2026-07-18 — Keep live automation out of the public repository

**Decision:** Document—but do not add—a private OIDC collection workflow. Public CI and the local
static demo use no tenant or OpenAI credentials.

**Why:** GitHub OIDC and Entra workload federation can issue short-lived credentials, but their
subjects, environments, tenant/application IDs, and retention are private deployment decisions.
The public repository cannot safely supply universal tenant-specific values.

## 2026-07-18 — Retire GitHub Pages and select Cloudflare Workers Static Assets

**Decision:** Remove the GitHub Pages `workflow_run` deployment and its `pages: write` and
deployment OIDC permissions. Keep MkDocs as a local/static build, and make Cloudflare Workers Static
Assets at `evidenceops.tmcoconsulting.com` the next separately reviewed milestone. Route only
same-origin `/api/*` through Worker code; serve other static assets directly.

**Why:** The Codex Security scan proved the branch-name-only `workflow_run` gate could select a
fork-controlled SHA for execution in the privileged deployment job. Retiring the obsolete hosting
path removes the sink rather than preserving unnecessary deployment privilege. Cloudflare
documents selective
[`run_worker_first`](https://developers.cloudflare.com/workers/static-assets/binding/#run_worker_first)
routing for hybrid static/API applications. No Cloudflare resource, configuration, secret, DNS
record, workflow, or deployment is created in this remediation.

## 2026-07-18 — Use one credential catalog at every egress

**Decision:** Publication sanitization, repository scanning, static-artifact scanning, and pre-model
egress import one high-confidence credential-pattern catalog. The catalog includes every GitHub
`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, and `github_pat_` form covered by regression tests.

**Why:** Duplicated patterns diverged and allowed underscore-form GitHub credentials to cross the
publication boundary. One catalog makes a missed update visible to every gate and test.

## 2026-07-18 — Verify typed claims; quarantine unrestricted prose

**Decision:** Narrative explanations carry an additive typed `deterministic_claim` with closed
`finding_status` code/value semantics. The verifier requires exact unique finding-ID coverage and
marks only those typed claims verified. All free-form generated prose remains quarantined for human
review, regardless of phrasing.

**Why:** A finite status-phrase matcher cannot establish the meaning of unrestricted natural
language. Exact identifiers and enum values are deterministic; prose is not. Legacy schema-v1
narratives remain readable but cannot verify without typed claims.

## 2026-07-18 — Defer production OpenAI key and BYOK to the Worker milestone

**Decision:** The future production runtime should use a dedicated EvidenceOps Project
service-account/project key stored only as a Cloudflare Worker secret. Fixture mode remains the
default when credits or the key are unavailable. Browser BYOK is deferred pending a dedicated
browser-key, logging, support, and abuse threat model.

**Why:** OpenAI recommends keeping API keys out of code and public repositories and supplying them
through environment variables or a secret manager. Cloudflare provides encrypted Worker secret
bindings. A browser-supplied key would create additional exposure surfaces and is not a safe
"easy" addition without those controls. See OpenAI
[production practices](https://developers.openai.com/api/docs/guides/production-best-practices)
and Cloudflare [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/).

## 2026-07-18 — Implement a small same-origin Worker before provisioning

**Decision:** Implement and independently validate a strict TypeScript Worker and Static Assets
configuration before creating Cloudflare resources, DNS, secrets, or deployment automation. Serve
static paths directly and run only `/api/*` Worker-first. Default to fixture mode; make OpenAI mode
explicit and never silently fall back.

**Why:** The runtime boundary can be reviewed, tested in workerd, bundled, and scanned without
creating external state or consuming model credits. Same-origin checks, byte/time/rate bounds,
allowlisted logs, shared publication scans, typed verification, and static security headers become
evidence before production authorization is granted.

**Dependencies:** Worker development dependencies are exact-pinned in `package.json` and fully
resolved in `package-lock.json`: Wrangler `4.112.0`, TypeScript `7.0.2`, Vitest `4.1.10`, Cloudflare
Vitest pool `0.18.6`, Oxlint `1.74.0`, Oxlint TypeScript companion `0.25.0`, Prettier `3.9.5`, and
Node types `26.1.1`. They are build/test tools, not Worker runtime packages. Their declared licenses
are MIT, Apache-2.0, or `MIT OR Apache-2.0`, compatible with the repository's Apache-2.0 source
license. Public CI uses Node 22 and `npm ci` against the lock.

**Sources:** Cloudflare documents [Static Assets bindings](https://developers.cloudflare.com/workers/static-assets/binding/),
[Vitest integration](https://developers.cloudflare.com/workers/testing/vitest-integration/), and
[secret bindings](https://developers.cloudflare.com/workers/configuration/secrets/). OpenAI
documents the [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
and [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## 2026-07-18 — Deploy fixture-first and keep BYOK rejected

**Decision:** Deploy `evidenceops` with Workers Static Assets, a Worker Custom Domain, dual native
rate limiters, and a fixed `gpt-5.6-terra` model policy. Store the dedicated EvidenceOps Project key
only as the Worker secret `OPENAI_API_KEY`. Keep production in explicit fixture mode after the
single bounded live validation returned capacity unavailable. Do not accept browser-supplied keys.

**Why:** Terra is the documented balanced GPT-5.6 cost/capability tier. The public fixture preserves
the end-to-end deterministic demonstration without a chargeable retry loop or misleading live-mode
label. BYOK would make the application a browser credential processor and expand storage,
exfiltration, support, logging, and abuse boundaries.

**Sources:** OpenAI documents [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
as the balanced cost/capability tier with Responses API and structured-output support. Cloudflare
documents the [Workers fetch request-context and public-routing rules](https://developers.cloudflare.com/workers/runtime-apis/fetch/).

**Operational boundary:** GitHub deployment is main-only, environment-protected, and disabled until
a narrowly scoped Cloudflare API token is stored. The manual Intune workflow is likewise main-only
and may authenticate only through the exact environment-scoped Entra federated identity. The trust
and required application consent are configured, but no feature-branch or live Graph run was made.

## 2026-07-18 — Activate exact Entra environment federation without running collection

**Decision:** Add `github-evidenceops-production` with the exact GitHub environment subject and
grant administrator consent only to application `DeviceManagementConfiguration.Read.All`. Create
no client secret and do not execute the audit until reviewed code reaches `main`.

**Why:** The environment subject excludes pull requests and arbitrary branches from the workload
identity. Keeping execution post-merge preserves the protected-code boundary while allowing the
existing manual workflow to use a short-lived Graph token later.

**Pre-existing state:** Eight consented delegated permissions remain on the application. They are
not used by the EvidenceOps application-only workflow, were not added for this proof, and were not
removed automatically because their ownership and unrelated consumers require human review.

## 2026-07-19 — Expand the Apple proof without adding mutation authority

**Decision:** Keep the provider-neutral and schema-v1 contracts, then add a separate Apple-focused
collector and Mission schema. Use exactly four Graph read-only permission families: configuration,
managed devices, managed applications, and service configuration. Retain one isolated beta
dependency for Settings Catalog because an adequate v1.0 contract was not available at the
implementation date.

**Why:** Policy evidence alone cannot explain Apple fleet, app, enrollment, assignment, and service
health. Independent adapters make partial permission or schema failures visible without inventing
a universal Intune response. The provider and transport still expose only collection/GET.

**Rejected:** `Directory.Read.All`, group/user scopes, raw tenant exports, write permissions,
client secrets, and silent beta/v1 substitution.

**Sources:** Microsoft [permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference),
[managed-device API](https://learn.microsoft.com/en-us/graph/api/intune-devices-manageddevice-list?view=graph-rest-1.0),
[Apps and Books API](https://learn.microsoft.com/en-us/graph/api/intune-onboarding-vpptoken-list?view=graph-rest-1.0),
and [APNs API](https://learn.microsoft.com/en-us/graph/api/intune-devices-applepushnotificationcertificate-get?view=graph-rest-1.0).

## 2026-07-19 — Pin an internally approved mSCP demo baseline

**Decision:** Pin mSCP revision `11b5896e4f12f43410686024f543792742562c91` and its macOS 26 CIS
Level 1 profile. Verify the source artifact and derived 98-rule inventory hashes. Approve it only as
the “TMCO macOS CIS Level 1 Build Week Demo Baseline.” Map five settings using identifiers from the
pinned source; keep all other rules visible but unsupported. Do not score iOS/iPadOS.

**Why:** Complete inventory visibility plus explicit mapping support avoids cherry-picking and
false coverage. Framework IDs are deterministic source metadata, not model-created mappings.

**License:** Derived mSCP metadata is attributed under CC BY 4.0 in `NOTICE`; Apple vendor
descriptions are excluded.

## 2026-07-19 — Use database-free sanitized history and a prefiltered assistant

**Decision:** Put current/previous sanitized snapshot deltas in the Mission package; do not add D1,
KV, or R2. Add same-origin `/api/ask`, accepting only a bounded question and snapshot ID. Load the
package server-side, classify a closed evidence intent, and send fewer than 16 KiB of allowlisted
context to fixed `gpt-5.6-terra` with `store: false`, no tools, low reasoning, strict JSON, exact
typed claims, and prose quarantine. Continue to reject BYOK.

**Why:** This proves history and grounded explanation without adding a persistence product or a
browser credential boundary. Prefiltering is cheaper and safer than sending a whole package.

## 2026-07-19 — Add non-executing CodeQL analysis

**Decision:** Add an exact-commit-pinned CodeQL v4 workflow for Python and
JavaScript/TypeScript. Both interpreted-language analyses use `build-mode: none`, so the scanner
analyzes pull-request source without executing it. Keep CodeQL separate from the required CI gate
and grant only repository/action read access plus `security-events: write` for analysis upload.

**Why:** GitHub's code-scanning API reported that no analysis existed. CodeQL is supported for this
public repository and adds data-flow analysis without giving untrusted pull-request code a secret,
deployment identity, or build step.

**Platform limitation:** GitHub's non-provider secret-pattern and secret-validity status remained
`disabled` after a repository-API enable request, so EvidenceOps does not claim those controls are
active. Provider secret scanning, push protection, the shared credential catalog, and fail-closed
repository/public-artifact scans remain enabled requirements.

## 2026-07-19 — Keep Graph type fallbacks inside a closed public taxonomy

**Decision:** Normalize a missing Microsoft Graph `@odata.type` to `unknown`, not the dotted SDK
namespace fallback `microsoft.graph.unknown`. Keep the public domain detector unchanged.

**Why:** The first protected-main live audit completed GET-only collection, but the publication
boundary correctly rejected the dotted fallback as a domain-shaped value. Dotted provider
namespaces are unnecessary in the public resource summary. Reducing the fallback to the existing
closed taxonomy retains useful resource-family evidence without allowlisting an arbitrary domain
pattern or exposing a tenant value.
