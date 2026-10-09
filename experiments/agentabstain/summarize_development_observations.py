#!/usr/bin/env python3
"""Summarize development-only AgentAbstain observations without holdout access.

This is an analysis aid, not an inference component. It consumes only the
development observation/label files emitted by the Reality Gate and produces
aggregate structural statistics that help decide whether proposition-specific
providers are feasible.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        raise ValueError(f"{path} must contain a JSON list of objects")
    return value


def _shape(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def summarize(observations: list[dict[str, Any]], labels: list[dict[str, Any]]) -> dict[str, Any]:
    label_by_case = {row["case_id"]: row["task_type"] for row in labels}
    if set(label_by_case) != {row["case_id"] for row in observations}:
        raise ValueError("development observation/label case mismatch")

    tool_counts: Counter[str] = Counter()
    tool_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    success_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    result_shape_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    object_key_counts: Counter[str] = Counter()
    object_key_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    string_marker_counts: Counter[str] = Counter()

    marker_terms = (
        "error", "failed", "failure", "warning", "risk", "hold",
        "blocked", "restricted", "conflict", "mismatch", "unsafe",
        "delete", "denied", "unavailable",
    )

    for row in observations:
        case_id = row["case_id"]
        label = str(label_by_case[case_id])
        tool = str(row.get("tool") or "<none>")
        tool_counts[tool] += 1
        tool_by_label[label][tool] += 1

        success = row.get("success")
        success_key = "none" if success is None else str(bool(success)).lower()
        success_by_label[label][success_key] += 1

        result = row.get("result")
        shape = _shape(result)
        result_shape_by_label[label][shape] += 1

        if isinstance(result, dict):
            for key in result:
                key_text = str(key)
                object_key_counts[key_text] += 1
                object_key_by_label[label][key_text] += 1

        text = json.dumps(result, sort_keys=True, ensure_ascii=False).lower()
        for marker in marker_terms:
            if marker in text:
                string_marker_counts[marker] += 1

    return {
        "development_variants": len(observations),
        "development_pairs": len({row["pair_id"] for row in observations}),
        "labels": Counter(label_by_case.values()),
        "tool_counts": tool_counts,
        "tool_by_label": {k: v for k, v in tool_by_label.items()},
        "success_by_label": {k: v for k, v in success_by_label.items()},
        "result_shape_by_label": {k: v for k, v in result_shape_by_label.items()},
        "top_object_keys": object_key_counts.most_common(60),
        "top_object_keys_by_label": {
            k: v.most_common(60) for k, v in object_key_by_label.items()
        },
        "string_marker_counts": string_marker_counts,
        "holdout_payload_consumed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = summarize(_load(args.observations), _load(args.labels))
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=dict) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
