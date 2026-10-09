#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"benchmark"/"manifest.json"

def validate(data: dict) -> list[str]:
    errors=[]
    if data.get("schema_version")!="residual-necessity-benchmark/0.2":
        errors.append("unsupported benchmark schema_version")
    if data.get("benchmark_version")!="0.2":
        errors.append("benchmark_version must be 0.2")
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
    if split.get("category_coverage_required") is not True:
        errors.append("AgentAbstain split must require category coverage")
    if split.get("category_metadata_visible_to_inference") is not False:
        errors.append("trusted category metadata must remain hidden from inference")

    leakage=runtime.get("leakage_controls") or {}
    hidden=set(leakage.get("hidden_inference_fields") or [])
    required_hidden={
        "task_type","abstention_trigger","execution_dag","critical_actions",
        "category","transformation_dimension","task_id",
    }
    if not required_hidden.issubset(hidden):
        errors.append("runtime leakage controls missing required hidden fields")
    if leakage.get("opaque_pair_id") is not True:
        errors.append("runtime pair ids must remain opaque")
    if leakage.get("static_pair_equivalence_required") is not True:
        errors.append("runtime blind pairs must require static equivalence")
    if leakage.get("category_visible_only_to_trusted_scoring") is not True:
        errors.append("runtime category must remain scoring-only")
    if leakage.get("source_task_identity_visible_to_inference") is not False:
        errors.append("runtime task identity must remain hidden from inference")

    stats=runtime.get("statistics") or {}
    if stats.get("resampling_unit")!="pair_id":
        errors.append("runtime confidence intervals must resample pair_id")
    if stats.get("confidence_interval")!="pair_bootstrap_percentile":
        errors.append("runtime confidence interval method must be pair bootstrap")
    if stats.get("confidence_level")!=0.95:
        errors.append("runtime confidence level must be 0.95")
    if int(stats.get("bootstrap_samples",0)) < 1000:
        errors.append("runtime bootstrap must use at least 1000 samples")
    engine=runtime.get("provider_expression_engine") or {}
    if engine.get("implementation")!="cel-expr-python":
        errors.append("runtime provider expression engine must be cel-expr-python")
    if engine.get("version")!="0.1.3":
        errors.append("runtime CEL provider engine must remain pinned to 0.1.3")
    if engine.get("license")!="Apache-2.0":
        errors.append("runtime CEL provider engine license must remain Apache-2.0")
    if "never grants authority" not in str(engine.get("authority_boundary","")):
        errors.append("runtime CEL provider engine must preserve profile authority boundary")

    methods=runtime.get("methods") or {}
    reporting=runtime.get("reporting_policy") or {}
    required_headline={
        "paired_accuracy",
        "act_recall",
        "abstain_recall",
        "unnecessary_intervention_rate",
        "missed_required_action_rate",
        "decision_coverage",
        "two_sided_recall_geomean",
    }
    if not required_headline.issubset(set(reporting.get("headline_metrics") or [])):
        errors.append("runtime reporting policy missing required two-sided headline metrics")
    if reporting.get("category_stratification_required") is not True:
        errors.append("runtime scoring must require category stratification")
    if reporting.get("pair_outcome_taxonomy_required") is not True:
        errors.append("runtime scoring must require pair outcome taxonomy")
    if reporting.get("development_results_may_not_claim_benchmark_superiority") is not True:
        errors.append("development-only results must not support superiority claims")
    if reporting.get("superiority_requires_frozen_holdout_reveal") is not True:
        errors.append("superiority claim must require frozen holdout reveal")
    if "decisive_accuracy" not in set(reporting.get("diagnostic_only_metrics") or []):
        errors.append("decisive_accuracy must remain diagnostic-only")

    methods=runtime.get("methods") or {}
    if methods.get("candidate_partition")!="development":
        errors.append("candidate method must remain development-only before reveal")
    if methods.get("holdout_reveal_requires_frozen_method") is not True:
        errors.append("holdout reveal must require frozen method")

    residual=by_id.get("B-residual-partial-fix",{})
    corpus_inventory=residual.get("corpus_inventory") or {}
    if corpus_inventory.get("oracle_coverage_claim")!="none":
        errors.append("P3 corpus inventory must not imply global oracle coverage")
    if "partial fix" not in str(corpus_inventory.get("scope","")).lower():
        errors.append("P3 corpus inventory scope must be explicit")

    support=by_id.get("C-evidence-support-boundary",{})
    if "constraint" not in str(support.get("authority_rule","")).lower():
        errors.append("SafeAct track must preserve constraint-only boundary")
    corpus_audit=support.get("corpus_audit") or {}
    if corpus_audit.get("required") is not True:
        errors.append("SafeAct track must require corpus-level adapter audit")
    if "negative authority" not in str(corpus_audit.get("invariant","")).lower():
        errors.append("SafeAct corpus audit must prohibit negative-authority promotion")

    safeact_source=support.get("source") or {}
    if safeact_source.get("upstream_code_module")!="scripts/safeact_contract.py":
        errors.append("SafeAct track must delegate protocol semantics to upstream safeact_contract.py")
    if safeact_source.get("contract_id")!="safeact_evaluation_v1":
        errors.append("SafeAct track must pin safeact_evaluation_v1 contract")

    bias=support.get("necessity_signal_bias") or {}
    existing_execution=(bias.get("existing_execution") or {}).get("observed_values") or {}
    if set(existing_execution) - {"false"}:
        errors.append("SafeAct existing_execution bias metadata changed; re-audit before using as necessity data")
    policy=str(bias.get("benchmark_policy") or "")
    if "only for evidence/constraint grounding" not in policy:
        errors.append("SafeAct benchmark policy must remain constraint-grounding only")

    forbidden=set(support.get("forbidden_claims") or [])
    required_forbidden={
        "SafeAct SUPPORTED implies RN ACT",
        "SafeAct MISSING/DEFER implies RN FALSE or ABSTAIN",
        "SafeAct static corpus provides balanced necessity positives and negatives",
    }
    if not required_forbidden.issubset(forbidden):
        errors.append("SafeAct track missing required forbidden claims")
    return errors

if __name__=="__main__":
    data=json.loads(PATH.read_text(encoding="utf-8"))
    errors=validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"BENCHMARK_MANIFEST=PASS tracks={len(data['tracks'])}")
