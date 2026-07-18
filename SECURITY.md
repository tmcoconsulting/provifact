# Security policy

## Supported versions

EvidenceOps is pre-release software. Only the current `main` branch receives security fixes during
Phase 0.

## Reporting a vulnerability

Use the repository's **Security** tab and GitHub private vulnerability reporting. Do not include
credentials, real tenant data, device data, or exploit details in a public issue or discussion.

If private reporting is unavailable, open a public issue containing no sensitive details and ask a
maintainer to establish a private channel.

## Scope and boundaries

- Phase 0 has no live Microsoft Graph integration and performs no endpoint-management writes.
- Synthetic fixtures are test data, not representative production exports.
- The public site is not an authorization source or compliance certification.
- AI-generated narrative is not implemented in Phase 0 and will never replace deterministic
  evidence or human approval.

See `docs/security-model.md`, `docs/data-handling.md`, and `docs/threat-model.md` for the current
design.
