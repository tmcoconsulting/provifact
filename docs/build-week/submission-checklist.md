# Submission Checklist

This checklist is evidence support, not a statement of Build Week rules. Verify current competition
requirements from their authoritative source before submission.

## Public repository

- [ ] Repository is public and owned by `tmcoconsulting`
- [ ] Apache License 2.0 and `NOTICE` are present
- [ ] `main` is protected and verified
- [ ] Issues and Discussions are enabled; Wiki is disabled
- [ ] CI and Pages workflows pass
- [ ] GitHub Pages is publicly reachable
- [ ] Dependency and secret alerts supported by the plan are enabled

## Product and security evidence

- [ ] Demo and dashboard are clearly synthetic
- [ ] No live tenant, person, device, group, or credential data is committed
- [ ] Sanitizer fails closed on unknown fields
- [ ] Generated site passes prohibited-pattern scanning
- [ ] Read-only provider and human-approval boundaries are documented
- [ ] Current limitations and rejected choices are visible
- [ ] Commit hashes and exact validation commands are recorded

## Private submission metadata

- [ ] Run `/feedback` in the primary Codex thread
- [ ] Preserve the returned Session ID privately
- [ ] Do not commit the Session ID unless rules explicitly require public disclosure
- [ ] Verify any Devpost or competition fields against authoritative current instructions

## Media review

- [ ] Record only synthetic demonstrations
- [ ] Review every frame for notifications, identities, secrets, and tenant/device data
- [ ] Distinguish implemented behavior from roadmap behavior
- [ ] Confirm asset and music usage rights
