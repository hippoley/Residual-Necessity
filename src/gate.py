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


def _negative_authority_matches(
    authority: Any,
    *,
    predicate_id: str,
    target: dict[str, Any],
) -> bool:
    if not isinstance(authority, dict):
        return False
    scope = authority.get("scope")
    if not isinstance(scope, dict):
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
    predicates = receipt.get("predicates")
    observations = receipt.get("observations")
    target = receipt.get("target")

    if (
        not isinstance(predicates, list)
        or not isinstance(observations, dict)
        or not isinstance(target, dict)
        or not isinstance(target.get("identity"), str)
        or not target.get("identity")
    ):
        return "INVESTIGATE", "missing predicates, observations, or target identity"

    required = [p for p in predicates if isinstance(p, dict) and p.get("required") is True]
    if not required:
        return "INVESTIGATE", "no required necessity predicates declared"

    unresolved: list[str] = []
    false: list[str] = []

    for predicate in required:
        pid = predicate.get("id")
        if not isinstance(pid, str) or not pid:
            return "INVESTIGATE", "required predicate without stable id"

        if predicate.get("human_only") is True:
            return "ESCALATE", f"predicate {pid!r} requires human resolution"

        observation = observations.get(pid)
        if not isinstance(observation, dict):
            unresolved.append(pid)
            continue

        status = observation.get("status")
        if status == "FALSE":
            if _negative_authority_matches(
                observation.get("negative_authority"),
                predicate_id=pid,
                target=target,
            ):
                false.append(pid)
            else:
                unresolved.append(pid)
        elif status in {"UNKNOWN", "CONFLICTED", "STALE", None}:
            unresolved.append(pid)
        elif status != "TRUE":
            unresolved.append(pid)

    if unresolved:
        return "INVESTIGATE", "required evidence unresolved: " + ", ".join(sorted(unresolved))

    if false:
        return "ABSTAIN", "necessity predicates false: " + ", ".join(sorted(false))

    return "ACT", "all required necessity predicates are currently witnessed"


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
