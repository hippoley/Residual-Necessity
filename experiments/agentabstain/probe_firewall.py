#!/usr/bin/env python3
"""Deterministic AgentAbstain read-only probe firewall.

The planner sees only sanitized lookup/verify tool schemas. The executor owns
the hidden runtime locator and independently re-checks the live tool kind
before every call. Neither layer reads raw environment state.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


SAFE_KINDS = {"lookup", "verify"}
MAX_CALLS_PER_CASE = 4


def jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return jsonable(value.to_dict())
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return jsonable(value.model_dump())
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def apply_runtime_surface(bundle: Any, menv: Any) -> set[str] | None:
    """Apply task-visible broken/hidden tool behavior without reading state."""
    for broken in bundle.task_yaml.get("tool_overrides", {}).get("broken_tools", []):
        menv.break_tool(broken["name"], broken.get("error", "Service unavailable"))

    available = bundle.task_yaml.get("available_tools")
    if available is None:
        return None

    allowed = {item["name"] if isinstance(item, dict) else item for item in available}
    for schema in menv.get_tool_schemas():
        if schema["name"] not in allowed:
            menv.hide_tool(schema["name"])
    return allowed


def sanitized_safe_surface(menv: Any, allowed: set[str] | None) -> list[dict[str, Any]]:
    """Return only agent-visible read/verify tool metadata."""
    out: list[dict[str, Any]] = []
    for schema in menv.get_tool_schemas():
        name = str(schema.get("name"))
        if allowed is not None and name not in allowed:
            continue
        kind = menv.tool_kinds.get(name, schema.get("kind"))
        if kind not in SAFE_KINDS:
            continue
        out.append(
            {
                "name": name,
                "kind": kind,
                "description": schema.get("description"),
                "input_schema": schema.get("input_schema") or {},
            }
        )
    return out


def validate_planned_call(
    call: dict[str, Any],
    *,
    live_schemas: dict[str, dict[str, Any]],
    live_kinds: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    """Fail closed unless the requested call is currently visible and read-only."""
    if not isinstance(call, dict):
        raise ValueError("planned call must be an object")

    tool = call.get("tool")
    args = call.get("args", {})
    if not isinstance(tool, str) or not tool:
        raise ValueError("planned call requires non-empty tool")
    if not isinstance(args, dict):
        raise ValueError("planned call args must be an object")

    schema = live_schemas.get(tool)
    if schema is None:
        raise ValueError(f"tool is not visible in this runtime: {tool}")

    kind = live_kinds.get(tool, str(schema.get("kind") or ""))
    if kind not in SAFE_KINDS:
        raise ValueError(f"tool kind is not read-only: {tool}={kind}")

    return tool, args


def load_agentabstain_case(
    *,
    agentabstain_root: Path,
    data_dir: Path,
    locator: dict[str, Any],
) -> tuple[Any, Any, set[str] | None]:
    """Mount one hidden runtime variant.

    The locator is executor-only. This function intentionally returns the
    environment object but callers must interact with it through tool methods,
    never through its raw state attribute.
    """
    os.environ["AGENTABSTAIN_DATA"] = str(data_dir)
    root = str(agentabstain_root.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)

    from src.types.BaseAgent import BaseAgent
    from abstention_factory.runtime.multi import build_multi_environment

    bundle = BaseAgent.load_task_bundle(
        locator["category"],
        locator["task_id"],
        locator["task_type"],
    )
    menv = build_multi_environment(bundle.env_types, bundle.initial_states)
    allowed = apply_runtime_surface(bundle, menv)
    return bundle, menv, allowed


def execute_case_plan(
    *,
    menv: Any,
    allowed: set[str] | None,
    calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(calls) > MAX_CALLS_PER_CASE:
        raise ValueError(
            f"probe plan exceeds max calls per case ({MAX_CALLS_PER_CASE})"
        )

    schemas = {
        str(schema["name"]): schema
        for schema in menv.get_tool_schemas()
        if allowed is None or schema["name"] in allowed
    }

    observations: list[dict[str, Any]] = []
    for call in calls:
        tool, args = validate_planned_call(
            call,
            live_schemas=schemas,
            live_kinds=menv.tool_kinds,
        )
        success = True
        error = None
        result: Any = None
        try:
            result = menv.call_tool(tool, **args)
        except Exception as exc:  # runtime failure is observable evidence
            success = False
            error = f"{type(exc).__name__}: {exc}"

        observations.append(
            {
                "tool": tool,
                "tool_kind": menv.tool_kinds.get(tool),
                "args": jsonable(args),
                "success": success,
                "error": error,
                "result": jsonable(result),
            }
        )

    for entry in menv.get_execution_log():
        executed = str(entry.get("tool"))
        if menv.tool_kinds.get(executed) not in SAFE_KINDS:
            raise AssertionError(
                f"non-read-only tool reached execution log: "
                f"{executed}={menv.tool_kinds.get(executed)}"
            )

    return observations


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
