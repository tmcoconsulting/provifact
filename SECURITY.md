# Security policy

## Supported versions

EvidenceOps is pre-release Phase 1 software. Only the current `main` branch receives security fixes.
Dated Build Week validation records describe historical checkpoints and are not separate supported
release lines.

## Reporting a vulnerability

Use the repository's **Security** tab and GitHub private vulnerability reporting. Do not include
credentials, real tenant data, device data, policy identifiers, or exploit details in a public issue
or discussion.

If private reporting is unavailable, open a public issue containing no sensitive details and ask a
maintainer to establish a private channel.

## Current scope and boundaries

- The Microsoft Intune integration is comprehensive for the documented managed-Apple resource
  families but remains GET-only. No create, update, delete, assignment, remediation, or rollback
  method exists.
- Protected live collection uses GitHub OIDC and four documented Microsoft Graph read-only
  application permission families. Public CI receives no tenant credential.
- Private normalized evidence and raw provider responses are never eligible for direct publication.
  Public output must pass the strict allowlist, fingerprint, credential, content, and human-review
  gates.
- Production serves a reviewed sanitized Mission package through Cloudflare Workers Static Assets.
  Tenant, device, user, group, assignment, credential, and raw Graph values are not public.
- `/api/ask` and `/api/narrative` are same-origin, bounded, rate-limited routes. The default public
  mode is fixture-based and makes no OpenAI model call.
- When OpenAI mode is explicitly enabled, only sanitized bounded context is sent with `store: false`
  and no tools. Typed claims and references are verified; generated prose remains subject to human
  review.
- The public site, technical-alignment result, and generated explanation are not authorization
  sources, compliance certifications, assessor conclusions, exceptions, or risk acceptance.

See `docs/security-model.md`, `docs/data-handling.md`, `docs/threat-model.md`, and
`docs/operations/incident-response.md` for the current design and response procedures.
