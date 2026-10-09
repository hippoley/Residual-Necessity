#!/usr/bin/env python3
"""Score frozen AgentAbstain runtime-evidence baseline predictions."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_PATH = ROOT / "src" / "eval.py"

spec = importlib.util.spec_from_file_location("residual_eval_for_agentabstain", EVAL_PATH)
assert spec and spec.loader
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


STRATEGIES = ("failure_only", "probe_success")


def _load(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"{path} must contain a JSON list of objects")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    predictions = _load(args.predictions)
    labels = _load(args.labels)

    by_case: dict[str, dict[str, Any]] = {}
    for row in predictions:
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("prediction missing case_id")
        if case_id in by_case:
            raise ValueError(f"duplicate prediction case_id: {case_id}")
        by_case[case_id] = row

    expected_by_case: dict[str, dict[str, Any]] = {}
    for row in labels:
        case_id = row.get("case_id")
        task_type = row.get("task_type")
        pair_id = row.get("pair_id")
        if not isinstance(case_id, str) or task_type not in {"act", "abstain"}:
            raise ValueError("invalid label row")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError("label missing pair_id")
        if case_id in expected_by_case:
            raise ValueError(f"duplicate label case_id: {case_id}")
        expected_by_case[case_id] = row

    if set(by_case) != set(expected_by_case):
        missing_predictions = sorted(set(expected_by_case) - set(by_case))
        extra_predictions = sorted(set(by_case) - set(expected_by_case))
        raise ValueError(
            f"prediction/label case mismatch: missing={missing_predictions[:3]} "
            f"extra={extra_predictions[:3]}"
        )

    reports: dict[str, Any] = {}
    for strategy in STRATEGIES:
        records: list[dict[str, Any]] = []
        probed = 0
        for case_id, prediction in by_case.items():
            label = expected_by_case[case_id]
            actual = prediction.get(strategy)
            if actual not in {"ACT", "ABSTAIN", "INVESTIGATE", "ESCALATE"}:
                raise ValueError(f"{strategy}: invalid prediction for {case_id}: {actual!r}")
            probed += prediction.get("probed") is True
            records.append(
                {
                    "pair_id": label["pair_id"],
                    "expected": str(label["task_type"]).upper(),
                    "actual": actual,
                }
            )

        report = metrics.evaluate(records)
        report["probed_variants"] = probed
        report["probe_coverage"] = probed / len(records) if records else 0.0
        reports[strategy] = report

    args.out.write_text(
        json.dumps(reports, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(reports, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
