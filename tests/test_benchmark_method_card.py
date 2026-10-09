from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((ROOT/"benchmark"/"method_submission.schema.json").read_text(encoding="utf-8"))
EXAMPLE=json.loads((ROOT/"benchmark"/"method_card.example.json").read_text(encoding="utf-8"))
VALIDATOR=Draft202012Validator(SCHEMA)


def errors(value: dict):
    return list(VALIDATOR.iter_errors(value))


def test_example_method_card_is_schema_valid_and_sealed() -> None:
    assert errors(EXAMPLE)==[]
    assert EXAMPLE["holdout_status"]=="sealed"
    assert EXAMPLE["holdout_release_commit"] is None


def test_released_method_card_requires_release_commit() -> None:
    value=json.loads(json.dumps(EXAMPLE))
    value["holdout_status"]="released"
    assert errors(value)


def test_method_card_rejects_unpinned_code_commit() -> None:
    value=json.loads(json.dumps(EXAMPLE))
    value["code_commit"]="main"
    assert errors(value)


def test_method_card_requires_benchmark_and_config_hashes() -> None:
    for key in (
        "benchmark_manifest_sha256",
        "split_manifest_sha256",
        "method_config_sha256",
    ):
        value=json.loads(json.dumps(EXAMPLE))
        value.pop(key)
        assert errors(value), key


def test_released_method_card_requires_frozen_holdout_prediction() -> None:
    value=json.loads(json.dumps(EXAMPLE))
    value["holdout_status"]="released"
    value["holdout_release_commit"]="1"*40
    value["holdout_prediction_sha256"]=None
    assert errors(value)

    value["holdout_prediction_sha256"]="2"*64
    assert errors(value)==[]
