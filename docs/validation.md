# Initial extraction validation

Source revision: `kingpanther13/Hubitat-local-MCP-server@0e6094bf688d7edefd18d1f52ffe7b0ee7ab2018`.

Tested toolkit code revision: `23aa23ccbdfaf57c6c632c5f463f8666e0c5fa5b`.

[GitHub Actions run 38186101914](https://github.com/kingpanther13/hubitat-ci-toolkit/actions/runs/38186101914) completed successfully. All six jobs passed:

| Job | Evidence |
| --- | --- |
| Python and packaging | 25 MCP/E2E offline tests, five bundle tests, example bundle build and artifact upload |
| Groovy primary | Sample app and driver behavior under Groovy 3 / eighty20results HubitatCI |
| Groovy 2.5 | The same starter specs under the joelwetzel framework fork |
| Groovy 2.4 parse | Parser regression fixtures, starter app/driver/library, and exact v3.1 watchdog source |
| Reference watchdog | Original `server.Watchdog*` regression specs; upstream-retired v1/v2 specs retain their original skips |
| Reference infrastructure | Original lease and lane-gate tests, plus active lease-script shell syntax |

The extraction check verified all **375 reference files** against the pinned SHA256 manifest and **eight exact copies**, including the standalone watchdog, lease scripts and Gradle wrapper.

A separate GPT-6.1 Sol reviewer checked workflow trust boundaries, E2E cleanup, protocol handling, packaging and documentation. Its important finding concerned inherited lease-script diagnostics exposing remote hub-variable text; the active workflow now suppresses that output and prints fixed status messages. The reviewer verified the correction and reported no remaining important issue.

The source Hubitat repository's checkout and tracked files were unchanged. No test hub was configured, contacted or modified for this extraction. The new manual live E2E workflow and standalone watchdog installation instructions have not been exercised on a newly provisioned physical hub as part of this extraction. The full original application test corpus remains available in `reference/`; only the watchdog and infrastructure subset listed above was executed in this toolkit's initial CI.

The final completion-record commit changes only documentation; the tested code revision above identifies the exact implementation that produced these results.
