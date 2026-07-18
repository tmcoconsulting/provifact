# Roadmap

Roadmap items describe intent, not operational capability or a delivery commitment.

## Phase 0 — foundation

- Public repository, Apache License 2.0, and contribution/security guidance
- Vendor-neutral read-only provider protocol
- Deterministic drift comparison and fingerprints
- Fail-closed sanitization contract and synthetic tests
- CI, Pages, repository protections, and Build Week evidence
- Synthetic documentation and dashboard shell

## Recommended Phase 1 — private collection proof

- Define a versioned normalized observation schema and provider conformance suite
- Select the minimum Intune/managed Apple Graph endpoints and read permissions
- Implement an Intune adapter behind the provider protocol with mocked contract tests
- Add workload-identity configuration as an opt-in private deployment example
- Produce a private raw-to-sanitized evidence package with explicit retention controls
- Add policy manifests for allowed fields and publication decisions
- Add evidence provenance linking desired-state commit, observation, and fingerprint
- Build grounding evaluations before enabling a GPT-5.6 narrative path

Phase 1 must not begin until its data inventory, permissions, threat-model update, and human approval
are reviewed.

## Later direction

- Managed Apple declaration and policy lifecycle evidence
- Exception ownership and expiry workflows
- Reviewed compliance mappings
- Grounded, labeled evidence narratives and evaluation harnesses
- Jamf and Omnissa Workspace ONE provider adapters
- Private evidence storage and signed publication manifests
- Auditor-focused evidence bundle export
- Optional custom domain after verified GitHub and DNS authorization

## Rejected for now

- Intune or Microsoft Graph writes
- Automatic remediation
- A generic data lake of raw tenant exports
- Publishing reversible device or user identifiers
- Treating model output as a compliance verdict
- Importing history or code from unrelated endpoint-management repositories
