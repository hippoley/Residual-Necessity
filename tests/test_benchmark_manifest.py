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
