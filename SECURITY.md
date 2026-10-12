# Security

The watchdog MCP endpoint grants administrative hub access. Treat its URL and OAuth token as secrets. Share this repository's code and examples, not real endpoint URLs or generated result files.

Normal CI uses no hub secrets. The live workflow is manual, restricted to `main`, and uses a separately configured GitHub environment. Arbitrary pull-request code must not run with hub credentials; the original suite's trusted-controller/fork-approval patterns are documented in the adaptation guide.

The E2E runner never retries uncertain writes automatically, checks lease ownership before each operation, and avoids printing response bodies or endpoint URLs in failures. The lease protocol is cooperative, not a hub-side atomic lock: serialize orchestration for a physical hub in one repository.

Report suspected vulnerabilities privately using GitHub's private vulnerability reporting when enabled, or contact the repository owner privately. Include affected files, revision and reproduction steps without real tokens or personal hub data.
