# Deployment Models

Phase 1 implements the credential-free local build, Python application core, and a deployed
Worker/static-assets runtime. The Entra trust and four required Graph application permissions are
configured; a protected GET-only tenant audit, separately reviewed sanitized publication, and one
bounded verified model response have completed. The public assistant remains in fixture narrative
mode by default.

## 1. Current local synthetic static artifact

Public CI uses no tenant or OpenAI credential. It regenerates tracked synthetic data, builds
`site/` with MkDocs, and scans that directory. Operators can serve the result locally. `site/` is a
build artifact, not evidence that a hosting platform or production API is operational.

## 2. Current public Cloudflare deployment

The public runtime code is a Worker intended for `evidenceops.tmcoconsulting.com`, serving the
scanned `site/` directory as static assets. Only `/api/*` runs Worker code first; the same-origin
endpoints are `/api/status` and `/api/narrative`. Cloudflare documents selective
[`run_worker_first`](https://developers.cloudflare.com/workers/static-assets/binding/#run_worker_first)
routing and encrypted [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/).

The repository now includes:

1. exact-pinned Wrangler/TypeScript/workerd tooling and a `site/` assets configuration;
2. a small typed Worker with explicit method, origin, body-size, timeout, and response bounds;
3. a non-secret `/api/status` contract;
4. `/api/narrative`, which repeats publication scanning and preserves typed-claim verification;
5. native rate-limit binding, allowlisted logs, static CSP/security headers, and fixture mode; and
6. credential-free CI contract tests, generated-binding checks, and bundle dry-run.

The Worker and preview exist, the custom domain/TLS are active, dual native rate limiters are
bound, and `OPENAI_API_KEY` exists only as an encrypted Worker secret. The protected GitHub
environment contains a working account-scoped deployment token with only Workers Scripts write
access; its value is not retrievable from the repository. Production serves a separately reviewed,
fail-closed sanitized live Mission package while the assistant remains in fixture narrative mode.
The routine deployment workflow is disabled outside an explicitly reviewed deployment window. See
the [Worker runbook](cloudflare-worker.md).

OpenAI recommends keeping API keys out of code/public repositories and exposing them through a
secret manager. It also recommends human review for high-stakes output:
[production practices](https://developers.openai.com/api/docs/guides/production-best-practices) and
[safety practices](https://developers.openai.com/api/docs/guides/safety-best-practices).

Fixture mode must remain available when credits or the runtime key are unavailable. Browser BYOK
is deferred: a browser-supplied key would cross the Worker, logging, support, and abuse boundaries.
If later approved, it must be request-scoped, never persisted or logged, never written to browser
storage, and clearly separated from the TMCO-funded service-account path.

## 3. Protected private collection and sanitized publication

The current public repository uses a manual, main-only collection workflow and the protected
`production` environment. GitHub Actions authenticates to Entra with OIDC/workload identity
federation; the federated subject is constrained to this repository and environment. The expanded
Apple proof uses the exact four read-only permission families documented in the machine-readable
manifest. Protected-main collection and one explicitly selected sanitized publication have
completed; no feature branch can obtain the identity.

The private workflow:

1. request `id-token: write` only in the collection job;
2. exchange the GitHub OIDC token for a short-lived Entra token;
3. collect to ephemeral restricted storage without logging responses;
4. sanitize and run policy/content tests before any artifact upload;
5. upload only the selected sanitized package with one-day retention;
6. require protected-environment approval before any sanitized package or deployment crosses its
   intended trust boundary; and
7. deny secrets and privileged jobs to fork-originated pull requests.

GitHub explains that OIDC avoids duplicated long-lived cloud secrets and yields job-scoped,
short-lived credentials in its [OIDC security guide](https://docs.github.com/actions/concepts/security/openid-connect).
Microsoft documents the corresponding
[workload identity federation](https://learn.microsoft.com/entra/workload-id/workload-identity-federation)
trust model.

The repository also includes a deliberately non-executable
[`examples/private-repository/intune-oidc.yml`](https://github.com/tmcoconsulting/evidenceops/blob/main/examples/private-repository/intune-oidc.yml)
reference. It is outside `.github/workflows`, pins actions to commit SHAs, collects with a
process-scoped Graph token, and uploads nothing. Copy it only after reviewing the Entra subject,
audience, tenant/application IDs, environment protection, retention, and publication topology.

## 4. Private corporate or enterprise presentation

A private repository may orchestrate the same collection and sanitization controls and present the
application through an access-controlled Worker or another approved internal platform. Repository
privacy does not weaken the private/public package boundary, OIDC restriction, retention,
sanitizer, verifier, or human approval gates, and it is never a reason to publish raw Graph
responses.
