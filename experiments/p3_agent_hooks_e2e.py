from __future__ import annotations

import argparse
import asyncio
import importlib.util
from pathlib import Path

from agent_hooks import AgentContextBuilder, InterceptionBlocked, InterceptionEmitter


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load_module(
    "p3_issue169_oracle_for_agent_hooks",
    ROOT / "experiments" / "p3" / "cave_story_issue169_oracle.py",
)
hooks = load_module(
    "residual_agent_hooks_for_p3",
    ROOT / "experiments" / "agent_hooks_interceptor.py",
)


def build_receipt(source: Path, revision: str) -> dict:
    text = source.read_text(encoding="utf-8", errors="replace")
    status, reason = oracle.inspect_source(text)
    return oracle.receipt(status, reason, revision, str(source))


def context(receipt: dict, *, call_id: str):
    builder = AgentContextBuilder(
        agent_id="p3-residual-e2e",
        framework="residual-necessity",
        session_id=f"session-{call_id}",
    )
    builder.with_l2(extensions={"residual_necessity": {"receipt": receipt}})
    return builder.pre_tool_call(
        call_id=call_id,
        name="apply_patch",
        args={"target": receipt["target"]["identity"]},
    )


async def run_case(receipt: dict, expected: str) -> None:
    emitter = InterceptionEmitter().register(hooks.ResidualNecessityInterceptor())
    ctx = context(receipt, call_id=receipt["target"]["revision"][:12])

    direct = hooks.ResidualNecessityInterceptor().intercept(ctx)
    assert direct.evidence is not None
    assert direct.evidence.artefact.startswith("sha256:")

    if expected == "ACT":
        outcome = await emitter.emit(ctx)
        assert outcome.record.proceeds is True
        assert outcome.record.verdict.decision.value == "allow"
        assert outcome.record.verdicts[0].reason == "residual_necessity:act"
        return

    if expected == "ABSTAIN":
        try:
            await emitter.emit(ctx)
        except InterceptionBlocked as exc:
            assert exc.result.verdict.reason == "residual_necessity:abstain"
            return
        raise AssertionError("final fixed revision must be blocked by Agent Hooks")

    raise ValueError(f"unsupported expected verdict: {expected}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expected", choices=["ACT", "ABSTAIN"], required=True)
    args = parser.parse_args()

    receipt = build_receipt(args.source, args.revision)
    await run_case(receipt, args.expected)
    print(
        f"P3_AGENT_HOOKS_E2E_PASS revision={args.revision} expected={args.expected}"
    )


if __name__ == "__main__":
    asyncio.run(main())
