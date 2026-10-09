#!/usr/bin/env python3
"""Run gold-blind runtime-evidence baselines over AgentAbstain runtime variants.

The trusted harness may know benchmark variant identity so it can instantiate
the public sandbox. Probe selection and prediction are delegated to separate
blind subprocesses that receive only sanitized inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.agentabstain.prepare_runtime_blind_slice import (
    ALLOWED_RUNTIME_CATEGORIES,
    load_jsonl,
)
from experiments.agentabstain.freeze_pair_split import assign as split_assignment
from experiments.agentabstain.probe_runtime_observation import (
    SAFE_KINDS,
    _apply_runtime_surface,
    _jsonable,
    _safe_catalog,
    _select_in_blind_subprocess,
    _load_binding_profiles,
)


BLIND_PREDICTOR = Path(__file__).resolve().with_name("blind_predict.py")


def _opaque_pair_id(value: str) -> str:
    return "pair_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _opaque_case_id(pair_id: str, task_type: str) -> str:
    raw = f"{pair_id}:{task_type}"
    return "case_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _predict_in_blind_subprocess(observation: dict[str, Any]) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="rn-blind-predict-") as tmp:
        tmp_path = Path(tmp)
        observation_path = tmp_path / "observation.json"
        out_path = tmp_path / "prediction.json"
        observation_path.write_text(
            json.dumps(observation, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(BLIND_PREDICTOR),
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
        value = json.loads(out_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("blind predictor output must be an object")
        allowed = {"failure_only", "probe_success", "proposition_specific"}
        if set(value) != allowed:
            raise ValueError(f"unexpected blind predictor keys: {sorted(value)}")
        for prediction in value.values():
            if prediction not in {"ACT", "ABSTAIN", "INVESTIGATE"}:
                raise ValueError(f"invalid prediction: {prediction!r}")
        return value


def _runtime_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("phase") != "runtime":
            continue
        if row.get("category") not in ALLOWED_RUNTIME_CATEGORIES:
            continue
        if row.get("task_type") not in {"act", "abstain"}:
            raise ValueError("runtime row missing task_type")
        if not isinstance(row.get("pair_id"), str):
            raise ValueError("runtime row missing pair_id")
        if not isinstance(row.get("task_id"), str):
            raise ValueError("runtime row missing task_id")
        out.append(row)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agentabstain-root", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tasks-jsonl", type=Path, required=True)
    parser.add_argument("--predictions-out", type=Path, required=True)
    parser.add_argument("--labels-out", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    parser.add_argument("--development-observations-out", type=Path)
    parser.add_argument("--development-labels-out", type=Path)
    args = parser.parse_args()

    os.environ["AGENTABSTAIN_DATA"] = str(args.data_dir)
    sys.path.insert(0, str(args.agentabstain_root.resolve()))

    from src.types.BaseAgent import BaseAgent
    from abstention_factory.runtime.multi import build_multi_environment

    predictions: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    probed_count = 0
    successful_probe_count = 0
    failed_probe_count = 0
    development_observations: list[dict[str, Any]] = []
    development_labels: list[dict[str, Any]] = []
    profiles = _load_binding_profiles()

    for row in _runtime_rows(load_jsonl(args.tasks_jsonl)):
        category = str(row["category"])
        task_id = str(row["task_id"])
        task_type = str(row["task_type"])
        pair_id = str(row["pair_id"])
        instruction = str(row.get("instruction") or "")

        bundle = BaseAgent.load_task_bundle(category, task_id, task_type)
        menv = build_multi_environment(bundle.env_types, bundle.initial_states)
        allowed = _apply_runtime_surface(bundle, menv)

        catalog = _safe_catalog(menv, allowed)
        selected = _select_in_blind_subprocess(catalog, instruction, profiles)

        observation: dict[str, Any]
        selected_tool: str | None = None
        observed_kind: str | None = None

        if selected is None:
            observation = {
                "probed": False,
                "success": None,
                "error": None,
                "result": None,
                "arguments": {},
                "profile_id": None,
                "provider_profile": None,
                "binding_complete": False,
                "unbound_fields": [],
            }
        else:
            selected_tool = str(selected["name"])
            arguments = selected.get("arguments") or {}
            if not isinstance(arguments, dict):
                raise ValueError("blind selector arguments must be an object")
            binding_complete = selected.get("binding_complete") is True
            unbound_fields = selected.get("unbound_fields") or []
            if not isinstance(unbound_fields, list):
                raise ValueError("blind selector unbound_fields must be a list")

            success = True
            error = None
            result: Any = None
            try:
                result = menv.call_tool(selected_tool, **arguments)
            except Exception as exc:
                success = False
                error = f"{type(exc).__name__}: {exc}"

            log = menv.get_execution_log()
            if not log:
                raise AssertionError(f"probe produced no execution log: {selected_tool}")

            observed_tool = str(log[-1].get("tool"))
            observed_kind = menv.tool_kinds.get(observed_tool)
            if observed_kind not in SAFE_KINDS:
                raise AssertionError(
                    f"blind-selected tool is not read-only: {observed_tool}={observed_kind}"
                )
            if any(
                menv.tool_kinds.get(str(entry.get("tool"))) == "commit"
                for entry in log
            ):
                raise AssertionError("commit-class tool appeared in batch probe log")

            probed_count += 1
            if success:
                successful_probe_count += 1
            else:
                failed_probe_count += 1

            observation = {
                "probed": True,
                "success": success,
                "error": error,
                "result": _jsonable(result),
                "tool": observed_tool,
                "tool_kind": observed_kind,
                "arguments": arguments,
                "profile_id": selected.get("profile_id"),
                "provider_profile": selected.get("provider_profile"),
                "binding_complete": binding_complete,
                "unbound_fields": unbound_fields,
            }

        blind_predictions = _predict_in_blind_subprocess(observation)

        opaque_pair = _opaque_pair_id(pair_id)
        case_id = _opaque_case_id(pair_id, task_type)
        predictions.append(
            {
                "case_id": case_id,
                "pair_id": opaque_pair,
                "probed": observation["probed"],
                "tool": selected_tool,
                "tool_kind": observed_kind,
                "profile_id": observation.get("profile_id"),
                "binding_complete": observation.get("binding_complete") is True,
                "unbound_fields": observation.get("unbound_fields") or [],
                "failure_only": blind_predictions["failure_only"],
                "probe_success": blind_predictions["probe_success"],
                "proposition_specific": blind_predictions["proposition_specific"],
            }
        )

        if split_assignment(opaque_pair) == "development":
            development_observations.append(
                {
                    "case_id": case_id,
                    "pair_id": opaque_pair,
                    "instruction": instruction,
                    "probed": observation["probed"],
                    "tool": selected_tool,
                    "tool_kind": observed_kind,
                    "success": observation.get("success"),
                    "error": observation.get("error"),
                    "result": observation.get("result"),
                    "arguments": observation.get("arguments") or {},
                    "profile_id": selected.get("profile_id") if selected else None,
                    "binding_provenance": selected.get("provenance") if selected else {},
                    "binding_complete": observation.get("binding_complete") is True,
                    "unbound_fields": observation.get("unbound_fields") or [],
                    "input_schema": selected.get("input_schema") if selected else None,
                }
            )
            development_labels.append(
                {
                    "case_id": case_id,
                    "pair_id": opaque_pair,
                    "task_type": task_type,
                }
            )

        labels.append(
            {
                "case_id": case_id,
                "pair_id": opaque_pair,
                "task_type": task_type,
            }
        )

    args.predictions_out.write_text(
        json.dumps(predictions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.labels_out.write_text(
        json.dumps(labels, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if args.development_observations_out is not None:
        args.development_observations_out.write_text(
            json.dumps(development_observations, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.development_labels_out is not None:
        args.development_labels_out.write_text(
            json.dumps(development_labels, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    summary = {
        "runtime_variants": len(predictions),
        "runtime_pairs": len({row["pair_id"] for row in labels}),
        "probed_variants": probed_count,
        "probe_coverage": (probed_count / len(predictions)) if predictions else 0.0,
        "successful_probes": successful_probe_count,
        "failed_probes": failed_probe_count,
        "blind_selector_process": True,
        "blind_predictor_process": True,
        "development_variants_exported": len(development_observations),
        "holdout_observation_payload_exported": False,
    }
    args.summary_out.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
