"""Offline protocol tests: run on GitHub, never against a real hub."""
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from hubitat_mcp import MCPClient, MCPError, main


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}


class ProtocolTests(unittest.TestCase):
    def client(self, envelope):
        def transport(request, timeout):
            self.request = json.loads(request.data)
            return Response(json.dumps(envelope).encode())
        return MCPClient("https://example.invalid/mcp?access_token=SECRET", transport=transport)

    def test_text_json_is_decoded_and_wire_arguments_are_preserved(self):
        client = self.client({"jsonrpc": "2.0", "id": 1, "result": {
            "content": [{"type": "text", "text": '{"source":"literal source"}'}]}})
        self.assertEqual(client.tool("hub_get_source", {"type": "app", "id": "42"}),
                         {"source": "literal source"})
        self.assertEqual(self.request, {"jsonrpc": "2.0", "id": 1,
                         "method": "tools/call", "params": {"name": "hub_get_source",
                         "arguments": {"type": "app", "id": "42"}}})

    def test_structured_content_is_supported(self):
        client = self.client({"jsonrpc": "2.0", "id": 1, "result": {
            "structuredContent": {"success": True}, "content": []}})
        self.assertEqual(client.tool("example", {}), {"success": True})

    def test_malformed_envelopes_fail_closed_without_payload_disclosure(self):
        fixtures = [[], {"jsonrpc": "2.0", "id": 2, "result": {}},
                    {"jsonrpc": "2.0", "id": True, "result": {}},
                    {"id": 1, "result": {}},
                    {"jsonrpc": "2.0", "id": 1, "result": {}, "error": {"message": "SECRET"}},
                    {"jsonrpc": "2.0", "id": 1, "result": {"content": []}},
                    {"jsonrpc": "2.0", "id": 1, "result": {"isError": "false", "content": []}},
                    {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": 2}]}},
                    {"jsonrpc": "2.0", "id": 1, "error": {"code": -1, "message": "SECRET URL"}},
                    {"jsonrpc": "2.0", "id": 1, "result": {
                        "isError": True, "content": [{"type": "text", "text": "SECRET"}]}}]
        for envelope in fixtures:
            with self.subTest(envelope=envelope):
                with self.assertRaises(MCPError) as caught:
                    self.client(envelope).tool("example", {})
                self.assertNotIn("SECRET", str(caught.exception))
                self.assertNotIn("example.invalid", str(caught.exception))

    def test_transport_failure_does_not_retry_a_write_or_echo_url(self):
        calls = []
        def transport(request, timeout):
            calls.append(request)
            raise URLError("https://secret.invalid?access_token=SECRET")
        client = MCPClient("https://secret.invalid?access_token=SECRET", transport=transport)
        with self.assertRaises(MCPError) as caught:
            client.tool("hub_update_app", {"source": "code"})
        self.assertEqual(len(calls), 1)
        self.assertNotIn("SECRET", str(caught.exception))

    def test_invalid_json_is_sanitized(self):
        def transport(request, timeout):
            return Response(b"SECRET malformed response")
        with self.assertRaises(MCPError) as caught:
            MCPClient("https://example.invalid", transport=transport).tool("example", {})
        self.assertNotIn("SECRET", str(caught.exception))

    def test_url_validation_rejects_credentials_fragments_and_non_http(self):
        for url in ["file:///etc/passwd", "https://user:secret@example.invalid",
                    "https://example.invalid/#secret", "not a url"]:
            with self.assertRaises(MCPError):
                MCPClient(url)

    def test_invalid_rpc_parameters_are_rejected_before_transport(self):
        client = self.client({})
        for params in ([], "bad", False):
            with self.assertRaises(MCPError):
                client.call("tools/call", params)
        self.assertFalse(hasattr(self, "request"))

    def test_real_http_post_and_redirect_refusal_without_replaying_write(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, body))
                if self.path == "/redirect":
                    self.send_response(307)
                    self.send_header("Location", "/secret-destination?access_token=SECRET")
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"jsonrpc": "2.0", "id": body["id"],
                    "result": {"content": [{"type": "text", "text": '{"success":true}'}]}}).encode())

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = "http://127.0.0.1:" + str(server.server_port)
            client = MCPClient(base + "/rpc")
            self.assertEqual(client.tool("hub_update_app", {"appId": "42", "confirm": True}),
                             {"success": True})
            self.assertEqual(client.tool("hub_get_info", {}), {"success": True})
            with self.assertRaises(MCPError) as caught:
                MCPClient(base + "/redirect").tool("hub_update_app", {"confirm": True})
            self.assertNotIn("SECRET", str(caught.exception))
            self.assertEqual([path for path, _ in requests], ["/rpc", "/rpc", "/redirect"])
            self.assertEqual([body["id"] for _, body in requests], [1, 2, 1])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_cli_domain_failure_exits_nonzero_without_echoing_payload(self):
        def transport(request, timeout):
            return Response(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {
                "content": [{"type": "text", "text": '{"success":false,"error":"SECRET"}'}]}}).encode())
        client = MCPClient("https://example.invalid", transport=transport)
        output = io.StringIO()
        with patch("hubitat_mcp.MCPClient", return_value=client), redirect_stdout(output), redirect_stderr(output):
            self.assertEqual(main(["--tool", "hub_install_bundle"]), 1)
        self.assertNotIn("SECRET", output.getvalue())
        self.assertNotIn('"ok": true', output.getvalue())

    def test_cli_checks_existing_result_file_before_sending_a_write(self):
        calls = []
        def transport(request, timeout):
            calls.append(request)
            raise AssertionError("write must never reach transport")
        client = MCPClient("https://example.invalid", transport=transport)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            path.write_text("existing", encoding="utf-8")
            output = io.StringIO()
            with patch("hubitat_mcp.MCPClient", return_value=client), redirect_stdout(output), redirect_stderr(output):
                self.assertEqual(main(["--tool", "hub_install_bundle", "--result-file", str(path)]), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "existing")
            self.assertEqual(calls, [])

    def test_cli_result_file_is_private_and_success_output_omits_data(self):
        client = self.client({"jsonrpc": "2.0", "id": 1, "result": {
            "content": [{"type": "text", "text": '{"success":true,"token":"SECRET"}'}]}})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            output = io.StringIO()
            with patch("hubitat_mcp.MCPClient", return_value=client), redirect_stdout(output), redirect_stderr(output):
                self.assertEqual(main(["--tool", "example", "--result-file", str(path)]), 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"success": True, "token": "SECRET"})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("SECRET", output.getvalue())


if __name__ == "__main__":
    unittest.main()
