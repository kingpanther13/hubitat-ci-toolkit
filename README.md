# Hubitat CI Toolkit

[![Toolkit CI](https://github.com/kingpanther13/hubitat-ci-toolkit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/kingpanther13/hubitat-ci-toolkit/actions/workflows/ci.yml)

A reusable GitHub Actions testing suite for Hubitat apps and drivers, with a **standalone watchdog MCP server** for installing code and administering a hub.

Extracted from [Hubitat-local-MCP-server](https://github.com/kingpanther13/Hubitat-local-MCP-server) at [`0e6094bf`](https://github.com/kingpanther13/Hubitat-local-MCP-server/tree/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018). This repository is independent: adopting it requires **no changes to that project**.

## Three ways to use it

1. **Start a project:** choose **Use this template**, replace the sample app/driver/library, and extend their tests. Hub-free CI runs on pushes and pull requests.
2. **Add CI to an existing project:** copy the relevant modules using the [adaptation guide](docs/adaptation.md). The [complete CI inventory](docs/ci-inventory.md) maps the original suite's workflows and their configuration points.
3. **Use just the watchdog:** install [the standalone Groovy app](watchdog/e2e-deadman-watchdog-v3-1.groovy), enable its OAuth endpoint, and connect an MCP client. It can install your own app/driver bundles, update app code, manage libraries, and inspect the hub. **The MCP Rule Server is not required for those general tools.** See the [watchdog guide](docs/watchdog.md).

## What is included

| Area | Adaptable starter | Complete reference |
| --- | --- | --- |
| Unit tests | Groovy/Spock examples, HubitatCI sandbox, mock devices/state/events | Full app and rule harnesses, helper stubs, integration fixtures and regression corpus |
| Compatibility | Groovy 2.4 parser/sandbox gate and Groovy 2.5 test lane | Original compatibility builds and tests |
| Live E2E | JSON-configured setup/test/cleanup, lease checks, source readback and restore | Full E2E runner, fixture provisioning, focused/full lane gates, SDK conformance and diagnostics |
| Watchdog | Independent v3.1 MCP app and usage guide | Earlier generations, maintenance scripts and recovery tests |
| Packaging | Reproducible app/driver/library bundle and CI artifact | Built-app packaging, fork artifacts, HPM release automation and PR guards |
| Maintenance | Starter workflow and dependency configuration | Original lint, dependency checks, review/release templates and automation |

The starter lives at the repository root. [`reference/hubitat-local-mcp-server/`](reference/hubitat-local-mcp-server/) preserves the existing suite and its source/build context; its nested workflows are reference material and do not execute here. [Per-file hashes](reference/provenance.json) identify the exact extraction.

## Quick start

Java 17 runs the Gradle wrapper; the Groovy compatibility lanes also need Java 11. Python 3.11+ runs the scripts with no third-party dependencies.

```sh
./gradlew test
./gradlew watchdogTest
./gradlew -p ci/groovy2x-spock test
./gradlew -p ci/groovy24-parse parse24
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s toolkit-tests -v
python3 tools/build_bundle.py
```

Change `apps/example-app.groovy`, `drivers/example-driver.groovy`, and the shared library to your project. Update `bundle.json` to declare your bundle and installation order. Follow [unit testing](docs/unit-testing.md) for harness setup and [packaging](docs/packaging.md) for distribution.

The [watchdog unit-test guide](docs/watchdog-testing.md) describes the active v3.1 suite, compilation cache, isolation checks, and retained test inventory.

Live testing is a separate, manually dispatched **Test hub E2E** workflow. Configure your own `test-hub` environment and watchdog endpoint using [the E2E guide](docs/e2e.md). The default smoke configuration only reads the watchdog; the deploy/readback example updates and restores a dedicated Apps Code class. No test hub, credentials, or shared hub access comes with this template.

Dependency updates use Renovate for Gradle and HubitatCI forks and Dependabot for GitHub Actions, with automatic merging after required offline checks. See [dependency maintenance](docs/dependency-updates.md) for compatibility limits and the repository settings adopters must recreate.

See the [validation record](docs/validation.md) for the initial CI results and test scope.

## Credits and license

The testing stack builds on [biocomp/hubitat_ci](https://github.com/biocomp/hubitat_ci), the [joelwetzel fork](https://github.com/joelwetzel/hubitat_ci), and the [eighty20results fork](https://github.com/eighty20results/hubitat_ci), plus Groovy, Spock and Gradle. See [CREDITS.md](CREDITS.md) for component provenance and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for retained notices.

Toolkit code is MIT licensed; upstream material retains its applicable notices. This is a community toolkit, not an official Hubitat product. Neither local harnesses nor parser checks emulate all firmware behavior; live tests supply that additional coverage.
