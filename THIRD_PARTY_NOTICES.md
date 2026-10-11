# Third-party notices

This repository's [MIT LICENSE](LICENSE) covers the original Hubitat-local-MCP-server implementation and toolkit adaptations under that license. It does not replace licenses or notices for separately licensed files or dependencies. Keep original headers and these notices when redistributing the relevant files.

## Included upstream implementation

Source: [kingpanther13/Hubitat-local-MCP-server at `0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`](https://github.com/kingpanther13/Hubitat-local-MCP-server/tree/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018).

Scope: the reference snapshot's original app/library sources, CI workflows/builds/helpers, docs/tests/fixtures, portable extractions/adaptations, and the byte-identical standalone v3.1 watchdog. The upstream notice reads `Copyright (c) 2025`; its complete MIT text remains in [LICENSE](LICENSE) and the reference copy of that file. The notice is preserved without inventing a copyright-holder name. [CREDITS.md](CREDITS.md) supplies source-history attribution separately.

## Gradle wrapper — Apache-2.0

Scope: `gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.jar`, and the corresponding files in the reference snapshot. The scripts retain `Copyright © 2015 the original authors.` and their Apache-2.0 headers. The JAR contains `META-INF/LICENSE`. [licenses/Gradle-LICENSE.txt](licenses/Gradle-LICENSE.txt) supplies the complete Gradle license text, verified against [Gradle v9.8.0](https://github.com/gradle/gradle/blob/v9.8.0/LICENSE), the configured distribution version. The downloaded Gradle distribution has its own included notices; it is not bundled here beyond the wrapper.

## Vendored MCP JSON schemas

Scope: `reference/hubitat-local-mcp-server/src/test/resources/mcp-schema/2025-06-18/schema.json` and `2026-07-28/schema.json`.

| Schema | Immutable upstream source | Retained license |
|---|---|---|
| 2025-06-18 | [Commit `35ccd9fd63501a68b733fe3ad9e187f62c7ac839`](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/35ccd9fd63501a68b733fe3ad9e187f62c7ac839/schema/2025-06-18/schema.json) | [MCP-schema-2025-LICENSE.txt](licenses/MCP-schema-2025-LICENSE.txt), MIT, `Copyright (c) 2024–2025 Anthropic, PBC and contributors` |
| 2026-07-28 | [Commit `5f5440bb26a62e2cf3440b92da5a667efa03b267`](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/5f5440bb26a62e2cf3440b92da5a667efa03b267/schema/2026-07-28/schema.json) | [MCP-schema-2026-LICENSE.txt](licenses/MCP-schema-2026-LICENSE.txt), the complete upstream Apache-2.0/MIT transition notice and terms |

The 2026 upstream license says new code/specification contributions and contributions whose relicensing consent was obtained are Apache-2.0, while earlier contributions without consent retain MIT. Its MIT notice names `Model Context Protocol a Series of LF Projects, LLC.` The same upstream file mentions CC-BY-4.0 for documentation excluding specifications; this toolkit vendors schemas, not that upstream documentation. The full file is retained to avoid simplifying away its original licensing boundary. Schema provenance/hashes are recorded in the [preserved README](reference/hubitat-local-mcp-server/src/test/resources/mcp-schema/README.md).

## HubitatCI — dependencies, Apache-2.0

No HubitatCI framework source or compiled dependency JAR is vendored. Build files resolve it separately. Its original and fork license texts are supplied for attribution:

- [biocomp/hubitat_ci](https://github.com/biocomp/hubitat_ci/blob/d3405cd11ea7ee967824b191801cf4149ba93f1c/LICENSE): [HubitatCI-biocomp-LICENSE.txt](licenses/HubitatCI-biocomp-LICENSE.txt).
- [joelwetzel/hubitat_ci at `a62a351eed9ab80342e9a640c89f9e3b7fe95aa4`](https://github.com/joelwetzel/hubitat_ci/blob/a62a351eed9ab80342e9a640c89f9e3b7fe95aa4/LICENSE): [HubitatCI-joelwetzel-LICENSE.txt](licenses/HubitatCI-joelwetzel-LICENSE.txt).
- [eighty20results/hubitat_ci v0.28.6 / `890d6b681dd39b25eea856b1efe3b21042a8f7f9`](https://github.com/eighty20results/hubitat_ci/blob/890d6b681dd39b25eea856b1efe3b21042a8f7f9/LICENSE): [HubitatCI-eighty20results-LICENSE.txt](licenses/HubitatCI-eighty20results-LICENSE.txt).

All three retain `Copyright 2019 Artem Tokmakov` and Apache-2.0. Fork-maintainer credits and lane usage are documented in [CREDITS.md](CREDITS.md).

## Other dependencies and platform resources

The preserved Gradle/Python/workflow files reference additional third-party packages and GitHub Actions. Those packages/action implementations are fetched separately, not copied into this repository. Their licenses and transitive notices apply when downloaded and must be retained if you redistribute them. The fixture bundle under `tests/fixtures/` contains original upstream test code and follows the upstream MIT notice.

Captured Hubitat UI JavaScript under the upstream `resources/hub2-source/` is omitted. Only explanatory upstream Markdown and source links remain. See the [pinned source resource tree](https://github.com/kingpanther13/Hubitat-local-MCP-server/tree/0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018/resources/hub2-source) for provenance. The toolkit does not grant a license to Hubitat firmware, proprietary admin UI assets, or trademarks.
