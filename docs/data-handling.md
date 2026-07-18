# Data Handling

## Public-data rule

GitHub Pages may contain only:

1. curated synthetic data, or
2. a live-derived package that passed the explicit sanitizer, schema/policy gate, and prohibited
   pattern scan.

Phase 0 publishes only the first category.

## Prohibited or transformed values

| Category | Examples | Public action |
| --- | --- | --- |
| Tenant and cloud identity | Tenant, subscription, application, service-principal identifiers | Pseudonymize or reject |
| People | User principal names, email addresses, personal names | Pseudonymize or reject |
| Devices | Names, serials, hardware identifiers, managed-device identifiers | Pseudonymize or reject |
| Directory and assignment | Object identifiers, group identifiers, real group names | Pseudonymize or reject |
| Network | Network addresses and internal domains | Pseudonymize or reject |
| Credentials | Access and refresh tokens, client secrets, private keys, certificates, authorization headers | Drop and fail scans |
| Correlation | Values that could re-identify a tenant or person | Classify explicitly; otherwise reject |

Deterministic pseudonyms are used only where the evidence engine needs stable cross-record
relationships. They are HMAC-derived with runtime key material. The key is never committed,
published, logged, or stored in workflow artifacts.

## Fail-closed contract

- Every mapping key must have an explicit action.
- An unknown field raises `UnknownFieldError`.
- A sensitive-looking value that survives an allowed field raises `SensitiveValueError`.
- A generated site containing prohibited patterns fails validation.
- Raw fixture markers are forbidden from site output.

This contract intentionally requires a human classification decision when a provider adds or
renames a field.

## Future live-data lifecycle

| Stage | Location | Retention |
| --- | --- | --- |
| Read-only API response | Restricted job memory or encrypted temporary storage | Minimum necessary |
| Normalized raw evidence | Private/restricted data plane | Policy-defined |
| Sanitized evidence package | Validated workspace | Review window |
| Public package | GitHub Pages artifact | Project retention |
| Pseudonym key | Approved secret store | Rotated; never in repository |

Workflow artifacts containing raw or sensitive data will be disabled where possible; if an
incident requires one, access is restricted and retention is explicitly minimized.

## TMCO identity

TMCO Consulting, LLC is the project sponsor and copyright holder for its original EvidenceOps
work. The demo does not imply that TMCO's production environment, customers, users, or devices are
represented. Public business identity is not a substitute for sanitized tenant data.
