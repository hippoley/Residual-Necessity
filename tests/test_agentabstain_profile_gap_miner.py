from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"experiments"/"agentabstain"/"profile_gap_miner.py"
spec=importlib.util.spec_from_file_location("profile_gap_miner",MODULE)
assert spec and spec.loader
miner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(miner)

def test_gap_miner_ranks_unprofiled_two_sided_tool_without_granting_authority() -> None:
    obs=[
      {"case_id":"a","pair_id":"p1","tool":"verify.x","tool_kind":"verify","success":True,"binding_complete":True,"result":{"ok":True}},
      {"case_id":"b","pair_id":"p1","tool":"verify.x","tool_kind":"verify","success":True,"binding_complete":True,"result":{"ok":False}},
      {"case_id":"c","pair_id":"p2","tool":"lookup.y","tool_kind":"lookup","success":True,"binding_complete":True,"result":{"value":1}},
    ]
    labels=[
      {"case_id":"a","pair_id":"p1","task_type":"act"},
      {"case_id":"b","pair_id":"p1","task_type":"abstain"},
      {"case_id":"c","pair_id":"p2","task_type":"act"},
    ]
    report=miner.mine(obs,labels,{"profiles":[]})
    assert report["holdout_consumed"] is False
    assert report["authority_granted"] is False
    assert report["authority_readiness_candidates"][0]["tool"]=="verify.x"
    assert report["authority_readiness_candidates"][0]["both_label_sides_present"] is True
    assert report["authority_readiness_candidates"][0]["authority_granted"] is False
    assert report["coverage_candidates"]
