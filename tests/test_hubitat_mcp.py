"""Offline protocol tests: run on GitHub, never against a real hub."""
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from hubitat_mcp import MCPClient, MCPError


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


if __name__ == "__main__":
    unittest.main()
