from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


freeze_method = _load("freeze_method_test", ROOT / "benchmark" / "freeze_method.py")
freeze_predictions = _load(
    "freeze_holdout_predictions_test",
    ROOT / "benchmark" / "freeze_holdout_predictions.py",
)


DEPENDENCIES = [
    {
        "name": "example-runtime",
        "version_or_commit": "v1",
        "license": "Apache-2.0",
        "purpose": "test",
    }
]
CLAIMS = {
    "intended_claim": "test a frozen method without revealing holdout gold",
    "non_claims": ["does not claim benchmark superiority"],
}


def _sealed_card(tmp_path: Path) -> dict:
    config = tmp_path / "method-config.json"
    report = tmp_path / "dev-report.json"
    config.write_text('{"threshold": 0.5}\n', encoding="utf-8")
    report.write_text('{"partition": "development"}\n', encoding="utf-8")
    return freeze_method.build_card(
        method_id="example-method",
        code_commit="a" * 40,
        method_config=config,
        development_report=report,
        dependencies=DEPENDENCIES,
        claims=CLAIMS,
    )


def test_freeze_method_builds_valid_sealed_card(tmp_path: Path) -> None:
    card = _sealed_card(tmp_path)
    assert card["schema_version"] == "rn-method-card/0.2"
    assert card["holdout_status"] == "sealed"
    assert card["holdout_prediction_sha256"] is None
    assert card["benchmark_manifest_sha256"] == freeze_method.sha256_file(
        freeze_method.MANIFEST
    )
    assert card["provider_profile_sha256"] == freeze_method.sha256_file(
        freeze_method.PROFILE_REGISTRY
    )


def test_holdout_prediction_freeze_never_needs_gold(tmp_path: Path) -> None:
    card = _sealed_card(tmp_path)
    predictions = tmp_path / "predictions.json"
    predictions.write_text(
        json.dumps(
            [
                {"case_id": "case_a", "prediction": "ACT"},
                {"case_id": "case_b", "prediction": "INVESTIGATE"},
            ]
        ),
        encoding="utf-8",
    )
    released = freeze_predictions.freeze(
        sealed_card=card,
        prediction_file=predictions,
        release_commit="b" * 40,
    )
    assert released["holdout_status"] == "released"
    assert released["holdout_prediction_sha256"] == freeze_predictions.sha256_file(
        predictions
    )


def test_holdout_freeze_rejects_benchmark_drift(tmp_path: Path) -> None:
    card = _sealed_card(tmp_path)
    card["benchmark_manifest_sha256"] = "0" * 64
    predictions = tmp_path / "predictions.json"
    predictions.write_text('[{"case_id":"case_a","prediction":"ACT"}]\n', encoding="utf-8")

    try:
        freeze_predictions.freeze(
            sealed_card=card,
            prediction_file=predictions,
            release_commit="b" * 40,
        )
    except ValueError as exc:
        assert "benchmark_manifest_sha256" in str(exc)
    else:
        raise AssertionError("benchmark drift must reject holdout prediction freeze")


def test_holdout_freeze_rejects_gold_or_identity_fields(tmp_path: Path) -> None:
    card = _sealed_card(tmp_path)
    predictions = tmp_path / "predictions.json"
    predictions.write_text(
        '[{"case_id":"case_a","prediction":"ACT","category":"critical_tool_failure"}]\n',
        encoding="utf-8",
    )
    try:
        freeze_predictions.freeze(
            sealed_card=card,
            prediction_file=predictions,
            release_commit="b" * 40,
        )
    except ValueError as exc:
        assert "forbidden gold/identity" in str(exc)
    else:
        raise AssertionError("gold-bearing holdout predictions must be rejected")


def test_holdout_freeze_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    card = _sealed_card(tmp_path)
    predictions = tmp_path / "predictions.json"
    predictions.write_text(
        '[{"case_id":"case_a","prediction":"ACT"},{"case_id":"case_a","prediction":"ABSTAIN"}]\n',
        encoding="utf-8",
    )
    try:
        freeze_predictions.freeze(
            sealed_card=card,
            prediction_file=predictions,
            release_commit="b" * 40,
        )
    except ValueError as exc:
        assert "duplicate holdout prediction case_id" in str(exc)
    else:
        raise AssertionError("duplicate prediction ids must be rejected")
