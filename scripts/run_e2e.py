#!/usr/bin/env python3
"""Run configured setup/test/cleanup tools only on a leased GitHub test hub."""
import argparse
import os
import re
import sys
import time
from pathlib import Path

from hubitat_mcp import MCPClient, MCPError, decode_json


class ConfigError(Exception):
    pass


class RunError(Exception):
    pass


_MISSING = object()
_ENV = re.compile(r"\$\{ENV:([A-Za-z_][A-Za-z0-9_]*)\}")
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def _repo_file(value, root):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ConfigError("file references must be repository-relative")
    path = (root / value).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ConfigError("file reference is missing or outside the repository")
    return path


def _pointer_tokens(pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ConfigError("invalid JSON pointer")
    if re.search(r"~(?![01])", pointer):
        raise ConfigError("invalid JSON pointer escape")
    return [] if pointer == "" else [item.replace("~1", "/").replace("~0", "~") for item in pointer[1:].split("/")]


def _pointer(value, pointer):
    for token in _pointer_tokens(pointer):
        if isinstance(value, dict):
            value = value.get(token, _MISSING)
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            index = int(token)
            value = value[index] if index < len(value) else _MISSING
        else:
            return _MISSING
        if value is _MISSING:
            return value
    return value


def _result_ref(value, known):
    if not isinstance(value, str) or "#" not in value:
        raise ConfigError("invalid result reference")
    step, pointer = value.split("#", 1)
    if step not in known:
        raise ConfigError("result reference must name an earlier step")
    _pointer_tokens(pointer)


def _static(value, root, env, known):
    if isinstance(value, str):
        # Syntax is validated before substitution; injected values are never interpreted.
        if "${" in _ENV.sub("", value):
            raise ConfigError("invalid environment substitution")
        def substitute(match):
            replacement = env.get(match.group(1))
            if not isinstance(replacement, str) or not replacement:
                raise ConfigError("required environment variable is missing")
            return replacement
        return _ENV.sub(substitute, value)
    if isinstance(value, list):
        return [_static(item, root, env, known) for item in value]
    if isinstance(value, dict):
        if "$file" in value:
            if set(value) != {"$file"}:
                raise ConfigError("invalid file reference")
            try:
                return _repo_file(value["$file"], root).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                raise ConfigError("file reference could not be read") from None
        if "$result" in value:
            if set(value) != {"$result"}:
                raise ConfigError("invalid result reference")
            _result_ref(value["$result"], known)
            return value
        if any(key.startswith("$") for key in value):
            raise ConfigError("unknown substitution")
        return {key: _static(item, root, env, known) for key, item in value.items()}
    return value


def load_config(path, root, env):
    """Resolve every file/env reference and validate all phases before network calls."""
    root = Path(root).resolve()
    try:
        path = Path(path).resolve()
        if not path.is_relative_to(root):
            raise ConfigError("configuration must be inside the repository")
        data = decode_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise ConfigError("configuration could not be read as JSON") from None
    if (not isinstance(data, dict) or set(data) - {"schema_version", "setup", "test", "cleanup"}
            or type(data.get("schema_version")) is not int or data["schema_version"] != 1):
        raise ConfigError("invalid configuration envelope")
    if not isinstance(data.get("test"), list) or not data["test"]:
        raise ConfigError("at least one test step is required")
    known = set()
    used_endpoints = {"watchdog"}
    for phase in ("setup", "test", "cleanup"):
        steps = data.setdefault(phase, [])
        if not isinstance(steps, list):
            raise ConfigError("phases must be arrays")
        for position, step in enumerate(steps):
            if (not isinstance(step, dict) or set(step) - {"id", "endpoint", "tool", "arguments", "assertions"}
                    or not isinstance(step.get("id"), str) or not _ID.fullmatch(step["id"])
                    or step["id"] in known or not isinstance(step.get("tool"), str)
                    or not re.fullmatch(r"[A-Za-z0-9_.-]+", step["tool"])
                    or not isinstance(step.get("arguments"), dict)):
                raise ConfigError("invalid step definition")
            endpoint = step.setdefault("endpoint", "watchdog")
            if not isinstance(endpoint, str) or endpoint not in {"watchdog", "target"}:
                raise ConfigError("invalid endpoint selector")
            used_endpoints.add(endpoint)
            step["arguments"] = _static(step["arguments"], root, env, known)
            assertions = step.get("assertions")
            if not isinstance(assertions, list) or not assertions:
                raise ConfigError("every step needs explicit assertions")
            for index, assertion in enumerate(assertions):
                if not isinstance(assertion, dict) or set(assertion) != {"path", "op", "value"}:
                    raise ConfigError("invalid assertion definition")
                _pointer_tokens(assertion["path"])
                if not isinstance(assertion["op"], str) or assertion["op"] not in {"equals", "contains", "exists", "type"}:
                    raise ConfigError("invalid assertion operator")
                assertion["value"] = _static(assertion["value"], root, env, known)
                if assertion["op"] == "exists" and type(assertion["value"]) is not bool:
                    raise ConfigError("exists assertions require a boolean")
                if assertion["op"] == "type" and (not isinstance(assertion["value"], str) or assertion["value"] not in {"object", "array", "string", "number", "boolean", "null"}):
                    raise ConfigError("invalid assertion type")
            known.add(step["id"])
    for endpoint in used_endpoints:
        variable = "WATCHDOG_URL" if endpoint == "watchdog" else "TARGET_MCP_URL"
        try:
            MCPClient(env.get(variable, ""))  # Validate only; never sends a request.
        except MCPError:
            raise ConfigError("required endpoint is missing or invalid") from None
    return data


def _resolve(value, results):
    if isinstance(value, dict):
        if "$result" in value:
            step, pointer = value["$result"].split("#", 1)
            result = _pointer(results.get(step, _MISSING), pointer)
            if result is _MISSING:
                raise RunError("required earlier result is unavailable")
            return result
        return {key: _resolve(item, results) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, results) for item in value]
    return value


