#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CANDIDATE_KEY_MARKERS = (
    "existing_",
    "already_",
    "_status",
    "idempot",
    "duplicate",
    "completed",
    "executed",
    "done",
    "remaining",
    "pending",
)


def walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, child in value.items():
            key_s = str(key)
            yield path + (key_s,), child
            yield from walk(child, path + (key_s,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk(child, path + (str(i),))


def interesting_key(key: str) -> bool:
    lower = key.lower()
    return (
        lower.startswith("existing_")
        or lower.startswith("already_")
        or lower.endswith("_status")
        or "idempot" in lower
        or lower in {"duplicate", "completed", "executed", "done", "remaining", "pending"}
    )


def summarize(root: Path) -> dict[str, Any]:
    key_counts: Counter[str] = Counter()
    value_counts: dict[str, Counter[str]] = defaultdict(Counter)
    files_scanned = 0

    for path in sorted(root.rglob("*.json")):
        if "materialized_evidence" not in path.parts:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        files_scanned += 1
        for p, value in walk(doc):
            key = p[-1]
            if not interesting_key(key):
                continue
            key_counts[key] += 1
            if value is None or isinstance(value, (str, int, float, bool)):
                value_counts[key][json.dumps(value, sort_keys=True)] += 1

    top = []
    for key, count in key_counts.most_common():
        top.append({
            "key": key,
            "count": count,
            "values": value_counts[key].most_common(30),
        })

    return {
        "materialized_evidence_files": files_scanned,
        "candidate_keys": top,
        "hidden_oracle_consumed": False,
        "purpose": "inventory_only_not_authority",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("safeact_root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = summarize(args.safeact_root)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
