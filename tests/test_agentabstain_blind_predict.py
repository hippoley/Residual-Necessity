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
    }


def test_failed_probe_abstains_in_both_baselines() -> None:
    result = predictor.predict({"probed": True, "success": False})
    assert result == {
        "failure_only": "ABSTAIN",
        "probe_success": "ABSTAIN",
    }


def test_successful_probe_separates_conservative_and_symmetric_baselines() -> None:
    result = predictor.predict({"probed": True, "success": True})
    assert result["failure_only"] == "INVESTIGATE"
    assert result["probe_success"] == "ACT"


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
        json.dumps({"probed": True, "success": False}),
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
