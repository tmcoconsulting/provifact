# Architecture

EvidenceOps separates collection, deterministic evaluation, publication policy, and generated
analysis so no one layer silently inherits another layer's authority.

```text
Reviewed desired state (Git)
              |
              v
Read-only provider adapter ---> normalized observations
                                      |
                                      v
                           deterministic drift engine
                                      |
                       +--------------+--------------+
                       |                             |
                       v                             v
             private evidence package       fail-closed sanitizer
                                                     |
                                                     v
                                          public evidence package
                                                     |
                                                     v
                                        labeled generated analysis
                                                     |
                                                     v
                                             human approval
```

## Core boundaries

### Provider contract

`EndpointInventoryProvider` exposes collection only. The normalized
`ConfigurationObservation` deliberately names no vendor API object and contains no create, update,
delete, assign, or sync operation. An Intune adapter, a later Jamf adapter, and a later Workspace
ONE adapter can therefore feed the same evidence engine.

### Deterministic evidence engine

The engine compares normalized JSON values directly and computes a stable SHA-256 fingerprint over
the inputs and algorithm version. A language model is not involved in compliance state.

### Publication policy

Every input field must be classified as allowed, dropped, or pseudonymized. Unrecognized fields
raise an error. Output then passes a content scan. Pseudonyms use HMAC-SHA-256 with runtime-supplied
key material of at least 32 bytes; the key is never persisted by EvidenceOps.

### Narrative boundary

The future narrative service will receive a bounded evidence package, cite evidence identifiers,
and label its output as generated analysis. It cannot mutate provider state, alter deterministic
results, grant exceptions, or publish without policy and human gates.

## Phase 0 modules

| Module | Responsibility | Intentional exclusion |
| --- | --- | --- |
| `domain` | Provider-neutral observations and findings | Vendor SDK objects |
| `providers` | Read-only collection protocol | Live adapters and writes |
| `evidence` | Reproducible drift and fingerprints | Model inference |
| `sanitization` | Explicit classification and public-output gate | Key persistence |
| `presentation` | Deterministic summary | Claims of audit certification |

## Future private/live data plane

The live design keeps collection and raw artifacts in a restricted plane. GitHub Actions would use
short-lived workload identity, collect with approved read permissions, sanitize before crossing the
public boundary, and publish only the resulting policy-approved package. A public pull request from
a fork never receives privileged credentials.
