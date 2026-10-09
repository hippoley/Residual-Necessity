from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "probe_firewall.py"

spec = importlib.util.spec_from_file_location("agentabstain_probe_firewall", MODULE)
assert spec and spec.loader
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)


class FakeEnv:
    def __init__(self) -> None:
        self.tool_kinds = {
            "env.lookup": "lookup",
            "env.verify": "verify",
            "env.commit": "commit",
        }
        self._schemas = [
            {
                "name": "env.lookup",
                "kind": "lookup",
                "description": "read",
                "input_schema": {"type": "object", "required": []},
            },
            {
                "name": "env.verify",
                "kind": "verify",
                "description": "verify",
                "input_schema": {"type": "object", "required": ["id"]},
            },
            {
                "name": "env.commit",
                "kind": "commit",
                "description": "mutate",
                "input_schema": {"type": "object", "required": []},
            },
        ]
        self._log = []

    def get_tool_schemas(self):
        return list(self._schemas)

    def call_tool(self, name, **kwargs):
        self._log.append({"tool": name, "params": kwargs})
        return {"ok": True, "name": name}

    def get_execution_log(self):
        return list(self._log)


def test_surface_exposes_only_lookup_and_verify() -> None:
    env = FakeEnv()
    surface = fw.sanitized_safe_surface(env, None)
    assert [item["name"] for item in surface] == ["env.lookup", "env.verify"]
    assert all(item["kind"] in {"lookup", "verify"} for item in surface)


def test_surface_respects_task_visibility() -> None:
    env = FakeEnv()
    surface = fw.sanitized_safe_surface(env, {"env.lookup"})
    assert [item["name"] for item in surface] == ["env.lookup"]


def test_commit_call_is_rejected_even_if_schema_exists() -> None:
    env = FakeEnv()
    schemas = {x["name"]: x for x in env.get_tool_schemas()}
    with pytest.raises(ValueError, match="not read-only"):
        fw.validate_planned_call(
            {"tool": "env.commit", "args": {}},
            live_schemas=schemas,
            live_kinds=env.tool_kinds,
        )


def test_hidden_tool_is_rejected() -> None:
    env = FakeEnv()
    with pytest.raises(ValueError, match="not visible"):
        fw.validate_planned_call(
            {"tool": "env.lookup", "args": {}},
            live_schemas={},
            live_kinds=env.tool_kinds,
        )


def test_executor_runs_readonly_call_and_audits_log() -> None:
    env = FakeEnv()
    observations = fw.execute_case_plan(
        menv=env,
        allowed={"env.lookup", "env.verify"},
        calls=[{"tool": "env.lookup", "args": {}}],
    )
    assert observations[0]["tool_kind"] == "lookup"
    assert observations[0]["success"] is True
    assert env.get_execution_log() == [{"tool": "env.lookup", "params": {}}]


def test_executor_rejects_too_many_calls() -> None:
    env = FakeEnv()
    calls = [{"tool": "env.lookup", "args": {}}] * (fw.MAX_CALLS_PER_CASE + 1)
    with pytest.raises(ValueError, match="exceeds max calls"):
        fw.execute_case_plan(menv=env, allowed=None, calls=calls)
