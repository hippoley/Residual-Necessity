#!/usr/bin/env python3
"""Audit whether paired AgentAbstain variants are statically indistinguishable.

The blind inference view should force the method to use runtime evidence rather
than variant-specific text or identifiers. Both members of a pair therefore
must expose identical static fields after gold/identity stripping.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        pair_id = row.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError("blind row missing pair_id")
        by_pair.setdefault(pair_id, []).append(row)

    differing_pairs: list[dict[str, Any]] = []
    field_diff_counts: Counter[str] = Counter()

    for pair_id, members in sorted(by_pair.items()):
        if len(members) != 2:
            raise ValueError(f"pair {pair_id!r} must contain exactly two blind variants")

        left = {k: v for k, v in members[0].items() if k != "pair_id"}
        right = {k: v for k, v in members[1].items() if k != "pair_id"}

        keys = sorted(set(left) | set(right))
        diff_fields = [key for key in keys if left.get(key) != right.get(key)]
        if diff_fields:
            for key in diff_fields:
                field_diff_counts[key] += 1
            differing_pairs.append(
                {
                    "pair_id": pair_id,
                    "fields": diff_fields,
                }
            )

    return {
        "pair_count": len(by_pair),
        "differing_pair_count": len(differing_pairs),
        "field_diff_counts": dict(sorted(field_diff_counts.items())),
        "sample_differences": differing_pairs[:20],
        "static_pair_equivalence_pass": not differing_pairs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blind_slice", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = json.loads(args.blind_slice.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(x, dict) for x in rows):
        raise ValueError("blind slice must contain a JSON list of objects")

    report = audit(rows)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["static_pair_equivalence_pass"]:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
