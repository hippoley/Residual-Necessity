#!/usr/bin/env python3
"""Deterministic reference evaluator for Residual Necessity."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("receipt must be a JSON object")
    return value


def _has_only_keys(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, dict) and set(value).issubset(allowed)


def _authority_matches(
    authority: Any,
    *,
    predicate_id: str,
    target: dict[str, Any],
) -> bool:
    if not _has_only_keys(authority, {"scope", "basis", "evidence_ref"}):
        return False
    scope = authority.get("scope")
    if not _has_only_keys(
        scope,
        {"predicate_id", "target_identity", "target_revision"},
    ):
        return False
    if scope.get("predicate_id") != predicate_id:
        return False
    if scope.get("target_identity") != target.get("identity"):
        return False

    expected_revision = target.get("revision")
    scoped_revision = scope.get("target_revision")
    if expected_revision is not None and scoped_revision != expected_revision:
        return False

    basis = authority.get("basis")
    evidence_ref = authority.get("evidence_ref")
    if not isinstance(basis, str) or not basis:
        return False
    if not isinstance(evidence_ref, str) or not evidence_ref:
        return False
    return True


def evaluate(receipt: dict[str, Any]) -> tuple[str, str]:
    if not _has_only_keys(
        receipt,
        {"schema_version", "intervention", "target", "predicates", "observations"},
    ):
        return "INVESTIGATE", "unknown top-level receipt field"

    if receipt.get("schema_version") != "0.3":
        return "INVESTIGATE", "unsupported or missing schema_version"

    predicates = receipt.get("predicates")
    observations = receipt.get("observations")
    target = receipt.get("target")
    intervention = receipt.get("intervention")

    if (
        not isinstance(predicates, list)
        or not isinstance(observations, dict)
        or not isinstance(target, dict)
        or not isinstance(target.get("identity"), str)
        or not target.get("identity")
        or not isinstance(target.get("revision"), str)
        or not target.get("revision")
        or not isinstance(intervention, dict)
    ):
        return "INVESTIGATE", "missing predicates, observations, target identity/revision, or intervention"

    if not _has_only_keys(intervention, {"id", "kind", "description", "justified_by"}):
        return "INVESTIGATE", "unknown intervention field"
    if not _has_only_keys(target, {"identity", "revision", "environment"}):
        return "INVESTIGATE", "unknown target field"
    if "environment" in target and not isinstance(target.get("environment"), dict):
        return "INVESTIGATE", "target environment must be an object"

    if (
        not isinstance(intervention.get("id"), str)
        or not intervention.get("id")
        or not isinstance(intervention.get("kind"), str)
        or not intervention.get("kind")
        or not isinstance(intervention.get("description"), str)
        or not intervention.get("description")
    ):
        return "INVESTIGATE", "intervention id/kind/description must be non-empty strings"

    justified_by = intervention.get("justified_by")
    if (
        not isinstance(justified_by, list)
        or not justified_by
        or not all(isinstance(x, str) and x for x in justified_by)
    ):
        return "INVESTIGATE", "intervention lacks explicit justification predicates"

    predicate_map: dict[str, dict[str, Any]] = {}
    for predicate in predicates:
        if not _has_only_keys(
            predicate,
            {"id", "required", "kind", "role", "human_only"},
        ):
            return "INVESTIGATE", "malformed or unknown predicate field"
        pid = predicate.get("id")
        if (
            not isinstance(pid, str)
            or not pid
            or not isinstance(predicate.get("required"), bool)
            or predicate.get("kind") not in {"reality", "freshness", "scope", "authority"}
            or predicate.get("role") not in {"necessity", "constraint"}
            or (
                predicate.get("role") == "necessity"
                and predicate.get("kind") != "reality"
            )
            or (
                "human_only" in predicate
                and not isinstance(predicate.get("human_only"), bool)
            )
        ):
            return "INVESTIGATE", "malformed predicate declaration"
        if pid in predicate_map:
            return "INVESTIGATE", f"duplicate predicate id: {pid}"
        predicate_map[pid] = predicate

    unknown_observations = set(observations) - set(predicate_map)
    if unknown_observations:
        return (
            "INVESTIGATE",
            "observations reference undeclared predicates: "
            + ", ".join(sorted(unknown_observations)),
        )

    required = [
        p for p in predicate_map.values()
        if p.get("required") is True
    ]
    if not required:
        return "INVESTIGATE", "no required necessity predicates declared"

    for pid in justified_by:
        predicate = predicate_map.get(pid)
        if not isinstance(predicate, dict):
            return "INVESTIGATE", f"intervention justification references unknown predicate: {pid}"
        if predicate.get("required") is not True:
            return "INVESTIGATE", f"intervention justification predicate is not required: {pid}"
        if predicate.get("kind") != "reality":
            return "INVESTIGATE", f"intervention justification must reference a reality predicate: {pid}"
        if predicate.get("role") != "necessity":
            return "INVESTIGATE", f"intervention justification must reference a necessity predicate: {pid}"

    unresolved: list[str] = []
    false_reality: list[str] = []
    false_freshness_or_scope: list[str] = []

    for predicate in required:
        pid = predicate["id"]

        if predicate.get("human_only") is True:
            return "ESCALATE", f"predicate {pid!r} requires human resolution"

        observation = observations.get(pid)
        if not isinstance(observation, dict):
            unresolved.append(pid)
            continue
        if not _has_only_keys(
            observation,
            {
                "status",
                "source",
                "observed_at",
                "positive_authority",
                "negative_authority",
                "details",
            },
        ):
            unresolved.append(pid)
            continue

        status = observation.get("status")

        if status == "TRUE" and "negative_authority" in observation:
            return "INVESTIGATE", f"contradictory authority on TRUE observation: {pid}"
        if status == "FALSE" and "positive_authority" in observation:
            return "INVESTIGATE", f"contradictory authority on FALSE observation: {pid}"

        if status == "TRUE":
            if not _authority_matches(
                observation.get("positive_authority"),
                predicate_id=pid,
                target=target,
            ):
                unresolved.append(pid)

        elif status == "FALSE":
            if not _authority_matches(
                observation.get("negative_authority"),
                predicate_id=pid,
                target=target,
            ):
                unresolved.append(pid)
                continue

            kind = predicate.get("kind")
            if kind == "reality":
                false_reality.append(pid)
            elif kind in {"freshness", "scope"}:
                false_freshness_or_scope.append(pid)
            elif kind == "authority":
                return "ESCALATE", f"authority predicate false: {pid}"
            else:
                unresolved.append(pid)

        elif status in {"UNKNOWN", "CONFLICTED", "STALE", None}:
            unresolved.append(pid)
        else:
            unresolved.append(pid)

    if unresolved:
        return "INVESTIGATE", "required evidence unresolved: " + ", ".join(sorted(unresolved))

    if false_freshness_or_scope:
        return (
            "INVESTIGATE",
            "required freshness/scope predicates false: "
            + ", ".join(sorted(false_freshness_or_scope)),
        )

    if false_reality:
        return "ABSTAIN", "necessity predicates false: " + ", ".join(sorted(false_reality))

    for pid in justified_by:
        observation = observations.get(pid) or {}
        if observation.get("status") != "TRUE":
            return "ABSTAIN", f"intervention justification is not currently true: {pid}"

    return "ACT", "all required evidence is scoped and intervention justification is currently witnessed"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: gate.py RECEIPT.json", file=sys.stderr)
        return 2

    try:
        receipt = load(argv[1])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVESTIGATE: {exc}")
        return 2

    verdict, reason = evaluate(receipt)
    print(f"{verdict}: {reason}")
    return {"ACT": 0, "ABSTAIN": 3, "INVESTIGATE": 4, "ESCALATE": 5}[verdict]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
