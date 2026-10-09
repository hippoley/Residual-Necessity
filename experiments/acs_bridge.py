from __future__ import annotations

import hashlib
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "src" / "gate.py"

spec = importlib.util.spec_from_file_location("residual_gate_for_acs", GATE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


GATE_VERDICTS = {"ACT", "ABSTAIN", "INVESTIGATE", "ESCALATE"}


def _digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class NecessityAnnotator:
    """Evaluate one full Residual Necessity receipt before ACS policy dispatch."""

    def __init__(self, provider: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self.provider = provider

    def dispatch(
        self,
        annotator_name: str,
        annotator_config: dict[str, Any],
        preliminary_policy_input: dict[str, Any],
    ) -> dict[str, Any]:
        _ = annotator_name, annotator_config
        receipt = self.provider(preliminary_policy_input)
        if not isinstance(receipt, dict):
            raise ValueError("necessity provider must return a receipt object")

        verdict, reason = gate.evaluate(receipt)
        if verdict not in GATE_VERDICTS:
            raise ValueError("gate returned invalid verdict")

        return {
            "verdict": verdict,
            "reason": reason,
            "receipt_digest": _digest(receipt),
            "schema_version": receipt.get("schema_version"),
        }


class NecessityPolicy:
    ANNOTATOR_NAME = "residual_necessity"

    def evaluate(self, invocation: dict[str, Any]) -> dict[str, Any]:
        policy_input = invocation.get("input") or {}
        annotations = policy_input.get("annotations") or {}
        annotation = annotations.get(self.ANNOTATOR_NAME) or {}

        verdict = annotation.get("verdict")
        digest = annotation.get("receipt_digest")
        evidence = {"artefact": digest} if isinstance(digest, str) and digest else {}

        if verdict == "ACT":
            return {
                "decision": "allow",
                "reason": annotation.get("reason") or "residual necessity witnessed",
                "evidence": evidence,
            }

        if verdict == "ABSTAIN":
            return {
                "decision": "deny",
                "reason": annotation.get("reason") or "intervention unnecessary",
                "evidence": evidence,
            }

        if verdict in {"INVESTIGATE", "ESCALATE"}:
            return {
                "decision": "escalate",
                "reason": annotation.get("reason") or "necessity unresolved",
                "evidence": evidence,
            }

        return {
            "decision": "deny",
            "reason": "necessity annotation missing or invalid",
            "evidence": evidence,
        }
