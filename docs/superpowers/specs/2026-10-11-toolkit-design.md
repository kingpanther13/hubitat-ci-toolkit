# Hubitat CI Toolkit design

Approved in conversation on 2026-10-11, including continued autonomous implementation and GitHub repository creation. The user subsequently requested GPT-6.1 Sol parallel implementers.

## Outcome

Publish `kingpanther13/hubitat-ci-toolkit` as a public GitHub template: an adaptable starter and the complete pinned CI suite extracted from `kingpanther13/Hubitat-local-MCP-server` commit `0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`. The existing repository must require no modifications, workflow changes, dependency, or migration.

The watchdog is itself a standalone MCP server. Its general administration tools install arbitrary app/driver bundles, update existing app code, manage libraries, and inspect the hub without the MCP Rule Server. Its original application-specific package and settings tools remain explicitly documented as such.

## Structure

- Root starter: sample app, driver, library, Groovy/Spock harness, Groovy 2.4 parse gate, Groovy 2.5 compatibility lane, Python tests, bundle artifact, explicit live E2E workflow.
- `watchdog/`: exact v3.1 upstream application, usable independently of the test suite.
- `scripts/` and `e2e/`: MCP client, guarded phase runner, unchanged upstream lease scripts, read-only smoke and deploy/readback/restore examples.
- `reference/hubitat-local-mcp-server/`: immutable full CI scripts/workflows/tests and their source/build/doc context. Nested workflows are inert in GitHub Actions. Captured proprietary Hubitat web UI JavaScript is linked rather than redistributed; its technical Markdown reference is retained.
- `reference/provenance.json`: source revision and per-file hashes; copied components and dependencies receive documented credits and original notices.

## Behavior and boundaries

Normal CI is hub-free and runs on pushes and pull requests. Live E2E is manually dispatched on trusted main, configured through the adopter's `test-hub` environment, serialized with GitHub concurrency, and checks the hub lease before each operation. No live hub is configured or contacted during extraction.

The generic runner resolves configuration before mutations, rejects invalid assertions/paths, performs cleanup after failures, and propagates cleanup failures. It must not retry ambiguous write requests automatically or expose endpoint tokens in logs. A 20-minute workflow budget stays below the upstream 30-minute lease TTL. Hub variables are not atomic locks; one orchestration repository must own a shared test hub.

The copied watchdog retains its behavior and identity. Automatic wedge reboot, the absence of automatic timed package rollback, and its guarded self-update behavior are documented accurately.

## Verification

Use GitHub Actions for runtime tests, without local dependency installation or test execution. Test starter behavior, MCP protocol failures, cleanup and lease ownership, reproducible bundle contents, and extraction hashes. Verify the remote repository is public, a template, and contains the final commit. Verify the original working tree remains unchanged.
