from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any

from agent_control_specification import AgentControl, AgentControlBlocked


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "experiments" / "acs_bridge.py"
MANIFEST_PATH = ROOT / "experiments" / "acs_manifest.yaml"

spec = importlib.util.spec_from_file_location("acs_bridge", BRIDGE_PATH)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def make_control(status: str) -> AgentControl:
    def provider(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": status,
            "predicate_id": "residual_violation_exists",
            "source": "acs_e2e",
        }

    return AgentControl.from_path(
        str(MANIFEST_PATH),
        annotator_dispatcher=bridge.NecessityAnnotator(provider),
        policy_dispatcher=bridge.NecessityPolicy(),
    )


async def assert_true_executes() -> None:
    executed = {"value": False}

    async def dangerous_write(args: dict[str, Any]) -> dict[str, Any]:
        executed["value"] = True
        return {"written": True, "target": args["target"]}

    control = make_control("TRUE")
    result = await control.run_tool(
        "dangerous_write",
        {"target": "/tmp/demo"},
        dangerous_write,
        tool_call_id="true-case",
    )
    assert executed["value"] is True
    assert result.value["written"] is True


async def assert_unknown_blocks_before_execution() -> None:
    executed = {"value": False}

    async def dangerous_write(args: dict[str, Any]) -> dict[str, Any]:
        executed["value"] = True
        return {"written": True, "target": args["target"]}

    control = make_control("UNKNOWN")

    try:
        await control.run_tool(
            "dangerous_write",
            {"target": "/tmp/demo"},
            dangerous_write,
            tool_call_id="unknown-case",
        )
    except AgentControlBlocked:
        pass
    else:
        raise AssertionError("UNKNOWN necessity evidence must block tool execution")

    assert executed["value"] is False


async def main() -> None:
    await assert_true_executes()
    await assert_unknown_blocks_before_execution()
    print("ACS_E2E_PASS")


if __name__ == "__main__":
    asyncio.run(main())
