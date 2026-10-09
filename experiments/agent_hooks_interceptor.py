from __future__ import annotations

import hashlib
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent_hooks import AgentContext, Decision, Evidence, Verdict


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "src" / "gate.py"

spec = importlib.util.spec_from_file_location("residual_gate_for_agent_hooks", GATE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


ReceiptProvider = Callable[[AgentContext], dict[str, Any]]


def _digest(receipt: dict[str, Any]) -> str:
    encoded = json.dumps(
        receipt,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def receipt_from_extension(ctx: AgentContext) -> dict[str, Any]:
    extensions = ctx.get("extensions")
    if not isinstance(extensions, dict):
        raise ValueError("missing extensions")
    namespace = extensions.get("residual_necessity")
    if not isinstance(namespace, dict):
        raise ValueError("missing extensions.residual_necessity")
    receipt = namespace.get("receipt")
    if not isinstance(receipt, dict):
        raise ValueError("missing extensions.residual_necessity.receipt")
    return receipt


class ResidualNecessityInterceptor:
    """Agent Hooks interceptor backed by the core Residual Necessity gate.

    Agent Hooks owns the control contract. This adapter only translates
    Residual Necessity's receipt verdict into the standard Agent Hooks Verdict.
    """

    def __init__(self, provider: ReceiptProvider = receipt_from_extension) -> None:
        self.provider = provider

    def intercept(self, ctx: AgentContext) -> Verdict:
        try:
            receipt = self.provider(ctx)
        except Exception as exc:
            return Verdict(
                decision=Decision.DENY,
                reason="residual_necessity:receipt_unavailable",
                message=str(exc),
                approval={},
            )

        verdict, detail = gate.evaluate(receipt)
        evidence = Evidence(artefact=_digest(receipt))

        if verdict == "ACT":
            return Verdict(
                decision=Decision.ALLOW,
                reason="residual_necessity:act",
                message=detail,
                evidence=evidence,
            )

        if verdict == "ABSTAIN":
            return Verdict(
                decision=Decision.DENY,
                reason="residual_necessity:abstain",
                message=detail,
                evidence=evidence,
            )

        if verdict == "ESCALATE":
            return Verdict(
                decision=Decision.DENY,
                reason="residual_necessity:escalate",
                message=detail,
                approval={},
                evidence=evidence,
            )

        return Verdict(
            decision=Decision.DENY,
            reason="residual_necessity:investigate",
            message=detail,
            approval={},
            evidence=evidence,
        )
