from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORACLE=ROOT/"experiments"/"p3"/"cave_story_issue169_oracle.py"
GATE=ROOT/"src"/"gate.py"

def load(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

oracle=load("p3_issue169_oracle",ORACLE)
gate=load("p3_issue169_gate",GATE)

PARTIAL="""
case CMD_BSL:
{
    args[0] = tsc_read_word();
    if(!args[0]) {
        bossBarEntity = NULL;
        break;
    }
    if((bossBarEntity = entity_find_by_event(args[0]))) {
        tsc_show_boss_health();
        break;
    }
    if((bossBarEntity = bossEntity)) {
        tsc_show_boss_health();
        break;
    }
}
break;
"""

FINAL="""
case CMD_BSL:
{
    args[0] = tsc_read_word();
    if(!args[0]) {
        if((bossBarEntity = bossEntity)) {
            bossMaxHealth = bossHealth = bossBarEntity->health;
            tsc_show_boss_health();
            break;
        }
    }
    else if((bossBarEntity = entity_find_by_event(args[0]))) {
        tsc_show_boss_health();
        break;
    }
}
break;
"""

def test_partial_source_exposes_residual_violation() -> None:
    status,reason=oracle.inspect_source(PARTIAL)
    assert status=="TRUE"
    receipt=oracle.receipt(status,reason,"partial","src/tsc.c")
    verdict,_=gate.evaluate(receipt)
    assert verdict=="ACT"

def test_final_source_proves_bounded_violation_absent() -> None:
    status,reason=oracle.inspect_source(FINAL)
    assert status=="FALSE"
    receipt=oracle.receipt(status,reason,"final","src/tsc.c")
    verdict,_=gate.evaluate(receipt)
    assert verdict=="ABSTAIN"

def test_unrecognized_zero_branch_stays_unknown() -> None:
    status,_=oracle.inspect_source(
        "case CMD_BSL: { if(!args[0]) { log_debug(); } } break;"
    )
    assert status=="UNKNOWN"
