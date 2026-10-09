#!/usr/bin/env python3
"""Audit SafeAct materialized evidence against the RN constraint boundary."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "experiments" / "safeact_constraint_adapter.py"

spec = importlib.util.spec_from_file_location("safeact_constraint_adapter_audit", ADAPTER_PATH)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def audit(root: Path) -> dict[str, Any]:
    files = sorted(
        path
        for path in root.rglob("*.json")
        if "materialized_evidence" in path.parts
    )
    if not files:
        raise ValueError("no SafeAct materialized evidence files found")

    status_counts: Counter[str] = Counter()
    source_status_counts: Counter[str] = Counter()
    predicate_count = 0
    positive_authority_count = 0
    negative_authority_count = 0
    failures: list[dict[str, str]] = []

    for path in files:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                raise ValueError("document must be an object")
            case_id = str(document.get("case_id") or path.stem)
            projected = adapter.project(
                document,
                target_identity=f"safeact:{case_id}",
                target_revision="pinned-safeact-corpus",
            )

            predicates = projected.get("predicates") or []
            observations = projected.get("observations") or {}
            if not isinstance(predicates, list) or not isinstance(observations, dict):
                raise ValueError("adapter returned malformed projection")

            for predicate in predicates:
                if predicate.get("role") != "constraint":
                    raise AssertionError("SafeAct adapter emitted non-constraint predicate")
                pid = predicate.get("id")
                observation = observations.get(pid)
                if not isinstance(observation, dict):
                    raise AssertionError(f"missing observation for predicate {pid!r}")

                predicate_count += 1
                status = str(observation.get("status") or "")
                status_counts[status] += 1
                details = observation.get("details") or {}
                source_status = str(details.get("safeact_status") or "")
                source_status_counts[source_status] += 1

                if "positive_authority" in observation:
                    positive_authority_count += 1
                if "negative_authority" in observation:
                    negative_authority_count += 1
                    raise AssertionError(
                        "SafeAct corpus projection must never grant negative authority"
                    )

                if source_status.upper() in {"MISSING", "DEFER", "DEFERRED"}:
                    if observation.get("status") == "FALSE":
                        raise AssertionError(
                            "SafeAct missing/defer must not be projected as FALSE"
                        )

            boundary = projected.get("semantic_boundary") or {}
            if boundary.get("provides_residual_necessity") is not False:
                raise AssertionError("SafeAct projection claims residual necessity")
            if boundary.get("missing_does_not_grant_negative_authority") is not True:
                raise AssertionError("SafeAct projection weakened missing-evidence boundary")
        except Exception as exc:
            failures.append(
                {
                    "path": str(path.relative_to(root)),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    report = {
        "materialized_files": len(files),
        "predicate_count": predicate_count,
        "status_counts": dict(sorted(status_counts.items())),
        "source_status_counts": dict(sorted(source_status_counts.items())),
        "positive_authority_count": positive_authority_count,
        "negative_authority_count": negative_authority_count,
        "failures": failures,
        "all_predicates_constraint_only": not failures,
        "provides_residual_necessity": False,
        "corpus_audit_pass": not failures and negative_authority_count == 0,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("safeact_root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.safeact_root)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["corpus_audit_pass"]:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
