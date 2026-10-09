from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"benchmark"/"validate_manifest.py"
MANIFEST=ROOT/"benchmark"/"manifest.json"

spec=importlib.util.spec_from_file_location("benchmark_manifest_validator",MODULE)
assert spec and spec.loader
validator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def test_current_benchmark_manifest_is_valid() -> None:
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert validator.validate(data)==[]

def test_single_total_score_is_rejected() -> None:
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["aggregation"]["single_total_score"]=True
    errors=validator.validate(data)
    assert any("aggregate score" in error for error in errors)


def test_manifest_preserves_nopatch_protocol_baseline() -> None:
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    track=next(t for t in data["tracks"] if t["id"]=="B-residual-partial-fix")
    names={x["name"] for x in track.get("protocol_baselines",[])}
    assert "NoPatch Prove First" in names


def test_manifest_keeps_three_semantic_tracks() -> None:
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids={t["id"] for t in data["tracks"]}
    assert {
        "A-runtime-necessity",
        "B-residual-partial-fix",
        "C-evidence-support-boundary",
    }.issubset(ids)
