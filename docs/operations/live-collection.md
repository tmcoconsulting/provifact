# Future Live Collection

!!! warning "Not operational in Phase 0"
    EvidenceOps contains no Microsoft Graph client, tenant credentials, collection workflow, or
    live-data storage path. This page records the required design boundary for later review.

## Intended flow

1. A protected GitHub Actions environment authorizes a specific workflow and branch.
2. GitHub obtains a short-lived Azure credential through workload identity federation.
3. An Entra application receives only separately approved Microsoft Graph read permissions.
4. The collector retrieves the minimum required fields and normalizes them in restricted memory or
   encrypted temporary storage.
5. Raw responses remain private, ephemeral, or subject to a documented restricted retention policy.
6. Sanitization runs before any public-output path.
7. A schema and policy gate validates the sanitized package.
8. Only a sanitized or synthetic package can become a Pages artifact.

GitHub documents [OpenID Connect with Azure](https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-azure)
and Microsoft documents [workload identity federation](https://learn.microsoft.com/entra/workload-id/workload-identity-federation).

## Required approval package

Before implementation, a pull request must include:

- exact Graph endpoints and fields;
- exact read permissions and Microsoft permission-reference links;
- authentication subject and audience restrictions;
- raw, normalized, sanitized, and published data inventories;
- retention and artifact settings;
- fork and pull-request threat analysis;
- fail-closed schema tests;
- a rollback and credential-revocation procedure; and
- human approval from the data and security owner.

## Forbidden design choices

- Client secrets committed to GitHub or long-lived workflow credentials
- Microsoft Graph write permissions
- Intune create, update, delete, assign, retire, wipe, sync, or remediation operations
- Raw-response upload to a public or broadly accessible artifact
- Live collection from fork-originated pull requests
- Publication that continues after an unknown field or scan failure
