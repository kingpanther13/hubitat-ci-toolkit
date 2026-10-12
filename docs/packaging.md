# Package apps, drivers and libraries

Edit [`bundle.json`](../bundle.json): choose your own namespace/bundle name, then list source files in installation order. Put libraries before consumers, and child apps before parent apps when the parent expects the child code to exist. File paths are relative to the manifest's directory; archive basenames must be unique. The example includes a library, driver and app.

```sh
python3 tools/build_bundle.py
# dist/hubitat-bundle.zip, with its SHA256 printed
python3 tools/build_bundle.py --manifest bundle.json --output dist/my-project.zip
```

The builder writes `install.txt` and `update.txt` in the Hubitat bundle format demonstrated by the [original suite's fixture](../reference/hubitat-local-mcp-server/tests/fixtures/mcp-e2e-throwaway-bundle.zip). Their entries preserve the manifest order. Timestamps and permissions are fixed for reproducible ZIP bytes. Inputs are validated before replacing an existing artifact. A `LICENSE` file next to the manifest is included when present. Source files remain unchanged; Hubitat resolves `#include` using the bundled libraries.

The **Toolkit CI** packaging job uploads the ZIP and checksum as a GitHub Actions artifact. Download it to import through **Developer Tools → Bundles**, or publish it at a stable HTTPS URL your hub can fetch, then use the standalone watchdog's `hub_install_bundle` tool. Actions artifact download URLs require GitHub authentication and are not suitable as direct hub import URLs.

```json
{
  "name": "hub_install_bundle",
  "arguments": {
    "importUrl": "https://github.com/YOUR-USER/YOUR-REPO/releases/download/v1.0.0/hubitat-bundle.zip",
    "confirm": true
  }
}
```

Code installation does not configure an installed app instance or create a virtual device. Finish that setup in the Hubitat UI, then configure any project-specific E2E checks.

For automated HPM publication, built-app stripping/inlining, fork-PR artifacts, release notes and version bumps, see the complete [reference tools](../reference/hubitat-local-mcp-server/tools/) and [release workflow](../reference/hubitat-local-mcp-server/.github/workflows/release.yml). Those original workflows encode that project's version locations, app names, bot credentials and branch conventions. Follow the [adaptation guide](adaptation.md) before activating them in your repository.
