# Changelog

## 2026-07-20 — Live audit cockpit

- Replaced semantic-key substring matching with a versioned registry of exact reviewed Microsoft
  Intune provider definition IDs and explicit mapping-review/value-normalization states.
- Added strict current/prior live public snapshots with new, resolved, changed, and unchanged drift.
- Made the protected production deployment require a successful trusted-main live audit artifact
  and its exact reviewed snapshot ID; removed every synthetic production fallback.
- Redesigned Mission Control around current attention, changes, findings, collection health, and
  expandable evidence; reduced Settings to a readable six-column view with accessible detail.
- Added site-wide Evidence Copilot with session-only history, current-page/snapshot context, selected
  evidence, fixed `gpt-5.6-terra` production mode, and useful deterministic local fallback.
- Added global live/synthetic/stale provenance, no-store snapshot refresh, official TMCO Consulting
  assets, and a company-name content gate.
- Added fail-closed regression tests for exact mappings, unsupported values, prior-package
  validation, deployment provenance, assistant intents, model egress, and browser boundaries.
- Merged the cockpit through protected `main`, completed two GET-only live audits with an exact
  sanitized prior-snapshot comparison, deployed the reviewed live package to Cloudflare, and
  accepted one bounded `gpt-5.6-terra` response only after deterministic verification.

## Evidence navigation and settings matrix

- Reorganized the documentation around clear Start Here, Product, How It Works, Operate, and Project paths.
- Added a searchable Intune setting and baseline matrix with observed values, approved targets,
  deterministic states, CIS/STIG/NIST/CMMC identifiers, public-safe evidence references, and exact
  non-mutating change guidance.
- Marked CIS Level 2 explicitly as not loaded instead of inferring coverage from Level 1 or another
  framework cross-reference.
- Paired the FileVault assistant task with deterministic setting context from the verified Mission
  package without expanding model egress.
- Corrected current-facing security, local-demo, deployment, video, homepage, and dashboard
  documentation while preserving dated validation records as historical evidence.
- Documented that the existing Cloudflare Worker plus Static Assets stack remains appropriate until
  authenticated private policy names, persistent history, approvals, or multi-tenancy require a
  dedicated application backend.

## Build Week Phase 1 vertical slice

- Added a comprehensive GET-only Microsoft Intune Apple collector with per-resource gaps.
- Added a pinned, hash-verified 98-rule mSCP macOS CIS Level 1 demo baseline and TMCO Consulting approval record.
- Added deterministic assignment/value/conflict evaluation, evidence traceability, and sanitized history.
- Added dynamic Mission Control assets and a bounded evidence-grounded `/api/ask` assistant.
- Expanded least-privilege Graph permission documentation to four read-only resource families.
- Preserved explicit local/preview fixture mode, no Intune writes, and fail-closed publication/model egress.
- Completed the reviewed live sanitized publication, Bot-Fight-safe deployment proof, independent
  production validation, and final protected-main GET-only audit retry.

See the Build Week contribution and decision logs for commit-level evidence after review.
