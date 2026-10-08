#!/usr/bin/env python3
"""Prepare a gold-hidden runtime-only slice from AgentAbstain tasks.jsonl.

The output is intentionally insufficient to reconstruct the benchmark label:
we remove task_type, abstention_trigger, execution_dag, critical_actions,
category, and transformation metadata from the inference view.

Only runtime-phase tasks are retained because Residual Necessity is specifically
about current-state evidence discovered during execution rather than generic
instruction ambiguity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HIDDEN_FIELDS = {
    "task_type",
    "abstention_trigger",
    "execution_dag",
    "critical_actions",
    "category",
    "transformation_dimension",
}

ALLOWED_RUNTIME_CATEGORIES = {
    "critical_tool_failure",
    "conflicting_evidence",
    "emergent_risk_discovery",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {number}: expected object")
        rows.append(value)
    return rows


def build_blind_slice(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blind: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []

    for row in rows:
        if row.get("phase") != "runtime":
            continue
        if row.get("category") not in ALLOWED_RUNTIME_CATEGORIES:
            continue

        pair_id = row.get("pair_id")
        task_type = row.get("task_type")
        if not isinstance(pair_id, str) or task_type not in {"act", "abstain"}:
            raise ValueError("runtime row missing valid pair_id/task_type")

        view = {k: v for k, v in row.items() if k not in HIDDEN_FIELDS}
        if "task_type" in view or "abstention_trigger" in view:
            raise AssertionError("gold field leaked into blind view")

        blind.append(view)
        labels.append({"pair_id": pair_id, "task_type": task_type})

    return blind, labels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks_jsonl", type=Path)
    parser.add_argument("--blind-out", type=Path, required=True)
    parser.add_argument("--labels-out", type=Path, required=True)
    args = parser.parse_args()

    blind, labels = build_blind_slice(load_jsonl(args.tasks_jsonl))
    args.blind_out.write_text(json.dumps(blind, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.labels_out.write_text(json.dumps(labels, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "runtime_variants": len(blind),
        "runtime_pairs": len({x["pair_id"] for x in labels}),
        "gold_fields_hidden": sorted(HIDDEN_FIELDS),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
