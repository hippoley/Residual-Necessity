from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any

from agent_hooks import (
    AgentContextBuilder,
    InterceptionBlocked,
    InterceptionEmitter,
)


ROOT = Path(__file__).resolve().parents[1]
INTERCEPTOR_PATH = ROOT / "experiments" / "agent_hooks_interceptor.py"

spec = importlib.util.spec_from_file_location("agent_hooks_interceptor", INTERCEPTOR_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def authority(predicate_id: str, revision: str = "r1") -> dict[str, Any]:
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": "resource:/tmp/demo",
            "target_revision": revision,
        },
        "basis": "agent_hooks_e2e",
        "evidence_ref": f"e2e:{predicate_id}:{revision}",
    }


def receipt(status: str, *, revision: str = "r1") -> dict[str, Any]:
    observation: dict[str, Any] = {"status": status}
    if status == "TRUE":
        observation["positive_authority"] = authority(
            "residual_violation_exists", revision
        )
    elif status == "FALSE":
        observation["negative_authority"] = authority(
            "residual_violation_exists", revision
        )

    return {
        "schema_version": "0.3",
        "intervention": {
            "id": "dangerous-write",
            "kind": "write",
            "description": "write only while a residual violation remains",
            "justified_by": ["residual_violation_exists"],
        },
        "target": {
            "identity": "resource:/tmp/demo",
            "revision": revision,
        },
        "predicates": [
            {
                "id": "residual_violation_exists",
                "required": True,
                "kind": "reality",
                "role": "necessity",
            }
        ],
        "observations": {
            "residual_violation_exists": observation,
        },
    }


def context(status: str, *, receipt_revision: str = "r1"):
    builder = AgentContextBuilder(
        agent_id="residual-e2e",
        framework="residual-test",
        session_id=f"session-{status.lower()}",
    )
    builder.with_l2(
        extensions={
            "residual_necessity": {
                "receipt": receipt(status, revision=receipt_revision)
            }
        }
    )
    return builder.pre_tool_call(
        call_id=f"call-{status.lower()}",
        name="dangerous_write",
        args={"target": "/tmp/demo"},
    )


async def assert_true_allows() -> None:
    emitter = InterceptionEmitter().register(mod.ResidualNecessityInterceptor())
    ctx = context("TRUE")
    direct = mod.ResidualNecessityInterceptor().intercept(ctx)
    assert direct.evidence is not None
    assert direct.evidence.artefact.startswith("sha256:")

    outcome = await emitter.emit(ctx)
    assert outcome.record.verdict.decision.value == "allow"
    assert outcome.record.proceeds is True
    assert outcome.record.verdicts
    assert outcome.record.verdicts[0].reason == "residual_necessity:act"


async def assert_false_blocks() -> None:
    emitter = InterceptionEmitter().register(mod.ResidualNecessityInterceptor())
    try:
        await emitter.emit(context("FALSE"))
    except InterceptionBlocked as exc:
        assert exc.result.verdict.reason == "residual_necessity:abstain"
    else:
        raise AssertionError("authoritative FALSE must block the tool call")


async def assert_unknown_fails_closed() -> None:
    emitter = InterceptionEmitter().register(mod.ResidualNecessityInterceptor())
    try:
        await emitter.emit(context("UNKNOWN"))
    except InterceptionBlocked as exc:
        assert exc.result.verdict.reason == "residual_necessity:investigate"
        assert exc.result.verdict.approval is not None
    else:
        raise AssertionError("UNKNOWN necessity must not silently permit execution")


async def assert_wrong_revision_fails_closed() -> None:
    bad = receipt("TRUE", revision="r1")
    bad["target"]["revision"] = "r2"

    builder = AgentContextBuilder(
        agent_id="residual-e2e",
        framework="residual-test",
        session_id="session-wrong-revision",
    )
    builder.with_l2(
        extensions={"residual_necessity": {"receipt": bad}}
    )
    ctx = builder.pre_tool_call(
        call_id="call-wrong-revision",
        name="dangerous_write",
        args={"target": "/tmp/demo"},
    )

    emitter = InterceptionEmitter().register(mod.ResidualNecessityInterceptor())
    try:
        await emitter.emit(ctx)
    except InterceptionBlocked as exc:
        assert exc.result.verdict.reason == "residual_necessity:investigate"
    else:
        raise AssertionError("wrong-revision evidence must fail closed")


async def main() -> None:
    await assert_true_allows()
    await assert_false_blocks()
    await assert_unknown_fails_closed()
    await assert_wrong_revision_fails_closed()
    print("AGENT_HOOKS_E2E_PASS")


if __name__ == "__main__":
    asyncio.run(main())
