# Contributing

Keep the starter independent of any particular app's names, IDs, endpoints or release process. Add behavior tests for code changes and preserve credits for borrowed components. Hub-free CI runs on every pull request.

The source snapshot under `reference/` is intentionally immutable. To adopt a new upstream revision, extract it as a deliberate update, refresh `reference/provenance.json`, review behavioral changes, and retain the upstream notices. The original Hubitat-local-MCP-server repository needs no changes.

Do not put real hub credentials in examples. Live E2E is separately configured by each adopter through the `test-hub` environment; the checked-in manual workflow only runs on `main`. Configure required reviewers on that environment when multiple people can dispatch tests. Use one orchestration repository for each shared physical hub.

See [unit testing](docs/unit-testing.md), [E2E](docs/e2e.md), [watchdog](docs/watchdog.md), and [packaging](docs/packaging.md) for the relevant verification commands. Static harnesses and Groovy compatibility checks do not reproduce every Hubitat firmware behavior.
