# Roadmap

Roadmap items describe intent, not operational capability or delivery commitments.

## Phase 0 — complete foundation

- Public Apache-2.0 repository, governance, CI, and protected main
- Historical GitHub Pages foundation (deployment path retired during Phase 1 security review)
- Provider-neutral domain, deterministic drift, fail-closed sanitizer, and synthetic demo
- Security/data-handling boundaries and Build Week evidence

## Phase 1 — Build Week vertical slice

- [x] Preserve the schema-v1 proof and add a strict Mission Control public projection
- [x] Implement the comprehensive GET-only Apple resource-family collector with partial gaps
- [x] Pin and hash the 98-rule mSCP macOS CIS Level 1 demo inventory
- [x] Approve the machine-readable TMCO Consulting technical demo baseline without claiming certification
- [x] Add four exact reviewed provider mappings, keep the fifth desired mapping explicitly
      unreviewed, and implement assignment/conflict drift with evidence traceability
- [x] Keep iOS/iPadOS posture visible but outside the macOS alignment denominator
- [x] Add allowlist publication, private normalized storage, and shared public/model egress scans
- [x] Build the dynamic synthetic Mission Control dashboard and bounded `/api/ask` assistant
- [x] Preserve local/preview fixture mode, typed-claim verification, and prose quarantine
- [x] Configure the exact environment-scoped Entra federated identity
- [x] Grant and independently verify the complete four-permission read-only application set
- [x] Run the expanded manual protected post-merge audit and retain no private artifact
- [x] Perform a bounded service-account GPT-5.6 request and configure fixed-model production mode
- [x] Publish one separately reviewed sanitized live Mission package through the protected handoff

Public CI never performs live collection.

## Evidence navigation and matrix — current review slice

- [x] Reorganize the site around product, methodology, operations, and project-history paths
- [x] Add a setting-level matrix for observed value, approved target, deterministic state, reviewed
      framework identifiers, evidence references, and required technical change
- [x] Pair the FileVault assistant task with deterministic package context without expanding model egress
- [x] Mark CIS Level 2 as not loaded rather than inferring it from Level 1 or another crosswalk
- [ ] Preserve a reviewed parent-policy reference in the private normalized model so an authenticated
      deployment can show the actual Intune policy that supplied each setting
- [ ] Define the data-classification, authorization, and retention rules for friendly tenant policy names
- [ ] Load and independently review a CIS Level 2 baseline before displaying Level 2 technical alignment
- [ ] Work through the visible 94-rule backlog and expand exact reviewed provider mappings only when
      provider identifiers, typed targets, collection completeness, and ownership are verified
- [x] Add matrix/evidence tests for aligned, value-drift, assignment, conflict, missing, collection-gap,
      unsupported, and baseline-not-loaded states
- [x] Flatten documented nested Settings Catalog groups so FileVault child settings join by exact
      provider ID without treating non-Apple policies as Apple collection gaps
- [x] Present desired, observed, missing/evidence-gap, and technical STIG cross-reference views in a
      full-width NOC-style Mission Control while keeping STIG explicitly not loaded
- [x] Show all 98 approved Level 1 rules by default with authoritative pinned-source titles and
      separate the 94-rule implementation backlog from the deterministic four-rule denominator
- [x] Group implementation work by baseline section and distinguish exact provider-mapping review
      from management/evidence-path planning
- [x] Add a bounded site-wide assistant contract with exact typed claims, selected evidence, and
      deterministic context selection; free prose remains quarantined

## Cloudflare runtime — live sanitized production deployed

- [x] Add exact-pinned Worker tooling and Static Assets configuration for `site/`
- [x] Implement `/api/status`, `/api/health`, `/api/ready`, `/api/narrative`, and `/api/ask` with
      method/origin/body/rate/timeout limits
- [x] Preserve explicit fixture mode with no model call or synthetic fallback from OpenAI mode
- [x] Add workerd tests, allowlisted logging, shared egress scans, security headers, and dry-run CI
- [x] Independently review the Worker runtime and production configuration
- [x] Configure a project-scoped Provifact runtime key as a Worker secret (never a repository/CI secret)
- [ ] Verify Cloudflare/OpenAI abuse monitoring, log retention, alert ownership, and rollback rehearsal
- [x] Create the Worker/custom domain at `evidenceops.tmcoconsulting.com` and verify DNS/TLS
- [x] Add disabled-by-default least-privilege GitHub deployment orchestration after manual validation
- [x] Store `CLOUDFLARE_API_TOKEN` by name in the protected production environment
- [x] Verify the account deployment token has only `Workers Scripts Write` and prove its GitHub
      secret binding without exposing the value
- [x] Merge the Bot-Fight-safe control-plane deployment proof and complete one green orchestration
      retry; the emergency enable flag remains `false`
- [x] Configure the dedicated OpenAI project budget alerts and model limits
- [ ] Complete the coordinated external brand cutover: repository/OIDC subject, custom domain,
      OpenAI project label, and infrastructure display names with rollback redirects
- [x] Validate bounded live `gpt-5.6-terra`; keep fixture mode only for local and preview

Phase 1 technical completion is recorded in the
[final implementation report](build-week/final-implementation-report.md). External submission,
media review, and the private `/feedback` identifier remain operator tasks rather than product
capabilities.

## When to change the application stack

Keep the current MkDocs Material plus Cloudflare Worker/Static Assets architecture for the public,
read-mostly evidence application. It already provides fast static delivery, same-origin APIs,
security headers, rate limits, and a simple reviewable deployment artifact.

Introduce a dedicated frontend application and persistent Cloudflare services only when the product
requires capabilities the current stack cannot safely express:

- Cloudflare Access or equivalent authentication for private policy names and evidence
- D1-backed sanitized history, approvals, exceptions, saved filters, or multi-tenant state
- Queues or Workflows for scheduled collection and long-running processing
- Server-side policy/control search over data that cannot be public
- Role-aware auditor, endpoint-admin, and security-leader views

A framework or CSS rewrite alone will not solve missing policy-to-setting joins or baseline mappings.
Those data-model contracts come first.

## Later application scope

- Add an independent reviewer for the expanded permission/normalization contract
- Re-evaluate Settings Catalog when Microsoft publishes an adequate v1.0 equivalent
- Add sanitized operational snapshot persistence only after a separate retention/access review
- Add a signed public-package manifest and broader narrative evaluation corpus
- Design explicit exception ownership/expiry without automatic exception grants
- Explore Jamf and Workspace ONE adapters against the same schema contract
- Reassess request-scoped BYOK only after a browser-key, logging, and abuse threat model

## Explicitly deferred or rejected

- Intune/Graph writes, automatic remediation, assignment, or rollback
- Generic raw-tenant data lake or public managed-device identity inventory
- Scheduled live workflow in the public repository
- Directory-wide permissions or any read permission not tied to a documented collector family
- Model tools, autonomous publication, exceptions, or compliance verdicts
- Browser-persisted API keys or public-CI OpenAI credentials
- Claims of complete CIS/STIG/NIST/CMMC coverage
- Inferred CIS Level 2 results without a loaded, reviewed Level 2 baseline
- Code/history imports from unrelated endpoint-management repositories
