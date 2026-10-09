from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load_module("safeact_adapter_e2e", ROOT / "experiments" / "safeact_adapter.py")
gate = load_module("residual_gate_safeact_e2e", ROOT / "src" / "gate.py")


def necessity_receipt(status: str = "TRUE") -> dict:
    observation = {"status": status}
    authority = {
        "scope": {
            "predicate_id": "residual_violation_exists",
            "target_identity": "safeact-demo:customer-action",
            "target_revision": "world:2026-08-02-customer-v13",
        },
        "basis": "independent_residual_probe",
        "evidence_ref": "sha256:independent-residual",
    }
    if status == "TRUE":
        observation["positive_authority"] = authority
    elif status == "FALSE":
        observation["negative_authority"] = authority

    return {
        "schema_version": "0.3",
        "intervention": {
            "id": "customer-action",
            "kind": "modify_state",
            "description": "execute only while a residual violation still exists",
            "justified_by": ["residual_violation_exists"],
        },
        "target": {
            "identity": "safeact-demo:customer-action",
            "revision": "world:2026-08-02-customer-v13",
        },
        "predicates": [
            {
                "id": "residual_violation_exists",
                "required": True,
                "kind": "reality",
                "role": "necessity",
            }
        ],
        "observations": {"residual_violation_exists": observation},
    }


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--safeact-root", type=Path, required=True)
    args = parser.parse_args()

    supported = load_json(
        args.safeact_root
        / "env/customer_policy_qa/materialized_evidence/SAB-V1-009.json"
    )
    deferred = load_json(
        args.safeact_root
        / "env/customer_policy_qa/materialized_evidence/SAB-V0-001.json"
    )

    target_identity = "safeact-demo:customer-action"
    target_revision = "world:2026-08-02-customer-v13"

    supported_fragment = adapter.constraint_fragment(
        supported,
        target_identity=target_identity,
        target_revision=target_revision,
    )
    assert supported_fragment["predicates"]
    assert all(p["role"] == "constraint" for p in supported_fragment["predicates"])
    assert all(
        obs["status"] == "TRUE"
        for obs in supported_fragment["observations"].values()
    )

    receipt = adapter.merge_constraints(necessity_receipt("TRUE"), supported_fragment)
    verdict, reason = gate.evaluate(receipt)
    assert verdict == "ACT", (verdict, reason)

    support_pid = supported_fragment["predicates"][0]["id"]
    bad = adapter.merge_constraints(necessity_receipt("TRUE"), supported_fragment)
    bad["intervention"]["justified_by"] = [support_pid]
    verdict, reason = gate.evaluate(bad)
    assert verdict == "INVESTIGATE", (verdict, reason)

    deferred_fragment = adapter.constraint_fragment(
        deferred,
        target_identity=target_identity,
        target_revision=target_revision,
    )
    assert any(
        obs["status"] in {"FALSE", "UNKNOWN"}
        for obs in deferred_fragment["observations"].values()
    )
    receipt = adapter.merge_constraints(necessity_receipt("TRUE"), deferred_fragment)
    verdict, reason = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE", (verdict, reason)

    print(
        json.dumps(
            {
                "safeact_supported_case": supported["case_id"],
                "safeact_deferred_case": deferred["case_id"],
                "supported_constraints": len(supported_fragment["predicates"]),
                "deferred_constraints": len(deferred_fragment["predicates"]),
                "support_never_promoted_to_necessity": True,
                "external_safeact_consumed": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
