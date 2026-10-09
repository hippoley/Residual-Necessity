#!/usr/bin/env python3
"""Summarize the pinned P3 partial-fix corpus without overclaiming oracle coverage."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.p3.normalize_partial_fix import (
    classify,
    extract_sequence,
    find_named,
    norm_key,
)


def summarize(root: Path, source_commit: str) -> dict[str, Any]:
    partial_tasks = 0
    reconstructable = 0
    repositories: set[str] = set()
    attempt_count_distribution: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []

    for path in sorted(root.rglob("*.yml")):
        if "partial-fixes" not in path.parts:
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue

        classification = norm_key(classify(doc) or "unknown")
        classifications[classification] += 1
        if classification != "partial_fix":
            continue

        partial_tasks += 1
        repository = find_named(doc, {"repository_url", "repository", "repo_url"})
        if repository is not None:
            repositories.add(str(repository))

        sequence = extract_sequence(doc)
        attempts = sequence["attempt_revisions"]
        attempt_count_distribution[str(len(attempts))] += 1

        complete = bool(
            sequence["base_revision"]
            and attempts
            and sequence["expected_revision"]
        )
        if complete:
            reconstructable += 1
            if len(examples) < 12:
                examples.append(
                    {
                        "task_path": str(path.relative_to(root)),
                        "repository_url": str(repository) if repository is not None else None,
                        "attempt_count": len(attempts),
                        "base_revision": sequence["base_revision"],
                        "expected_revision": sequence["expected_revision"],
                    }
                )

    if partial_tasks == 0:
        raise ValueError("pinned P3 checkout contains no partial-fix tasks")

    return {
        "schema_version": "p3-corpus-inventory/0.1",
        "source": "SoSy-Lab/P3",
        "source_commit": source_commit,
        "partial_fix_tasks": partial_tasks,
        "reconstructable_revision_chains": reconstructable,
        "reconstructable_fraction": reconstructable / partial_tasks,
        "unique_repositories": len(repositories),
        "attempt_count_distribution": dict(sorted(attempt_count_distribution.items())),
        "classification_counts": dict(sorted(classifications.items())),
        "examples": examples,
        "oracle_coverage_claim": "none",
        "purpose": "corpus breadth inventory; bounded RN oracle remains separate",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("p3_root", type=Path)
    parser.add_argument("--p3-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = summarize(args.p3_root, args.p3_commit)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
