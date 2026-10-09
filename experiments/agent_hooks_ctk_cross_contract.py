#!/usr/bin/env python3
"""Cross-contract validation against the official Agent Hooks Python CTK.

This does not make a §13 host-conformance claim for Residual Necessity.
It verifies two independent facts:

1. the pinned official Agent Hooks CTK/reference host is internally green;
2. the Residual Necessity interceptor behaves correctly on the same pinned
   Agent Hooks SDK/control contract for its declared pre-tool surface.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

from agent_hooks import AgentContextBuilder, InterceptionBlocked, InterceptionEmitter
from agent_hooks.ctk import load_vectors, run_vector
from agent_hooks.ctk.reference import ReferenceHarness


ROOT = Path(__file__).resolve().parents[1]
INTERCEPTOR_PATH = ROOT / "experiments" / "agent_hooks_interceptor.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = load_module("rn_agent_hooks_interceptor_ctk", INTERCEPTOR_PATH)


def authority(predicate_id: str, revision: str = "r1") -> dict[str, Any]:
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": "resource:/ctk/demo",
            "target_revision": revision,
        },
        "basis": "agent_hooks_ctk_cross_contract",
        "evidence_ref": f"ctk-cross:{predicate_id}:{revision}",
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
            "id": "ctk-demo-write",
            "kind": "write",
            "description": "write only while residual violation remains",
            "justified_by": ["residual_violation_exists"],
        },
        "target": {
            "identity": "resource:/ctk/demo",
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


def context(receipt_value: dict[str, Any]):
    builder = AgentContextBuilder(
        agent_id="rn-ctk-cross",
        framework="residual-necessity",
        session_id="cross-contract",
    )
    builder.with_l2(
        extensions={"residual_necessity": {"receipt": receipt_value}}
    )
    return builder.pre_tool_call(
        call_id="call-1",
        name="dangerous_write",
        args={"target": "/ctk/demo"},
    )


async def run_interceptor_cases() -> list[dict[str, Any]]:
    cases = [
        ("authoritative_true", receipt("TRUE"), "allow"),
        ("authoritative_false", receipt("FALSE"), "deny"),
        ("unknown", receipt("UNKNOWN"), "deny"),
    ]

    wrong_revision = receipt("TRUE", revision="r1")
    wrong_revision["target"]["revision"] = "r2"
    cases.append(("wrong_revision_true", wrong_revision, "deny"))

    out: list[dict[str, Any]] = []
    for name, receipt_value, expected in cases:
        emitter = InterceptionEmitter().register(mod.ResidualNecessityInterceptor())
        ctx = context(receipt_value)
        observed = "allow"
        reason = None
        try:
            outcome = await emitter.emit(ctx)
            reason = outcome.record.verdicts[0].reason if outcome.record.verdicts else None
        except InterceptionBlocked as exc:
            observed = "deny"
            reason = exc.result.verdict.reason

        out.append(
            {
                "case": name,
                "expected": expected,
                "observed": observed,
                "reason": reason,
                "pass": observed == expected,
            }
        )
    return out


async def run_ctk(vectors_dir: Path | None) -> dict[str, Any]:
    vectors = load_vectors(vectors_dir) if vectors_dir else load_vectors()
    counts: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []

    for vector in vectors:
        result = await run_vector(ReferenceHarness(), vector)
        counts[result.status] += 1
        if result.status == "fail":
            failures.append(
                {
                    "id": result.id,
                    "title": result.title,
                    "failures": list(result.failures),
                }
            )

    return {
        "vector_count": len(vectors),
        "status_counts": dict(counts),
        "failures": failures,
    }


async def main_async(args: argparse.Namespace) -> int:
    ctk = await run_ctk(args.vectors)
    interceptor = await run_interceptor_cases()

    report = {
        "schema_version": "rn-agent-hooks-cross-contract/0.1",
        "claim_type": "interceptor_compatibility_not_host_conformance",
        "agent_hooks_sdk": args.sdk_version,
        "official_ctk_reference": ctk,
        "residual_necessity_interceptor": {
            "declared_surface": ["pre_tool_call"],
            "cases": interceptor,
        },
        "host_conformance_claimed": False,
    }

    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    if ctk["failures"]:
        return 2
    if any(not case["pass"] for case in interceptor):
        return 3
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sdk-version", required=True)
    parser.add_argument("--vectors", type=Path)
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
