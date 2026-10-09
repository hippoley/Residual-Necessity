#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cel_expr_python import cel


def validate(registry: dict) -> list[str]:
    errors: list[str] = []
    env = cel.NewEnv(variables={"result": cel.Type.DYN})
    for profile in registry.get("profiles") or []:
        if not isinstance(profile, dict):
            continue
        pid = profile.get("profile_id")
        for proposition in profile.get("propositions") or []:
            if not isinstance(proposition, dict) or proposition.get("kind") != "cel":
                continue
            expression = proposition.get("expression")
            prop_id = proposition.get("id")
            if not isinstance(expression, str) or not expression.strip():
                errors.append(f"{pid}/{prop_id}: CEL expression missing")
                continue
            try:
                env.compile(expression)
            except Exception as exc:
                errors.append(
                    f"{pid}/{prop_id}: CEL compile failed: "
                    f"{type(exc).__name__}: {exc}"
                )
    return errors


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--registry",type=Path,required=True)
    args=parser.parse_args()
    registry=json.loads(args.registry.read_text(encoding="utf-8"))
    errors=validate(registry)
    if errors:
        raise SystemExit("\n".join(errors))
    count=sum(
        1
        for profile in registry.get("profiles") or []
        for prop in profile.get("propositions") or []
        if isinstance(prop,dict) and prop.get("kind")=="cel"
    )
    print(f"CEL_PROVIDER_PROFILES=PASS expressions={count}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
