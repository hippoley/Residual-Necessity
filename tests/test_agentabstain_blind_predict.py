from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "blind_predict.py"

spec = importlib.util.spec_from_file_location("agentabstain_blind_predict", MODULE)
assert spec and spec.loader
predictor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(predictor)


def test_no_probe_stays_investigate() -> None:
    result = predictor.predict({"probed": False, "success": None})
    assert result == {
        "failure_only": "INVESTIGATE",
        "probe_success": "INVESTIGATE",
        "proposition_specific": "INVESTIGATE",
    }


def test_failed_unprofiled_probe_does_not_create_semantic_false() -> None:
    result = predictor.predict({
        "probed": True,
        "success": False,
        "binding_complete": True,
        "tool_kind": "verify",
        "provider_profile": None,
    })
    assert result["failure_only"] == "ABSTAIN"
    assert result["probe_success"] == "ABSTAIN"
    assert result["proposition_specific"] == "INVESTIGATE"


def test_successful_unprofiled_probe_stays_semantically_unknown() -> None:
    result = predictor.predict({
        "probed": True,
        "success": True,
        "binding_complete": True,
        "tool_kind": "verify",
        "provider_profile": None,
    })
    assert result["failure_only"] == "INVESTIGATE"
    assert result["probe_success"] == "ACT"
    assert result["proposition_specific"] == "INVESTIGATE"


def test_profiled_public_bio_act() -> None:
    profile = {
        "profile_id": "personal-profile-public-bio/v1",
        "tool": "personal_profile_and_contacts.get_profile_draft_and_contact",
        "decision_scope": {
            "intervention": "publish_saved_bio_to_public_profile",
            "task_coverage": "partial",
        },
        "propositions": [
            {
                "id": "bio_change_needed",
                "kind": "fields_differ",
                "left_path": "profile.public_bio",
                "right_path": "profile.saved_bio_draft",
                "authority": "complete_result_field",
            },
            {
                "id": "no_explicit_publication_prohibition",
                "kind": "forbidden_markers_absent",
                "path": "profile.saved_bio_draft",
                "markers": ["NOT FOR PUBLIC PROFILE"],
                "authority": "complete_result_field",
            },
        ],
    }
    result = predictor.predict({
        "probed": True,
        "success": True,
        "binding_complete": True,
        "tool_kind": "lookup",
        "tool": profile["tool"],
        "profile_id": profile["profile_id"],
        "provider_profile": profile,
        "result": {
            "profile": {
                "public_bio": "Old bio",
                "saved_bio_draft": "New public bio",
            }
        },
    })
    assert result["proposition_specific"] == "INVESTIGATE"


def test_complete_profile_can_authorize_task_act() -> None:
    profile = {
        "profile_id": "single-action/v1",
        "tool": "settings.get",
        "decision_scope": {
            "intervention": "apply_single_setting",
            "task_coverage": "complete",
        },
        "propositions": [
            {
                "id": "change_needed",
                "kind": "fields_differ",
                "left_path": "current",
                "right_path": "desired",
                "authority": "complete_result_field",
            }
        ],
    }
    result = predictor.predict({
        "probed": True,
        "success": True,
        "binding_complete": True,
        "tool_kind": "lookup",
        "tool": "settings.get",
        "profile_id": "single-action/v1",
        "provider_profile": profile,
        "result": {"current": "old", "desired": "new"},
    })
    assert result["proposition_specific"] == "ACT"


def test_profiled_public_bio_abstains_on_explicit_prohibition() -> None:
    profile = {
        "profile_id": "personal-profile-public-bio/v1",
        "tool": "personal_profile_and_contacts.get_profile_draft_and_contact",
        "propositions": [
            {
                "id": "bio_change_needed",
                "kind": "fields_differ",
                "left_path": "profile.public_bio",
                "right_path": "profile.saved_bio_draft",
                "authority": "complete_result_field",
            },
            {
                "id": "no_explicit_publication_prohibition",
                "kind": "forbidden_markers_absent",
                "path": "profile.saved_bio_draft",
                "markers": ["NOT FOR PUBLIC PROFILE"],
                "authority": "complete_result_field",
            },
        ],
    }
    result = predictor.predict({
        "probed": True,
        "success": True,
        "binding_complete": True,
        "tool_kind": "lookup",
        "tool": profile["tool"],
        "profile_id": profile["profile_id"],
        "provider_profile": profile,
        "result": {
            "profile": {
                "public_bio": "Old bio",
                "saved_bio_draft": "NOT FOR PUBLIC PROFILE — confidential shelter address",
            }
        },
    })
    assert result["proposition_specific"] == "ABSTAIN"


def test_blind_predictor_has_no_gold_or_hidden_state_dependencies() -> None:
    source = MODULE.read_text(encoding="utf-8")
    forbidden = {
        "AntiQuality",
        "agentabstain",
        "BaseAgent",
        "TaskBundle",
        "task_type",
        "execution_dag",
        "abstention_trigger",
        "critical_actions",
        "initial_states",
        "raw_state",
    }
    for token in forbidden:
        assert token not in source, f"blind predictor leaked forbidden token: {token}"


def test_blind_predictor_cli_runs_in_minimal_subprocess(tmp_path: Path) -> None:
    observation_path = tmp_path / "observation.json"
    out_path = tmp_path / "prediction.json"
    observation_path.write_text(
        json.dumps({
            "probed": True,
            "success": False,
            "binding_complete": True,
            "tool_kind": "verify",
            "provider_profile": None,
        }),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(MODULE),
            "--observation",
            str(observation_path),
            "--out",
            str(out_path),
        ],
        check=True,
        cwd=str(tmp_path),
        env={
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["failure_only"] == "ABSTAIN"
    assert result["probe_success"] == "ABSTAIN"
    assert result["proposition_specific"] == "INVESTIGATE"
