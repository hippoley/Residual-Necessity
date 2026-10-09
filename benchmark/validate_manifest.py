#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"benchmark"/"manifest.json"

def validate(data: dict) -> list[str]:
    errors=[]
    if data.get("schema_version")!="residual-necessity-benchmark/0.1":
        errors.append("unsupported benchmark schema_version")
    tracks=data.get("tracks")
    if not isinstance(tracks,list) or not tracks:
        errors.append("tracks must be non-empty")
        return errors
    ids=set()
    for track in tracks:
        tid=track.get("id")
        if not isinstance(tid,str) or not tid:
            errors.append("track missing id")
            continue
        if tid in ids:
            errors.append(f"duplicate track id: {tid}")
        ids.add(tid)
        if not track.get("purpose"):
            errors.append(f"{tid}: missing purpose")
        if not isinstance(track.get("metrics"),list) or not track["metrics"]:
            errors.append(f"{tid}: missing metrics")
        source=track.get("source")
        if not isinstance(source,dict) or not source.get("name"):
            errors.append(f"{tid}: missing source provenance")
        if not track.get("authority_rule"):
            errors.append(f"{tid}: missing authority rule")

    agg=data.get("aggregation") or {}
    if agg.get("single_total_score") is not False:
        errors.append("single aggregate score must remain disabled")

    by_id={x["id"]:x for x in tracks if isinstance(x,dict) and "id" in x}
    runtime=by_id.get("A-runtime-necessity",{})
    split=runtime.get("split") or {}
    if split.get("development_pairs",0)+split.get("holdout_pairs",0)!=97:
        errors.append("AgentAbstain split must cover all 97 pairs")
    methods=runtime.get("methods") or {}
    if methods.get("candidate_partition")!="development":
        errors.append("candidate method must remain development-only before reveal")
    if methods.get("holdout_reveal_requires_frozen_method") is not True:
        errors.append("holdout reveal must require frozen method")

    support=by_id.get("C-evidence-support-boundary",{})
    if "constraint" not in str(support.get("authority_rule","")).lower():
        errors.append("SafeAct track must preserve constraint-only boundary")
    return errors

if __name__=="__main__":
    data=json.loads(PATH.read_text(encoding="utf-8"))
    errors=validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"BENCHMARK_MANIFEST=PASS tracks={len(data['tracks'])}")
