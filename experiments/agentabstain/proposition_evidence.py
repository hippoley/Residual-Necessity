#!/usr/bin/env python3
"""Conservative proposition-evidence boundary for AgentAbstain probes.

This is intentionally stricter than the historical generic baselines.
A tool result is not proposition evidence merely because a read/verify call
ran successfully. Before any provider-specific profile exists, incomplete
argument binding, lookup-only observations, tool failures, and unprofiled
verify results remain UNKNOWN.
"""

from __future__ import annotations

from typing import Any


def classify(observation: dict[str, Any]) -> dict[str, str]:
    if observation.get("probed") is not True:
        return {"status": "UNKNOWN", "reason": "no_probe"}

    if observation.get("binding_complete") is not True:
        return {"status": "UNKNOWN", "reason": "incomplete_argument_binding"}

    if observation.get("tool_kind") != "verify":
        return {"status": "UNKNOWN", "reason": "lookup_is_not_proposition_authority"}

    if observation.get("success") is not True:
        return {"status": "UNKNOWN", "reason": "verification_tool_unavailable"}

    return {"status": "UNKNOWN", "reason": "no_explicit_provider_profile"}


def permits_decision(status: str) -> bool:
    """Only explicit TRUE/FALSE from a future provider profile may decide."""
    return status in {"TRUE", "FALSE"}
