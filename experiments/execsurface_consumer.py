from __future__ import annotations

from typing import Any

CAPABILITY = "fd_read_write_effect"
EXPECTED_PROFILE = "linux-ptrace-metadata-v2"
KNOWN_HEALTH = {
    "complete",
    "incomplete_loss",
    "incomplete_limit",
    "incomplete_capability",
    "incomplete_ambiguity",
    "error",
}


def _warning_codes(raw_observation: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    for warning in raw_observation.get("warnings") or []:
        if isinstance(warning, dict):
            code = warning.get("code")
            if isinstance(code, str) and code:
                codes.add(code)
    return codes


def validate_typed_evidence(report: dict[str, Any]) -> None:
    if report.get("schema_version") != 1:
        raise ValueError("unsupported schema")
    if report.get("report_kind") != "typed_observation_evidence":
        raise ValueError("unexpected report kind")
    if report.get("stability") != "experimental":
        raise ValueError("unexpected stability")

    backend = report.get("backend")
    if not isinstance(backend, dict) or backend.get("profile") != EXPECTED_PROFILE:
        raise ValueError("unsupported backend profile")

    health = report.get("collection_health")
    if not isinstance(health, dict):
        raise ValueError("missing collection health")
    state = health.get("state")
    if state not in KNOWN_HEALTH:
        raise ValueError("unknown collection health state")

    raw = report.get("raw_observation")
    if not isinstance(raw, dict) or raw.get("schema_version") != 2:
        raise ValueError("missing or unsupported raw observation")

    raw_backend = raw.get("backend")
    if not isinstance(raw_backend, dict) or raw_backend.get("name") != EXPECTED_PROFILE:
        raise ValueError("typed/raw backend mismatch")

    raw_complete = raw.get("complete")
    if not isinstance(raw_complete, bool):
        raise ValueError("raw observation completeness missing")
    if (state == "complete") != raw_complete:
        raise ValueError("collection health contradicts raw completeness")

    typed_codes = set(health.get("warning_codes") or [])
    raw_codes = _warning_codes(raw)
    if typed_codes != raw_codes:
        raise ValueError("typed/raw warning codes disagree")

    nonclaims = set(report.get("does_not_assert") or [])
    if "policy_verdict" not in nonclaims:
        raise ValueError("typed evidence must disclaim policy verdict authority")


def target_write_observation(
    report: dict[str, Any],
    effect_target: str,
    *,
    predicate_id: str,
    target_identity: str,
    target_revision: str | None = None,
) -> dict[str, Any]:
    validate_typed_evidence(report)

    health = report["collection_health"]
    if health["state"] != "complete":
        return {
            "status": "UNKNOWN",
            "reason": f"collection_health={health['state']}",
        }

    unsupported = set(report.get("unsupported_capabilities") or [])
    if CAPABILITY in unsupported:
        return {"status": "UNKNOWN", "reason": "unsupported capability"}

    effects = report.get("effects")
    if not isinstance(effects, list):
        raise ValueError("effects must be a list")

    for effect in effects:
        if not isinstance(effect, dict):
            continue
        if (
            effect.get("proposition") == "file_fd_write_effect_observed"
            and effect.get("target") == effect_target
        ):
            scope = {
                "predicate_id": predicate_id,
                "target_identity": target_identity,
            }
            if target_revision is not None:
                scope["target_revision"] = target_revision

            return {
                "status": "TRUE",
                "reason": "matching effect observed",
                "source": "execsurface:typed_observation_evidence",
                "positive_authority": {
                    "scope": scope,
                    "basis": "matching_typed_runtime_effect",
                    "evidence_ref": (
                        f"execsurface:{report.get('backend', {}).get('implementation_version', 'unknown')}"
                    ),
                },
            }

    return {"status": "UNKNOWN", "reason": "absence is not negative evidence"}
