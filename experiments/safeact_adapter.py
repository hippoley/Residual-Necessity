from __future__ import annotations

import hashlib
import json
from typing import Any


def _authority(
    *,
    predicate_id: str,
    target_identity: str,
    target_revision: str,
    case_id: str,
    rule_id: str,
    trace_entry: dict[str, Any],
) -> dict[str, Any]:
    canonical = json.dumps(
        trace_entry,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": target_identity,
            "target_revision": target_revision,
        },
        "basis": "safeact_deterministic_rule_trace",
        "evidence_ref": f"safeact:{case_id}:{rule_id}:sha256:{digest}",
    }


def constraint_fragment(
    materialized: dict[str, Any],
    *,
    target_identity: str,
    target_revision: str,
) -> dict[str, Any]:
    """Project SafeAct deterministic rule traces into RN constraint evidence.

    This adapter intentionally NEVER emits role=necessity. SafeAct establishes
    whether an action is evidence-supported / deferred / blocked under its own
    contract. Residual Necessity still requires an independent current-world
    necessity predicate before ACT or ABSTAIN may be justified.
    """

    if not isinstance(materialized, dict):
        raise ValueError("SafeAct materialized evidence must be an object")

    case_id = materialized.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("SafeAct materialized evidence missing case_id")

    traces = materialized.get("rule_execution_trace")
    if not isinstance(traces, list) or not traces:
        raise ValueError("SafeAct materialized evidence missing rule_execution_trace")

    predicates: list[dict[str, Any]] = []
    observations: dict[str, dict[str, Any]] = {}

    for index, entry in enumerate(traces):
        if not isinstance(entry, dict):
            raise ValueError("SafeAct rule_execution_trace entries must be objects")

        rule_id = entry.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            rule_id = f"rule_{index}"

        predicate_id = f"safeact_support:{case_id}:{rule_id}"
        predicates.append(
            {
                "id": predicate_id,
                "required": True,
                "kind": "reality",
                "role": "constraint",
            }
        )

        status = entry.get("status")
        result = entry.get("predicate_result")

        observation: dict[str, Any] = {
            "source": "safeact",
            "details": {
                "case_id": case_id,
                "rule_id": rule_id,
                "safeact_status": status,
                "safeact_predicate_result": result,
                "safeact_reason": entry.get("reason"),
                "safeact_management_effect": entry.get("management_effect"),
            },
        }

        if status == "SUPPORTED" and result == "TRUE":
            observation["status"] = "TRUE"
            observation["positive_authority"] = _authority(
                predicate_id=predicate_id,
                target_identity=target_identity,
                target_revision=target_revision,
                case_id=case_id,
                rule_id=rule_id,
                trace_entry=entry,
            )
        elif result == "FALSE" or status in {"MISSING", "BLOCKED", "UNSUPPORTED"}:
            observation["status"] = "FALSE"
            observation["negative_authority"] = _authority(
                predicate_id=predicate_id,
                target_identity=target_identity,
                target_revision=target_revision,
                case_id=case_id,
                rule_id=rule_id,
                trace_entry=entry,
            )
        elif result in {"UNKNOWN", None}:
            observation["status"] = "UNKNOWN"
        else:
            observation["status"] = "UNKNOWN"

        observations[predicate_id] = observation

    return {
        "provider": "safeact",
        "provider_case_id": case_id,
        "predicates": predicates,
        "observations": observations,
    }


def merge_constraints(
    receipt: dict[str, Any],
    fragment: dict[str, Any],
) -> dict[str, Any]:
    """Merge only SafeAct constraint predicates into an RN receipt."""

    if not isinstance(receipt, dict):
        raise ValueError("receipt must be an object")

    predicates = fragment.get("predicates")
    observations = fragment.get("observations")
    if not isinstance(predicates, list) or not isinstance(observations, dict):
        raise ValueError("invalid SafeAct constraint fragment")

    for predicate in predicates:
        if predicate.get("role") != "constraint":
            raise ValueError("SafeAct adapter may emit constraint predicates only")

    result = json.loads(json.dumps(receipt))
    existing_ids = {p.get("id") for p in result.get("predicates", []) if isinstance(p, dict)}
    for predicate in predicates:
        pid = predicate.get("id")
        if pid in existing_ids:
            raise ValueError(f"duplicate predicate id while merging SafeAct fragment: {pid}")
        existing_ids.add(pid)
        result.setdefault("predicates", []).append(predicate)

    for pid, observation in observations.items():
        if pid in result.setdefault("observations", {}):
            raise ValueError(f"duplicate observation id while merging SafeAct fragment: {pid}")
        result["observations"][pid] = observation

    return result
