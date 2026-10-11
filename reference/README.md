# Complete source CI reference

`hubitat-local-mcp-server/` contains the CI workflows, scripts, all tests, harnesses, watchdog generations, fixtures, source files, libraries, build tools, release metadata and supporting docs at the revision recorded in [provenance.json](provenance.json).

These are **original project-specific files**, not the starter's active workflows. Their original names and assumptions are intentional; see [CI inventory](../docs/ci-inventory.md) and [adaptation guide](../docs/adaptation.md). Nested `.github/workflows` files do not run in this repository. Start with the root starter and consult this reference when adopting advanced features.

Each file's SHA256 is recorded. Agent instructions are archived as `UPSTREAM_AGENT_GUIDANCE.md` for context, not inherited as toolkit instructions. Captured Hubitat UI JavaScript is excluded; it is not CI implementation, and this toolkit does not grant a license to Hubitat firmware. The original Markdown API observations are preserved with their links to those captures.

This is a one-way snapshot. It neither changes nor adds a dependency to the original repository. Upstream updates can be adopted deliberately in this repository at a new pinned commit.
