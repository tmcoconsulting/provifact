# Cloudflare Worker Runtime

## Current state

The production configuration at `https://evidenceops.tmcoconsulting.com/` requires a reviewed live
sanitized Mission package and fixed `gpt-5.6-terra` Provifact Copilot. The credential-free preview
configuration remains explicit fixture mode. The custom domain/TLS, Static Assets, dual native rate
limiters, and encrypted `OPENAI_API_KEY` binding are active.

Cloudflare Workers Static Assets serves the scanned MkDocs `site/` directory. The
[`run_worker_first`](https://developers.cloudflare.com/workers/static-assets/binding/#run_worker_first)
configuration sends only `/api/*` through Worker code before static-asset handling.

## Local fixture validation

Node.js 22 or later and Python 3.12 or later are required.

```bash
npm ci --ignore-scripts --no-audit --no-fund
python -m provifact rebuild-static-demo
mkdocs build --strict
python scripts/check_public_artifacts.py site
npm run validate:worker
npm run dev
```

The development script disables Wrangler `.env` and `.dev.vars` loading. Visit the local URL
printed by Wrangler and open **Live Demo**. The status panel must show `Fixture runtime ready`.
Running the narrative produces the tracked fixture and reports `Model call performed: no`.

## Same-origin API contract

| Route | Method | Public behavior |
| --- | --- | --- |
| `/api/health` | `GET` | Process liveness only; it does not claim that evidence or OpenAI is ready |
| `/api/ready` | `GET` | Fails closed unless the runtime mode and fingerprint-verified Mission package are usable |
| `/api/status` | `GET` | Returns mode, safe Mission identity/data mode, model name, and safety flags; never a secret |
| `/api/ask` | `POST` | Accepts a bounded question plus current snapshot ID and answers from server-selected safe evidence |
| `/api/narrative` | `POST` | Accepts one sanitized public package; returns narrative plus deterministic verification |

The narrative route enforces, in order:

1. exact method and same-origin `Origin`/`Sec-Fetch-Site` checks;
2. rejection of browser `Authorization` and `X-OpenAI-Key` headers;
3. client-keyed and global native rate limits; the one-way client digest is never logged;
4. JSON-only, identity-encoded input with a 64 KiB limit and strict UTF-8;
5. the explicit publication-field policy and shared credential/public-value catalog;
6. strict public-package schema and evidence-reference validation;
7. exact fixture identity in fixture mode, or one bounded Responses API request in OpenAI mode;
8. strict model-output schema, repeated egress scan, and deterministic verifier; and
9. a human-review-required response with generated prose quarantined.

OpenAI mode pins `gpt-5.6-terra`, uses `store: false`, exposes no tools, makes no retry, times out
after 20 seconds, caps `/api/ask` at 700 output tokens and the full-package narrative route at 1,600,
and reads at most 256 KiB of response JSON. It never falls back to fixture output.
Upstream error inspection reads at most 16 KiB and retains only a strictly formatted `error.code`
or `error.type` long enough to distinguish quota exhaustion from request-rate limiting. Upstream
messages and bodies are never returned or logged; an unknown or oversized 429 remains a generic
capacity failure.
Historical operational validation proved one bounded structured response through the dedicated
service-account key. The final production configuration keeps OpenAI mode active only with the
fixed model and required secret; fixture mode remains limited to local/preview and does not silently
substitute for a failed live call.

## Secret and logging boundary

The runtime key belongs only in the encrypted
[Worker secret](https://developers.cloudflare.com/workers/configuration/secrets/). It must not be a
Wrangler plain-text variable, GitHub public-CI secret, browser value, repository file, build
argument, or log field. The Worker logs only event code, request ID, method, route, and status. It
does not log client IPs, headers, packages, prompts, model responses, or error bodies.

The production `OPENAI_API_KEY` binding now contains the only active key owned by the project
service account dedicated to Provifact. The OpenAI Platform project currently retains the
legacy `evidenceops` identifier. The service account is assigned the custom
`evidenceops-responses-runtime` role, which grants only Responses API model capability. The value is
not in GitHub, the repository, documentation, or browser state.

The `global_fetch_strictly_public` compatibility flag forces the fixed OpenAI hostname through its
public route rather than treating it as an implicit Worker-to-Worker service binding. No arbitrary
egress target is accepted from a request.

Browser BYOK is deliberately unsupported. It would make Provifact a credential processor and
requires its own browser storage, transit, redaction, support, exfiltration, and abuse design.

## Production validation and remaining operations

Completed: account/zone verification, preview and production deployment, custom-domain/TLS checks,
static/API/header tests, fixture verification, rate-limit proof, secure Worker-secret transfer,
exact Entra environment federation, required Graph application consent, a bounded verified Terra
response, a successful expanded protected-main GET-only Intune audit, separate scanned-public
artifact review, and live sanitized publication. Each final deployment must independently prove its
exact source snapshot and current `/api/status`; older run IDs below are historical evidence.

Repository-controlled static and JSON responses declare CSP, HSTS, MIME, referrer, permissions,
cross-origin, and frame protections. `/api/ready` validates the Mission schema, fingerprint, data
mode metadata, and runtime configuration; `/api/health` remains a deliberately narrower liveness
signal. Worker API responses set `Cache-Control: no-store`; the current
`/assets/data/mission-control.json` Static Assets rule detaches the broader asset cache directive
and applies `no-store`. A browser refresh or explicit snapshot check therefore does not reuse the
prior deployment's status or Mission payload.

The protected production workflow has no synthetic-build branch. A reviewer must supply a
successful trusted-main Intune audit run ID and the exact reviewed `mission-…` snapshot ID. The
workflow rejects an absent, malformed, unsuccessful, non-main, or wrong-workflow selector; requires
one fingerprint-valid `LIVE SANITIZED TENANT DATA` artifact; checks its snapshot before the upload;
and proves that the snapshot-bound Worker version is the only active version at 100% traffic after
the upload. Local and preview workflows remain the only synthetic paths.

Review the one-file sanitized artifact before dispatch and record its validated `snapshot_id`.
Then supply both values explicitly:

```bash
gh workflow run deploy-cloudflare.yml --ref main \
  -f confirm_production_deploy=true \
  -f sanitized_audit_run_id='<successful-reviewed-audit-run-id>' \
  -f expected_source_snapshot_id='mission-<24-lowercase-hex>'
```

An omitted or mismatched value stops before deployment. Enabling the separate
`CLOUDFLARE_DEPLOY_ENABLED` environment gate remains an operator-controlled reviewed-window action;
restore it to `false` immediately after the run.

Remaining operations:

1. keep `CLOUDFLARE_DEPLOY_ENABLED=false` outside an explicitly reviewed deployment window;
2. review Cloudflare observability/alert retention in the dashboard;
3. use `wrangler deployments list --env production` and
   `wrangler rollback <known-good-version> --env production` for rollback; and
4. confirm `/api/status` reports the fixed model and live package after each deployment.

The active account token `evidenceops-github-deploy` has only `Workers Scripts Write` on the TMCO Consulting
account, and the protected workflow proved that GitHub holds that working token without
revealing its value. The first upload activated the reviewed Worker and assets, then Wrangler tried
to inspect the existing zone route because the custom domain was still declarative and correctly
received an authorization error. Production status nevertheless confirmed the exact live sanitized
snapshot. Routine upload configuration now omits route/domain management; the already-provisioned
custom domain remains a separately managed control-plane resource. Cloudflare scopes Workers Script
write at the account, not an individual Worker, so manual main-only execution, the fixed Worker
name, exact snapshot check, and protected environment are necessary residual controls.

The first route-isolated protected retry uploaded the reviewed bundle successfully. Its immediate
custom-domain curl received a Cloudflare Bot Fight Mode managed challenge because the caller was a
cloud-hosted command-line runner; Cloudflare Security Analytics independently correlated the exact
timestamp. The domain returned the correct snapshot and HTTPS/security headers from an independent
network immediately afterward. Provifact preserves Bot Fight Mode and instead attaches the
reviewed snapshot ID as a Worker-version message, then verifies through Wrangler that the exact
version is the sole active deployment at 100% traffic. Public HTTP, browser rendering, and header
validation remain a separate unauthenticated post-run operator check.

Protected-main deployment run `29703512007` completed that corrected path. The snapshot-bound
version was the sole active deployment at 100% traffic, and independent HTTPS, browser, status,
Mission-package, TLS, and header checks passed. Bot Fight Mode remained enabled, and the emergency
deployment flag was restored and re-read as `false`.

Cloudflare documents [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/),
[custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/),
[versions and deployments](https://developers.cloudflare.com/workers/versions-and-deployments/),
[Static Assets response headers](https://developers.cloudflare.com/workers/static-assets/headers/),
and [rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/).
