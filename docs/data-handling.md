# Data Handling

## Public-data rule

Any public static artifact may contain only curated synthetic data or a live-derived package that
passed schema validation, allowlist construction, reference validation, content and credential
scans, and human publication review. The current Cloudflare deployment serves only the tracked
synthetic Mission package.

## Collection minimization

The expanded Apple adapter requests only fields needed for aggregate device posture, policy and
setting normalization, assignment scope, application governance, compliance metadata, enrollment,
and Apple service health. Device and source object IDs may exist only in the private normalized
package when needed for deterministic joins. Device/user names, serials, hardware/network values,
free-form descriptions, group names, tenant domains, tokens, certificates, and raw response bodies
are not requested or are rejected before public construction.

## Prohibited or transformed values

| Category | Examples | Public action |
| --- | --- | --- |
| Tenant/cloud identity | Tenant, subscription, app, service-principal IDs | Pseudonymize or reject |
| People | UPNs, emails, names | Pseudonymize or reject |
| Devices | Names, serials, IMEI/MEID, hardware/managed-device IDs | Pseudonymize or reject |
| Directory/assignment | Object/group IDs and real group names | Pseudonymize or reject |
| Network | IP addresses and internal domains | Pseudonymize or reject |
| Credentials | Tokens, secrets, keys, certificates, authorization headers | Drop and fail scans |
| Correlation | Any value that can reasonably re-identify a tenant/person | Classify or reject |

Deterministic pseudonyms are used only where correlation is necessary. They are HMAC-derived with
runtime key material of at least 32 bytes. EvidenceOps never persists that key.

## Lifecycle and retention

| Stage | Location | Retention |
| --- | --- | --- |
| Graph response | Process memory | Request lifetime only |
| Private normalized package | Operator-selected ignored directory | Explicit 1–30 days for the expanded Apple slice |
| Sanitized package | Reviewed workspace | Publication policy |
| Public synthetic package | Tracked data/local static artifact | Repository/build policy |
| Tokens/pseudonym key | Process environment/memory | Current operation only |
| OpenAI project service-account key | Cloudflare Worker secret | Operator-managed rotation and immediate revocation on incident |

Private packages are written without overwrite at mode `0600` where supported. EvidenceOps records
the deletion deadline but does not silently delete operator data; the operator must remove the
package and backups securely at expiry.

## TMCO identity

TMCO Consulting, LLC is the project sponsor and copyright holder for its original EvidenceOps work.
Public company identity may appear in documentation. That authorization does not extend to TMCO
tenant identifiers, directory/device data, credentials, or configuration exports. The synthetic
static demo does not represent TMCO production state.
