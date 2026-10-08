from __future__ import annotations

from collections.abc import Callable
from typing import Any


EVIDENCE_STATUSES = {"TRUE", "FALSE", "UNKNOWN", "CONFLICTED", "STALE"}


class NecessityAnnotator:
    def __init__(self, provider: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self.provider = provider

    def dispatch(
        self,
        annotator_name: str,
        annotator_config: dict[str, Any],
        preliminary_policy_input: dict[str, Any],
    ) -> dict[str, Any]:
        _ = annotator_name, annotator_config
        evidence = self.provider(preliminary_policy_input)
        if not isinstance(evidence, dict):
            raise ValueError("necessity provider must return an object")
        status = evidence.get("status")
        if status not in EVIDENCE_STATUSES:
            raise ValueError("necessity provider returned invalid status")
        return evidence


class NecessityPolicy:
    ANNOTATOR_NAME = "residual_necessity"

    def evaluate(self, invocation: dict[str, Any]) -> dict[str, Any]:
        policy_input = invocation.get("input") or {}
        annotations = policy_input.get("annotations") or {}
        evidence = annotations.get(self.ANNOTATOR_NAME) or {}
        status = evidence.get("status")

        if status == "TRUE":
            return {
                "decision": "allow",
                "reason": "current evidence supports residual necessity",
            }

        if status == "FALSE":
            return {
                "decision": "deny",
                "reason": "current evidence shows the intervention is unnecessary",
            }

        if status in {"UNKNOWN", "CONFLICTED", "STALE"}:
            return {
                "decision": "deny",
                "reason": "necessity evidence is unresolved",
                "approval": {
                    "kind": "residual_necessity_review",
                    "evidence_status": status,
                },
            }

        return {
            "decision": "deny",
            "reason": "necessity annotation missing or invalid",
            "approval": {"kind": "residual_necessity_review"},
        }
