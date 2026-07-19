# Incident Response

This procedure covers suspected credential, tenant-data, device-data, or public-artifact exposure.

## Immediate actions

1. Stop the affected workflow, static publication, or future Worker deployment without deleting
   evidence needed for response.
2. Restrict access to the exposed artifact or repository surface.
3. Revoke or rotate the affected credential or pseudonymization key through its owning platform.
4. Preserve minimal audit metadata in a restricted location; do not paste sensitive content into a
   public issue, commit, or workflow log.
5. Notify the repository security owner through GitHub private vulnerability reporting.

## Assess

Determine the source, fields, affected artifacts, public reachability, access window, log exposure,
fork involvement, and whether pseudonyms can be linked back to a real environment. Treat raw
responses and reversible identifiers as sensitive even if no credential was exposed.

## Contain and recover

- Disable the faulty publication or collection path.
- Remove public access using the least destructive supported mechanism.
- Rotate credentials and invalidate cached artifacts.
- Correct the field policy, workflow scope, or retention setting.
- Re-run sanitization and prohibited-pattern validation from a clean environment.
- Verify the public URL no longer serves affected content.

History rewriting is a security-sensitive last resort because clones and caches may retain data.
Coordinate it explicitly; do not assume deleting a branch or workflow run removes all copies.

## Learn

Record a sanitized timeline, root cause, control failures, affected versions, corrective actions,
and prevention tests. Update the threat model before re-enabling publication or live collection.
