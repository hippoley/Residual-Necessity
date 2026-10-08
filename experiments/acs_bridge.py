from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any


EVIDENCE_STATUSES = {"TRUE", "FALSE", "UNKNOWN", "CONFLICTED", "STALE"}


def _artefact(evidence: dict[str, Any]) -> dict[str, str]:
    encoded = json.dumps(
        evidence,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {"artefact": f"sha256:{digest}"}


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
        artefact = _artefact(evidence)

        if status == "TRUE":
            return {
                "decision": "allow",
                "reason": "current evidence supports residual necessity",
                "evidence": artefact,
            }

        if status == "FALSE":
            return {
                "decision": "deny",
                "reason": "current evidence shows the intervention is unnecessary",
                "evidence": artefact,
            }

        if status in {"UNKNOWN", "CONFLICTED", "STALE"}:
            return {
                "decision": "deny",
                "reason": "necessity evidence is unresolved",
                "approval": {
                    "kind": "residual_necessity_review",
                    "evidence_status": status,
                },
                "evidence": artefact,
            }

        return {
            "decision": "deny",
            "reason": "necessity annotation missing or invalid",
            "approval": {"kind": "residual_necessity_review"},
            "evidence": artefact,
        }
