from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "benchmark" / "validate_provider_profiles.py"
REGISTRY = ROOT / "experiments" / "agentabstain" / "probe_binding_profiles.json"
SCHEMA_DOC = json.loads(
    (ROOT / "benchmark" / "provider_profile_registry.schema.json").read_text(encoding="utf-8")
)

spec = importlib.util.spec_from_file_location("provider_profile_validator", MODULE)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_checked_in_provider_registry_is_valid() -> None:
    registry = json.loads(
        (ROOT / "experiments" / "agentabstain" / "probe_binding_profiles.json")
        .read_text(encoding="utf-8")
    )
    schema = json.loads(
        (ROOT / "benchmark" / "provider_profile_registry.schema.json")
        .read_text(encoding="utf-8")
    )
    assert validator.validate(registry, schema) == []


def test_duplicate_profile_id_is_rejected() -> None:
    registry = json.loads(
        (ROOT / "experiments" / "agentabstain" / "probe_binding_profiles.json")
        .read_text(encoding="utf-8")
    )
    registry["profiles"].append(dict(registry["profiles"][0]))
    schema = json.loads(
        (ROOT / "benchmark" / "provider_profile_registry.schema.json")
        .read_text(encoding="utf-8")
    )
    errors = validator.validate(registry, schema)
    assert any("duplicate profile_id" in error for error in errors)


def test_provider_profile_requires_auditable_contract_reference() -> None:
    registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
    profile=registry["profiles"][0]
    profile["source"].pop("contract_ref",None)
    errors=validator.validate(registry,SCHEMA_DOC)
    assert any("contract_ref" in error for error in errors)


def test_fixture_contract_cannot_claim_complete_task_coverage() -> None:
    registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
    profile=registry["profiles"][0]
    profile["source"]["contract_type"]="pinned_fixture_contract"
    profile["decision_scope"]["task_coverage"]="complete"
    errors=validator.validate(registry,SCHEMA_DOC)
    assert any("fixture-bounded" in error for error in errors)
