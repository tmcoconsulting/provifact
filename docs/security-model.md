# Security Model

EvidenceOps assumes endpoint inventory and configuration history can identify people,
organizations, and managed devices. Collection is therefore privileged even when it is read-only.

## Security invariants

1. **No management-plane writes.** Provider interfaces and credentials are collection-only.
2. **No public raw data.** Raw live responses cannot enter GitHub Pages or public workflow
   artifacts.
3. **Fail closed on schema change.** Unknown fields stop sanitization and publication.
4. **Short-lived future cloud authentication.** Live automation will prefer workload identity over
   stored client secrets.
5. **Deterministic evidence remains authoritative.** Generated narrative cannot alter findings.
6. **Human approval remains visible.** Exceptions, publication, and material decisions retain a
   human review boundary.
7. **Fork isolation.** Untrusted pull-request code never receives privileged credentials.

## Permission boundary

Phase 0 requests no Microsoft Graph permission. A future Intune adapter must justify the smallest
approved application or delegated **read** permission for each endpoint it calls. Graph write
permissions and Intune mutation operations are out of scope.

Microsoft's [permissions reference](https://learn.microsoft.com/graph/permissions-reference) is the
authority for permission names and privilege classifications. The design will also follow
[Microsoft Graph best practices](https://learn.microsoft.com/graph/best-practices-concept), including
least privilege, safe credential handling, and resilient API use.

## Workflow boundary

GitHub workflows declare explicit job permissions. Validation receives read-only repository
content. Pages deployment receives `pages: write` and `id-token: write` only in the deployment
workflow and protected environment. Repository-wide Actions defaults remain read-only.

GitHub documents both
[least-privilege workflow permissions](https://docs.github.com/actions/security-for-github-actions/security-guides/automatic-token-authentication#modifying-the-permissions-for-the-github_token)
and [immutable action pinning](https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#using-third-party-actions).

## Model boundary

GPT-generated text is analysis, not evidence. Future prompts receive only policy-approved evidence
fields, request citations to evidence references, and are evaluated for unsupported claims. Output
is labeled and reviewed before it becomes part of an evidence package.

## Non-goals

- Endpoint remediation or policy assignment
- Compliance certification
- Storage of a tenant's complete inventory
- Publication of reversible identifiers
- Autonomous exception approval
