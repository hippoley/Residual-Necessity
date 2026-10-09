#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != "rn-holdout-policy/0.1":
        errors.append("unsupported holdout policy version")
    if policy.get("track_id") != "A-runtime-necessity":
        errors.append("holdout policy must target A-runtime-necessity")
    if policy.get("status") not in {"sealed", "released"}:
        errors.append("status must be sealed or released")
    if policy.get("holdout_pairs") != 33:
        errors.append("holdout policy must preserve 33-pair split")
    if policy.get("split_manifest_sha256") != "97957135fa566fdd0ece3add73fee2dfaa0d594b342910d180fbbbeac4cbcd79":
        errors.append("holdout policy split hash drifted")

    released = policy.get("released_candidate")
    if policy.get("status") == "sealed":
        if released is not None:
            errors.append("sealed holdout may not name a released candidate")
    else:
        if not isinstance(released, dict):
            errors.append("released holdout requires released_candidate metadata")
        else:
            for key in (
                "candidate_method_id",
                "candidate_code_commit",
                "provider_profile_sha256",
                "development_report_sha256",
            ):
                value = released.get(key)
                if not isinstance(value, str) or not value:
                    errors.append(f"released candidate missing {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("benchmark/holdout_policy.json"),
    )
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        raise SystemExit("holdout policy must be a JSON object")
    errors = validate_policy(policy)
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        json.dumps(
            {
                "HOLDOUT_POLICY": "PASS",
                "status": policy["status"],
                "policy_sha256": _sha256(args.policy),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
