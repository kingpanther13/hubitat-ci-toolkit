# Adapt the toolkit to your app

You can use the portable CI project and standalone watchdog without changing Hubitat-local-MCP-server. Start with this repository's examples, replace the application under test with your app or driver, and follow [watchdog.md](watchdog.md) for independent deployment over MCP.

The preserved [`reference/hubitat-local-mcp-server/`](../reference/hubitat-local-mcp-server/) contains the upstream CI implementation and application source at commit `0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`, including its full Spock corpus, fixtures, build lanes, workflow helpers, MCP application libraries, release tooling, and E2E runner. Treat it as a reference snapshot. Copy selected files into your own project before adapting them; changes to your copies do not require changes to the original repository. [ci-inventory.md](ci-inventory.md) maps every preserved workflow.

## Choose how much to adopt

| Starting point | Appropriate use | What you must supply |
|---|---|---|
| Portable parse/unit lanes | Ordinary app/driver syntax and behavior checks without a hub | Your Groovy source, specs, and required Hubitat API stubs |
| Watchdog generic tools | Install your own bundle or update an existing app/library | Reachable deployment artifacts, correct class IDs, installed-instance setup, and app-specific verification |
| Complete upstream suite | Study or reproduce the original MCP server's checks | Original MCP package and test fixtures, or substantial replacements for the MCP-specific assertions and deployment flow |

Local HubitatCI is a simulation, not the Hubitat firmware. Groovy 2.4 parsing catches syntax and class restrictions; Groovy 2.5/3.0 specs exercise behavior against different framework forks. A passing result does not prove a built-in Hubitat application or live device behavior. Native Rule Machine, Hubitat's admin web stack, hardware, scheduling, and firmware integrations still need dedicated real-hub validation.

## Adapt source and harness paths

Replace the app/driver filenames and `definition`/`metadata` identities in your project. In the upstream suite, `IncludeResolver`, `HarnessSpec`, `RuleHarnessSpec`, helper mocks, and the two additive builds assume the original root app files and `libraries/`. Decide which includes, mocks, production files, scaffold overrides, and specs apply to your project. Remove irrelevant original MCP assertions from your adopted corpus; changing names alone will not make those tests test your app.

Keep the Gradle daemon/toolchain distinction: the archived wrapper is Gradle 9.8.0, the active wrapper is maintained by Renovate, the CI daemon uses Java 17, and these Groovy builds target a Java 11 toolchain. Verify the selected Java/toolchain and dependency versions when intentionally upgrading. The original default harness uses eighty20results/hubitat_ci v0.28.6 with Groovy 3.0.25; its additive runtime lane uses joelwetzel/hubitat_ci `a62a351eed` with Groovy 2.5.23; the parse lane uses Groovy 2.4.21. Preserve the required framework-specific scaffold where you reuse those APIs.

## Adapt GitHub Actions

Copy workflows from the reference directory into your repository's `.github/workflows/` only after adapting them. Nested reference workflows do not run automatically. Review all of these together:

- Branch names (`main`, `bundle-artifacts`), event triggers, workflow dispatch inputs, path filters, checkout/ref handling, and artifact paths. The original tests often run from the repository root.
- Workflow/job names and required check names in your repository ruleset. Required checks with path filters can leave a PR waiting forever when the workflow never starts.
- Repository-owner/user checks (`kingpanther13`, `level99`), trusted-author associations, environment names (`e2e-auto`, `e2e-approval`), and environment approval policies.
- Labels (`release:patch`, `release:minor`, `release:major`, `e2e:full`, `e2e:skip`) and the `lane_gate.js`, `e2e_scope.py`, and status-posting logic that interprets them.
- Secrets and URL variable mappings. The original live suite uses `LEVEL99_TEST_HUB_MCP_URL` for its app under test and `WATCHDOG31_MCP_URL` for the independent watchdog. Your app may have a different interface and may need only the watchdog URL for deployment. `RELEASE_DEPLOY_KEY` belongs to the original release automation, not ordinary checks.
- Permissions: ordinary source checks are read-only; artifact publishing and release workflows write branches/tags/releases, the dependency check opens issues, and the live workflow posts statuses. Enable only the operations you intend.
- Concurrency and hub ownership. Preserve a shared hub queue across workflows that mutate the same hub, and use the same lease identity/TTL/release convention for CI and human operators. A per-PR queue alone does not protect one shared hub.

The upstream `hub-e2e.yml` uses privileged `pull_request_target` plus approval gates and exact-ref handling. It is not a drop-in workflow for arbitrary forks. Review its checkout, trust boundary, fork scanning, artifact publication, and secret-bearing steps before adopting it. Ordinary unprivileged source checks can use `pull_request` without live-hub secrets.

## Adapt real-hub deployment and lifecycle

For another app, use the watchdog's generic `hub_install_bundle`, `hub_update_app`, and library tools. Replace the original `hub_update_package` deployment path: it hard-codes the MCP Rule/MCP Rule Server package contract even when its repository base URLs are changed. The same applies to original MCP settings/developer-mode preparation, fixture discovery, server conformance assertions, and package progress verification.

Specify your app's bundle format, artifact URL, class/instance IDs, initial installation, preferences, disposable devices, and cleanup. Bundle installation delivers code; it does not create an app instance. Avoid hard-coded upstream hub/device IDs. Copy relevant `tests/e2e_config.example.json` fields into your own fixture plan and provision only what your app uses.

Use a dedicated test hub and a unique fixture namespace/prefix. Keep deployment sources immutable and verify the installed source and intended behavior. If a deployment call times out, inspect the resulting code/state before retrying: an already-submitted hub write can continue after the caller disconnects. Implement explicit cleanup on success, failure, and cancellation, retain a record of the baseline you intend to restore, and document hard-kill recovery. The copied v3.1 watchdog never restores a package on a timer, and the snapshot's normal E2E flow leaves the PR code installed; `install_main` is a separate explicit maintenance action.

Use the original `watchdog_maintenance.sh`, exact-ref CI gate, source backups, and peer validation as references for controlled watchdog maintenance. The generic deployment surface does not require the original MCP server, but the copied watchdog's own MCP self-update guard does. Preserve that distinction in your project instructions.

## Attribution and omitted platform assets

Retain the original MIT notice when copying upstream implementation or tests, the Apache notices for the Gradle wrapper, and the notices for any additional vendored assets. Framework dependencies have their own licenses. See [CREDITS.md](../CREDITS.md) and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

Captured proprietary Hubitat admin UI JavaScript is deliberately absent. The snapshot retains the upstream explanatory documentation under `resources/hub2-source/`, and the [upstream resource tree at the pinned commit](https://github.com/kingpanther13/Hubitat-local-MCP-server/tree/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018/resources/hub2-source) provides source context. Hubitat platform assets are not relicensed by this toolkit's MIT license.
