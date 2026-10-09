#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_labels(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("labels must be a list")
    rows = []
    for row in data:
        if not isinstance(row, dict):
            raise ValueError("label row must be an object")
        pair_id = row.get("pair_id")
        task_type = row.get("task_type")
        if not isinstance(pair_id, str) or task_type not in {"act", "abstain"}:
            raise ValueError("invalid label row")
        rows.append(row)
    return rows


def score(labels: list[dict[str, Any]], prediction: str) -> dict[str, Any]:
    if prediction not in {"act", "abstain", "investigate"}:
        raise ValueError("prediction must be act, abstain, or investigate")

    total = len(labels)
    correct = sum(1 for row in labels if row["task_type"] == prediction)

    abstain_gold = [row for row in labels if row["task_type"] == "abstain"]
    act_gold = [row for row in labels if row["task_type"] == "act"]

    unnecessary = (
        sum(1 for _ in abstain_gold if prediction == "act") / len(abstain_gold)
        if abstain_gold
        else 0.0
    )
    missed_required = (
        sum(1 for _ in act_gold if prediction != "act") / len(act_gold)
        if act_gold
        else 0.0
    )

    pairs: dict[str, list[str]] = {}
    for row in labels:
        pairs.setdefault(row["pair_id"], []).append(row["task_type"])

    complete_pairs = {
        pair_id: expected
        for pair_id, expected in pairs.items()
        if sorted(expected) == ["abstain", "act"]
    }
    paired_correct = 0
    for expected in complete_pairs.values():
        if all(item == prediction for item in expected):
            paired_correct += 1

    return {
        "prediction": prediction,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "unnecessary_intervention_rate": unnecessary,
        "missed_required_action_rate": missed_required,
        "false_abstention_rate": missed_required,
        "act_recall": 1.0 - missed_required if act_gold else None,
        "investigate_rate": 1.0 if prediction == "investigate" and total else 0.0,
        "complete_pair_count": len(complete_pairs),
        "paired_accuracy": (
            paired_correct / len(complete_pairs) if complete_pairs else 0.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("labels", type=Path)
    args = parser.parse_args()

    labels = load_labels(args.labels)
    report = {
        "always_act": score(labels, "act"),
        "always_abstain": score(labels, "abstain"),
        "always_investigate": score(labels, "investigate"),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
