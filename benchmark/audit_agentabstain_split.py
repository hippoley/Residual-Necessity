#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(labels: list[dict[str, Any]], split: dict[str, Any]) -> dict[str, Any]:
    assignments = split.get("assignments")
    if not isinstance(assignments, dict):
        raise ValueError("split manifest missing assignments")

    pair_category: dict[str, str] = {}
    pair_member_counts: Counter[str] = Counter()

    for row in labels:
        pair_id = row.get("pair_id")
        source_pair_id = row.get("source_pair_id")
        task_type = row.get("task_type")
        if not isinstance(pair_id, str) or not isinstance(source_pair_id, str):
            raise ValueError("label row missing pair identifiers")
        if task_type not in {"act", "abstain"}:
            raise ValueError("invalid task_type")

        category = source_pair_id.split("/", 1)[0]
        if not category:
            raise ValueError("source_pair_id does not expose trusted category prefix")

        existing = pair_category.setdefault(pair_id, category)
        if existing != category:
            raise ValueError(f"pair {pair_id} spans multiple categories")
        pair_member_counts[pair_id] += 1

    bad_pairs = sorted(pair for pair, count in pair_member_counts.items() if count != 2)
    if bad_pairs:
        raise ValueError(f"pairs must have exactly two variants: {bad_pairs[:5]}")

    if set(pair_category) != set(assignments):
        raise ValueError("split assignments and label pairs differ")

    totals = Counter(pair_category.values())
    by_partition: dict[str, Counter[str]] = {
        "development": Counter(),
        "holdout": Counter(),
    }
    for pair_id, category in pair_category.items():
        partition = assignments.get(pair_id)
        if partition not in by_partition:
            raise ValueError(f"invalid partition for {pair_id}: {partition!r}")
        by_partition[partition][category] += 1

    missing: dict[str, list[str]] = {}
    categories = sorted(totals)
    for partition, counts in by_partition.items():
        absent = [category for category in categories if counts[category] == 0]
        if absent:
            missing[partition] = absent

    distribution = {}
    total_pairs = len(pair_category)
    for category in categories:
        total = totals[category]
        distribution[category] = {
            "total_pairs": total,
            "total_fraction": total / total_pairs,
            "development_pairs": by_partition["development"][category],
            "development_fraction_within_category": (
                by_partition["development"][category] / total
            ),
            "holdout_pairs": by_partition["holdout"][category],
            "holdout_fraction_within_category": (
                by_partition["holdout"][category] / total
            ),
        }

    report = {
        "pair_count": total_pairs,
        "categories": categories,
        "partition_counts": {
            partition: sum(counts.values())
            for partition, counts in by_partition.items()
        },
        "category_distribution": distribution,
        "missing_category_coverage": missing,
        "inference_view_exposed_category": False,
    }

    if missing:
        raise ValueError(
            "split lacks category coverage: "
            + json.dumps(missing, sort_keys=True)
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    labels = _load(args.labels)
    split = _load(args.split)
    if not isinstance(labels, list) or not all(isinstance(x, dict) for x in labels):
        raise ValueError("labels must be a JSON list of objects")
    if not isinstance(split, dict):
        raise ValueError("split must be a JSON object")

    report = audit(labels, split)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
