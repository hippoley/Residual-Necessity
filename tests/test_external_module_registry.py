from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"audit"/"validate_external_modules.py"
REGISTRY=ROOT/"audit"/"external_modules.json"

spec=importlib.util.spec_from_file_location("external_module_validator",MODULE)
assert spec and spec.loader
validator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def test_current_external_module_registry_is_valid() -> None:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert validator.validate(data)==[]

def test_safeact_support_cannot_be_reclassified_as_necessity() -> None:
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    safeact=next(x for x in data["modules"] if x["id"]=="safeact-contract")
    safeact["semantic_boundary"]["forbidden_mapping"]=[]
    errors=validator.validate(data)
    assert any("forbidden mappings" in e for e in errors)
