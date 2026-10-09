#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "experiments" / "agentabstain" / "probe_binding_profiles.json"
SCHEMA = ROOT / "benchmark" / "provider_profile_registry.schema.json"


def validate(registry: dict, schema: dict) -> list[str]:
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(registry), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(x) for x in err.absolute_path)
        errors.append(f"schema:{path}: {err.message}")

    profiles = registry.get("profiles")
    if not isinstance(profiles, list):
        return errors

    profile_ids: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        pid = profile.get("profile_id")
        if isinstance(pid, str):
            if pid in profile_ids:
                errors.append(f"duplicate profile_id: {pid}")
            profile_ids.add(pid)

        required = profile.get("required_fields") or []
        extractors = profile.get("extractors") or {}
        if isinstance(required, list) and isinstance(extractors, dict):
            extra_extractors = sorted(set(extractors) - set(required))
            if extra_extractors:
                errors.append(
                    f"{pid}: extractors reference non-required fields {extra_extractors}"
                )

        propositions = profile.get("propositions") or []
        proposition_ids: set[str] = set()
        for proposition in propositions:
            if not isinstance(proposition, dict):
                continue
            proposition_id = proposition.get("id")
            if isinstance(proposition_id, str):
                if proposition_id in proposition_ids:
                    errors.append(
                        f"{pid}: duplicate proposition id {proposition_id}"
                    )
                proposition_ids.add(proposition_id)

        source = profile.get("source") or {}
        if isinstance(source, dict):
            version = source.get("version_or_commit")
            if not isinstance(version, str) or not version:
                errors.append(f"{pid}: external source must be pinned")

        non_claims = profile.get("non_claims")
        if not isinstance(non_claims, list) or not non_claims:
            errors.append(f"{pid}: non_claims required")

    return errors


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = validate(registry, schema)
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"PROVIDER_PROFILE_REGISTRY=PASS profiles={len(registry.get('profiles', []))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
