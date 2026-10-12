# Groovy testing starter

The starter tests ordinary Hubitat apps and drivers. It does not require MCP, hub credentials, a running hub, or a live device. The complete original MCP project is preserved separately in `reference/` for examples beyond this small starter.

## Run in CI

Install JDK 17 for the Gradle 9.8 daemon and JDK 11 for the test toolchain, then run from the repository root:

```sh
./gradlew --no-daemon test
./gradlew --no-daemon -p ci/groovy2x-spock test
./gradlew --no-daemon -p ci/groovy24-parse parse24
```

| Lane | Runtime and dependency | What it verifies |
| --- | --- | --- |
| Primary | Groovy 3.0.25, Spock 2.3, `eighty20results/hubitat_ci:v0.28.6` | Sample app behavior inside HubitatCI and driver method behavior |
| Optional runtime | Groovy 2.5.23, Spock 2.3, `joelwetzel/hubitat_ci:a62a351eed` | The same specs under an older Groovy runtime |
| Parse | Groovy 2.4.21 | App, driver, library, and copied watchdog syntax; explicit empty closure parameters; curated blocked classes; class and method size budgets |

HubitatCI is resolved through JitPack with POM metadata because the published Gradle module metadata omits dependencies. The HTTP builder, Quartz, and Chromecast dependencies are declared explicitly because HubitatCI exposes their classes through public bytecode while its POM declares them runtime-only. `commons-collections` is constrained to its patched 3.2.2 version. None of these test dependencies is deployed to a hub.

The parse task first runs the copied checker fixture suite. It resolves `#include` against repository-level `libraries/`, preserving original file and line locations in diagnostics. Libraries are also parsed independently. It always checks `watchdog/e2e-deadman-watchdog-v3-1.groovy` without changing that copy. A curated blocked-class check is an early warning, not a full implementation of Hubitat's sandbox. Unresolved hub-only class references produce an explicit notice and skip the blocked-class and bytecode-size checks for that file.

## Sample app and driver

`apps/example-app.groovy` defines `toolkit / CI Toolkit Motion Switches`. Select motion sensors and switches in the app preferences. `installed()` calls `initialize()`, which subscribes each sensor's `motion` attribute to `motionHandler()`. Active motion turns every selected switch on; inactive motion turns them off. `updated()` clears old subscriptions before rebuilding them. With multiple sensors, every inactive event turns the switches off; this example does not aggregate occupancy across sensors.

`drivers/example-driver.groovy` defines `toolkit / CI Toolkit Virtual Dimmer`. `on()` and `off()` emit switch events, and `setLevel(value, duration = null)` emits a level clamped to 0–100 plus the matching switch state. This virtual driver accepts the duration argument without simulating a transition. Install `libraries/levels.groovy` (`toolkit.Levels`) before compiling the driver on a hub. Its `boundedLevel()` helper is inlined by `#include toolkit.Levels`.

`ExampleAppSpec` loads the actual app through `HubitatAppSandbox`, with a fresh `AppExecutor` mock and fixture state for every feature. It tests subscription wiring, synthetic active/inactive events, replacement after settings changes, repeated updates, and unknown motion values. Motion sensors are `DeviceWrapper` stubs with an ENUM `motion` attribute, so HubitatCI validates subscription device types, attribute names, and handler methods before forwarding calls to the recorder. Switch targets use the smaller recording `TestDevice` fixture. The sandbox skips definition and preference validation and does not run top-level DSL declarations; it executes real app method bodies. The Groovy 2.5 build supplies one explicit fork selection property so the sandbox receives only the options its fork supports.

`ExampleDriverSpec` resolves the actual driver's library and parses its method bodies through `DriverHarness`. It records `sendEvent()` calls without executing the driver metadata DSL. The tests cover installation defaults, switch commands, and level boundaries. The parse lane checks metadata syntax only. A real-hub fixture should validate driver metadata semantics and platform behavior for your application.

## Adapt to another project

1. Replace the files under `apps/`, `drivers/`, and `libraries/`; update the sample spec source paths and device settings.
2. Use `DeviceWrapper` stubs with supported `Attribute` stubs for subscribed devices (see `motionSensor()` in `ExampleAppSpec`). Subscription validation happens before the executor receives calls. Use `SubscriptionRecorder.record()` in your app executor stub, then `fireEvent()` to exercise the subscribed handler. It uses source identity and fails when no subscription matches.
3. Seed `TestDevice.attributeValues` for attribute reads; inspect `commands` for device command dispatch. The fixture intentionally does not pretend that a command proves a physical device changed state.
4. Add APIs your app actually calls to its executor mock. Use `TestAtomicState` when testing `atomicState.updateMapValue()`, and `PermissiveLog.messages` to inspect logging. Each test should own its state and reset any metaclass changes it introduces.
5. Adjust `productionFiles` in `ci/groovy24-parse/build.gradle` if your source layout changes. Preserve the watchdog entry when using the shared-hub E2E workflow.

The helpers and parse checker carry provenance comments linking them to the pinned MIT-licensed reference. `IncludeResolver` and the parse checker are compatible with Groovy 2.4 so all three lanes can share the same library expansion. The starter does not import the reference project's MCP-specific harness, child-app factories, request drivers, or tool schema validators. Platform helper stubs and the pass-through sandbox validator are available in that complete reference if your project needs them.

Test results are written to `build/test-results/test/` and `build/reports/tests/test/`; the optional runtime lane writes the same paths under `ci/groovy2x-spock/build/`.
