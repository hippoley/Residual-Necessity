#!/usr/bin/env python3
"""Deterministic, auditable binding of instruction facts to probe arguments.

JSON Schema answers whether a tool call is syntactically valid. A binding
profile answers a different question: which argument fields must be grounded
for this tool result to bear on a particular proposition.

Models may eventually propose candidate bindings, but this reference binder
only accepts explicit extractors and returns provenance for every bound field.
Missing semantic bindings remain incomplete rather than being defaulted.
"""

from __future__ import annotations

import re
from typing import Any


def _coerce(value: str, schema: dict[str, Any]) -> Any:
    typ = schema.get("type")
    if isinstance(typ, list):
        types = [x for x in typ if x != "null"]
        typ = types[0] if len(types) == 1 else None

    if typ == "integer":
        return int(value)
    if typ == "number":
        return float(value)
    if typ == "boolean":
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
        raise ValueError(f"cannot coerce boolean from {value!r}")
    return value


def _extract_regex(
    instruction: str,
    *,
    field_schema: dict[str, Any],
    spec: dict[str, Any],
) -> tuple[Any, dict[str, Any]] | None:
    pattern = spec.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        raise ValueError("regex extractor requires non-empty pattern")
    flags = re.IGNORECASE if spec.get("ignore_case", True) else 0
    match = re.search(pattern, instruction, flags)
    if not match:
        return None

    group = spec.get("group", "value")
    try:
        raw = match.group(group)
    except (IndexError, KeyError):
        if group == "value" and match.lastindex:
            raw = match.group(1)
        else:
            raise ValueError(f"regex extractor group not found: {group!r}")

    value = _coerce(raw, field_schema)
    start, end = match.span(group if group != "value" or "value" in match.groupdict() else 1)
    return value, {
        "extractor": "regex",
        "span": [start, end],
        "text": instruction[start:end],
    }


def _extract_enum_literal(
    instruction: str,
    *,
    field_schema: dict[str, Any],
    spec: dict[str, Any],
) -> tuple[Any, dict[str, Any]] | None:
    values = spec.get("values")
    if values is None:
        values = field_schema.get("enum")
    if not isinstance(values, list) or not values:
        raise ValueError("enum_literal extractor requires values or schema enum")

    matches: list[tuple[Any, int, int]] = []
    lowered = instruction.lower()
    for value in values:
        if not isinstance(value, (str, int, float, bool)):
            continue
        needle = str(value)
        start = lowered.find(needle.lower())
        if start >= 0:
            matches.append((value, start, start + len(needle)))

    if len(matches) != 1:
        return None

    value, start, end = matches[0]
    return value, {
        "extractor": "enum_literal",
        "span": [start, end],
        "text": instruction[start:end],
    }


def bind(
    *,
    instruction: str,
    tool: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Bind one tool call under an explicit semantic profile."""

    if not isinstance(instruction, str):
        raise ValueError("instruction must be a string")
    if not isinstance(tool, dict) or not isinstance(profile, dict):
        raise ValueError("tool/profile must be objects")

    tool_name = tool.get("name")
    if profile.get("tool") != tool_name:
        raise ValueError("binding profile tool mismatch")

    schema = tool.get("input_schema") or {}
    properties = schema.get("properties") or {}
    if not isinstance(properties, dict):
        raise ValueError("tool input_schema.properties must be an object")

    required_fields = profile.get("required_fields") or []
    if (
        not isinstance(required_fields, list)
        or not all(isinstance(x, str) and x for x in required_fields)
        or len(required_fields) != len(set(required_fields))
    ):
        raise ValueError("profile required_fields must be unique non-empty strings")

    extractors = profile.get("extractors") or {}
    if not isinstance(extractors, dict):
        raise ValueError("profile extractors must be an object")

    unknown_fields = [field for field in required_fields if field not in properties]
    if unknown_fields:
        raise ValueError(
            "profile references fields absent from tool schema: "
            + ", ".join(sorted(unknown_fields))
        )

    arguments: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    unbound: list[str] = []

    for field in required_fields:
        spec = extractors.get(field)
        if not isinstance(spec, dict):
            unbound.append(field)
            continue

        kind = spec.get("kind")
        if kind == "regex":
            extracted = _extract_regex(
                instruction,
                field_schema=properties[field],
                spec=spec,
            )
        elif kind == "enum_literal":
            extracted = _extract_enum_literal(
                instruction,
                field_schema=properties[field],
                spec=spec,
            )
        else:
            raise ValueError(f"unsupported binding extractor: {kind!r}")

        if extracted is None:
            unbound.append(field)
            continue

        value, evidence = extracted
        arguments[field] = value
        provenance[field] = evidence

    return {
        "tool": tool_name,
        "profile_id": profile.get("profile_id"),
        "arguments": arguments,
        "bound_fields": sorted(arguments),
        "unbound_fields": sorted(unbound),
        "binding_complete": not unbound,
        "provenance": provenance,
    }
