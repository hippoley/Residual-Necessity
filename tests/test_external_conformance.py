from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_language_neutral_conformance_runner_accepts_reference_gate(tmp_path: Path) -> None:
    out=tmp_path/"report.json"
    proc=subprocess.run(
        [
            sys.executable,
            str(ROOT/"conformance"/"run_external.py"),
            "--evaluator",
            f"{sys.executable} {ROOT/'conformance'/'reference_stdio.py'}",
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
    )
    assert proc.returncode==0, proc.stdout+proc.stderr
    report=json.loads(out.read_text(encoding="utf-8"))
    assert report["failed"]==0
    assert report["passed"]==report["total"]
    assert report["total"]>=7


def test_external_runner_rejects_invalid_evaluator_protocol(tmp_path: Path) -> None:
    bad=tmp_path/"bad.py"
    bad.write_text("print('not-json')\n",encoding="utf-8")
    proc=subprocess.run(
        [
            sys.executable,
            str(ROOT/"conformance"/"run_external.py"),
            "--evaluator",
            f"{sys.executable} {bad}",
        ],
        text=True,
        capture_output=True,
    )
    assert proc.returncode==1
    report=json.loads(proc.stdout)
    assert report["failed"]==report["total"]
    assert all(case["protocol_ok"] is False for case in report["cases"])
