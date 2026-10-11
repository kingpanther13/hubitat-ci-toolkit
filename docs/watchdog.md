# Standalone watchdog MCP server

[`watchdog/e2e-deadman-watchdog-v3-1.groovy`](../watchdog/e2e-deadman-watchdog-v3-1.groovy) is an independent MCP server that runs as a Hubitat user app. Anyone can install it and use its generic administration tools to install their own app, driver, and library bundles or update an existing Apps Code class. The original MCP Rule Server is **not a prerequisite** for those tools. You do not need to edit or install the original repository to use this server.

The file is copied byte-for-byte from [Hubitat-local-MCP-server at `0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`](https://github.com/kingpanther13/Hubitat-local-MCP-server/blob/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018/e2e-deadman-watchdog-v3-1.groovy). Its upstream app name, namespace, description, and tool names are preserved. It was built for a dedicated E2E hub and grants administrative access; use a dedicated development/test hub for CI.

## Install and connect

1. In the Hubitat admin UI, open **Apps Code → New App**, paste the complete watchdog source, and save it.
2. In that code editor, open **OAuth**, enable OAuth for the app, and save the OAuth settings.
3. Open **Apps → Add User App**, select **E2E Dead-Man Watchdog v3.1**, and install the instance. If Hub Security is enabled, supply its username and password in the watchdog's settings so its loopback admin requests can authenticate.
4. Review **Auto-reboot when the hub's loopback HTTP stays dead for 4+ minutes**. This setting defaults to **on**. Choose the behavior you want before completing installation.
5. Click **Done** once to create the access token, then reopen the app. Copy the complete URL shown under **MCP Deploy Endpoint**, including `?access_token=…`.
6. Add that URL to an MCP client that supports HTTP JSON-RPC POST requests. Treat the entire URL as a secret. OAuth here protects the Hubitat app endpoint with its access token; the client uses the token already present in the URL.

For an HTTP-capable client whose configuration accepts this shape:

```json
{
  "mcpServers": {
    "hubitat-watchdog": {
      "url": "<complete endpoint URL copied from the watchdog app>"
    }
  }
}
```

Client configuration keys vary. This endpoint serves request/response MCP over **POST** and returns HTTP 405 for GET; it does not provide SSE or GET streaming. It negotiates `2025-06-18`, `2025-03-26`, or `2024-11-05` and identifies itself as `e2e-deadman-watchdog-v3-1`, version `3.1`. Use the app's displayed cloud endpoint for remote access. On a reachable LAN, the equivalent local endpoint uses `http://<hub-ip>/apps/api/<watchdog-instance-id>/mcp?access_token=<token>`.

The following JSON-RPC messages can be sent to that endpoint to check the connection:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"my-hubitat-ci","version":"1.0"}}}
```

```json
{"jsonrpc":"2.0","method":"notifications/initialized"}
```

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hub_get_info","arguments":{}}}
```

Check both the JSON-RPC response and the tool's returned `success`/error details; an HTTP response alone does not establish deployment success.

## Install your own app or driver bundle

`hub_install_bundle` accepts a Hubitat-compatible code bundle ZIP at a URL the **hub itself** can fetch. The bundle can contain apps, drivers, and libraries. Publish your own bundle at an immutable release URL or commit-specific URL, then call:

```json
{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"hub_install_bundle","arguments":{"importUrl":"https://example.com/releases/my-hubitat-app-1.0.0.zip","confirm":true}}}
```

Replace the example URL with a real Hubitat bundle. `primary` is an optional boolean and defaults to false. The implementation selects the modern `/bundle2/uploadZipFromUrl` route on firmware 2.3.8.108 and later, with the older bundle route as fallback for older firmware. A local workstation path or URL accessible only to the CI runner will not work: Hubitat fetches and unpacks the ZIP.

Installing code places the bundle's components into Code. It does **not** create or configure an installed app instance, choose devices for its preferences, or create a device using a newly installed driver. Add/configure the user app or device separately in Hubitat, or implement a project-specific provisioning step. This watchdog has no general `hub_create_app` or standalone `hub_update_driver` tool; driver delivery uses bundles.

Read the resulting inventory:

```json
{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"hub_list_bundles","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"hub_list_apps","arguments":{"scope":"types"}}}
```

## Update an existing Apps Code class

Use `hub_list_apps` with `scope:"types"` to find the existing **Apps Code class ID**. `hub_update_app.appId` is that class ID, not the installed app instance ID from the Apps page.

```json
{"jsonrpc":"2.0","id":20,"method":"tools/call","params":{"name":"hub_update_app","arguments":{"appId":"123","importUrl":"https://example.com/releases/my-app-1.0.1.groovy","confirm":true}}}
```

Supply one source mode: `source` (inline Groovy), `sourceFile` (a file already in Hubitat File Manager), `importUrl` (source fetched by the hub), or `resave:true` (resave existing source). Substitute your actual class ID. Leave `selfUpdate` and `selfClassId` out when deploying another app. They describe the watchdog's own class reload, not normal app updates.

