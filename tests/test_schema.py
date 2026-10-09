from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema" / "necessity.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def validate_receipt(receipt: dict) -> None:
    errors = sorted(VALIDATOR.iter_errors(receipt), key=lambda e: list(e.path))
    assert not errors, "\n".join(error.message for error in errors)


def test_residual_act_example_matches_schema() -> None:
    receipt = json.loads((ROOT / "examples" / "residual-act.json").read_text(encoding="utf-8"))
    validate_receipt(receipt)


def test_all_conformance_receipts_match_schema() -> None:
    cases = json.loads((ROOT / "conformance" / "core-cases.json").read_text(encoding="utf-8"))
    for case in cases:
        try:
            validate_receipt(case["receipt"])
        except AssertionError as exc:
            raise AssertionError(f"{case['id']}: {exc}") from exc


def test_unknown_predicate_field_is_rejected_by_schema() -> None:
    receipt = json.loads((ROOT / "examples" / "residual-act.json").read_text(encoding="utf-8"))
    receipt["predicates"][0]["human_ony"] = True
    errors = list(VALIDATOR.iter_errors(receipt))
    assert errors


def test_unknown_observation_field_is_rejected_by_schema() -> None:
    receipt = json.loads((ROOT / "examples" / "residual-act.json").read_text(encoding="utf-8"))
    first = next(iter(receipt["observations"].values()))
    first["positive_authorit"] = first.get("positive_authority")
    errors = list(VALIDATOR.iter_errors(receipt))
    assert errors


def test_true_requires_only_positive_authority() -> None:
    receipt = json.loads((ROOT / "examples" / "residual-act.json").read_text(encoding="utf-8"))
    first_key = next(iter(receipt["observations"]))
    receipt["observations"][first_key]["negative_authority"] = receipt["observations"][first_key]["positive_authority"]
    errors = list(VALIDATOR.iter_errors(receipt))
    assert errors


def test_false_requires_negative_authority() -> None:
    cases = json.loads((ROOT / "conformance" / "core-cases.json").read_text(encoding="utf-8"))
    receipt = next(case["receipt"] for case in cases if case["id"] == "already-resolved-abstain")
    receipt = json.loads(json.dumps(receipt))
    obs = receipt["observations"]["residual_violation_exists"]
    obs.pop("negative_authority")
    errors = list(VALIDATOR.iter_errors(receipt))
    assert errors
