# Threat Model

This Phase 0 model covers the public repository, CI, Pages deployment, sanitizer, synthetic
fixtures, and planned read-only collection boundary.

## Assets

- Desired configuration and approval history
- Future raw endpoint inventory and configuration responses
- Sanitized evidence packages and deterministic fingerprints
- Pseudonymization key material
- Future cloud workload identity
- Repository and workflow administration rights
- Generated analysis and its evidence citations

## Trust boundaries

| Boundary | Less-trusted side | More-trusted side |
| --- | --- | --- |
| Pull request | Contributor code and fixtures | Protected `main` |
| Provider | External API response | Normalized evidence engine |
| Publication | Raw or private package | Sanitized public package |
| Model | Generated text | Deterministic finding and human decision |
| Deployment | Build job | Protected Pages environment |

## Primary threats and controls

| Threat | Impact | Phase 0 control | Deferred control |
| --- | --- | --- | --- |
| Credential committed to Git | Account compromise | Ignore rules, local/CI high-confidence scan, GitHub alerts | Organization incident drill |
| Raw fixture reaches Pages | Re-identification | Synthetic-only data, raw markers, generated-site scan | Signed publication manifest |
| Provider adds sensitive field | Silent disclosure | Unknown fields fail closed | Provider schema conformance suite |
| Workflow dependency compromised | Build compromise | First-party actions pinned to full commits | Dependency review policy |
| Fork obtains collection credential | Tenant disclosure | No live collector; explicit fork prohibition | OIDC subject/environment policy |
| Graph permission expands to write | Endpoint mutation | No Graph integration; read-only provider protocol | Permission manifest policy gate |
| Narrative invents compliance claim | Audit error | Narrative not implemented; evidence remains deterministic | Grounding evals and reviewer UI |
| Pseudonyms become reversible | Re-identification | Runtime-only HMAC key; output content checks | Key rotation and private mapping controls |
| Maintainer bypasses review | Unreviewed change | Protected branch and required checks | Additional independent maintainer |

## Abuse cases

- A contributor disguises a real export as a fixture.
- A provider response nests an identifier under a new field name.
- Documentation embeds a token in a workflow-debug excerpt.
- A generated narrative states that drift is resolved when the finding remains open.
- A compromised action uploads a broader path than the generated site.

Tests and workflow scopes target these cases, but no control is absolute. Operators must still
review fixture provenance, permission changes, workflow diffs, and generated claims.

## Review triggers

Update this threat model before adding live collection, a new provider, credentialed workflows,
model runtime calls, evidence retention, user authentication, custom-domain deployment, or a new
public data field.
