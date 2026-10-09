#!/usr/bin/env python3
"""Gold-blind selection logic for AgentAbstain runtime probes.

This program intentionally has no AgentAbstain imports and receives no task
metadata, task type, raw state, dataset path, or gold labels. Its complete
input is a sanitized JSON tool catalog prepared by the trusted harness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import re


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) >= 3}


def choose_zero_arg_probe(
    tool_catalog: list[dict[str, Any]],
    instruction: str = "",
) -> dict[str, Any] | None:
    """Choose one deterministic zero-argument probe from the visible surface.

    Instruction overlap is only a relevance heuristic; it does not infer the
    benchmark label and never receives hidden task metadata.
    """

    instruction_tokens = _tokens(instruction)
    candidates: list[tuple[int, str, dict[str, Any]]] = []
    for tool in tool_catalog:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        input_schema = tool.get("input_schema") or {}
        if not isinstance(name, str) or not name:
            continue
        if not isinstance(input_schema, dict):
            continue
        required = input_schema.get("required") or []
        if required:
            continue
        projected = {
            "name": name,
            "description": str(tool.get("description") or ""),
            "input_schema": input_schema,
        }
        tool_tokens = _tokens(name.replace(".", " ").replace("_", " "))
        tool_tokens |= _tokens(projected["description"])
        score = len(instruction_tokens & tool_tokens)
        candidates.append((score, name, projected))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.catalog.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        catalog = payload
        instruction = ""
    elif isinstance(payload, dict):
        catalog = payload.get("tools")
        instruction = payload.get("instruction") or ""
    else:
        raise ValueError("catalog input must be a JSON list or object")

    if not isinstance(catalog, list) or not isinstance(instruction, str):
        raise ValueError("invalid blind selector input")

    selected = choose_zero_arg_probe(catalog, instruction)
    args.out.write_text(
        json.dumps(selected, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
