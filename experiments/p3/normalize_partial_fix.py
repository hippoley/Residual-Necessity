#!/usr/bin/env python3
"""Normalize one real P3 partial-fix task from a pinned external checkout."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def find_key(mapping: dict[str, Any], names: set[str]) -> tuple[str, Any] | None:
    for key, value in mapping.items():
        if norm_key(str(key)) in names:
            return str(key), value
    return None


def walk_mappings(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_mappings(child)


def find_named(value: Any, names: set[str]) -> Any:
    for mapping in walk_mappings(value):
        found = find_key(mapping, names)
        if found is not None:
            return found[1]
    return None


def commit_of(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    found = find_key(value, {"commit_sha1", "commit_sha", "commit", "revision"})
    if found is None:
        return None
    commit = found[1]
    return str(commit) if commit is not None else None


def classify(doc: dict[str, Any]) -> str | None:
    value = find_named(doc, {"classification", "fix_classification", "class"})
    return str(value) if value is not None else None


def extract_sequence(doc: dict[str, Any]) -> dict[str, Any]:
    base = find_named(doc, {"base_version", "base"})
    attempts = find_named(doc, {"fix_attempt", "fix_attempts", "attempts"})
    expected = find_named(doc, {"expected_fix", "final_fix", "expected"})

    if isinstance(attempts, dict):
        attempts = [attempts]
    if not isinstance(attempts, list):
        attempts = []

    return {
        "base_revision": commit_of(base),
        "attempt_revisions": [
            commit
            for item in attempts
            if (commit := commit_of(item)) is not None
        ],
        "expected_revision": commit_of(expected),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("p3_root", type=Path)
    parser.add_argument("--p3-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    candidates: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(args.p3_root.rglob("*.yml")):
        if "partial-fixes" not in path.parts:
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        if classify(doc) == "Partial Fix":
            candidates.append((path, doc))

    if not candidates:
        raise SystemExit("no P3 task classified exactly as 'Partial Fix'")

    for path, doc in candidates:
        sequence = extract_sequence(doc)
        if (
            sequence["base_revision"]
            and sequence["attempt_revisions"]
            and sequence["expected_revision"]
        ):
            repository = find_named(doc, {"repository_url", "repository", "repo_url"})
            related_issue = find_named(doc, {"related_issue", "issue_url", "issue"})
            record = {
                "schema_version": "p3-residual-sequence/0.1",
                "source": "SoSy-Lab/P3",
                "source_commit": args.p3_commit,
                "task_path": str(path.relative_to(args.p3_root)),
                "classification": "Partial Fix",
                "repository_url": str(repository) if repository is not None else None,
                "related_issue": str(related_issue) if related_issue is not None else None,
                **sequence,
                "residual_semantics": {
                    "intermediate_attempt_is_curated_incomplete_fix": True,
                    "expected_fix_follows_partial_attempt": True,
                },
            }
            args.out.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps(record, sort_keys=True))
            return 0

    raise SystemExit(
        f"found {len(candidates)} Partial Fix tasks, but none exposed a complete "
        "base/attempt/expected revision chain under the documented schema"
    )


if __name__ == "__main__":
    raise SystemExit(main())