def _equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def _assert(result, assertion, results):
    actual = _pointer(result, assertion["path"])
    expected = _resolve(assertion["value"], results)
    op = assertion["op"]
    passed = False
    if op == "exists":
        passed = (actual is not _MISSING) is expected
    elif actual is not _MISSING:
        if op == "equals":
            passed = _equal(actual, expected)
        elif op == "contains":
            passed = ((isinstance(actual, str) and isinstance(expected, str) and expected in actual)
                      or (isinstance(actual, list) and any(_equal(item, expected) for item in actual)))
        elif op == "type":
            types = {dict: "object", list: "array", str: "string", int: "number",
                     float: "number", bool: "boolean", type(None): "null"}
            passed = types.get(type(actual)) == expected
    if not passed:
        raise RunError("assertion failed")


class E2ERunner:
    def __init__(self, config, clients, env, now_ms=None, emit=print):
        self.config = config
        self.clients = clients
        self.env = env
        self.now_ms = now_ms or (lambda: int(time.time() * 1000))
        self.emit = emit
        self.results = {}

    def _runtime_guard(self):
        if (self.env.get("GITHUB_ACTIONS") != "true" or self.env.get("HUBITAT_TEST_HUB") != "true"
                or not re.fullmatch(r"[0-9]+", self.env.get("GITHUB_RUN_ID", ""))):
            raise RunError("GitHub Actions and the explicit test-hub flag are required")

    def _lease_guard(self):
        self._runtime_guard()
        try:
            data = self.clients["watchdog"].tool("hub_manage_variables", {
                "action": "get", "name": "_TEST_HUB_LEASED_BY"})
            if not isinstance(data, dict) or data.get("success") is False or not isinstance(data.get("value"), str):
                raise ValueError()
            lease = decode_json(data["value"])
            if (not isinstance(lease, dict) or lease.get("by") != "ci-run-" + self.env["GITHUB_RUN_ID"]
                    or type(lease.get("until")) is not int or lease["until"] <= self.now_ms()):
                raise ValueError()
        except Exception:
            raise RunError("live watchdog lease could not be verified for this run") from None

    def _step(self, phase, position, step):
        # Resolve first so an unavailable snapshot never causes a cleanup write.
        arguments = _resolve(step["arguments"], self.results)
        self._lease_guard()
        result = self.clients[step["endpoint"]].tool(step["tool"], arguments)
        for assertion in step["assertions"]:
            _assert(result, assertion, self.results)
        # Failed assertions must never publish an incomplete snapshot to cleanup.
        self.results[step["id"]] = result
        self.emit(f"{phase} step {position}: passed")

    def run(self):
        self._runtime_guard()
        self._lease_guard()  # Refuse to begin, including cleanup, if not our hub.
        failures = []
        try:
            for phase in ("setup", "test"):
                for position, step in enumerate(self.config[phase], 1):
                    try:
                        self._step(phase, position, step)
                    except Exception:
                        failures.append(f"{phase} step {position} failed")
                        raise RunError("phase failed") from None
        except RunError:
            pass
        finally:
            for position, step in enumerate(self.config["cleanup"], 1):
                try:
                    self._step("cleanup", position, step)
                except Exception:
                    failure = f"cleanup step {position} failed"
                    failures.append(failure)
                    self.emit(failure)
        if failures:
            raise RunError("; ".join(failures))
        self.emit("E2E passed; all configured cleanup assertions passed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true", help="validate the entire scenario without network calls")
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).resolve().parents[1]
        config = load_config(args.config, root, os.environ)
        if args.validate_only:
            print("E2E configuration valid; no network calls made")
            return 0
        endpoints = {step["endpoint"] for phase in ("setup", "test", "cleanup") for step in config[phase]}
        clients = {"watchdog": MCPClient(os.environ["WATCHDOG_URL"])}
        if "target" in endpoints:
            clients["target"] = MCPClient(os.environ["TARGET_MCP_URL"])
        E2ERunner(config, clients, os.environ).run()
        return 0
    except (ConfigError, RunError, MCPError) as error:
        print("E2E failed: " + str(error), file=sys.stderr)
    except Exception:
        print("E2E failed: invalid configuration or internal operation", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
