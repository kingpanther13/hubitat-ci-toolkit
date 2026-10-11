"""Exercise the real runner using a deterministic external-tool boundary."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from hubitat_mcp import MCPError
from run_e2e import ConfigError, E2ERunner, RunError, load_config


ENV = {"GITHUB_ACTIONS": "true", "HUBITAT_TEST_HUB": "true", "GITHUB_RUN_ID": "123",
       "WATCHDOG_URL": "https://watchdog.invalid?access_token=SECRET"}
LEASE = {"by": "ci-run-123", "until": 1800001}


class FakeHub:
    def __init__(self):
        self.lease = dict(LEASE)
        self.calls = []
        self.fail_tools = set()
        self.responses = {}
        self.lose_lease_on_write = False

    def tool(self, tool, args):
        self.calls.append((tool, args))
        if tool == "hub_manage_variables":
            return {"value": json.dumps(self.lease)}
        if tool in self.fail_tools:
            raise MCPError("transport failed")
        if tool == "write" and self.lose_lease_on_write:
            self.lease = {"by": "other", "until": 1800001}
        if tool in self.responses:
            return self.responses[tool]
        if tool == "read":
            return {"source": "original", "hasMore": False}
        return {"success": True}


def config():
    return {"schema_version": 1, "setup": [
        {"id": "snapshot", "tool": "read", "arguments": {}, "assertions": [
            {"path": "/hasMore", "op": "equals", "value": False}]}],
        "test": [{"id": "deploy", "tool": "write", "arguments": {}, "assertions": [
            {"path": "/success", "op": "equals", "value": True}]}],
        "cleanup": [{"id": "restore", "tool": "restore", "arguments": {
            "source": {"$result": "snapshot#/source"}}, "assertions": [
            {"path": "/success", "op": "equals", "value": True}]}]}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.hub = FakeHub()

    def tearDown(self):
        self.temp.cleanup()

    def load(self, data, env=None):
        path = self.root / "scenario.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return load_config(path, self.root, ENV if env is None else env)

    def runner(self, data=None, env=None):
        return E2ERunner(self.load(config() if data is None else data, env),
                         {"watchdog": self.hub}, ENV if env is None else env,
                         now_ms=lambda: 1, emit=lambda message: None)

    def test_success_verifies_lease_and_restores_snapshot(self):
        self.runner().run()
        calls = self.hub.calls
        self.assertEqual([name for name, _ in calls if name != "hub_manage_variables"],
                         ["read", "write", "restore"])
        self.assertEqual(calls[-1], ("restore", {"source": "original"}))
        for index, (name, _) in enumerate(calls):
            if name != "hub_manage_variables":
                self.assertEqual(calls[index - 1], ("hub_manage_variables", {
                    "action": "get", "name": "_TEST_HUB_LEASED_BY"}))

    def test_test_failure_still_cleans_up_and_propagates_failure(self):
        self.hub.fail_tools.add("write")
        with self.assertRaises(RunError) as caught:
            self.runner().run()
        self.assertEqual(self.hub.calls[-1], ("restore", {"source": "original"}))
        self.assertIn("test", str(caught.exception))

    def test_cleanup_failure_fails_an_otherwise_successful_run(self):
        self.hub.fail_tools.add("restore")
        with self.assertRaises(RunError) as caught:
            self.runner().run()
        self.assertIn("cleanup", str(caught.exception))

    def test_cleanup_continues_after_an_individual_cleanup_failure(self):
        data = config()
        data["cleanup"].append({"id": "other", "tool": "other", "arguments": {},
                                "assertions": [{"path": "/success", "op": "equals", "value": True}]})
        self.hub.fail_tools.add("restore")
        with self.assertRaises(RunError):
            self.runner(data).run()
        self.assertEqual(self.hub.calls[-1], ("other", {}))

    def test_untrusted_runtime_is_rejected_before_network(self):
        for field, value in [("GITHUB_ACTIONS", "false"), ("HUBITAT_TEST_HUB", "false"),
                             ("GITHUB_RUN_ID", "not-a-run")]:
            env = dict(ENV, **{field: value})
            with self.assertRaises(RunError):
                self.runner(env=env).run()
        self.assertEqual(self.hub.calls, [])

    def test_wrong_expired_and_malformed_leases_prevent_actions(self):
        for lease in [{"by": "other", "until": 999}, {"by": "ci-run-123", "until": 1},
                      {"by": "ci-run-123", "until": True}, {}, [], "SECRET"]:
            self.hub.lease = lease
            self.hub.calls = []
            with self.assertRaises(RunError) as caught:
                self.runner().run()
            self.assertTrue(all(name == "hub_manage_variables" for name, _ in self.hub.calls))
            self.assertNotIn("SECRET", str(caught.exception))

    def test_assertion_failure_does_not_capture_a_partial_snapshot(self):
        data = config()
        data["setup"][0]["assertions"][0]["value"] = True
        with self.assertRaises(RunError):
            self.runner(data).run()
        self.assertFalse(any(name in {"write", "restore"} for name, _ in self.hub.calls))

    def test_lost_lease_blocks_cleanup_writes_and_fails_the_run(self):
        self.hub.lose_lease_on_write = True
        with self.assertRaises(RunError) as caught:
            self.runner().run()
        self.assertIn("cleanup", str(caught.exception))
        self.assertFalse(any(name == "restore" for name, _ in self.hub.calls))

    def test_domain_failure_and_wrong_json_type_fail_assertions_and_still_restore(self):
        for result in ({"success": False, "error": "SECRET"}, {"success": 1}, {}):
            self.hub.calls = []
            self.hub.responses["write"] = result
            with self.assertRaises(RunError) as caught:
                self.runner().run()
            self.assertIn("test", str(caught.exception))
            self.assertNotIn("SECRET", str(caught.exception))
            self.assertEqual(self.hub.calls[-1], ("restore", {"source": "original"}))

    def test_missing_environment_or_file_in_cleanup_fails_before_network(self):
        for replacement in ["${ENV:MISSING}", {"$file": "missing.groovy"}]:
            data = config()
            data["cleanup"][0]["arguments"]["source"] = replacement
            with self.assertRaises(ConfigError):
                self.runner(data)
        self.assertEqual(self.hub.calls, [])

    def test_repository_path_escape_and_symlink_are_rejected(self):
        outside = self.root.parent / (self.root.name + "-outside")
        outside.write_text("secret", encoding="utf-8")
        try:
            (self.root / "link").symlink_to(outside)
            for relative in ["../" + outside.name, str(outside), "link"]:
                data = config()
                data["test"][0]["arguments"] = {"source": {"$file": relative}}
                with self.assertRaises(ConfigError):
                    self.load(data)
        finally:
            outside.unlink()

    def test_file_environment_and_result_substitutions_preserve_literal_source(self):
        (self.root / "app.groovy").write_text("literal ${ENV:MISSING}\n", encoding="utf-8")
        data = config()
        data["test"][0]["arguments"] = {"source": {"$file": "app.groovy"},
                                         "appId": "${ENV:APP_CODE_ID}"}
        loaded = self.load(data, dict(ENV, APP_CODE_ID="42"))
        self.assertEqual(loaded["test"][0]["arguments"], {
            "source": "literal ${ENV:MISSING}\n", "appId": "42"})

    def test_invalid_config_and_forward_references_fail_before_actions(self):
        invalid = []
        data = config(); data["test"][0]["assertions"] = []; invalid.append(data)
        data = config(); data["cleanup"][0]["arguments"] = {"x": {"$result": "missing#/x"}}; invalid.append(data)
        data = config(); data["test"][0]["endpoint"] = "target"; invalid.append(data)
        data = config(); data["test"][0]["arguments"] = {"x": "${BAD}"}; invalid.append(data)
        data = config(); data["test"][0]["assertions"][0]["op"] = "eval"; invalid.append(data)
        data = config(); data["schema_version"] = True; invalid.append(data)
        for data in invalid:
            with self.subTest(data=data):
                with self.assertRaises(ConfigError):
                    self.load(data)
        self.assertEqual(self.hub.calls, [])

    def test_checked_in_scenarios_resolve_without_network(self):
        root = Path(__file__).resolve().parents[1]
        for scenario in ("lease-smoke", "deploy-readback"):
            loaded = load_config(root / "e2e" / (scenario + ".json"), root,
                                 dict(ENV, APP_CODE_ID="42"))
            self.assertTrue(loaded["test"])
        self.assertEqual(self.hub.calls, [])


if __name__ == "__main__":
    unittest.main()
