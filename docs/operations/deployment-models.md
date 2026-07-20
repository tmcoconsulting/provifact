# Deployment Models

Provifact currently combines a Python evidence engine, a credential-free synthetic build, a
protected read-only collection workflow, and a deployed Cloudflare Worker plus Static Assets
runtime. The deployed evidence package is a reviewed sanitized live projection; the public
assistant uses fixed-model OpenAI mode while local and preview builds remain fixture mode.

## 1. Local synthetic application

Public CI and local development use no tenant or OpenAI credential. The CLI regenerates the tracked
synthetic Mission package, MkDocs builds `site/`, and the public-artifact scanner verifies the exact
output. Mission Control and the settings matrix read the same package.

Use the local Worker (`npm run dev`) when testing `/api/*`. A plain static server cannot reproduce
same-origin API behavior, rate limits, readiness validation, or the assistant route.

## 2. Public Cloudflare application

The production application runs at `evidenceops.tmcoconsulting.com` and consists of:

1. the scanned MkDocs `site/` directory served through Workers Static Assets;
2. a small TypeScript Worker that runs first only for `/api/*`;
3. native per-client and global rate-limit bindings;
4. an encrypted `OPENAI_API_KEY` Worker secret;
5. repository-controlled CSP, HSTS, MIME, referrer, permissions, frame, and cross-origin headers;
6. persistent structured Worker logs containing only allowlisted operational metadata; and
7. a reviewed sanitized Mission package that drives Mission Control and the settings matrix.

The same-origin API contract is:

| Route | Method | Purpose |
| --- | --- | --- |
| `/api/health` | `GET` | Process liveness only |
| `/api/ready` | `GET` | Fails closed unless runtime configuration and the fingerprint-verified Mission package are usable |
| `/api/status` | `GET` | Non-secret mode, data-package, model, and safety state |
| `/api/ask` | `POST` | Bounded evidence question with server-selected sanitized context |
| `/api/narrative` | `POST` | Complete sanitized public-package narrative and deterministic verification path |

The current Worker/Static Assets stack is appropriate for the read-mostly Phase 1 application. A
frontend migration by itself would not add missing policy-to-control semantics. A dedicated SPA and
D1-backed API become justified when Provifact introduces authenticated private policy names,
long-term history, approvals, exceptions, multi-tenancy, or server-side matrix queries.

## 3. Protected private collection and sanitized publication

The public repository uses a manual, trusted-main collection workflow and the protected GitHub
`production` environment. GitHub Actions exchanges its environment-scoped OIDC token through an
Entra federated credential. The workflow receives four documented Microsoft Graph read-only
application permission families and has no client secret.

The collection/publication boundary:

1. calls only allowlisted Graph `GET` paths;
2. normalizes provider responses without retaining a generic raw export;
3. writes private evidence only to restricted ephemeral storage;
4. computes findings and framework mappings deterministically;
5. reconstructs a public package through an explicit allowlist;
6. verifies fingerprints and scans credentials, identities, and prohibited content;
7. optionally retains exactly one reviewed public Mission package for one day; and
8. requires a separate protected deployment action, exact audit run ID, and exact snapshot ID
   before public presentation changes.

Production never invokes the synthetic demo builder. The deployment validates that the selected
artifact came from a successful trusted-main Intune audit, requires `LIVE SANITIZED TENANT DATA`,
checks the expected snapshot before upload, and verifies that the snapshot-bound Worker version is
the sole active deployment afterward. Synthetic generation remains limited to local development,
preview, and credential-free CI.

The current public package intentionally excludes tenant policy display names, object IDs, group
names, and assignment identities. A private enterprise deployment can retain approved friendly
policy references only after a separate data-classification, access-control, and retention review.

## 4. Private enterprise presentation

A private repository or internal application may use the same collector, evaluator, sanitizer, and
verifier while placing the presentation layer behind Cloudflare Access or another approved identity
provider. Repository privacy does not weaken the private/public package boundary, OIDC restriction,
retention, sanitizer, or human-review requirements.

The recommended enterprise progression is:

- first add a stable parent-policy reference and reviewed friendly-name classification;
- then gate private evidence with SSO and role-based authorization;
- store only sanitized operational snapshots in D1 or another reviewed regional store;
- use Queues or Workflows for scheduled collection and longer-running processing; and
- preserve the GET-only provider and deterministic finding authority.

## 5. Explicitly unsupported deployment patterns

- Publishing raw Intune or Graph responses to static assets
- Browser-persisted OpenAI or Graph credentials
- Giving the public Worker Microsoft Graph write permissions
- Treating a matrix cell or AI response as a compliance certification
- Inferring CIS Level 2 or another baseline that is not loaded and reviewed
- Allowing a feature branch or fork to obtain the production OIDC identity

See the [Cloudflare Worker runbook](cloudflare-worker.md), [live collection guide](live-collection.md),
[security model](../security-model.md), and [settings matrix](../settings-matrix.md).
