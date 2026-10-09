#!/usr/bin/env python3
"""Create a deterministic pair-level development/holdout split without gold labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SPLIT_VERSION = "agentabstain-pair-split/0.1"
HOLDOUT_PERCENT = 30
SALT = "residual-necessity-reality-gate-v1"


def assign(pair_id: str) -> str:
    digest = hashlib.sha256(f"{SALT}:{pair_id}".encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:8], "big") % 100
    return "holdout" if bucket < HOLDOUT_PERCENT else "development"


def build(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pair_ids = sorted({
        row["pair_id"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("pair_id"), str)
    })
    if not pair_ids:
        raise ValueError("blind slice contains no pair ids")

    assignments = {pair_id: assign(pair_id) for pair_id in pair_ids}
    counts = {
        "development": sum(v == "development" for v in assignments.values()),
        "holdout": sum(v == "holdout" for v in assignments.values()),
    }
    if not counts["development"] or not counts["holdout"]:
        raise ValueError(f"degenerate split: {counts}")

    return {
        "schema_version": SPLIT_VERSION,
        "salt": SALT,
        "holdout_percent": HOLDOUT_PERCENT,
        "pair_count": len(pair_ids),
        "counts": counts,
        "assignments": assignments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blind_slice", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows = json.loads(args.blind_slice.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("blind slice must be a JSON list")

    manifest = build(rows)
    args.out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "pair_count": manifest["pair_count"],
        "counts": manifest["counts"],
        "gold_used": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
