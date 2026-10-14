# Private policy lineage and public matrix

Normalized policy relationships carry a stable private `parent_policy_ref`; their parent carries
`private_policy_ref`. The reference is derived from provider, resource family, and source object ID,
independently of collection time or friendly name. This unkeyed source-derived reference is a
confidential join key, not a safe public pseudonym.

Each record preserves its resource family, API version, and exact private source endpoint. Settings
Catalog policy names use Microsoft's documented `name` field; other reviewed policy families use
`displayName`. Names never select a provider mapping. See Microsoft's
[configuration-policy reference](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfigv2-devicemanagementconfigurationpolicy?view=graph-rest-beta).

Multiple policies remain separate sources. Different values produce **Conflicting policy**;
effective precedence remains **unknown**, and Provifact does not choose a winner. Orphan settings,
incomplete settings collection, and unavailable assignment collection produce collection gaps.

## Classification

| Field | Classification | Private handling | Public/model handling |
| --- | --- | --- | --- |
| Friendly policy names | Confidential tenant configuration | Normalized package only | Omitted |
| Group names | Confidential directory context | Not collected | Excluded |
| Assignment object/group IDs and exact scope | Confidential tenant configuration | Normalized package only | Reviewed aggregate summaries only |
| Policy/source object IDs and endpoints containing IDs | Confidential tenant identifiers | Normalized package only | Omitted; public references use runtime-keyed HMAC |
| `private_policy_ref` / `parent_policy_ref` | Confidential source-derived correlation | Normalized package only | Omitted |
| Public `parent_resource_refs` | Reviewed pseudonymous references | Publication validation | Allowed in sanitized Mission/matrix |
| Synthetic friendly labels | Curated fixture data | Local/preview fixture | Explicit synthetic mode only |

A tenant-provided pseudonymous label cannot enter the public contract on reviewer judgment alone.
Only constructed HMAC references and generic labels are permitted. Another label requires separate
schema, classification, sanitizer, and privacy review. Pseudonymization keys are never persisted.

## Retention, export, logging, and incidents

Use the existing ignored owner-only package boundary: directory mode `0700`, file mode `0600`, no
overwrite, explicit 1–30 day operator-managed retention, and deletion of expired copies/backups.
Protected live collection removes private evidence before the job ends. Names, IDs, exact endpoints,
and private join keys are never CI artifacts, static assets, model input, logs, analytics dimensions,
or public issue text.

Private export is an explicit operator action to an access-controlled location with the same
retention and permissions. Public exports reconstruct the canonical sanitized projection. Log only
non-identifying status, counts, timestamps, and reviewed public snapshot identity. Treat accidental
lineage disclosure as tenant-data exposure under the [incident-response procedure](incident-response.md),
including affected exports and backups.

## Authenticated matrix boundary

The current Worker serves sanitized public evidence only. No private route or authentication
deployment is enabled here. A future matrix that displays names must meet these requirements:

- Protect a dedicated private origin and every API/export route with Cloudflare Access. At the
  origin, validate the JWT signature, expected issuer/audience, expiry, and tenant binding. A header
  or an unprotected Worker URL is insufficient.
- Enforce tenant-scoped roles at the origin: evidence-reader for approved tenant evidence,
  evidence-exporter for separately authorized export. Baseline approval remains a separate human
  authority. No role grants Intune writes.
- Deny invalid tokens, unknown roles, cross-tenant queries, exports without the export role, and
  public-cache access. Use `no-store`, restrictive origin checks, protected storage, and logs that
  exclude request bodies and private identifiers.
- Review identity/group membership, retention, encryption, export audit metadata, incident owner,
  bypass routes, and adversarial authorization tests before provisioning or publication.

These are design requirements, not a claim that private routes or roles exist today. The local CLI
relies on the operator's protected workstation and package permissions.

## Canonical matrix, profiles, and Assistant

`evidenceops/evidence/matrix.py` constructs `settings-matrix.json` from a validated public Mission.
Rows contain baseline profile/benchmark version, setting/requirement, target, observation, assignment
summary, outcome, technical framework mappings, public policy/evidence references, limitations, and
deterministic read-only guidance. The frontend verifies snapshot identity, fingerprint, complete row
coverage, and exact joins before rendering. Historical projections retain source and benchmark version.

CIS Level 2 has an independently loaded comparison profile with its own pinned source hash. TJ's
2026-10-14 decision keeps it comparison-only. Missing profiles/rules provide no result; membership
cannot infer targets, alignment, drift, approval, or compliance from Level 1 or cross-references.
Additional desired-state profiles require separate human approval.

The Assistant keeps its existing bounded typed-claim contract. Private lineage, setting keys,
framework identifiers, and change guidance are not added to model context. Expansion requires exact
typed claims, verifier tests, and a separate egress review first. Deterministic matrix context remains
separate from generated prose.
