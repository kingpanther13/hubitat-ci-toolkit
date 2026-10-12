# Watchdog v3.1 unit tests

Run `./gradlew watchdogTest` from the repository root. This dedicated source set
loads `watchdog/e2e-deadman-watchdog-v3-1.groovy`; it does not execute v3, v2 or v1.
The Groovy 2.4 parse lane also checks the shipped v3.1 source. No physical hub is
needed or contacted by these tests.

## Compilation and isolation

`WatchdogV31Factory` compiles v3.1 once per test JVM through the existing
`PassThroughAppValidator` sandbox parser. It caches only the compiled class. Each
call gets a fresh script instance and the normal HubitatCI initialization path,
including fresh API wrappers, settings, preferences, bindings and test mocks.

Before and after each feature (including each data-driven iteration), the base
spec removes class metaclass overrides and restores the initial contents of the
app's static maps. That resets the manual-write claim, deployment progress,
health-tick state and loopback counters. Map objects and lock identities stay
stable. Peer instances created within a feature share those maps and locks;
creating a peer does not erase an in-progress operation.

The suite runs sequentially in one test JVM. Do not enable parallel Spock
features against this shared-class fixture. Every spec asserts that exactly one
compilation occurred. Regression tests check fresh instances, state/settings/API
isolation, instance and class metaclass overrides, static-map defaults and
peer-instance coordination.

## Test inventory and provenance

The active tests are adapted from the MIT-licensed extraction of
`kingpanther13/Hubitat-local-MCP-server@0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`:

| Active spec | Archived source | Retained passing cases |
| --- | --- | ---: |
| `WatchdogV31ManualSpec` | `server/WatchdogV3ManualSpec.groovy`, retargeted to v3.1 | 173 |
| `WatchdogV31PurgeFixturesSpec` | `server/WatchdogV3PurgeFixturesSpec.groovy`, retargeted to v3.1 | 6 |
| `WatchdogV31PackageDeploySpec` | `server/WatchdogV31PackageDeploySpec.groovy` | 61 |
| `WatchdogV31ParitySpec` | `server/WatchdogV31ParitySpec.groovy` | 64 |

These paths are relative to `reference/hubitat-local-mcp-server/src/test/groovy`.
The active `WatchdogV31Harness`, `PassThroughAppValidator` and
`PassThroughSandboxClassLoader` retain the same source attribution. The cache
factory, isolation base spec and cache regression spec are toolkit additions.
The archived files and their extraction hashes remain unchanged.

`ci/watchdog/v31-test-inventory.json` records all 304 retained executed case names
from [the passing pre-change run](https://github.com/kingpanther13/hubitat-ci-toolkit/actions/runs/38280167143).
Two descriptions now say v3.1; all parameterized cases are retained. The old v3
package/parity copies are superseded by the v3.1 specs, and retired v1/v2 specs
are no longer selected. References to older version names inside fixtures test
v3.1's source-protection behavior; they do not load those old apps.

CI runs `python3 tools/check_watchdog_results.py` against the actual JUnit XML.
It rejects missing retained cases, missing suites, empty reports, failed or
skipped cases, and any unexpected suite (including retired watchdog versions).
New cases can be added without shrinking the retained inventory. The five
cache regressions bring the initial active total to 309 passing cases.

## Verification of this change

The cache regression failed on the uncached harness because every instance had
a distinct compiled class. After caching, all 304 retained cases and all five
new regression cases passed, with one compilation reported throughout the JVM.
[Run 38283283384](https://github.com/kingpanther13/hubitat-ci-toolkit/actions/runs/38283283384)
took 1m17s for the watchdog job and about 1m33s for Toolkit CI's jobs through the
required gate. The preceding archived-watchdog job took 10m. The improvement
combines compilation reuse with selecting only v3.1; those effects were not
benchmarked separately. Runner queues and cold dependency downloads can add time.
