#!/usr/bin/env python3
"""Freeze holdout predictions without reading or scoring holdout gold."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmark" / "manifest.json"
POLICY = ROOT / "benchmark" / "holdout_policy.json"
PROFILE_REGISTRY = ROOT / "experiments" / "agentabstain" / "probe_binding_profiles.json"
SCHEMA = ROOT / "benchmark" / "method_submission.schema.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_card(card: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(load_json(SCHEMA)).validate(card)


def freeze(
    *,
    sealed_card: dict[str, Any],
    prediction_file: Path,
    release_commit: str,
) -> dict[str, Any]:
    validate_card(sealed_card)
    if sealed_card.get("holdout_status") != "sealed":
        raise ValueError("input Method Card must be sealed")
    if sealed_card.get("holdout_prediction_sha256") is not None:
        raise ValueError("sealed Method Card already contains holdout prediction hash")
    if len(release_commit) != 40 or any(ch not in "0123456789abcdef" for ch in release_commit):
        raise ValueError("release_commit must be lowercase 40-hex")

    policy = load_json(POLICY)
    if policy.get("status") != "sealed":
        raise ValueError("repository holdout policy is already released")

    expected = {
        "benchmark_manifest_sha256": sha256_file(MANIFEST),
        "split_manifest_sha256": policy.get("split_manifest_sha256"),
        "provider_profile_sha256": sha256_file(PROFILE_REGISTRY),
    }
    for key, value in expected.items():
        if sealed_card.get(key) != value:
            raise ValueError(
                f"sealed Method Card drift for {key}: "
                f"{sealed_card.get(key)!r} != current {value!r}"
            )

    predictions = load_json(prediction_file)
    if not isinstance(predictions, list) or not predictions:
        raise ValueError("holdout predictions must be a non-empty JSON list")

    forbidden = {
        "task_type",
        "abstention_trigger",
        "execution_dag",
        "critical_actions",
        "category",
        "transformation_dimension",
        "task_id",
    }
    case_ids: set[str] = set()
    for row in predictions:
        if not isinstance(row, dict):
            raise ValueError("holdout prediction rows must be objects")
        if forbidden.intersection(row):
            raise ValueError(
                "holdout prediction artifact contains forbidden gold/identity fields"
            )
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("holdout prediction row missing case_id")
        if case_id in case_ids:
            raise ValueError(f"duplicate holdout prediction case_id: {case_id}")
        case_ids.add(case_id)

    released = json.loads(json.dumps(sealed_card))
    released["holdout_status"] = "released"
    released["holdout_release_commit"] = release_commit
    released["holdout_prediction_sha256"] = sha256_file(prediction_file)
    validate_card(released)
    return released


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sealed-card", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--release-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    released = freeze(
        sealed_card=load_json(args.sealed_card),
        prediction_file=args.predictions,
        release_commit=args.release_commit,
    )
    args.out.write_text(
        json.dumps(released, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "method_id": released["method_id"],
        "holdout_status": released["holdout_status"],
        "holdout_prediction_sha256": released["holdout_prediction_sha256"],
        "released_method_card_sha256": sha256_file(args.out),
        "gold_consumed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
