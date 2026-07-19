# Cloudflare Worker Runtime

## Current state

The Worker runtime is deployed at `https://evidenceops.tmcoconsulting.com/` with a live sanitized
Mission package and explicit fixture narrative mode. The credential-free preview is available at
`https://evidenceops-preview.tmco-consulting.workers.dev/`. The custom domain/TLS, Static Assets,
dual native rate limiters, and encrypted `OPENAI_API_KEY` binding are active. The default fixture
narrative mode does not call OpenAI.

Cloudflare Workers Static Assets serves the scanned MkDocs `site/` directory. The
[`run_worker_first`](https://developers.cloudflare.com/workers/static-assets/binding/#run_worker_first)
configuration sends only `/api/*` through Worker code before static-asset handling.

## Local fixture validation

Node.js 22 or later and Python 3.12 or later are required.

```bash
npm ci --ignore-scripts --no-audit --no-fund
python -m evidenceops rebuild-static-demo
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
after 20 seconds, caps output at 1,600 tokens, and reads at most 256 KiB of response JSON. It never
falls back to fixture output.
Upstream error inspection reads at most 16 KiB and retains only a strictly formatted `error.code`
or `error.type` long enough to distinguish quota exhaustion from request-rate limiting. Upstream
messages and bodies are never returned or logged; an unknown or oversized 429 remains a generic
capacity failure.
One bounded production request through the dedicated service-account key returned structured
`gpt-5.6-terra` output. The deterministic verifier accepted the complete typed-claim set, rejected
none, quarantined every prose field, and retained the human-review boundary. Production was then
returned to explicit fixture mode. Fixture mode makes no OpenAI request and does not silently fall
back from a failed live call.

## Secret and logging boundary

The runtime key belongs only in the encrypted
[Worker secret](https://developers.cloudflare.com/workers/configuration/secrets/). It must not be a
Wrangler plain-text variable, GitHub public-CI secret, browser value, repository file, build
argument, or log field. The Worker logs only event code, request ID, method, route, and status. It
does not log client IPs, headers, packages, prompts, model responses, or error bodies.

The production `OPENAI_API_KEY` binding now contains the only active key owned by the dedicated
EvidenceOps project service account. The service account is assigned the custom
`evidenceops-responses-runtime` role, which grants only Responses API model capability. The value is
not in GitHub, the repository, documentation, or browser state.

The `global_fetch_strictly_public` compatibility flag forces the fixed OpenAI hostname through its
public route rather than treating it as an implicit Worker-to-Worker service binding. No arbitrary
egress target is accepted from a request.

Browser BYOK is deliberately unsupported. It would make EvidenceOps a credential processor and
requires its own browser storage, transit, redaction, support, exfiltration, and abuse design.

## Production validation and remaining gates

Completed: account/zone verification, preview and production deployment, custom-domain/TLS checks,
static/API/header tests, fixture verification, rate-limit proof, secure Worker-secret transfer,
exact Entra environment federation, required Graph application consent, one bounded verified Terra
response, one successful expanded protected-main GET-only Intune audit, the separate scanned-public
artifact review, and live sanitized publication. The public assistant remains in fixture narrative
mode.

Repository-controlled static and JSON responses declare CSP, HSTS, MIME, referrer, permissions,
cross-origin, and frame protections. `/api/ready` validates the Mission schema, fingerprint, data
mode metadata, and runtime configuration; `/api/health` remains a deliberately narrower liveness
signal.

Remaining:

1. merge the routine-deployment fix that removes the already-provisioned custom domain from the
   Wrangler upload configuration, then complete one green protected workflow retry;
2. keep `CLOUDFLARE_DEPLOY_ENABLED=false` outside an explicitly reviewed deployment window;
3. review Cloudflare observability/alert retention in the dashboard;
4. use `wrangler deployments list --env production` and
   `wrangler rollback <known-good-version> --env production` for rollback; and
5. leave OpenAI mode off by default unless a separately reviewed operational policy authorizes it.

The active account token `evidenceops-github-deploy` has only `Workers Scripts Write` on the TMCO
Consulting account, and the protected workflow proved that GitHub holds that working token without
revealing its value. The first upload activated the reviewed Worker and assets, then Wrangler tried
to inspect the existing zone route because the custom domain was still declarative and correctly
received an authorization error. Production status nevertheless confirmed the exact live sanitized
snapshot. Routine upload configuration now omits route/domain management; the already-provisioned
custom domain remains a separately managed control-plane resource. Cloudflare scopes Workers Script
write at the account, not an individual Worker, so manual main-only execution, the fixed Worker
name, exact snapshot check, and protected environment are necessary residual controls.

Cloudflare documents [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/),
[custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/),
and [rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/).
