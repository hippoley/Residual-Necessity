from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"benchmark"/"validate_holdout_policy.py"
spec=importlib.util.spec_from_file_location("holdout_policy",MODULE)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def base_policy() -> dict:
    return {
        "schema_version":"rn-holdout-policy/0.1",
        "track_id":"A-runtime-necessity",
        "status":"sealed",
        "split_manifest_sha256":"97957135fa566fdd0ece3add73fee2dfaa0d594b342910d180fbbbeac4cbcd79",
        "holdout_pairs":33,
        "released_candidate":None,
    }


def test_sealed_policy_is_valid() -> None:
    assert mod.validate_policy(base_policy())==[]


def test_released_policy_requires_frozen_candidate_metadata() -> None:
    p=base_policy()
    p["status"]="released"
    errors=mod.validate_policy(p)
    assert any("released_candidate" in e for e in errors)


def test_released_policy_accepts_frozen_candidate() -> None:
    p=base_policy()
    p["status"]="released"
    p["released_candidate"]={
        "candidate_method_id":"rn-proposition-v1",
        "candidate_code_commit":"abc123",
        "provider_profile_sha256":"def456",
        "development_report_sha256":"ghi789",
        "method_card_sha256":"jkl012",
    }
    assert mod.validate_policy(p)==[]
