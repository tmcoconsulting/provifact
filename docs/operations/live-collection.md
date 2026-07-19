# Live Read-Only Collection

Live collection is an opt-in private operator action. It reads a narrow Microsoft Intune
configuration slice and never publishes automatically.

## Supported Microsoft Graph contract

EvidenceOps calls only these Microsoft Graph v1.0 endpoints:

| Method and endpoint | Purpose | Normalized/public data |
| --- | --- | --- |
| `GET /deviceManagement/deviceConfigurations` | Find macOS general device configurations | Two supported setting values and modified time |
| `GET /deviceManagement/deviceConfigurations/{id}/assignments` | Count assignment records/target kinds | Counts/kinds only; no group IDs or names |

The adapter supports only `#microsoft.graph.macOSGeneralDeviceConfiguration` and two documented
properties: `passwordRequired` and `passwordMinutesOfInactivityBeforeScreenTimeout`. The latter is
normalized from minutes to seconds. Policy IDs remain only in the private trace. Display names,
descriptions, groups, users, devices, domains, and raw response objects are not retained.

No `/beta` endpoint is used. Managed-device counts were deliberately omitted because they require
the additional `DeviceManagementManagedDevices.Read.All` permission.

Microsoft documents the [configuration list](https://learn.microsoft.com/graph/api/intune-deviceconfig-deviceconfiguration-list?view=graph-rest-1.0),
[assignment list](https://learn.microsoft.com/graph/api/intune-deviceconfig-deviceconfigurationassignment-list?view=graph-rest-1.0),
[macOS resource properties](https://learn.microsoft.com/graph/api/resources/intune-deviceconfig-macosgeneraldeviceconfiguration?view=graph-rest-1.0),
[paging contract](https://learn.microsoft.com/graph/paging), and
[429 handling](https://learn.microsoft.com/graph/throttling).

## Exact permission

The machine-readable source of truth is `manifests/microsoft-graph-permissions.v1.json`.

| Profile | Permission | Permission ID | Admin consent | Accessible data |
| --- | --- | --- | --- | --- |
| Attended delegated | `DeviceManagementConfiguration.Read.All` | `f1493658-876a-4c87-8fa7-edb559b3476a` | Yes | Intune device configuration/compliance policies and assignments available to the signed-in operator |
| Private automation application | `DeviceManagementConfiguration.Read.All` | `dc377aa6-52d8-4e23-b271-2a7ae04cedf3` | Yes | Tenant-wide Intune device configuration/compliance policies and assignments |

No write permission, `Directory.Read.All`, user/group permission, or managed-device inventory
permission is requested. Microsoft describes this permission in the
[Graph permissions reference](https://learn.microsoft.com/graph/permissions-reference#devicemanagementconfigurationreadall).

## Attended local setup

1. Create or select an approved public-client Entra app in the intended tenant.
2. Add only delegated `DeviceManagementConfiguration.Read.All`; obtain administrator consent.
3. Enable the public-client/device-code flow according to organizational policy.
4. Place only the IDs in the current process environment—not in a file:

   ```bash
   export AZURE_TENANT_ID='operator-supplied-value'
   export AZURE_CLIENT_ID='operator-supplied-value'
   python -m evidenceops live-collect --auth device-code \
     --private-dir artifacts/private --retention-days 7
   ```

MSAL uses its in-memory cache; EvidenceOps does not configure persistent token caching. The device
code is shown only for the attended sign-in and is never placed in evidence.

An already acquired short-lived token can instead be placed in
`EVIDENCEOPS_GRAPH_ACCESS_TOKEN` and used with `--auth environment-token`. EvidenceOps never writes
that token.

## Private evidence lifecycle

- The selected directory must be inside the repository and covered by `.gitignore`.
- Directory/file modes are restricted to `0700`/`0600` where supported.
- Existing packages are never overwritten and symlinks are not followed.
- Retention is explicit (default seven days; maximum 90). The operator must securely delete the
  package and backups at expiry.
- Publication is a separate, fail-closed command with a runtime-only pseudonym key.

```bash
export EVIDENCEOPS_PSEUDONYM_KEY='operator-generated-random-value-at-least-32-bytes'
python -m evidenceops publish artifacts/private/private-evidence-….json \
  --output build/sanitized-public.json
```

Human review of a sanitized live package is required before any public placement.

## TMCO test-tenant validation status

The adapter has mocked contract coverage for pagination, empty collections, assignments, malformed
fields, hostile next links, 401/403/404/429, and transient 5xx behavior. The repository now contains
a manual-only, main-only `intune-audit.yml` workflow targeting the protected `production`
environment. It requests only `contents: read` and `id-token: write`, obtains a process-scoped Graph
token, writes private evidence only to ignored ephemeral storage, publishes/scans in memory and
ignored build paths, reports aggregate sanitized counts, and deletes both packages at job end.

The existing Entra application now has the following environment-scoped federated identity
credential, which was created and then independently re-opened in the Entra control plane:

```text
name: github-evidenceops-production
issuer: https://token.actions.githubusercontent.com
subject: repo:tmcoconsulting/evidenceops:environment:production
audience: api://AzureADTokenExchange
```

Application `DeviceManagementConfiguration.Read.All` is present and shows administrator consent.
No Entra client secret exists or was created. The application also retains these pre-existing
delegated permissions, all already consented before the EvidenceOps application permission was
added:

- `DeviceManagementApps.Read.All`
- `DeviceManagementCloudCA.Read.All`
- `DeviceManagementConfiguration.Read.All`
- `DeviceManagementManagedDevices.Read.All`
- `DeviceManagementRBAC.Read.All`
- `DeviceManagementScripts.Read.All`
- `DeviceManagementServiceConfig.Read.All`
- `User.Read`

The EvidenceOps production workflow does not request or use those delegated permissions. Several
are broader than the narrow configuration collection proof; they were left unchanged because they
pre-date this project and require application-owner review before removal.

Live TMCO validation remains outstanding. The privileged workflow is manual, checks out reviewed
`main`, and targets the protected `production` environment, so it must not be executed from this
feature branch. No endpoint is reported as live-validated until that controlled post-merge run
succeeds. Do not add a client secret or broaden the documented application permission.
