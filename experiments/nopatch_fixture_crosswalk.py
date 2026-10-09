#!/usr/bin/env python3
"""Consume pinned NoPatch evaluation fixtures as an external protocol baseline.

NoPatch's agent-produced Prove Report is NOT treated as evidence authority.
This adapter consumes the deterministic fixture state and focused tests from
the pinned NoPatch black-box evaluation corpus, then emits bounded RN receipts.

The semantic crosswalk is intentionally narrow:

- NoPatch partial fixture:
  known-good focused case passes AND residual focused case fails
  -> bounded residual necessity TRUE -> ACT.
- NoPatch no-patch fixture:
  focused reported behavior passes
  -> bounded residual necessity FALSE -> ABSTAIN.

The result says nothing about arbitrary repository defects or authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "src" / "gate.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gate = load_module("rn_gate_nopatch_crosswalk", GATE_PATH)


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def authority(
    *,
    predicate_id: str,
    target_identity: str,
    target_revision: str,
    basis: str,
    evidence_ref: str,
) -> dict[str, Any]:
    return {
        "scope": {
            "predicate_id": predicate_id,
            "target_identity": target_identity,
            "target_revision": target_revision,
        },
        "basis": basis,
        "evidence_ref": evidence_ref,
    }


def receipt(
    *,
    case_name: str,
    status: str,
    revision: str,
    evidence: str,
    reason: str,
) -> dict[str, Any]:
    predicate_id = f"nopatch:{case_name}:reported_gap_remains"
    target_identity = f"nopatch-fixture:{case_name}"
    observation: dict[str, Any] = {
        "status": status,
        "source": "NoPatch 1.0.0 deterministic forward-eval fixture",
        "details": {
            "case": case_name,
            "reason": reason,
            "protocol_boundary": (
                "NoPatch fixture/test evidence is used only for this bounded "
                "defect claim; NoPatch patch eligibility is not treated as "
                "authorization or general necessity authority."
            ),
        },
    }
    auth = authority(
        predicate_id=predicate_id,
        target_identity=target_identity,
        target_revision=revision,
        basis="nopatch_pinned_focused_test_probe",
        evidence_ref=evidence,
    )
    if status == "TRUE":
        observation["positive_authority"] = auth
    elif status == "FALSE":
        observation["negative_authority"] = auth

    return {
        "schema_version": "0.3",
        "intervention": {
            "id": f"repair-{case_name}",
            "kind": "modify_code",
            "description": f"repair only the bounded live defect in NoPatch fixture {case_name}",
            "justified_by": [predicate_id],
        },
        "target": {
            "identity": target_identity,
            "revision": revision,
            "environment": {
                "external_protocol": "NoPatch Prove First 1.0.0",
                "fixture": case_name,
            },
        },
        "predicates": [
            {
                "id": predicate_id,
                "required": True,
                "kind": "reality",
                "role": "necessity",
            }
        ],
        "observations": {predicate_id: observation},
    }


def baseline_revision(workspace: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], workspace)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout.strip()


def evidence_ref(
    *,
    nopatch_commit: str,
    case_name: str,
    probes: list[tuple[str, subprocess.CompletedProcess[str]]],
) -> str:
    material = {
        "nopatch_commit": nopatch_commit,
        "case": case_name,
        "probes": [
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            for command, result in probes
        ],
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"nopatch:{nopatch_commit}:{case_name}:sha256:{digest}"


def evaluate_partial(
    runner: Any,
    *,
    nopatch_commit: str,
    root: Path,
) -> dict[str, Any]:
    fixture = runner.FIXTURES["partial"]
    if fixture.expected_status != "partial":
        raise ValueError("pinned NoPatch partial fixture changed expected status")

    workspace = runner.prepare_workspace(root, "codex", fixture)
    top_cmd = f"{sys.executable} -m unittest -q test_exporter.ExporterTests.test_top_level_empty_array"
    residual_cmd = f"{sys.executable} -m unittest -q test_exporter.ExporterTests.test_nested_empty_array"

    top = run(top_cmd.split(), workspace)
    residual = run(residual_cmd.split(), workspace)

    if top.returncode == 0 and residual.returncode != 0:
        status = "TRUE"
        reason = "known-good top-level case passes while nested residual case still fails"
    elif top.returncode == 0 and residual.returncode == 0:
        status = "FALSE"
        reason = "both bounded cases pass; no residual gap remains in the fixture claim"
    else:
        status = "UNKNOWN"
        reason = "fixture does not preserve the expected known-good/residual structure"

    revision = baseline_revision(workspace)
    ev = evidence_ref(
        nopatch_commit=nopatch_commit,
        case_name="partial",
        probes=[(top_cmd, top), (residual_cmd, residual)],
    )
    return receipt(
        case_name="partial",
        status=status,
        revision=revision,
        evidence=ev,
        reason=reason,
    )


def evaluate_no_patch(
    runner: Any,
    *,
    nopatch_commit: str,
    root: Path,
) -> dict[str, Any]:
    fixture = runner.FIXTURES["no-patch"]
    if fixture.expected_status != "no-patch":
        raise ValueError("pinned NoPatch no-patch fixture changed expected status")

    workspace = runner.prepare_workspace(root, "codex", fixture)
    command = f"{sys.executable} -m unittest -q test_exporter.ExporterTests.test_keeps_empty_arrays"
    result = run(command.split(), workspace)

    if result.returncode == 0:
        status = "FALSE"
        reason = "focused reported behavior passes in the current fixture"
    else:
        status = "TRUE"
        reason = "focused reported behavior still fails in the current fixture"

    revision = baseline_revision(workspace)
    ev = evidence_ref(
        nopatch_commit=nopatch_commit,
        case_name="no-patch",
        probes=[(command, result)],
    )
    return receipt(
        case_name="no-patch",
        status=status,
        revision=revision,
        evidence=ev,
        reason=reason,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nopatch-root", type=Path, required=True)
    parser.add_argument("--nopatch-commit", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(
        (args.nopatch_root / "manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("protocol_version") != "1.0.0":
        raise ValueError("expected NoPatch protocol 1.0.0")

    runner = load_module(
        "pinned_nopatch_forward_eval",
        args.nopatch_root / "scripts" / "run_forward_eval.py",
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rn-nopatch-partial-") as partial_tmp:
        partial_receipt = evaluate_partial(
            runner,
            nopatch_commit=args.nopatch_commit,
            root=Path(partial_tmp),
        )
    with tempfile.TemporaryDirectory(prefix="rn-nopatch-no-patch-") as no_patch_tmp:
        no_patch_receipt = evaluate_no_patch(
            runner,
            nopatch_commit=args.nopatch_commit,
            root=Path(no_patch_tmp),
        )

    partial_verdict, partial_reason = gate.evaluate(partial_receipt)
    no_patch_verdict, no_patch_reason = gate.evaluate(no_patch_receipt)

    if partial_verdict != "ACT":
        raise AssertionError((partial_verdict, partial_reason))
    if no_patch_verdict != "ABSTAIN":
        raise AssertionError((no_patch_verdict, no_patch_reason))

    (args.out_dir / "partial-receipt.json").write_text(
        json.dumps(partial_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "no-patch-receipt.json").write_text(
        json.dumps(no_patch_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "source": "alessiomarcone/no-patch",
        "source_commit": args.nopatch_commit,
        "protocol_version": "1.0.0",
        "partial_expected_protocol_status": "partial",
        "partial_rn_verdict": partial_verdict,
        "no_patch_expected_protocol_status": "no-patch",
        "no_patch_rn_verdict": no_patch_verdict,
        "agent_report_used_as_authority": False,
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
