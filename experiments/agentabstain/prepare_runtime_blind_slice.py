#!/usr/bin/env python3
"""Partition AgentAbstain runtime tasks into inference, execution, and scoring views.

The planner/inference view must not contain benchmark gold or a source locator.
The executor gets a separate hidden runtime map so it can mount the correct
sandbox variant without exposing that locator to the planner.
The scorer gets labels only after predictions have been frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator


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


def _opaque_pair_id(pair_id: str) -> str:
    return "pair_" + hashlib.sha256(pair_id.encode("utf-8")).hexdigest()[:20]


def _opaque_case_id(pair_id: str, task_type: str) -> str:
    material = f"{pair_id}\0{task_type}"
    return "case_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def _runtime_rows(rows: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for row in rows:
        if row.get("phase") != "runtime":
            continue
        if row.get("category") not in ALLOWED_RUNTIME_CATEGORIES:
            continue
        pair_id = row.get("pair_id")
        task_type = row.get("task_type")
        category = row.get("category")
        task_id = row.get("task_id")
        if (
            not isinstance(pair_id, str)
            or task_type not in {"act", "abstain"}
            or not isinstance(category, str)
            or not isinstance(task_id, str)
        ):
            raise ValueError("runtime row missing valid pair/category/task/task_type")
        yield row


def build_blind_slice(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return planner-safe inference rows and scoring-only labels."""
    blind: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []

    for row in _runtime_rows(rows):
        pair_id = row["pair_id"]
        task_type = row["task_type"]
        opaque_pair_id = _opaque_pair_id(pair_id)
        opaque_case_id = _opaque_case_id(pair_id, task_type)

        view = {k: v for k, v in row.items() if k not in HIDDEN_FIELDS}
        view["pair_id"] = opaque_pair_id
        view["case_id"] = opaque_case_id

        if HIDDEN_FIELDS.intersection(view):
            raise AssertionError("gold field leaked into blind view")
        if "/" in opaque_pair_id or "/" in opaque_case_id:
            raise AssertionError("semantic locator leaked through opaque identifiers")

        blind.append(view)
        labels.append(
            {
                "case_id": opaque_case_id,
                "pair_id": opaque_pair_id,
                "task_type": task_type,
            }
        )

    return blind, labels


def build_runtime_map(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return executor-only source locators.

    This file is deliberately separated from both planner input and scoring
    labels. It contains enough information to load a sandbox variant but no
    inference output should ever copy these fields forward.
    """
    runtime_map: list[dict[str, Any]] = []
    for row in _runtime_rows(rows):
        pair_id = row["pair_id"]
        task_type = row["task_type"]
        runtime_map.append(
            {
                "case_id": _opaque_case_id(pair_id, task_type),
                "category": row["category"],
                "task_id": row["task_id"],
                "task_type": task_type,
            }
        )
    return runtime_map


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks_jsonl", type=Path)
    parser.add_argument("--blind-out", type=Path, required=True)
    parser.add_argument("--labels-out", type=Path, required=True)
    parser.add_argument("--runtime-map-out", type=Path)
    args = parser.parse_args()

    rows = load_jsonl(args.tasks_jsonl)
    blind, labels = build_blind_slice(rows)
    runtime_map = build_runtime_map(rows)

    args.blind_out.write_text(
        json.dumps(blind, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.labels_out.write_text(
        json.dumps(labels, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.runtime_map_out is not None:
        args.runtime_map_out.write_text(
            json.dumps(runtime_map, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "runtime_variants": len(blind),
                "runtime_pairs": len({x["pair_id"] for x in labels}),
                "runtime_map_rows": len(runtime_map),
                "gold_fields_hidden": sorted(HIDDEN_FIELDS),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
