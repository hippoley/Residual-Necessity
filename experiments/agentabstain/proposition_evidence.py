#!/usr/bin/env python3
"""Conservative proposition evidence derived from bound runtime probes.

Tool kind, call success, or schema validity never grant proposition authority
on their own. An explicit provider profile must state which complete result
fields support which propositions. Missing fields, incomplete binding, tool
failure, or absent authority remain UNKNOWN.
"""

from __future__ import annotations

from typing import Any


_MISSING = object()


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if not part:
            return _MISSING
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _evaluate_rule(result: Any, rule: dict[str, Any]) -> dict[str, Any]:
    if rule.get("authority") != "complete_result_field":
        return {
            "status": "UNKNOWN",
            "reason": "rule_lacks_complete_field_authority",
        }

    kind = rule.get("kind")

    if kind == "fields_differ":
        left_path = rule.get("left_path")
        right_path = rule.get("right_path")
        if not isinstance(left_path, str) or not isinstance(right_path, str):
            raise ValueError("fields_differ requires left_path/right_path")
        left = _get_path(result, left_path)
        right = _get_path(result, right_path)
        if left is _MISSING or right is _MISSING:
            return {"status": "UNKNOWN", "reason": "result_field_missing"}
        return {
            "status": "TRUE" if left != right else "FALSE",
            "reason": "complete_fields_compared",
            "evidence_paths": [left_path, right_path],
        }

    if kind == "forbidden_markers_absent":
        path = rule.get("path")
        markers = rule.get("markers")
        if (
            not isinstance(path, str)
            or not isinstance(markers, list)
            or not markers
            or not all(isinstance(x, str) and x for x in markers)
        ):
            raise ValueError("forbidden_markers_absent requires path and markers")
        value = _get_path(result, path)
        if value is _MISSING or not isinstance(value, str):
            return {"status": "UNKNOWN", "reason": "result_field_missing"}
        lowered = value.lower()
        matched = [marker for marker in markers if marker.lower() in lowered]
        return {
            "status": "FALSE" if matched else "TRUE",
            "reason": "explicit_forbidden_marker_present" if matched else "complete_field_has_no_forbidden_marker",
            "evidence_paths": [path],
            "matched_markers": matched,
        }

    raise ValueError(f"unsupported proposition rule kind: {kind!r}")


def classify(
    observation: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if observation.get("probed") is not True:
        return {"status": "UNKNOWN", "reason": "no_probe"}

    if observation.get("binding_complete") is not True:
        return {"status": "UNKNOWN", "reason": "incomplete_argument_binding"}

    if observation.get("success") is not True:
        reason = (
            "verification_tool_unavailable"
            if observation.get("tool_kind") == "verify"
            else "probe_unavailable"
        )
        return {"status": "UNKNOWN", "reason": reason}

    if profile is None:
        reason = (
            "lookup_is_not_proposition_authority"
            if observation.get("tool_kind") == "lookup"
            else "no_explicit_provider_profile"
        )
        return {"status": "UNKNOWN", "reason": reason}

    if profile.get("tool") != observation.get("tool"):
        raise ValueError("provider profile tool does not match observation")
    if profile.get("profile_id") != observation.get("profile_id"):
        raise ValueError("provider profile id does not match bound observation")

    propositions = profile.get("propositions")
    if (
        not isinstance(propositions, list)
        or not propositions
        or not all(isinstance(x, dict) for x in propositions)
    ):
        return {"status": "UNKNOWN", "reason": "profile_has_no_propositions"}

    evaluated: dict[str, dict[str, Any]] = {}
    statuses: list[str] = []
    for rule in propositions:
        pid = rule.get("id")
        if not isinstance(pid, str) or not pid:
            raise ValueError("proposition rule requires non-empty id")
        if pid in evaluated:
            raise ValueError(f"duplicate proposition id: {pid}")
        value = _evaluate_rule(observation.get("result"), rule)
        evaluated[pid] = value
        statuses.append(value["status"])

    if "UNKNOWN" in statuses:
        overall = "UNKNOWN"
        reason = "one_or_more_propositions_unknown"
    elif "FALSE" in statuses:
        overall = "FALSE"
        reason = "one_or_more_required_propositions_false"
    else:
        overall = "TRUE"
        reason = "all_profile_propositions_true"

    decision_scope = profile.get("decision_scope")
    if not isinstance(decision_scope, dict):
        return {
            "status": "UNKNOWN",
            "reason": "profile_has_no_decision_scope",
            "profile_id": profile.get("profile_id"),
            "propositions": evaluated,
        }

    task_coverage = decision_scope.get("task_coverage")
    intervention = decision_scope.get("intervention")
    if task_coverage not in {"partial", "complete"}:
        raise ValueError("decision_scope.task_coverage must be partial or complete")
    if not isinstance(intervention, str) or not intervention:
        raise ValueError("decision_scope.intervention must be a non-empty string")

    return {
        "status": overall,
        "reason": reason,
        "profile_id": profile.get("profile_id"),
        "decision_scope": {
            "intervention": intervention,
            "task_coverage": task_coverage,
        },
        "propositions": evaluated,
    }


def decision_for(evidence: dict[str, Any] | str) -> str:
    if isinstance(evidence, str):
        status = evidence
        coverage = "complete"
    elif isinstance(evidence, dict):
        status = evidence.get("status")
        scope = evidence.get("decision_scope")
        coverage = scope.get("task_coverage") if isinstance(scope, dict) else None
    else:
        raise ValueError("evidence must be a status string or evidence object")

    if status == "FALSE":
        return "ABSTAIN"
    if status == "UNKNOWN":
        return "INVESTIGATE"
    if status == "TRUE":
        # Positive evidence for one sub-intervention is not authority for every
        # other requested mutation in a composite task.
        return "ACT" if coverage == "complete" else "INVESTIGATE"
    raise ValueError(f"unsupported proposition status: {status!r}")


def permits_decision(status: str) -> bool:
    return status in {"TRUE", "FALSE"}
