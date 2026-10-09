#!/usr/bin/env python3
"""Generate and validate a sealed Residual Necessity Benchmark Method Card."""

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
    schema = load_json(SCHEMA)
    jsonschema.Draft202012Validator(schema).validate(card)


def build_card(
    *,
    method_id: str,
    code_commit: str,
    method_config: Path,
    development_report: Path,
    dependencies: list[dict[str, Any]],
    claims: dict[str, Any],
) -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    policy = load_json(POLICY)

    if manifest.get("benchmark_version") != "0.2":
        raise ValueError("freeze_method supports Reality Benchmark 0.2 only")
    if policy.get("status") != "sealed":
        raise ValueError("holdout policy is not sealed")

    split_hash = policy.get("split_manifest_sha256")
    if not isinstance(split_hash, str) or len(split_hash) != 64:
        raise ValueError("holdout policy missing frozen split hash")

    if not method_id:
        raise ValueError("method_id required")
    if len(code_commit) != 40 or any(ch not in "0123456789abcdef" for ch in code_commit):
        raise ValueError("code_commit must be a lowercase 40-hex commit")

    card: dict[str, Any] = {
        "schema_version": "rn-method-card/0.2",
        "method_id": method_id,
        "track_id": "A-runtime-necessity",
        "code_commit": code_commit,
        "benchmark_manifest_sha256": sha256_file(MANIFEST),
        "split_manifest_sha256": split_hash,
        "method_config_sha256": sha256_file(method_config),
        "provider_profile_sha256": sha256_file(PROFILE_REGISTRY),
        "development_report_sha256": sha256_file(development_report),
        "prediction_protocol": "freeze_before_holdout_reveal",
        "holdout_status": "sealed",
        "holdout_release_commit": None,
        "holdout_prediction_sha256": None,
        "dependencies": dependencies,
        "claims": claims,
    }
    validate_card(card)
    return card


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method-id", required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--method-config", type=Path, required=True)
    parser.add_argument("--development-report", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    dependencies = load_json(args.dependencies)
    claims = load_json(args.claims)
    if not isinstance(dependencies, list):
        raise ValueError("dependencies must be a JSON array")
    if not isinstance(claims, dict):
        raise ValueError("claims must be a JSON object")

    card = build_card(
        method_id=args.method_id,
        code_commit=args.code_commit,
        method_config=args.method_config,
        development_report=args.development_report,
        dependencies=dependencies,
        claims=claims,
    )
    args.out.write_text(
        json.dumps(card, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "method_id": card["method_id"],
        "holdout_status": card["holdout_status"],
        "method_card_sha256": sha256_file(args.out),
        "benchmark_manifest_sha256": card["benchmark_manifest_sha256"],
        "split_manifest_sha256": card["split_manifest_sha256"],
        "provider_profile_sha256": card["provider_profile_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
