# Credits and provenance

This toolkit extracts and adapts reusable testing and deployment infrastructure from [kingpanther13/Hubitat-local-MCP-server](https://github.com/kingpanther13/Hubitat-local-MCP-server). The complete CI/application source reference is pinned to [`0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`](https://github.com/kingpanther13/Hubitat-local-MCP-server/tree/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018). [`reference/provenance.json`](reference/provenance.json) records retained source files and their SHA-256 hashes, path mappings, and deliberate omissions. The original MIT license and copyright notice are retained in [LICENSE](LICENSE).

## Directly extracted implementation

Credit **kingpanther13 and the upstream contributors** for the original application, CI workflows, test corpus, fixtures, helper scripts, and independent watchdog server. The watchdog's own `definition` names `kingpanther13` as author and is retained unchanged. Representative source-history evidence:

| Contribution | Upstream author recorded by Git | Source commit |
|---|---|---|
| Initial Gradle/Spock/HubitatCI scaffold | kingpanther13 | [`e0bfea41`](https://github.com/kingpanther13/Hubitat-local-MCP-server/commit/e0bfea41) |
| Self-configuring real-hub E2E workflow | Dan Cox | [`4c916dbc`](https://github.com/kingpanther13/Hubitat-local-MCP-server/commit/4c916dbc) |
| Groovy 2.5 runtime lane | kingpanther13 | [`203d5d2e`](https://github.com/kingpanther13/Hubitat-local-MCP-server/commit/203d5d2e) |
| Independent v2 watchdog MCP deployment server | kingpanther13 | [`a247ed54`](https://github.com/kingpanther13/Hubitat-local-MCP-server/commit/a247ed54) |
| Manual v3 package deployment and wedge recovery | kingpanther13 | [`6ebb4607`](https://github.com/kingpanther13/Hubitat-local-MCP-server/commit/6ebb4607) |
| v3.1 built-package support | kingpanther13 | [`864998ff`](https://github.com/kingpanther13/Hubitat-local-MCP-server/commit/864998ff) |

At the pinned commit, `git log` records these distinct author names: kingpanther13, Dan Cox, Dan, Gordon Thelander, nemodio, TonyMajorDev, ashwinma14, Claude, github-actions[bot], and dependabot[bot]. These are source-history author labels, including automation/AI labels; they are not a claim that every named author contributed to every copied file. The original history remains authoritative for per-file attribution. Credits do not change the original copyright notice or license.

## HubitatCI framework lineage and dependencies

The HubitatCI framework is a dependency resolved from its own repositories, rather than source code copied into this toolkit. Credit its original author and the fork maintainers separately from the upstream toolkit implementation:

- **[biocomp / Artem Tokmakov](https://github.com/biocomp/hubitat_ci)** created the original Hubitat script testing framework and public API. The verified [license](https://github.com/biocomp/hubitat_ci/blob/d3405cd11ea7ee967824b191801cf4149ba93f1c/LICENSE) carries `Copyright 2019 Artem Tokmakov` and Apache-2.0 terms. GitHub identifies this as the source repository for both forks below.
- **[joelwetzel / Joel Wetzel](https://github.com/joelwetzel/hubitat_ci)** maintains a fork extending the original framework. The Groovy 2.5 runtime lane uses commit [`a62a351eed9ab80342e9a640c89f9e3b7fe95aa4`](https://github.com/joelwetzel/hubitat_ci/commit/a62a351eed9ab80342e9a640c89f9e3b7fe95aa4); its [license](https://github.com/joelwetzel/hubitat_ci/blob/a62a351eed9ab80342e9a640c89f9e3b7fe95aa4/LICENSE) retains the original Apache-2.0 notice. The original MCP repository previously used this fork as its default harness before migrating.
- **[eighty20results / Thomas Sjølshagen](https://github.com/eighty20results/hubitat_ci)** maintains the Groovy 3 framework fork used by the original default unit-test lane. That build pins `v0.28.6`, resolved to [`890d6b681dd39b25eea856b1efe3b21042a8f7f9`](https://github.com/eighty20results/hubitat_ci/commit/890d6b681dd39b25eea856b1efe3b21042a8f7f9); its [license](https://github.com/eighty20results/hubitat_ci/blob/890d6b681dd39b25eea856b1efe3b21042a8f7f9/LICENSE) retains the original Apache-2.0 notice.

GitHub repository metadata, pinned source commits, licenses, and the preserved Gradle build files were checked for this attribution. Both forks descend directly from biocomp according to GitHub's `parent`/`source` metadata; this document does not infer a linear fork chain between them. Copies of all three verified license files are included under [licenses/](licenses/).

## Other copied components and supporting tools

**Gradle and its original authors** provide the copied wrapper scripts and wrapper JAR. Their Apache-2.0 terms apply independently of this toolkit's MIT license. The scripts retain their copyright/license headers, the JAR embeds `META-INF/LICENSE`, and [licenses/Gradle-LICENSE.txt](licenses/Gradle-LICENSE.txt) retains the license text.

**Model Context Protocol contributors** provide the two vendored official JSON schemas used by the original wire-conformance specs. Their immutable source URLs/hashes are recorded in the preserved [schema README](reference/hubitat-local-mcp-server/src/test/resources/mcp-schema/README.md). The 2025 schema revision's upstream MIT license and the 2026 revision's Apache-2.0/MIT transition notice are both retained under [licenses/](licenses/).

Groovy, Spock, JitPack, Byte Buddy, networknt JSON Schema Validator, the MCP SDK, Python/pytest/requests/Ruff, Node.js, and GitHub Actions support build and CI execution. They are dependencies/services, not authors of the extracted watchdog or workflows. Their own licenses apply when they are downloaded or redistributed; [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) distinguishes included files from dependency references.

Hubitat provides the target platform and public documentation. Captured proprietary Hubitat web UI JavaScript is deliberately omitted; source links and explanatory upstream documentation are retained instead. This extraction does not claim ownership of, permission to relicense, or redistribution of Hubitat firmware/frontend code.
