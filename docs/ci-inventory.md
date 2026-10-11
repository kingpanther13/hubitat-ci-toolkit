# Complete upstream CI inventory

The immutable source reference is [`reference/hubitat-local-mcp-server/`](../reference/hubitat-local-mcp-server/) from [commit `0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`](https://github.com/kingpanther13/Hubitat-local-MCP-server/tree/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018). It preserves all 15 upstream workflow files and their implementation dependencies. The portable examples at the toolkit root cover a smaller starting point; the reference retains the complete suite for advanced reuse. Workflows inside the nested reference directory are documentation/source, not active workflows for this toolkit.

| Preserved workflow | What it checks or performs | Hub / writes | Main adaptation points |
|---|---|---|---|
| `unit-tests.yml` | Groovy 3.0/Spock + eighty20results HubitatCI; normal/strict × gateway/flat matrix; aggregate `test` gate | No hub | `build.gradle`, `src/test/groovy/`, helper stubs; gateway toggle is original MCP behavior |
| `groovy24-parse.yml` | Groovy 2.4.21 parsing, closure-parameter and sandbox-class checks, including generated release files | No hub | `ci/groovy24-parse/`, production files/includes, build-release paths |
| `groovy2x-spock.yml` | Groovy 2.5.23/Spock + joelwetzel HubitatCI; framework-specific scaffold variants; `groovy2x-spock` gate | No hub | `ci/groovy2x-spock/`, imported shared specs, excluded fork-coupled specs |
| `sandbox-lint.yml` | Hubitat sandbox/source policy and vendored schema provenance rules | No hub | `tests/sandbox_lint.py`, source conventions and target paths |
| `python-tests.yml` | Python helper/runner/build/release regression tests | No live hub | `tests/test_*.py`, `.github/scripts/`, build tooling and fixtures |
| `ruff.yml` | Python formatting and lint checks | No hub | Python paths and lint configuration |
| `pr-guard.yml` | PR content/version/package policy checks | No hub | `.github/scripts/pr_guard.py`, branch/ref and package assumptions |
| `lane-gate-test.yml` | Decision logic for focused/full/skipped E2E runs | No hub | `.github/scripts/lane_gate.js`, `tests/lane_gate_test.js`, labels/status contracts |
| `lease-scripts-test.yml` | Shared-hub lease script regression checks | Mocked; no live hub | `.github/scripts/lease_acquire.sh`, `lease_release.sh`, `tests/lease_scripts_test.sh` |
| `self-deploy-recovery.yml` | Hub-less self-deployment/recovery controller regressions in unprivileged PR context | Mocked; no live hub | `.github/scripts/test_self_deploy_recovery.sh`, deployment helpers |
| `hub-e2e.yml` | Approval/lane gates, exact-head deployment, fixture setup/cleanup, real-hub assertions, official SDK conformance; probe/install-main/watchdog-maintenance dispatch modes | Dedicated hub; privileged writes | MCP-specific `tests/e2e_test.py`, `sdk_conformance_test.py`, `.github/scripts/` deployment/controller scripts, endpoints/secrets, environments, labels, concurrency |
| `e2e-setup-fixtures.yml` | Manual creation of permanent real-hub E2E fixture scaffolding | Dedicated hub; writes | `tests/e2e_test.py --setup-perm-fixtures`, fixture IDs/prefixes, both endpoint secrets, shared lease/queue |
| `publish-bundle-artifact.yml` | Builds comment-stripped/inlined release parent and child; publishes branch- and SHA-keyed files to `bundle-artifacts` | GitHub branch writes | `tools/build-release-app.py`, `strip_source.py`, `groovy_lex.py`, source names, artifact branch; name retained from older bundle delivery |
| `release.yml` | Post-merge version/changelog/release-note automation | GitHub branch/tag/release writes | `.github/scripts/release_bump.py`, labels, package manifest, deploy key and repository rules |
| `hubitat-ci-version-check.yml` | Scheduled/manual release-tag comparison; tracking issue for default eighty20results dependency | GitHub issue writes | Dependency coordinates and issue policy; does not update the joelwetzel SHA pin |

Browse the [workflow directory](../reference/hubitat-local-mcp-server/.github/workflows/) and [workflow helpers](../reference/hubitat-local-mcp-server/.github/scripts/) for exact commands and gates. The [upstream testing guide](../reference/hubitat-local-mcp-server/docs/testing.md) explains the original corpus. Application source, `libraries/`, `src/main/groovy/` helper stubs, `src/test/groovy/`, `src/test/resources/`, Python tests, fixtures, and all four historical watchdog files are preserved with that CI implementation. `reference/provenance.json` records file hashes, source-path mappings, and deliberate omissions.

The captured Hubitat UI JavaScript and root agent policy/skill packaging are omitted; explanatory platform documentation remains. The snapshot is complete for the CI implementation and app sources, not a redistribution of Hubitat firmware or its captured frontend assets. Existing source paths in tests may refer to those research assets; adapt any such dependency to your project's authorized platform references.

The toolkit includes the standalone v3.1 watchdog as a separate byte-identical copy. Its generic tools work for other apps; the original live E2E runner and package controller remain specific to the original MCP application. See [watchdog.md](watchdog.md) for that boundary and [adaptation.md](adaptation.md) before enabling a live workflow.