Saving source does not configure an installed instance or call through its preference pages. Verify source and relevant app behavior separately. `hub_get_info.lastSelfDeploy` records the latest `hub_update_app` outcome, despite the historical field name; it does not record `hub_update_package` results.

```json
{"jsonrpc":"2.0","id":21,"method":"tools/call","params":{"name":"hub_get_source","arguments":{"type":"app","id":"123","noSave":true}}}
```

`hub_get_source` is chunked (`offset`/`length`). Use `noSave:true` for a read-only operation: without it, source over 64,000 characters is also copied to File Manager.

## Libraries and instances

Generic library tools work independently of the original integration:

```json
{"jsonrpc":"2.0","id":30,"method":"tools/call","params":{"name":"hub_create_library","arguments":{"importUrl":"https://example.com/releases/my-library.groovy","confirm":true}}}
```

```json
{"jsonrpc":"2.0","id":31,"method":"tools/call","params":{"name":"hub_list_libraries","arguments":{}}}
```

```json
{"jsonrpc":"2.0","id":32,"method":"tools/call","params":{"name":"hub_update_library","arguments":{"libraryId":"456","importUrl":"https://example.com/releases/my-library-1.0.1.groovy","confirm":true}}}
```

`hub_create_library` supports `source`, `sourceFile`, or `importUrl`; `hub_update_library` also supports `resave:true`. Use the returned/listed library ID. A bundle-managed library may require replacement through its bundle rather than an in-place update; inspect a failed update's result before choosing another operation.

| Object | Inventory | ID meaning / operations |
|---|---|---|
| App code | `hub_list_apps(scope:"types")` | Class ID for `hub_update_app`, `hub_get_source(type:"app")`, `hub_delete_item(type:"app")` |
| Installed app | `hub_list_app_instances` or `hub_list_apps(scope:"instances")` | Instance ID for `hub_set_app_disabled` and `hub_force_delete_app` |
| Library code | `hub_list_libraries` | Library ID for `hub_update_library`, source reads, and code deletion |
| Bundle | `hub_list_bundles` | Bundle container ID for `hub_delete_bundle` |

Write tools require `confirm:true`. The watchdog refuses deletion of its own code or instance and refuses disabling its own instance. Its other generic tools include hub metrics/logs/jobs, File Manager reads/writes, backups, variable reads/sets, manual reboot, and platform-update administration. Consult `tools/list` for the exact schema before calling a tool. `hub_purge_e2e_artifacts` encodes upstream fixture names/types and should be treated as an advanced cleanup operation, not a universal uninstaller.

## Specialized original-integration operations

`hub_update_package` is an explicit, asynchronous repair/deployment tool for the **existing MCP Rule + MCP Rule Server package**, not a generic package installer. It validates the original manifest identities and source paths in namespace `mcp`, requires a full commit SHA, and verifies supplied app or library SHA-256 hashes. New libraries can arrive through the package's bundle. Built packages use the two original app hashes. It does not update the watchdog or OAuth. `hub_get_package_deployment` reports progress; `hub_set_package_deployment` releases the safety hold after verification or explicit abandonment. A held deployment blocks competing manual writes. Use the preserved [upstream v3 guide](../reference/hubitat-local-mcp-server/docs/watchdog-v3.md) and [v3.1 differences](../reference/hubitat-local-mcp-server/docs/watchdog-v3-1.md) for that integration's complete deployment protocol.

`hub_set_mcp_developer_mode` and `hub_update_mcp_settings` likewise verify the original MCP Rule Server identity and act on its installed instance. They are not generic preference-setting APIs for another app.

There is also an existing boundary on **updating the watchdog's own code through MCP**: it requires exactly one enabled MCP Rule Server instance whose local MCP endpoint answers `tools/list` and offers `hub_manage_code` or `hub_update_app`. `hub_get_info(peer:true)` checks that peer. A standalone installation can use all ordinary generic operations without this peer, but the preserved self-update guard will refuse its own code update without it. Update the watchdog through the Hubitat code editor when that guard cannot be satisfied; do not set self-update flags to bypass it.

## Automatic behavior and CI coordination

V3.1 has **no timed automatic package rollback**. Restoration needs an explicit deployment request. The older v1/v2 watchdogs in the reference snapshot have different behavior; they are historical sources, not the standalone server installed here.

Its only automatic recovery action is a hub reboot when loopback HTTP has been dead for more than four minutes, at least eight consecutive calls have failed, and a fresh probe still fails. A minute health tick drives the probe even when no client is calling it. `autoRebootOnWedge` defaults to true; attempts are limited to one per 30 minutes and deliberate reboot/platform-update windows suppress another reboot. These checks do not guarantee recovery when the underlying reboot request cannot reach the hub's web stack; physical recovery can still be necessary.

Serialize all CI/operator mutations on one test hub. The [lease scripts](../scripts/) coordinate cooperating users; the watchdog's per-operation write lock and package hold do not independently enforce an external CI lease. Keep the watchdog at a known version during app tests, reserve its maintenance for a separate operation, record deployment IDs and readbacks, and implement your app's explicit teardown/restoration policy. See [adaptation.md](adaptation.md) for adopting the complete upstream suite.
