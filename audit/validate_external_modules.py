#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"audit"/"external_modules.json"

def validate(data: dict) -> list[str]:
    errors=[]
    if data.get("schema_version")!="external-modules/0.1":
        errors.append("unsupported external module registry schema")
    modules=data.get("modules")
    if not isinstance(modules,list) or not modules:
        return errors+["modules must be a non-empty list"]

    ids=set()
    for module in modules:
        mid=module.get("id")
        if not isinstance(mid,str) or not mid:
            errors.append("module missing id")
            continue
        if mid in ids:
            errors.append(f"duplicate module id: {mid}")
        ids.add(mid)

        for field in ("source","pin","integration_role","local_glue","workflow","failure_policy"):
            if not module.get(field):
                errors.append(f"{mid}: missing {field}")

        local_glue=module.get("local_glue")
        workflow=module.get("workflow")
        if isinstance(local_glue,str) and not (ROOT/local_glue).exists():
            errors.append(f"{mid}: local_glue path missing: {local_glue}")
        if isinstance(workflow,str) and not (ROOT/workflow).exists():
            errors.append(f"{mid}: workflow path missing: {workflow}")

        boundary=module.get("semantic_boundary")
        if not isinstance(boundary,dict) or not boundary:
            errors.append(f"{mid}: semantic_boundary required")

    safeact=next((x for x in modules if x.get("id")=="safeact-contract"),None)
    if safeact is None:
        errors.append("safeact-contract external module entry required")
    else:
        if safeact.get("upstream_module")!="scripts/safeact_contract.py":
            errors.append("SafeAct must delegate protocol semantics to scripts/safeact_contract.py")
        if safeact.get("code_license")!="MIT":
            errors.append("SafeAct code license must remain MIT")
        if safeact.get("data_license")!="CC BY 4.0":
            errors.append("SafeAct data license must remain CC BY 4.0")
        forbidden=set((safeact.get("semantic_boundary") or {}).get("forbidden_mapping") or [])
        required={
            "SafeAct action support -> RN necessity",
            "SafeAct MISSING/DEFER -> RN FALSE/negative authority",
        }
        if not required.issubset(forbidden):
            errors.append("SafeAct semantic boundary lost required forbidden mappings")

    cel_entry=next((x for x in modules if x.get("id")=="cel-expression-engine"),None)
    if cel_entry is None:
        errors.append("cel-expression-engine external module entry required")
    else:
        if cel_entry.get("pin")!="cel-expr-python==0.1.3":
            errors.append("CEL provider runtime must remain pinned to cel-expr-python==0.1.3")
        if cel_entry.get("code_license")!="Apache-2.0":
            errors.append("CEL provider runtime license must remain Apache-2.0")
        forbidden=set((cel_entry.get("semantic_boundary") or {}).get("forbidden_mapping") or [])
        required={
            "CEL expression success -> authority without provider profile",
            "CEL runtime error -> FALSE",
            "non-boolean CEL result -> proposition truth",
        }
        if not required.issubset(forbidden):
            errors.append("CEL semantic boundary lost required forbidden mappings")

    return errors

if __name__=="__main__":
    data=json.loads(PATH.read_text(encoding="utf-8"))
    errors=validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"EXTERNAL_MODULE_REGISTRY=PASS modules={len(data['modules'])}")
