from __future__ import annotations

from typing import Any

CAPABILITY = "fd_read_write_effect"


def target_write_observation(report: dict[str, Any], target: str) -> dict[str, str]:
    if report.get("schema_version") != 1:
        raise ValueError("unsupported schema")
    if report.get("report_kind") != "typed_observation_evidence":
        raise ValueError("unexpected report kind")
    if report.get("stability") != "experimental":
        raise ValueError("unexpected stability")

    health = report.get("collection_health")
    if not isinstance(health, dict):
        raise ValueError("missing collection health")

    if health.get("state") != "complete":
        return {"status": "UNKNOWN", "reason": "incomplete collection"}

    unsupported = set(report.get("unsupported_capabilities") or [])
    if CAPABILITY in unsupported:
        return {"status": "UNKNOWN", "reason": "unsupported capability"}

    effects = report.get("effects")
    if not isinstance(effects, list):
        raise ValueError("effects must be a list")

    for effect in effects:
        if not isinstance(effect, dict):
            continue
        if effect.get("proposition") == "file_fd_write_effect_observed" and effect.get("target") == target:
            return {"status": "TRUE", "reason": "matching effect observed"}

    return {"status": "UNKNOWN", "reason": "absence is not negative evidence"}
