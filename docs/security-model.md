# Security Model

EvidenceOps assumes endpoint configuration can identify an organization, people, and devices.
Collection is privileged even when it is read-only.

## Security invariants

1. **No management-plane writes.** The provider and its HTTP transport expose collection/GET only.
2. **No public private data.** Private packages cannot enter static builds, snapshots, fixtures,
   model requests, or logs.
3. **Fail closed on change.** Unknown schema or publication fields stop processing.
4. **No stored credentials.** EvidenceOps never writes Graph/OpenAI tokens or pseudonym keys.
5. **Deterministic findings remain authoritative.** GPT cannot select or alter finding status.
6. **Human judgment remains visible.** Verification is not approval or certification.
7. **Fork isolation.** Public CI receives no Graph, tenant, or OpenAI credential.
8. **No browser keys.** The Worker rejects authorization and BYOK headers at its public boundary.

## Read-only integration boundary

The Intune transport implements one network method, `GET`, restricted to HTTPS on
`graph.microsoft.com` and explicitly allowed `v1.0` or isolated `beta` paths. Pagination follows
same-host, same-version `@odata.nextLink` values. Bounded retry honors `Retry-After`, adds jitter,
and backs off transient 5xx responses. There is no create, update, delete, assign, sync, rollback,
remediation, or apply method.

The expanded Apple slice uses exactly `DeviceManagementConfiguration.Read.All`,
`DeviceManagementManagedDevices.Read.All`, `DeviceManagementApps.Read.All`, and
`DeviceManagementServiceConfig.Read.All`. It does not request `Directory.Read.All`, user/group
permissions, privileged device operations, or any write scope. The one beta dependency is Settings
Catalog; its version and collection gap are explicit. See the
[permission and setup guide](operations/live-collection.md).

## Private-to-public boundary

Private packages contain normalized traceability metadata, not bulk raw Graph responses. They can
exist only in a selected Git-ignored repository directory and are written without overwrite or
symlink following. The expanded Apple command permits 1–30 day retention; operators remain responsible for secure
deletion at expiry. EvidenceOps does not persist the pseudonymization key.

Publication applies `evidenceops-publication-v1.0.0`. Every field is allow, drop, or pseudonymize;
unknown nested fields fail closed even under a dropped parent. A shared credential catalog is used
by publication, repository scanning, static-artifact scanning, and pre-model egress. It covers all
GitHub `gh*_` families and `github_pat_` as well as other high-confidence token/key signatures. A
second content scan rejects tenant identifiers, identity data, domains, IP addresses, serials,
tokens, keys, and certificates. Static builds fail if prohibited paths or values enter the
artifact.

## AI and human authority

GPT receives only a bounded package that already crossed the public boundary and passed a repeated
credential/content scan. The request uses no tools and cannot call Graph or publish. Output is
strict JSON but remains untrusted. The verifier requires unique explanation finding IDs with exact
set equality against package findings. It can verify only a closed `finding_status` claim code with
a typed value equal to the authoritative finding. Unknown claim codes, missing/duplicate/extra
findings, prohibited verdicts, unexpected fields, and out-of-package references are rejected.
Free-form prose is never semantically verified by a finite phrase list; it remains generated and
quarantined for human review.

All narratives remain labeled **AI-generated analysis subject to human review**. The verifier does
not grant approval. Human assessors retain final judgment.

## Workflow boundary

Public CI uses only repository content and read-only `contents` permission. The privileged GitHub
Pages workflow/site and its `pages: write`/deployment OIDC permissions were removed. Executable
actions are pinned to immutable commit SHAs. Separate main-only workflows target the protected
`production` environment. The manual Intune audit has an exact environment-scoped Entra FIC and is
restricted to trusted `main`. The expanded four-permission application grant is consented and was
independently re-read; its first live audit must still succeed before live collection is described
as operational. No client secret exists.

The public Worker runtime is deployed in fixture mode. It uses Worker-first routing only for
`/api/*`, exact methods, same-origin checks, a 64 KiB request bound, compressed-body rejection,
native client and global rate limiting, a 20-second OpenAI timeout, bounded model context/output,
a 256 KiB upstream-response bound, one non-retrying model request, and generic error responses. Logs contain request IDs,
method, route, status, and event code—not headers, IP addresses, evidence, prompts, responses, or
secrets. Cloudflare's privileged live-tail transport includes platform request metadata, so tail
access is administrative and stored invocation logs are disabled. Static assets carry
the security headers in `docs/_headers`; JSON responses set CSP, HSTS, MIME, referrer,
permissions, cross-origin, and frame protections in code. Separate liveness and fail-closed
readiness routes prevent a running Worker from being mistaken for a usable evidence runtime.

Public CI installs exact-pinned Worker dependencies, runs workerd contract tests, checks generated
bindings, and performs Wrangler dry-runs only. It has `contents: read` and no Cloudflare/OpenAI
credential. CodeQL separately analyzes Python and JavaScript/TypeScript in `build-mode: none` with
immutable GitHub-owned action pins, so pull-request code is analyzed without being executed and the
workflow receives only read access plus its code-scanning result permission. The production OpenAI
project key exists only as a Worker secret.

## Residual risks

- Read permission can expose broad Intune configuration data even though normalization is narrow.
- Pattern scans reduce but cannot eliminate re-identification risk; a human must review sanitized
  live publication.
- A valid narrative may still be incomplete, poorly worded, or operationally misleading.
- A repository administrator can bypass controls outside this codebase.
- An unauthenticated public narrative endpoint remains an abuse/spend target even with native rate
  limiting; production requires provider-side budget alerts, operational monitoring, and rollback.
