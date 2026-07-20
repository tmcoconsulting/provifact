# Judge Guide

Provifact™ demonstrates one bounded proposition: **a reviewed endpoint change can produce a
traceable, privacy-safe evidence chain without giving the evidence system permission to change
Intune.** This guide is a product walkthrough, not a statement of any competition's judging rules.

## Three-minute path

1. Open [Mission Control](evidence-dashboard.md). Confirm the evidence-mode banner, approved
   baseline identity, current freshness, exact Intune joins, deterministic drift, implementation
   backlog, and collection gaps.
2. Open one deterministic finding. Follow the desired value, observed value, provider definition,
   assignment evidence, public-safe parent reference, evidence IDs, fingerprints, and human-only
   operator guidance.
3. Switch **Baseline posture** between the full 98-rule implementation plan and the evaluated-only
   denominator. The dashboard never hides the 94 rules that still need an approved implementation
   or mapping path.
4. Open the [Baseline Plan](settings-matrix.md). Filter by Auditing, Operating System, Password
   Policy, System Settings, or Supplemental. A planning item is not mislabeled as a failed control.
5. Ask Provifact Assistant what requires attention. Typed claims and cited evidence are checked
   deterministically; generated prose remains generated analysis subject to human review.
6. Finish at **Evidence health and privacy**: Graph is GET-only, raw tenant responses are not public,
   and the site exposes only a scanned sanitized package.

## What is real, synthetic, and bounded

| Surface | Evidence boundary | Meaning |
| --- | --- | --- |
| Production Mission package | The banner states `LIVE SANITIZED TENANT DATA` only when a reviewed protected-main collection artifact was deployed | Tenant, device, user, policy, assignment, and object identities remain private |
| Local build | `SYNTHETIC DEMO DATA` | Reproducible without Microsoft or OpenAI credentials |
| Drift status | Deterministic engine | GPT cannot create, alter, resolve, or approve a finding |
| Provifact Assistant | Bounded sanitized context | Typed claims are verified; prose is quarantined from evidence authority |
| CIS Level 1 plan | 98 hash-pinned rules from the recorded NIST mSCP revision | Four exact Intune joins are evaluated; 94 rules are visible implementation work |
| STIG lens | Cross-references on reviewed evidence only | No STIG baseline, score, compliance verdict, or certification is claimed |

## The macOS onboarding use case

A team bringing Macs into an existing environment can begin with the approved 98-rule inventory,
then triage each item into one of three queues:

- **Deterministically evaluated:** an exact reviewed Intune definition and typed target exist.
- **Provider mapping review required:** desired metadata exists, but the exact Intune definition has
  not yet passed review.
- **Implementation planning required:** choose and approve an Intune Settings Catalog, custom
  profile, script or agent, or alternate-evidence path before evaluation.

This is intentionally more useful than a fabricated red score. It distinguishes current technical
drift from controls the team has not yet designed or evidenced.

## Trust boundaries worth inspecting

- The Microsoft provider exposes collection only and its transport accepts GET only.
- GitHub's protected production workflow uses an environment-scoped OIDC identity; no Entra client
  secret is stored.
- Unknown public fields, credential patterns, invalid fingerprints, and private artifact paths fail
  closed.
- Cloudflare serves static assets plus same-origin bounded APIs. The OpenAI key stays server-side.
- The OpenAI request uses one fixed model, structured output, `store: false`, no tools, bounded
  input/output, and deterministic post-verification.
- Git revert changes reviewed desired-state history; it does not revert Intune.

The pinned source inventory and attribution are recorded in the
[architecture](architecture.md), [decision log](build-week/decision-log.md), and `NOTICE`. The
authoritative upstream project is the
[NIST macOS Security Compliance Project](https://github.com/usnistgov/macos_security).

## Honest limitations

- Only four exact Intune provider mappings currently enter the technical denominator.
- CIS Level 2 and a full STIG baseline are not loaded.
- iOS and iPadOS appear as sanitized aggregate posture but are not scored against a macOS baseline.
- No Intune write, remediation, assignment, exception, or rollback capability exists.
- Technical configuration evidence can support an assessment objective; human assessors retain
  final judgment over organizational compliance.

For command-level reproduction, use the [demo package](build-week/demo-package.md). For the security
boundary, read the [security model](security-model.md) and [threat model](threat-model.md).
