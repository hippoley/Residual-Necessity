#!/usr/bin/env python3
"""Score one frozen candidate only on the AgentAbstain development partition.

This script deliberately accepts the development label file emitted by the
Reality Gate, not the full benchmark labels. Holdout outcomes therefore cannot
enter candidate-development metrics.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.agentabstain.freeze_pair_split import assign as split_assignment

RUNTIME_CATEGORIES = {
    "critical_tool_failure",
    "conflicting_evidence",
    "emergent_risk_discovery",
}
EVAL_PATH = ROOT / "src" / "eval.py"
BOOTSTRAP_PATH = ROOT / "src" / "bootstrap.py"

spec = importlib.util.spec_from_file_location("residual_eval_dev_candidate", EVAL_PATH)
assert spec and spec.loader
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)

bootstrap_spec = importlib.util.spec_from_file_location(
    "residual_bootstrap_dev_candidate",
    BOOTSTRAP_PATH,
)
assert bootstrap_spec and bootstrap_spec.loader
bootstrap = importlib.util.module_from_spec(bootstrap_spec)
bootstrap_spec.loader.exec_module(bootstrap)


def _load(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"{path} must contain a JSON list of objects")
    return value


def score(
    predictions: list[dict[str, Any]],
    development_labels: list[dict[str, Any]],
    *,
    strategy: str = "proposition_specific",
) -> dict[str, Any]:
    prediction_by_case: dict[str, dict[str, Any]] = {}
    for row in predictions:
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("prediction missing case_id")
        if case_id in prediction_by_case:
            raise ValueError(f"duplicate prediction case_id: {case_id}")
        prediction_by_case[case_id] = row

    records: list[dict[str, Any]] = []
    profile_counts: dict[str, int] = {}
    complete_binding = 0
    profiled_variants = 0

    for label in development_labels:
        case_id = label.get("case_id")
        pair_id = label.get("pair_id")
        task_type = label.get("task_type")
        category = label.get("category")
        if (
            not isinstance(case_id, str)
            or not isinstance(pair_id, str)
            or task_type not in {"act", "abstain"}
            or category not in RUNTIME_CATEGORIES
        ):
            raise ValueError("invalid development label row")
        if split_assignment(pair_id) != "development":
            raise ValueError(
                f"non-development pair leaked into candidate scoring: {pair_id}"
            )

        prediction = prediction_by_case.get(case_id)
        if prediction is None:
            raise ValueError(f"missing prediction for development case: {case_id}")

        actual = prediction.get(strategy)
        if actual not in {"ACT", "ABSTAIN", "INVESTIGATE", "ESCALATE"}:
            raise ValueError(f"invalid {strategy} prediction: {actual!r}")

        profile_id = prediction.get("profile_id")
        if isinstance(profile_id, str) and profile_id:
            profile_counts[profile_id] = profile_counts.get(profile_id, 0) + 1
            profiled_variants += 1
        if prediction.get("binding_complete") is True:
            complete_binding += 1

        records.append(
            {
                "pair_id": pair_id,
                "expected": str(task_type).upper(),
                "actual": actual,
                "category": category,
            }
        )

    report = metrics.evaluate(records)
    report["confidence_intervals"] = bootstrap.confidence_intervals(
        records,
        evaluate_fn=metrics.evaluate,
    )
    by_category: dict[str, Any] = {}
    for category in sorted(RUNTIME_CATEGORIES):
        subset = [row for row in records if row["category"] == category]
        if not subset:
            raise ValueError(f"missing development category: {category}")
        category_report = metrics.evaluate(subset)
        category_report["confidence_intervals"] = bootstrap.confidence_intervals(
            subset,
            evaluate_fn=metrics.evaluate,
        )
        by_category[category] = category_report

    report.update(
        {
            "partition": "development",
            "strategy": strategy,
            "development_variants": len(records),
            "development_pairs": len({row["pair_id"] for row in records}),
            "complete_binding_variants": complete_binding,
            "profiled_variants": profiled_variants,
            "provider_profile_coverage": (
                profiled_variants / len(records) if records else 0.0
            ),
            "complete_binding_coverage": (
                complete_binding / len(records) if records else 0.0
            ),
            "profile_counts": profile_counts,
            "holdout_labels_consumed": False,
            "by_category": by_category,
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--development-labels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = score(_load(args.predictions), _load(args.development_labels))
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
