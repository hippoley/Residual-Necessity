#!/usr/bin/env python3
"""Score frozen AgentAbstain predictions without prematurely revealing holdout.

Historical baselines are scored on the full frozen dataset because they were
preregistered before the development/holdout split. The proposition-specific
candidate is scored on development only until a separate frozen-method event
explicitly authorizes holdout reveal.
"""

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


FULL_DATASET_STRATEGIES = ("failure_only", "probe_success")
DEVELOPMENT_ONLY_STRATEGIES = ("proposition_specific",)


def _load(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"{path} must contain a JSON list of objects")
    return value


def _load_split(path: Path) -> dict[str, str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("split manifest must be an object")
    assignments = value.get("assignments")
    if not isinstance(assignments, dict) or not assignments:
        raise ValueError("split manifest missing assignments")
    for pair_id, split in assignments.items():
        if not isinstance(pair_id, str) or split not in {"development", "holdout"}:
            raise ValueError("invalid split assignment")
    return assignments


def _score(
    *,
    strategy: str,
    predictions: dict[str, dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    assignments: dict[str, str],
    partition: str,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    probed = 0

    for case_id, prediction in predictions.items():
        label = labels[case_id]
        pair_id = label["pair_id"]
        split = assignments.get(pair_id)
        if split not in {"development", "holdout"}:
            raise ValueError(f"pair missing from frozen split: {pair_id}")

        if partition != "all" and split != partition:
            continue

        actual = prediction.get(strategy)
        if actual not in {"ACT", "ABSTAIN", "INVESTIGATE", "ESCALATE"}:
            raise ValueError(f"{strategy}: invalid prediction for {case_id}: {actual!r}")
        probed += prediction.get("probed") is True
        records.append(
            {
                "pair_id": pair_id,
                "expected": str(label["task_type"]).upper(),
                "actual": actual,
            }
        )

    report = metrics.evaluate(records)
    report["partition"] = partition
    report["probed_variants"] = probed
    report["probe_coverage"] = probed / len(records) if records else 0.0
    report["holdout_scored"] = partition == "holdout" or partition == "all"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    prediction_rows = _load(args.predictions)
    label_rows = _load(args.labels)
    assignments = _load_split(args.split_manifest)

    predictions: dict[str, dict[str, Any]] = {}
    for row in prediction_rows:
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("prediction missing case_id")
        if case_id in predictions:
            raise ValueError(f"duplicate prediction case_id: {case_id}")
        predictions[case_id] = row

    labels: dict[str, dict[str, Any]] = {}
    for row in label_rows:
        case_id = row.get("case_id")
        task_type = row.get("task_type")
        pair_id = row.get("pair_id")
        if not isinstance(case_id, str) or task_type not in {"act", "abstain"}:
            raise ValueError("invalid label row")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError("label missing pair_id")
        if case_id in labels:
            raise ValueError(f"duplicate label case_id: {case_id}")
        labels[case_id] = row

    if set(predictions) != set(labels):
        missing_predictions = sorted(set(labels) - set(predictions))
        extra_predictions = sorted(set(predictions) - set(labels))
        raise ValueError(
            f"prediction/label case mismatch: missing={missing_predictions[:3]} "
            f"extra={extra_predictions[:3]}"
        )

    reports: dict[str, Any] = {}
    for strategy in FULL_DATASET_STRATEGIES:
        reports[strategy] = _score(
            strategy=strategy,
            predictions=predictions,
            labels=labels,
            assignments=assignments,
            partition="all",
        )

    for strategy in DEVELOPMENT_ONLY_STRATEGIES:
        reports[strategy] = _score(
            strategy=strategy,
            predictions=predictions,
            labels=labels,
            assignments=assignments,
            partition="development",
        )
        if reports[strategy]["holdout_scored"] is not False:
            raise AssertionError("development candidate must not score holdout")

    args.out.write_text(
        json.dumps(reports, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(reports, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
