# Configured live E2E tests

`scripts/run_e2e.py` runs JSON-configured setup, test, and cleanup tool calls. It uses only Python's standard library. Run it from the repository root on GitHub Actions; the standalone client described below can also be used by a human outside CI.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_e2e.py --config e2e/deploy-readback.json --validate-only
python3 scripts/run_e2e.py --config e2e/lease-smoke.json
python3 scripts/run_e2e.py --config e2e/deploy-readback.json
```

Offline unit tests use fake responses and a local HTTP server. They do not connect to a hub. The first live example reads watchdog information. The second temporarily replaces the source of one existing Apps Code class, checks exact source readback, restores the original source, and checks restoration. `APP_CODE_ID` must point to a dedicated disposable Apps Code **class** with no installed instances, not an installed app instance or the watchdog's own class. That example deploys the repository's `apps/example-app.groovy`; change both `$file` values to your application's source when adapting it. The example does not create or run an installed app instance.

## Preconditions and lease

In GitHub repository Settings → Environments, create an environment named `test-hub`. Restrict its deployment branches to `main` and configure required reviewers if you want a human approval gate. Set these environment secrets and variables:

| Kind | Name | Value |
| --- | --- | --- |
| Secret | `WATCHDOG_URL` | The watchdog MCP URL for your dedicated test hub, including its access token. |
| Secret | `TARGET_MCP_URL` | Optional endpoint for the app under test on that same hub. Required by scenarios with `endpoint: "target"`. |
| Variable | `HUBITAT_TEST_HUB` | Exactly `true`, confirming this is a dedicated test hub. |
| Variable | `APP_CODE_ID` | Existing disposable Apps Code class ID, required for `deploy-readback`. |

On the test hub, create Hub Variable `_TEST_HUB_LEASED_BY` with type **String** and initial value **`{}`**. Initialize it nonempty: Hubitat can drop an empty String variable, and the watchdog does not create missing variables. Install/configure the standalone watchdog as described in [watchdog.md](watchdog.md), then select **Test hub E2E** in GitHub Actions and manually dispatch `lease-smoke` from `main`. Dispatch `deploy-readback` once the dedicated class and its variable are configured. The provided workflow has no push or pull-request live trigger.

`--validate-only` checks a scenario's complete configuration without accessing either endpoint and can run before lease acquisition. It still needs the scenario's required URL and substitution environment variables.

The live runner requires all of these:

- `GITHUB_ACTIONS=true` and `HUBITAT_TEST_HUB=true`.
- A numeric `GITHUB_RUN_ID`.
- `WATCHDOG_URL`: the complete stateless HTTP MCP endpoint, including its access token when needed.
- A live watchdog read of Hub Variable `_TEST_HUB_LEASED_BY` returning a JSON string with `by` equal to `ci-run-${GITHUB_RUN_ID}` and an integer `until` in epoch milliseconds later than the current time.
- `TARGET_MCP_URL` when a configured step selects `endpoint: "target"`.

The workflow acquires and releases the 30-minute lease with `scripts/lease_acquire.sh` and `scripts/lease_release.sh`. The runner does not claim or renew it. It verifies the live lease before every configured call, including reads and cleanup; an unreadable, expired, or different owner's lease blocks that call. Keep the workflow's live test timeout below the lease TTL and release with the same owner identifier in an `always()` step.

The flags are explicit operator declarations. They do not independently identify the physical hub. Provision the `test-hub` GitHub environment with an endpoint for a dedicated test hub. Point both watchdog and target URLs at that same hub; the runner cannot prove that independently for arbitrary target MCP servers. The lease is a cooperative protocol, not an atomic lock. Other tooling must respect it, and there remains a small read-to-call race.

## Configuration

The envelope accepts only `schema_version: 1` and the three phase arrays. At least one `test` step is required; `setup` and `cleanup` may be empty. Every step has a unique `id`, a tool name, an arguments object, and a nonempty assertions list. Its endpoint defaults to `watchdog`; use `target` to call the app under test.

```json
{
  "schema_version": 1,
  "setup": [],
  "test": [
    {
      "id": "application_info",
      "endpoint": "target",
      "tool": "my_app_status",
      "arguments": {"label": "ci-${ENV:GITHUB_RUN_ID}"},
      "assertions": [{"path": "/ready", "op": "equals", "value": true}]
    }
  ],
  "cleanup": []
}
```

Arguments and assertion values accept three substitutions:

| Form | Behavior |
| --- | --- |
| `"${ENV:APP_CODE_ID}"` | Substitute a required nonempty environment variable into a string; strings can contain several substitutions. |
| `{"$file": "apps/my-app.groovy"}` | Load UTF-8 text from a repository-relative file. Paths and resolved symlinks must stay inside the repository. Source text is kept literally, including any `${...}` in Groovy source. |
| `{"$result": "snapshot#/source"}` | Use a JSON Pointer into a successful earlier step's result. An empty pointer selects its complete result. |

All phases' structure, endpoint URLs, environment substitutions, file contents, and reference ordering are checked before network calls. A result reference must name an earlier step and is resolved before the dependent call. Missing results or pointers stop that call. A response becomes available to later steps only after its assertions pass. Failed snapshot assertions therefore cannot supply incomplete source to a restore operation.

Each assertion uses an RFC 6901 JSON Pointer (`""` is the root, `/source` selects a field, `/items/0/id` selects an array element, and `~0`/`~1` escape `~`/`/`). Its three fields are `path`, `op`, and `value`:

| Operator | Expected value |
| --- | --- |
| `equals` | Exact JSON value, including type. `true` does not equal `1`. |
| `contains` | A substring for a string result, or an exact element for an array result. |
| `exists` | Boolean: whether the pointer resolves, including a present `null`. |
| `type` | `object`, `array`, `string`, `number`, `boolean`, or `null`. |

Tool results decode their single text JSON block or use `structuredContent`. Plain text stays a string; multiple content blocks remain under `/content`. A JSON-RPC error or MCP `isError: true` fails the step. A tool's domain-specific `success: false` is caught by your explicit assertion; assert it whenever that tool provides a success flag.

## Cleanup and uncertain writes

A setup or test failure stops those phases. Once the initial lease check passed, cleanup runs in its configured order, attempts every cleanup step, and fails the run if any cleanup call or assertion fails. The original setup/test failure remains part of the failure summary. No fixture naming conventions, blanket purge, or upstream MCP deployment are built in. Define cleanup specifically for resources your scenario owns.

Every HTTP call has a timeout and **no automatic retries**, including writes. A timeout may occur after the hub applied a write. The runner preserves failure and proceeds to configured cleanup when it still owns the lease. Cleanup itself can also time out or be refused after lease expiry. Hard termination of a GitHub runner can prevent cleanup altogether; use snapshots, targeted disposable resources, and manual readback/recovery for such cases. Logs report only phase, position, and a safe failure summary; they do not print tool payloads, URLs, or remote exception text.

`hub_get_source` returns at most 64,000 characters per call. The deploy/readback example deliberately asserts `hasMore: false` on the snapshot before deploying; larger apps need a scenario with complete chunked snapshot and restoration handling. Its `noSave: true` avoids the watchdog's automatic File Manager copy during source reads. Prefer a small disposable class for this example.

## Fresh app installations

`hub_update_app` updates an existing Apps Code class; it does not install a new app class or create a running app instance. For fresh app/driver/library code, create a Hubitat bundle and ask the watchdog's `hub_install_bundle` tool to install it. The hub fetches `importUrl`, so use an artifact URL reachable by the hub. The exact tool arguments are:

```json
{"importUrl": "https://example.org/my-app.zip", "primary": true, "confirm": true}
```

Check that deployment result explicitly, then use `hub_list_apps` or `hub_list_bundles` to discover and assert the resulting identities. Installed app instances require their own explicit installation/configuration flow. Write cleanup around the returned IDs; `hub_delete_bundle` removes a bundle container, and individual class/instance removal semantics must be checked for your scenario. The toolkit does not infer which installed resources belong to a run. See [packaging.md](packaging.md) for the bundle layout.

## Standalone MCP client

`scripts/hubitat_mcp.py` has no CI or test-hub restriction. It can call any MCP tool through the stateless watchdog or another compatible stateless endpoint:

```sh
python3 scripts/hubitat_mcp.py --url-env WATCHDOG_URL --tool hub_get_info
python3 scripts/hubitat_mcp.py --url-env WATCHDOG_URL --tool hub_update_app --arguments-file deploy-arguments.json
python3 scripts/hubitat_mcp.py --url-env TARGET_MCP_URL --tool my_app_status --result-file status.private.json
```

`deploy-arguments.json` contains `{"appId":"42","source":"<complete Groovy source>","confirm":true}`. Load actual source using your preferred JSON-producing tool rather than interpolating it into shell syntax. Arguments files must be plain JSON; E2E substitutions are supported by the runner, not this client.

The CLI prints only result metadata by default. It exits nonzero for protocol errors, MCP `isError: true`, and an explicit top-level `success: false`; other domain-specific failures need application-specific checks. `--result-file` explicitly saves full tool data to a newly created file with mode `0600`; the file can contain secrets and should not be uploaded as a public CI artifact. The path is reserved before sending a call, so existing files and symlinks are refused before a potential write. A transport failure can leave an empty reserved file; a tool-domain failure can leave its full diagnostic result there. URLs come from environment variables and never appear in diagnostics. Redirects are refused to avoid forwarding token-bearing URLs to a different endpoint. HTTP and HTTPS are accepted for Hubitat LAN and cloud endpoints; HTTPS uses the standard certificate verification.

This client is deliberately stateless: it sends `tools/call` JSON directly, matching the watchdog. Servers requiring an initialize/session handshake or SSE responses need a full MCP SDK client instead.

The workflow suppresses the preserved lease scripts' raw output because they can include remote Hub Variable contents. It reports a safe acquisition result. Release is best-effort in the upstream script; an unconfirmed release is bounded by the 30-minute lease TTL. The upstream scripts retry lease requests, while configured scenario calls through the Python client are never retried.
