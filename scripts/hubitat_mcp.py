#!/usr/bin/env python3
"""Small stateless HTTP JSON-RPC client. No retries and no remote error echoing."""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class MCPError(Exception):
    """A safe diagnostic that never embeds a URL, arguments, or remote content."""


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def decode_json(text):
    """Reject ambiguous duplicate fields and non-JSON numeric constants."""
    def invalid_constant(value):
        raise ValueError("invalid constant")
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=invalid_constant)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MCPClient:
    def __init__(self, url, timeout=30, transport=None):
        try:
            parts = urlsplit(url)
            if (parts.scheme not in {"http", "https"} or not parts.hostname
                    or parts.username is not None or parts.password is not None
                    or parts.fragment or any(character.isspace() for character in url)):
                raise ValueError()
            parts.port  # Validate malformed ports without exposing the URL.
            if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise MCPError("invalid endpoint or timeout") from None
        self._url = url
        self._timeout = timeout
        self._transport = transport or build_opener(_NoRedirect()).open
        self._next_id = 1

    def call(self, method, params=None):
        if not isinstance(method, str) or not method or (params is not None and not isinstance(params, dict)):
            raise MCPError("invalid JSON-RPC request")
        request_id = self._next_id
        self._next_id += 1
        try:
            body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method,
                               "params": {} if params is None else params}, allow_nan=False).encode("utf-8")
            request = Request(self._url, data=body, headers={
                "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
            with self._transport(request, timeout=self._timeout) as response:
                if response.status != 200:
                    raise MCPError("HTTP request failed")
                payload = response.read(8 * 1024 * 1024 + 1)
            if len(payload) > 8 * 1024 * 1024:
                raise MCPError("response exceeded size limit")
        except MCPError:
            raise
        except Exception:
            # urllib exceptions can include credentials from the request URL.
            raise MCPError("HTTP request failed; outcome may be unknown") from None
        try:
            envelope = decode_json(payload.decode("utf-8"))
        except (UnicodeError, ValueError, TypeError):
            raise MCPError("invalid JSON-RPC response") from None
        if (not isinstance(envelope, dict) or envelope.get("jsonrpc") != "2.0"
                or type(envelope.get("id")) is not int or envelope["id"] != request_id
                or ("result" in envelope) == ("error" in envelope)):
            raise MCPError("invalid JSON-RPC envelope")
        if "error" in envelope:
            raise MCPError("JSON-RPC server reported an error")
        if not isinstance(envelope["result"], dict):
            raise MCPError("invalid JSON-RPC result")
        return envelope["result"]

    def tool(self, name, arguments):
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or not isinstance(arguments, dict):
            raise MCPError("invalid tool request")
        result = self.call("tools/call", {"name": name, "arguments": arguments})
        if "isError" in result and type(result["isError"]) is not bool:
            raise MCPError("invalid tool result")
        if result.get("isError") is True:
            raise MCPError("tool reported an error; outcome may be unknown")
        content = result.get("content")
        if content is not None:
            if not isinstance(content, list):
                raise MCPError("invalid tool content")
            for block in content:
                if (not isinstance(block, dict) or not isinstance(block.get("type"), str)
                        or (block["type"] == "text" and not isinstance(block.get("text"), str))):
                    raise MCPError("invalid tool content")
        if "structuredContent" in result:
            if not isinstance(result["structuredContent"], dict):
                raise MCPError("invalid structured tool content")
            return result["structuredContent"]
        if not content:
            raise MCPError("missing tool content")
        if len(content) == 1 and content[0]["type"] == "text":
            try:
                return decode_json(content[0]["text"])
            except ValueError:
                return content[0]["text"]
        return {"content": content}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-env", default="WATCHDOG_URL", help="environment variable holding the MCP URL")
    parser.add_argument("--tool", required=True)
    parser.add_argument("--arguments-file", type=Path, help="JSON object; defaults to empty arguments")
    parser.add_argument("--result-file", type=Path, help="opt-in full tool data, saved privately; may contain secrets")
    args = parser.parse_args(argv)
    result_handle = None
    try:
        arguments = decode_json(args.arguments_file.read_text(encoding="utf-8")) if args.arguments_file else {}
        if not isinstance(arguments, dict):
            raise MCPError("arguments must be a JSON object")
        client = MCPClient(os.environ.get(args.url_env, ""))
        if args.result_file:
            # Reserve before a potentially mutating call: output-file errors must not
            # tempt a human to replay a write that already applied.
            descriptor = os.open(args.result_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            result_handle = os.fdopen(descriptor, "w", encoding="utf-8")
        result = client.tool(args.tool, arguments)
        if result_handle:
            json.dump(result, result_handle, ensure_ascii=False, allow_nan=False)
            result_handle.write("\n")
            result_handle.flush()
            result_handle.close()
            result_handle = None
        if isinstance(result, dict) and result.get("success") is False:
            raise MCPError("tool reported unsuccessful operation; outcome may be unknown")
        print(json.dumps({"ok": True, "result_type": type(result).__name__}))
        return 0
    except MCPError as error:
        print("MCP call failed: " + str(error), file=sys.stderr)
    except Exception:
        print("MCP call failed: invalid input or result-file operation", file=sys.stderr)
    finally:
        if result_handle:
            try:
                result_handle.close()
            except Exception:
                pass  # An earlier safe failure diagnostic already covers this path.
    return 1


if __name__ == "__main__":
    sys.exit(main())
