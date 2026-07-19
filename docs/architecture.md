# Architecture

EvidenceOps separates collection, deterministic evaluation, publication policy, generated
analysis, and human judgment so no layer silently inherits another layer's authority.

```text
Reviewed desired state (Git)                  private trust zone
              |                                      |
              +----> GET-only provider ---> normalized observations
                                                   |
                                        deterministic drift v1
                                                   |
                                      private evidence package
                                                   |
                                     field policy + content scan
                                                   |
                                            PUBLIC BOUNDARY
                                                   |
                                      sanitized evidence package
                                          /                \
                               local static demo       optional GPT-5.6
                                                             |
                                             typed-claim verifier
                                                             |
                                             generated prose quarantine
                                                             |
                                                     human review only
```

## Provider contract

The additive `VersionedEvidenceProvider` exposes `collect` only. The Intune implementation uses
Microsoft Graph v1.0 and its transport exposes only `get`. It currently recognizes
`macOSGeneralDeviceConfiguration` and normalizes `passwordRequired` plus
`passwordMinutesOfInactivityBeforeScreenTimeout`. Unsupported policy types are counted privately
and never guessed. A later Jamf or Workspace ONE adapter can produce the same observation objects.

## Deterministic evidence engine

The engine compares normalized JSON values directly and records desired-state, observation, source
collection, Git SHA, algorithm version, and input fingerprints in every finding. Its restrained
statuses describe evidence relationships—not framework or organizational compliance. A language
model is never involved in status selection.

## Private-to-public boundary

Live collection creates no generic raw export. It normalizes only classified fields and retains
source object IDs only inside the private package when needed for traceability. That package must
be written to a Git-ignored, operator-selected directory with mode `0700`/`0600` where supported.
Publication is a separate command requiring an ephemeral pseudonymization key.

Every mapping key is classified as allow, drop, or pseudonymize. A new field—including one nested
under a dropped object—stops publication. The resulting package receives policy and content
fingerprints, reference-graph validation, and a second content scan.

## Narrative boundary

The opt-in narrative service uses the OpenAI Responses API with `store: false`, no tools, a strict
JSON schema, and a 64 KiB sanitized-package limit. The documented Build Week model is
`gpt-5.6-terra`. The verifier treats the returned object as untrusted and checks its schema, evidence
IDs, exact finding coverage, typed deterministic claim codes/values, limitations, and human-review
language. Only a `finding_status` claim whose typed value equals the authoritative finding can be
machine-verified. Free-form executive, explanation, impact, limitation, and question text remains
labeled generated and is always quarantined for human review. This deliberately avoids claiming
that finite phrase matching can prove the meaning of unrestricted prose.

The adapter also repeats the shared credential and sensitive-content scan immediately before any
OpenAI request. A package that merely has the public object shape cannot bypass that egress gate.

## Static application boundary

`mkdocs build --strict` produces a self-contained `site/` directory from synthetic or policy-gated
data. It is currently a local build artifact only. The GitHub Pages deployment workflow was removed
after security review; executable public workflows now have read-only repository permission.

The exact-pinned Cloudflare Workers runtime serves `site/` as Static Assets. Only `/api/*` routes
run Worker code first. `/api/status` exposes a deliberately small non-secret status contract;
`/api/narrative` accepts only same-origin bounded JSON, applies the publication and credential
gates again, rate limits before parsing, and then uses either the exact synthetic fixture or one
bounded OpenAI Responses API request. Static assets retain their direct-serving path.

The Worker ports the package schema and deterministic narrative verifier into strict TypeScript and
imports the same credential/public-value catalogs and strict narrative JSON schema as Python. The
deployed production environment pins `gpt-5.6-terra`, stores its project key only as a Worker
secret, and serves the custom domain in explicit fixture mode while project capacity is unavailable.
The GitHub deployment workflow remains disabled until a narrow Cloudflare token is configured.

The manual Intune workflow uses an exact GitHub `production`-environment federated identity and a
consented application `DeviceManagementConfiguration.Read.All` permission. It is intentionally not
run from feature branches; the first live audit remains a protected post-merge validation gate.

## Phase 1 modules

| Module | Responsibility | Intentional exclusion |
| --- | --- | --- |
| `domain` | Ten strict schema-v1 evidence object types | Vendor SDK objects |
| `providers` | Contract plus narrow GET-only Intune adapter | Writes and device identity inventory |
| `evidence` | Reproducible drift, packages, and fingerprints | Model inference |
| `sanitization` | Manifest classification and public-output gate | Key persistence |
| `narrative` | Optional structured generation, typed claims, and prose quarantine | Semantic approval of prose, remediation, or approval |
| `cli` | Six explicit operator workflows | Apply, assignment, or synthetic fallback |

## Compatibility

Phase 0 objects and imports remain available. New evidence uses schema `1.0.0`; unknown fields,
unknown object types, incompatible versions, and tampered fingerprints fail validation. The
machine-readable catalog is `schemas/evidenceops-v1.schema.json`. The optional
`deterministic_claim` member is an additive schema-v1 extension: legacy narrative objects still
validate, but the verifier refuses to verify them without the typed claim.
