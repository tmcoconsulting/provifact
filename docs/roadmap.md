# Roadmap

Roadmap items describe intent, not operational capability or delivery commitments.

## Phase 0 — complete foundation

- Public Apache-2.0 repository, governance, CI, and protected main
- Historical GitHub Pages foundation (deployment path retired during Phase 1 security review)
- Provider-neutral domain, deterministic drift, fail-closed sanitizer, and synthetic demo
- Security/data-handling boundaries and Build Week evidence

## Phase 1 — narrow proof on this branch

- Ten versioned schema-v1 objects with tamper-evident IDs/fingerprints
- GET-only Graph v1.0 Intune adapter for two macOS general-configuration fields
- Exact read-permission manifest and in-memory attended authentication
- Private package writer, explicit retention, and fail-closed public publication
- Four-state vendor-neutral desired/observed demonstration
- Optional GPT-5.6 structured narrative plus typed-claim/prose-quarantine verifier
- Credential-free end-to-end CLI and polished local synthetic static walkthrough
- Shared credential detection across publication, repository/static scans, and model egress

- [x] Configure the environment-scoped Entra federated identity and grant administrator consent to
  application `DeviceManagementConfiguration.Read.All`
- [ ] Run the manual protected post-merge audit and record sanitized counts only

Public CI never performs live collection.

## Cloudflare runtime — fixture production deployed

- [x] Add exact-pinned Worker tooling and Static Assets configuration for `site/`
- [x] Implement `/api/status` and `/api/narrative` with method/origin/body/rate/timeout limits
- [x] Preserve explicit fixture mode with no model call or synthetic fallback from OpenAI mode
- [x] Add workerd tests, allowlisted logging, shared egress scans, security headers, and dry-run CI
- [x] Independently review the Worker runtime and production configuration
- [x] Configure an EvidenceOps Project key as a Worker secret (never a repository/CI secret)
- [ ] Verify Cloudflare/OpenAI budget alerts, abuse monitoring, log retention, and rollback
- [x] Create the Worker/custom domain at `evidenceops.tmcoconsulting.com` and verify DNS/TLS
- [x] Add disabled-by-default least-privilege GitHub deployment orchestration after manual validation
- [x] Store `CLOUDFLARE_API_TOKEN` by name in the protected production environment
- [ ] Verify the Cloudflare token scope and enable the protected workflow; deployment remains
      disabled with `CLOUDFLARE_DEPLOY_ENABLED=false`
- [ ] Configure OpenAI budget alerts/limits and enable live mode only after usable capacity exists

## Later application scope

- Privately validate the two documented Graph endpoints and record only sanitized metadata
- Add an independent reviewer for the permission/normalization contract
- Evaluate Settings Catalog support only after confirming a supported v1.0 contract
- Add a signed public-package manifest and broader narrative evaluation corpus
- Design explicit exception ownership/expiry without automatic exception grants
- Explore Jamf and Workspace ONE adapters against the same schema contract
- Reassess request-scoped BYOK only after a browser-key, logging, and abuse threat model

## Explicitly deferred or rejected

- Intune/Graph writes, automatic remediation, assignment, or rollback
- Generic raw-tenant data lake or managed-device identity inventory
- Scheduled live workflow in the public repository
- Directory-wide or managed-device permissions for convenience
- Model tools, autonomous publication, exceptions, or compliance verdicts
- Browser-persisted API keys or public-CI OpenAI credentials
- Claims of complete CIS/STIG/NIST/CMMC coverage
- Code/history imports from unrelated endpoint-management repositories
