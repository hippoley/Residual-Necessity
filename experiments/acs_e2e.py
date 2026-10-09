from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any

from agent_control_specification import AgentControl, InterventionPoint


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "experiments" / "acs_bridge.py"
MANIFEST_PATH = ROOT / "experiments" / "acs_manifest.yaml"

spec = importlib.util.spec_from_file_location("acs_bridge", BRIDGE_PATH)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def authority(predicate_id: str) -> dict[str, Any]:
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": "resource:/tmp/demo",
            "target_revision": "r1",
        },
        "basis": "acs_e2e_probe",
        "evidence_ref": f"e2e:{predicate_id}:r1",
    }


def receipt(status: str) -> dict[str, Any]:
    observation: dict[str, Any] = {"status": status}
    if status == "TRUE":
        observation["positive_authority"] = authority("residual_violation_exists")
    elif status == "FALSE":
        observation["negative_authority"] = authority("residual_violation_exists")

    return {
        "schema_version": "0.3",
        "intervention": {
            "id": "dangerous-write",
            "kind": "write",
            "description": "write the demo target only when a residual violation remains",
            "justified_by": ["residual_violation_exists"],
        },
        "target": {"identity": "resource:/tmp/demo", "revision": "r1"},
        "predicates": [
            {
                "id": "residual_violation_exists",
                "required": True,
                "kind": "reality",
                "role": "necessity",
            },
        ],
        "observations": {
            "residual_violation_exists": observation,
        },
    }


def make_control(status: str) -> AgentControl:
    def provider(_: dict[str, Any]) -> dict[str, Any]:
        return receipt(status)

    return AgentControl.from_path(
        str(MANIFEST_PATH),
        annotator_dispatcher=bridge.NecessityAnnotator(provider),
        policy_dispatcher=bridge.NecessityPolicy(),
    )


async def evaluate(status: str):
    control = make_control(status)
    return await control.evaluate_intervention_point(
        InterventionPoint.PRE_TOOL_CALL,
        {
            "tool_call": {
                "id": f"{status.lower()}-case",
                "name": "dangerous_write",
                "args": {"target": "/tmp/demo"},
            }
        },
    )


async def assert_true_allows() -> None:
    result = await evaluate("TRUE")
    assert result.verdict.decision.value == "allow"


async def assert_false_denies() -> None:
    result = await evaluate("FALSE")
    assert result.verdict.decision.value == "deny"


async def assert_unknown_is_not_permit() -> None:
    result = await evaluate("UNKNOWN")
    assert result.verdict.decision.value != "allow"


async def main() -> None:
    await assert_true_allows()
    await assert_false_denies()
    await assert_unknown_is_not_permit()
    print("ACS_PRE_TOOL_E2E_PASS")


if __name__ == "__main__":
    asyncio.run(main())
