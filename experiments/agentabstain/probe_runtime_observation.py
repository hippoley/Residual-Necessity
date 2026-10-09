#!/usr/bin/env python3
"""Obtain one tool-visible AgentAbstain runtime observation without gold access.

Run this script inside a checkout of the public AgentAbstain repository.
The caller provides the dataset directory. The trusted harness instantiates the benchmark environment, but the blind
selector receives only a sanitized read-only tool catalog. The selector has no
AgentAbstain imports and no access to task type, task metadata, or raw state.
The harness verifies that no commit-class tool is executed.

It scans runtime-phase categories for the first task variant exposing a
zero-required-argument lookup/verify tool, calls exactly one such tool, and
emits a sanitized observation record with an opaque case id.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

BLIND_SELECTOR = Path(__file__).resolve().with_name("blind_probe.py")


RUNTIME_CATEGORIES = (
    "critical_tool_failure",
    "conflicting_evidence",
    "emergent_risk_discovery",
)
SAFE_KINDS = {"lookup", "verify"}


def _opaque(value: str) -> str:
    return "case_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _jsonable(value.model_dump())
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _apply_runtime_surface(bundle: Any, menv: Any) -> set[str] | None:
    for broken in bundle.task_yaml.get("tool_overrides", {}).get("broken_tools", []):
        menv.break_tool(broken["name"], broken.get("error", "Service unavailable"))

    available = bundle.task_yaml.get("available_tools")
    if available is None:
        return None

    allowed = {t["name"] if isinstance(t, dict) else t for t in available}
    for schema in menv.get_tool_schemas():
        if schema["name"] not in allowed:
            menv.hide_tool(schema["name"])
    return allowed


def _safe_catalog(menv: Any, allowed: set[str] | None) -> list[dict[str, Any]]:
    """Trusted-harness projection of the public read-only tool surface.

    Tool kind is used only here to prevent commit-class tools from reaching the
    blind selector. The projected catalog intentionally omits kind and all
    benchmark metadata.
    """
    out: list[dict[str, Any]] = []
    for schema in menv.get_tool_schemas():
        name = schema.get("name")
        if allowed is not None and name not in allowed:
            continue
        if schema.get("kind") not in SAFE_KINDS:
            continue
        out.append(
            {
                "name": name,
                "description": schema.get("description") or "",
                "input_schema": schema.get("input_schema") or {},
            }
        )
    return out



def _select_in_blind_subprocess(catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Run selector in a separate process with a deliberately minimal environment."""
    with tempfile.TemporaryDirectory(prefix="rn-blind-probe-") as tmp:
        tmp_path = Path(tmp)
        catalog_path = tmp_path / "catalog.json"
        out_path = tmp_path / "selected.json"
        catalog_path.write_text(
            json.dumps(catalog, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(BLIND_SELECTOR),
                "--catalog",
                str(catalog_path),
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
        selected = json.loads(out_path.read_text(encoding="utf-8"))
        if selected is not None and not isinstance(selected, dict):
            raise ValueError("blind selector output must be an object or null")
        return selected


def _iter_variants(data_dir: Path):
    tasks_root = data_dir / "tasks"
    for category in RUNTIME_CATEGORIES:
        category_dir = tasks_root / category
        if not category_dir.exists():
            continue
        for task_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            for task_type in ("act", "abstain"):
                variant = task_dir / task_type
                if variant.exists():
                    yield category, task_dir.name, task_type


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agentabstain-root", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    os.environ["AGENTABSTAIN_DATA"] = str(args.data_dir)
    sys.path.insert(0, str(args.agentabstain_root.resolve()))

    from src.types.BaseAgent import BaseAgent
    from abstention_factory.runtime.multi import build_multi_environment

    attempts: list[str] = []

    for category, task_id, task_type in _iter_variants(args.data_dir):
        bundle = BaseAgent.load_task_bundle(category, task_id, task_type)
        menv = build_multi_environment(bundle.env_types, bundle.initial_states)
        allowed = _apply_runtime_surface(bundle, menv)

        catalog = _safe_catalog(menv, allowed)
        selected = _select_in_blind_subprocess(catalog)
        if selected is None:
            attempts.append(f"{category}/{task_id}/{task_type}: no zero-arg safe tool")
            continue

        tool_name = str(selected["name"])

        success = True
        error = None
        result: Any = None
        try:
            result = menv.call_tool(tool_name)
        except Exception as exc:  # tool failure is itself runtime evidence
            success = False
            error = f"{type(exc).__name__}: {exc}"

        log = menv.get_execution_log()
        if not log:
            attempts.append(f"{tool_name}: no execution log")
            continue

        last = log[-1]
        observed_tool = str(last.get("tool"))
        observed_kind = menv.tool_kinds.get(observed_tool)
        if observed_kind not in SAFE_KINDS:
            raise AssertionError(
                f"probe executed forbidden tool kind: {observed_tool}={observed_kind}"
            )
        if any(menv.tool_kinds.get(str(entry.get("tool"))) == "commit" for entry in log):
            raise AssertionError("commit-class tool appeared in probe execution log")

        case_key = f"{category}/{task_id}/{task_type}"
        record = {
            "schema_version": "agentabstain-tool-probe/0.2",
            "case_id": _opaque(case_key),
            "tool": observed_tool,
            "tool_kind": observed_kind,
            "success": success,
            "error": error,
            "result": _jsonable(result),
            "execution_log_length": len(log),
            "selection_module": "blind_probe.py",
            "selection_process_isolated": True,
            "trusted_harness_knows_variant": True,
            "selection_process_isolated": True,
            "trusted_harness_knows_variant": True,
            "gold_fields_exposed_to_selector": False,
            "raw_state_exposed_to_selector": False,
        }
        args.out.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "case_id": record["case_id"],
            "tool": observed_tool,
            "tool_kind": observed_kind,
            "success": success,
            "gold_fields_exposed_to_selector": False,
            "raw_state_exposed_to_selector": False,
        }, sort_keys=True))
        return 0

    raise SystemExit(
        "no zero-required-argument lookup/verify probe found; attempts="
        + repr(attempts[:10])
    )


if __name__ == "__main__":
    raise SystemExit(main())
