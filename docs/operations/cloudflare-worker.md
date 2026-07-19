# Cloudflare Worker Runtime

## Current state

The Worker runtime is deployed at `https://evidenceops.tmcoconsulting.com/` in explicit fixture
mode. The credential-free preview is available at
`https://evidenceops-preview.tmco-consulting.workers.dev/`. The custom domain/TLS, Static Assets,
dual native rate limiters, and encrypted `OPENAI_API_KEY` binding are active. Fixture mode does not
call OpenAI.

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
| `/api/status` | `GET` | Returns mode, model name, synthetic/public boundary, and safety flags; never a secret |
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
The public production deployment remains in explicit fixture mode while the OpenAI project returns
capacity unavailable. A bounded production request proved that the Worker reached OpenAI, but no
model output was returned or accepted. Fixture mode makes no OpenAI request and does not silently
fall back from a failed live call.

## Secret and logging boundary

The runtime key belongs only in the encrypted
[Worker secret](https://developers.cloudflare.com/workers/configuration/secrets/). It must not be a
Wrangler plain-text variable, GitHub public-CI secret, browser value, repository file, build
argument, or log field. The Worker logs only event code, request ID, method, route, and status. It
does not log client IPs, headers, packages, prompts, model responses, or error bodies.

The current control-plane session could verify that `OPENAI_API_KEY` exists as a Worker secret, but
could not verify its present OpenAI owner. The last directly observed transfer used a
project-scoped user-owned key. Service-account replacement and revocation of that temporary key
must therefore remain open gates until the OpenAI project UI and Worker secret are both checked.

The `global_fetch_strictly_public` compatibility flag forces the fixed OpenAI hostname through its
public route rather than treating it as an implicit Worker-to-Worker service binding. No arbitrary
egress target is accepted from a request.

Browser BYOK is deliberately unsupported. It would make EvidenceOps a credential processor and
requires its own browser storage, transit, redaction, support, exfiltration, and abuse design.

## Production validation and remaining gates

Completed: account/zone verification, preview and production deployment, custom-domain/TLS checks,
static/API/header tests, fixture verification, rate-limit proof, initial secure Worker-secret
transfer, exact Entra environment federation, and required Graph application consent. The bounded
live request reached OpenAI and returned capacity unavailable; no output was accepted. Production
was returned to fixture mode.

Remaining:

1. sign in to **OpenAI Platform → EvidenceOps project → Service accounts**; create or verify
   `evidenceops-cloudflare-runtime`, create one restricted project key, transfer it directly to the
   existing Worker secret, verify service-account ownership, and revoke the temporary user-owned
   key;
2. in **EvidenceOps project → Limits**, set a `$5` monthly soft budget with 50%, 80%, and 100%
   alerts, allow only `gpt-5.6-terra` where supported, and set at most 5 RPM and 25,000 TPM (or the
   lowest accepted values); verify usable billing. The budget is an alert, not a hard cap;
3. independently verify that the token stored as the protected GitHub environment secret
   `CLOUDFLARE_API_TOKEN` is restricted to the TMCO Consulting account with Account `Workers
   Scripts Edit`; do not add zone, route, DNS, KV, R2, account-settings, membership, user-details,
   billing, or unrelated-account access. The workflow supplies the exact account ID, so it does not
   need membership discovery. The secret exists by name, but its value and scope have not been
   retrieved or claimed as verified;
4. keep `CLOUDFLARE_DEPLOY_ENABLED=false` until the token scope is validated against the exact
   workflow, then enable deployment only after review;
5. review Cloudflare observability/alert retention in the dashboard;
6. after merge, manually run the protected GET-only Intune audit and retain only sanitized counts;
7. use `wrangler deployments list --env production` and
   `wrangler rollback <known-good-version> --env production` for rollback; and
8. enable OpenAI mode only after a single bounded request succeeds and the dashboard label is
   revalidated.

The current workflow uses `wrangler deploy` while the custom domain remains declarative in
`wrangler.jsonc`. Cloudflare's [Attach Domain API](https://developers.cloudflare.com/api/resources/workers/subresources/domains/methods/update/)
accepts `Workers Scripts Write`, and the existing custom-domain operation does not require a zone
route or DNS permission. Cloudflare scopes `Workers Scripts Edit` at the account resource, not an
individual Worker, so protected-main execution, the fixed Worker name, and environment review are
necessary residual controls even for the narrowest practical token. This proposed minimum still
requires a real token validation before deployment is enabled.

Cloudflare documents [Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/),
[custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/),
and [rollbacks](https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/).
