# Automatic dependency maintenance

The hosted Renovate GitHub App manages the active Gradle builds, Gradle wrapper,
Renovate validator, and both consumed HubitatCI forks. Dependabot manages GitHub
Actions weekly, grouping its action updates. The managers do not overlap.

Both bots automatically squash-merge passing updates, including major versions
where the compatibility rules below permit them. Failed checks leave the PR open.
Renovate waits for all checks and rebases behind-main branches before merging;
Dependabot enables GitHub's native auto-merge, which waits for branch protection.
No automatic review approval or personal access token is needed.

## Compatibility boundaries

- Root tests stay on Groovy 3.0 and Spock 2's `groovy-3.0` variant.
- The compatibility runtime stays on Groovy 2.5 and Spock 2's `groovy-2.5` variant.
- The hub syntax parser stays on Groovy 2.4. Java 11 remains the test toolchain.
- Chromecast stays at 0.11.1 because later POM version ranges break resolution.
- Byte Buddy follows standard releases, excluding its separate `-jdk5` variant.
- `eighty20results/hubitat_ci` follows GitHub releases. The untagged
  `joelwetzel/hubitat_ci` fork follows `master` with immutable commit SHA updates.

The immutable `reference/` archive is excluded from Renovate. Its original
versions and per-file hashes remain historical evidence. The active Gradle wrapper
may evolve independently; archive hashes, watchdog, lease scripts and license
copies remain checked. Updating a dependency does not refresh the archived suite.

## Required repository settings

These settings are outside the template files and must be recreated by adopters:

1. Install the hosted Renovate GitHub App for the repository and enable Dependabot.
2. Enable **Allow auto-merge** and squash merging in repository settings.
3. Protect the default branch, requiring an up-to-date PR and these checks from
   GitHub Actions: `Toolkit CI required` and `dependency-updates`.
4. Do not require human reviews if unattended bot merging is desired. Keep force
   pushes and branch deletion disabled. Do not give the bots a bypass of checks.

The aggregate `Toolkit CI required` check rejects failed, cancelled or skipped
Python/packaging, Groovy matrix, active v3.1 watchdog and infrastructure jobs.
The watchdog job checks all retained test cases and rejects skipped or older-version executions.
`dependency-updates` validates the Renovate schema and performs read-only real
lookups from current and deliberately stale fixtures. It verifies discovery of
both forks, correct Groovy/Spock variants, immutable SHA updates and exclusion
of archived manifests. It does not run Gradle or modify repository dependencies.

The Dependabot workflow runs on `pull_request` solely to enable auto-merge for
same-repository PRs authored by `dependabot[bot]`. It never checks out or executes
PR code. Renovate uses its own app identity to merge. A changed PR head must pass
checks again; neither bot receives an unconditional merge bypass.

Live hub E2E remains manual-only (`workflow_dispatch`) and is not a required check.
Dependency PRs neither request deployment approval nor touch a hub. This toolkit
has no automatic app-version or release workflow. Offline CI cannot prove that a
new dependency behaves identically on every adopter's physical hub.

For an already-open bot PR, a new bot update/rebase picks up this configuration.
Renovate's onboarding PR becomes obsolete when `.github/renovate.json` reaches the
default branch; it does not also need to be merged.

## Provenance and references

The compatibility rules, fork regex managers and discovery checker were adapted
from [Hubitat-local-MCP-server PR #534](https://github.com/kingpanther13/Hubitat-local-MCP-server/pull/534)
under its MIT license. See [CREDITS.md](../CREDITS.md) for upstream framework credits.
The active toolkit does not declare the original project's JSON schema validator.

- [Renovate auto-merge](https://docs.renovatebot.com/key-concepts/automerge/)
- [GitHub's Dependabot auto-merge guide](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/automate-dependabot-with-actions)
