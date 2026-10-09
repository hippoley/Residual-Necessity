# External Evidence Ledger

This file records third-party evidence that may strengthen or falsify Residual Necessity. It deliberately separates **evidence qualification** from adoption, citation, endorsement, and dependency.

## ExecSurface real-workload record

- Upstream: AETHERXGLOBAL/execsurface
- Intake: issue #140, P9.5 / P8-A4 external real-workload evidence
- Residual-Necessity report: comment 6056218704
- Upstream qualification: comment 6056888111
- Workload: Residual-Necessity PR #2, Python 3.11, `python -m pytest -q`
- ExecSurface artifact: public v0.1.0-alpha.6 release binary with checksum verification
- Environment: GitHub-hosted Ubuntu x86_64
- Preserved initial result:
  - `doctor`: PASS
  - target workload: 15 tests passed
  - `learn`: exit 2
  - observation incomplete; no baseline or downstream PASS/REVIEW/BLOCK verdict manufactured
- Upstream scientific classification:
  - genuine external real-workload evidence record
  - provisional family: `PARTIAL_OR_UNSUPPORTED / INCOMPLETE`
  - root cause intentionally left open pending collection-health / warning diagnostics

### What this establishes

A third-party project has independently reviewed and retained a Residual-Necessity workload result under its own preregistered evidence protocol.

The record supports one concrete distinction:

> target workload success does not imply that observation is sufficient to authorize a baseline or a state transition.

### What this does not establish

It does **not** establish:
- adoption of Residual Necessity;
- a dependency on this repository;
- endorsement;
- a citation in scientific literature;
- superiority over another runtime-governance system;
- that ExecSurface has a defect;
- that Residual Necessity improves abstention metrics.

## ExecSurface consumer-contract discussion

- Upstream: AETHERXGLOBAL/execsurface
- Thread: issue #155
- Residual-Necessity feedback: comment 6056614778
- Question under discussion: whether complete/supported observation authorizes proposition-level negative evidence from effect absence, or whether an explicit negative-evidence guarantee is required.

Residual Necessity currently chooses the conservative contract:

- positive matching evidence may support `TRUE`;
- incomplete/unsupported evidence becomes `UNKNOWN`;
- effect absence does not become `FALSE` without explicit negative authority.

This rule is enforced by the reference gate: `FALSE` without a matching scoped `negative_authority` object remains unresolved and cannot produce `ABSTAIN`.


## AgentAbstain preregistered trivial baselines

Public CI run 37764233694 consumed the public AgentAbstain dataset and rebuilt the gold-hidden runtime-only slice.

Observed dataset shape:

- runtime pairs: **97**
- runtime variants: **194**
- hidden from inference: `task_type`, `abstention_trigger`, `execution_dag`, `critical_actions`, category, transformation metadata

Preregistered trivial baselines:

| Baseline | Accuracy | Unnecessary intervention | Missed required action | ACT recall | Paired accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| always-act | 0.50 | 1.00 | 0.00 | 1.00 | 0.00 |
| always-abstain | 0.50 | 0.00 | 1.00 | 0.00 | 0.00 |
| always-investigate | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 |

These numbers are not a Residual Necessity result. They are minimum Reality Gate baselines. The always-investigate row is deliberately included so a system cannot appear safe merely by withholding every required action.

The blind static view contains only:
`action_type`, `environments`, `instruction`, `pair_id`, `phase`, `system_prompt`, and `task_id`.

That static view does not contain the decisive runtime observations. A valid Residual Necessity evaluation therefore requires actual runtime state / execution logs or independently supplied rollouts before gold scoring.

## ExecSurface diagnostic qualification

Follow-up run 37869646669 preserved typed evidence before baseline learning.

Observed classification:

- workload: **39 tests passed**
- `collection_health.state = incomplete_capability`
- warning code: `side_effectful_open_identity_divergence`
- `raw_observation.complete = false`
- typed effects observed: 41
- `learn` exit code: 2
- downstream classification: `FAIL_CLOSED_ON_INCOMPLETE_EVIDENCE`

The warning specifically reports successful side-effectful opens whose lexical path was `/tmp` while the returned file descriptor resolved to deleted kernel-object paths such as `/tmp/#94573 (deleted)`; raw observation v2 states it cannot serialize a dedicated successful-open object identity for that case.

The workflow now treats that result as a successful diagnostic classification, **not** as a successful ExecSurface baseline. No PASS/REVIEW/BLOCK verdict is manufactured when observation is incomplete.

This diagnostic was reported back to ExecSurface #140 as follow-up evidence.


## Agent Hooks canonical control-contract interoperability

Residual Necessity now runs as a real interceptor on the public Agent Hooks Beta Python SDK.

Verified CI:
- workflow: `Agent Hooks end to end`
- successful runs: 37870271897 (push) and 37870276997 (pull request)
- SDK: `agent-hooks-sdk==0.1.0b1`
- spec surface: AGENT-HOOKS-0.1

The E2E uses the canonical `AgentContextBuilder`, `InterceptionEmitter`, `InterceptionBlocked`, and standard Agent Hooks `Verdict/Evidence` types.

Verified behavior:
- scoped authoritative TRUE → combined permit;
- scoped authoritative FALSE → block;
- UNKNOWN necessity → fail closed as a liftable deny;
- positive evidence bound to the wrong target revision → fail closed.

The interceptor reads a receipt from the namespaced extension:
`extensions.residual_necessity.receipt`

and routes every decision through the same `src/gate.py` semantics.

This establishes **runtime interoperability with the Agent Hooks control contract**. It does not establish upstream adoption, a conformance claim, or endorsement by the Agent Hooks maintainers.

### Permit-evidence composition finding

The E2E also exposed a standards-level question: an individual interceptor can return allow + evidence, but the default all-permit composition synthesizes a new combined allow and unions warnings/result labels, not evidence.

The individual interceptor's reason survives in the per-interceptor record summary, while its evidence pointer is not preserved on the combined permit verdict.

The finding is documented in `docs/AGENT_HOOKS_PERMIT_EVIDENCE_NOTE.md`. An attempt to open the upstream issue was blocked by the current GitHub integration's external-write permission, so no upstream discussion is claimed yet.


## Microsoft ACS pre-tool compatibility

Residual Necessity also has a lower-level compatibility proof against the released Microsoft ACS Python runtime:

- workflow: `ACS end to end`
- successful run: 37870420582
- package: `agent-control-specification==0.3.1b1`
- boundary tested: `PRE_TOOL_CALL` via `evaluate_intervention_point`

Verified:
- authoritative TRUE → allow;
- authoritative FALSE → deny;
- UNKNOWN → not allow.

The test intentionally does not use `run_tool()`, because that helper also requires a configured `post_tool_call` boundary. Residual Necessity's current contract is pre-side-effect necessity; extending into post-tool semantics would widen the project without adding necessity value.

This is compatibility evidence with a released policy runtime. It is not an ACS endorsement, conformance claim, or adoption.


## AgentAbstain tool-visible runtime observation

### First-generation probe — superseded as a firewall proof

Public run `37871728936` successfully exercised one read-only AgentAbstain lookup tool and preserved a real execution-log entry. It was useful evidence that the external sandbox can be consumed.

However, a later adversarial audit found that the probe and trusted benchmark setup still lived in the same script/process:

- the harness iterated the `act` / `abstain` variant paths;
- `BaseAgent.load_task_bundle` loaded task metadata containing gold-only fields;
- benchmark initial state was loaded to instantiate the environment.

The probe logic did not intentionally inspect those gold/state fields when choosing the lookup tool, but the isolation boundary was not strong enough to support the stronger claim that the inference selector itself was structurally unable to access them.

Therefore run `37871728936` is retained as **runtime-interoperability evidence**, not as the final gold-firewall proof.

### Stricter replacement

The current implementation separates:

- a **trusted harness** that instantiates the benchmark variant and enforces that only upstream `lookup` / `verify` tools are projected;
- `experiments/agentabstain/blind_probe.py`, which has no AgentAbstain imports and receives only a sanitized tool catalog.

CI additionally scans the blind module for benchmark/gold/hidden-state dependency tokens.

The stricter path must pass public CI before the observation-boundary user story is closed again. Even after that, it proves only a blind observation surface — **not** an ACT/ABSTAIN prediction or benchmark improvement.


## AgentAbstain gold-blind runtime-evidence falsification

Public workflow run **37875541342** completed the first full runtime-evidence baseline over the 97 runtime pairs / 194 variants.

The experiment used:
- pinned AgentAbstain runtime and dataset revisions;
- trusted benchmark setup;
- a process-isolated blind probe selector receiving only public instruction + sanitized lookup/verify tool catalog;
- a process-isolated blind predictor receiving only sanitized probe outcome;
- no commit-class tool calls;
- frozen prediction file before label scoring.

Prediction SHA-256:
`e13d77cfb08f113ce19f5e1d929d743e584e45eba025410e6b1c44f11140793a`

Preserved artifact:
- `agentabstain-runtime-evidence-baselines`
- artifact id **11592366000**

Observed probe surface:
- variants: **194**
- pairs: **97**
- safely probed variants: **172**
- probe coverage: **88.66%**
- successful probes: **165**
- failed probes: **7**

### Baseline results

| Strategy | Accuracy | ACT recall | Unnecessary intervention | Missed required action | Investigate | Paired accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| failure-only | 3.61% | 0.00% | 0.00% | 100.00% | 96.39% | 0.00% |
| probe-success | 47.94% | 88.66% | 81.44% | 11.34% | 11.34% | 7.22% |

Interpretation:

> **Generic runtime evidence availability is not a necessity predicate.**

A read-only probe being callable/successful is common on both should-act and should-abstain variants. Treating probe success as permission to act preserves much ACT recall but still performs unnecessary intervention on **81.44%** of abstain cases. Treating only probe failure as an abstention signal collapses legitimate-action recall to zero.

This falsifies the next-lowest-complexity route: “add a generic read/verify probe and infer necessity from whether it succeeds.”

The next independent-project experiment must therefore be **predicate-specific**:
- identify the exact violated proposition relevant to the proposed transition;
- choose observations whose semantics bear on that proposition;
- preserve UNKNOWN when those observations do not have proposition-level authority;
- freeze the resulting receipt/verdict before gold scoring.

This result is evidence **against** generic evidence heuristics, not evidence that Residual Necessity already improves AgentAbstain.


## P3 real-world partial-fix sequence

Public workflow run **37876394371** consumed the external SoSy-Lab P3 partial-fix dataset at pinned commit:

`bfd73658`

A real task classified by the P3 schema as `partial fix` was normalized and frozen:

- source task: `partial-fixes/andwn_cave-story-md/partial_2/task.yml`
- repository: `https://github.com/andwn/cave-story-md`
- related issue: `https://github.com/andwn/cave-story-md/issues/169`
- base revision: `af62a60ad322bfa1258449acbef936daeedb6973`
- partial attempt 1: `814ddfad88e27c5734d6725341a984c791073b24`
- partial attempt 2: `62d8c669e0aa335eed9c50f4fd7b753dd75f3676`
- expected/final fix: `2c11d40fd1338f17cc84da46005fa29cbf37ca77`

Normalized evidence SHA-256:

`4a34d59cc9608e5737739fc0bf887d95969f6f7c06eb1fe469636ecc7e5ae39b`

Preserved artifact:
- name: `p3-real-partial-fix`
- artifact id: **11592786218**

What this establishes:

> The project now has a pinned, independently curated, real-world sequence in which one or more intermediate fixes are explicitly classified as incomplete before a later expected fix.

What this does **not** establish:

- that Residual Necessity can automatically discover the residual violated predicate;
- that its ACT/ABSTAIN gate improves an agent benchmark;
- that the P3 task exposes a tool-visible runtime predicate compatible with AgentAbstain;
- that FixedBench partial-fix cases have been integrated.

This closes the need for synthetic-only partial-fix semantics evidence. The harder agentic question remains separate.


## AgentAbstain frozen development / holdout split

Before any predicate-specific method is tuned, the 97 opaque runtime pair IDs were split **without gold labels** using the deterministic pair-level split in `freeze_pair_split.py`.

Public run: **37876394319**

Frozen split:
- total pairs: **97**
- development: **64 pairs**
- holdout: **33 pairs**
- holdout percentage target: 30%
- gold used to assign split: **false**

Manifest SHA-256:

`97957135fa566fdd0ece3add73fee2dfaa0d594b342910d180fbbbeac4cbcd79`

Preserved artifact:
- name: `agentabstain-pair-split`
- artifact id: **11591769261**

Research rule from this point forward:

> Predicate-specific probe/evidence semantics may be developed against the development partition. Holdout pair outcomes must not be used to tune the method and should only be scored after a candidate method is frozen.

Both variants of a pair share the same partition because assignment is pair-level.


## P3 bounded real residual-necessity pair

Public workflow run **37892134518** exercised the same bounded issue-derived necessity predicate on two real revisions of `andwn/cave-story-md`.

External repository:
- `https://github.com/andwn/cave-story-md`
- issue basis: `#169`

Partial revision:
- commit: `62d8c669e0aa335eed9c50f4fd7b753dd75f3676`
- predicate: `bsl0000_zero_branch_fails_to_bind_boss_entity`
- observed status: **TRUE**
- Residual Necessity verdict: **ACT**
- receipt SHA-256: `70ca3e0562cf65accb7c217934fd5ffb898a25c80dc6d5e8b7c71aeacf1cbb75`

Final fixed revision:
- commit: `2c11d40fd1338f17cc84da46005fa29cbf37ca77`
- same bounded predicate: **FALSE**
- scoped negative authority present
- Residual Necessity verdict: **ABSTAIN**
- receipt SHA-256: `e01d9dd398fe7b9dad89ec34b5dfef61ae668cd9c2bfdab74dbf25b5945453c2`

Artifact:
- `p3-residual-necessity-pair`
- artifact id: **11599285242**

The oracle is intentionally bounded to the `CMD_BSL` zero-argument branch. It is derived from issue semantics and current source shape, not by comparing the candidate revision against the final patch.

This establishes one real external ACT→ABSTAIN residual-necessity transition across a partial fix and final fix. It does not establish automatic discovery of arbitrary necessity predicates.


## Latest-head P0 closure checkpoint

The P0 semantic/system closure set passed on the same validated branch state before this bookkeeping commit:

- SafeAct evidence interop: run **37892615899** — success.
  - Pinned SafeAct commit: `841816cf1e376e6fbf8600cffac5df1736e1d369`
  - SUPPORTED rule evidence remains `role=constraint`.
  - MISSING/DEFER-style evidence remains UNKNOWN and does not receive negative authority.
  - Support evidence cannot appear in `intervention.justified_by` as necessity.
- P3 residual necessity pair: run **37892615862** — success.
  - Partial revision `62d8c669...` → bounded necessity TRUE → ACT.
  - Final revision `2c11d40f...` → same bounded necessity FALSE → ABSTAIN.
- Core CI: run **37892615817** — success on Python **3.10, 3.11, 3.12**.
  - pytest passed;
  - horizontal completeness matrix validation passed;
  - receipt schema 0.3 migration validation passed;
  - dependency impact analysis passed;
  - reference gate/evaluator smoke tests passed.

This checkpoint is the evidence basis for marking US-38, US-39 and US-40 as Verified Closed.


## Language-neutral conformance pack

Core CI run **37893874090** verified the implementation-neutral conformance boundary.

Protocol:
- one evaluator process per vector;
- receipt JSON on stdin;
- one JSON object with `verdict` on stdout;
- allowed verdicts: ACT / ABSTAIN / INVESTIGATE / ESCALATE;
- non-zero exit, timeout, invalid JSON, or invalid verdict is a conformance failure.

The reference gate passed the current semantic vectors through this external-process interface, while an intentionally invalid evaluator was rejected.

The pack includes:
- `conformance/manifest.json`
- `conformance/core-cases.json`
- `conformance/run_external.py`
- `conformance/reference_stdio.py`
- `conformance/freeze_pack.py`

This establishes implementation-neutral consumability inside public CI. It is **not** evidence of third-party adoption; US-22 remains partial until an independent implementation or upstream conformance process consumes it.


## AgentAbstain generalization kill decision

The project intentionally stops treating broad AgentAbstain superiority as an active success criterion.

Latest development-only proposition-specific result, public run **37894155290**:
- development pairs: **64**
- variants: **128**
- accuracy: **0.78%**
- ACT recall: **0%**
- paired accuracy: **0%**
- investigate rate: **99.22%**
- unnecessary intervention: **0%**
- matched provider profile: `personal-profile-public-bio/v1` on **2 variants**

Earlier generic runtime-evidence result on all 97 pairs:
- probe-success ACT recall: **88.66%**
- unnecessary intervention: **82.47%**
- paired accuracy: **6.19%** on the latest rerun

Interpretation:

> AgentAbstain is useful as a falsification / anti-overclaim benchmark, but its runtime abstention gold mixes capability failure, conflicting evidence, emergent risk, support and other constraints. Those semantics are intentionally distinct from Residual Necessity's question of whether a current state transition is still necessary.

Therefore US-26 and US-27 are **Superseded by Evidence**, not silently abandoned and not falsely marked Verified Closed. Their replacement path is:
- SafeAct for mature evidence/support constraints (US-38),
- P3/real current-state sources for actual residual necessity (US-39),
- implementation-neutral conformance + upstream control-plane integration for adoption (US-22/US-36).


## P3 → Agent Hooks control-plane E2E

Public run **37897404767** upgraded the real P3 residual pair from a gate-only check to a composed control-plane path:

```text
real cave-story-md revision
        ↓
issue-derived bounded current-revision oracle
        ↓
Residual Necessity 0.3 receipt
        ↓
ResidualNecessityInterceptor
        ↓
Agent Hooks InterceptionEmitter
```

Verified on the same external issue/revisions:

- partial revision `62d8c669...`
  - bounded residual predicate = TRUE
  - RN gate = ACT
  - Agent Hooks = ALLOW / proceeds
- final revision `2c11d40f...`
  - bounded residual predicate = FALSE
  - RN gate = ABSTAIN
  - Agent Hooks = DENY / blocks

Both paths emitted `P3_AGENT_HOOKS_E2E_PASS` in the public workflow.

Receipt hashes from the same run:
- partial: `70ca3e0562cf65accb7c217934fd5ffb898a25c80dc6d5e8b7c71aeacf1cbb75`
- final: `e01d9dd398fe7b9dad89ec34b5dfef61ae668cd9c2bfdab74dbf25b5945453c2`

This closes the **cross-module control-plane integration** gap for one bounded real external partial-fix case. It still does not establish a general agent capability to discover arbitrary residual predicates automatically.


## NoPatch protocol baseline

Residual Necessity now consumes a pinned external **NoPatch / Prove First 1.0.0** fixture corpus as a Track B protocol baseline.

Pinned source:
- repository: `alessiomarcone/no-patch`
- commit: `30d7048132c996684d6f9d3946772c205e9fe47c`
- license: MIT
- protocol version: 1.0.0

Public run: **37899632344**

The crosswalk deliberately does **not** use an agent-generated Prove Report as authority. It materializes NoPatch's own deterministic forward-evaluation fixtures and runs their focused tests directly.

Verified bounded crosswalk:

- NoPatch `partial` fixture:
  - known-good top-level case passes;
  - residual nested case fails;
  - RN bounded residual predicate = TRUE;
  - RN verdict = **ACT**.

- NoPatch `no-patch` fixture:
  - focused reported behavior passes in the current fixture;
  - RN bounded residual predicate = FALSE;
  - RN verdict = **ABSTAIN**.

The protocol classification remains a baseline/semantic comparison, not a source of necessity authority.

Frozen receipt hashes:
- partial: `de9a61506ccd635ac020e5b79e60aa2bb2dc9253c9b75fc6b20856d8f1c93ad0`
- no-patch: `85af250ce50fbaa87e3f89a440412234c41bd1e24c4e4028a28411c716c99941`

Artifact:
- `nopatch-protocol-baseline`
- artifact id **11601334725**

This strengthens Track B with a second independent, versioned partial/no-patch protocol source in addition to the real P3 history. It still does not prove general autonomous residual-predicate discovery.


## Benchmark 0.2 clean delivery checkpoint

Clean delivery branch `delivery/benchmark-external-modules` was reconstructed from current `main` rather than merging the long-lived exploratory branch.

Validated head before evidence-only finalization:
`fc42f0165a171b9ea305840970cc7106171df41f`

All nine required workflows passed on that same head:

- CI — run **37921383526**
- AgentAbstain reality — run **37921383492**
- SafeAct evidence interop — run **37921383483**
- P3 residual necessity pair — run **37921383528**
- P3 partial-fix reality — run **37921383530**
- NoPatch protocol baseline — run **37921383571**
- Agent Hooks end to end — run **37921383510**
- Agent Hooks upstream candidate — run **37921383565**
- Agent Hooks official CTK cross-contract — run **37921383519**

The delivery upgrades the benchmark/governance surface without replacing the existing NoPatch baseline:

- benchmark manifest 0.2;
- pair-preserving bootstrap uncertainty;
- category-stratified development scoring;
- gold-free split and sealed holdout policy;
- method-card / method-freeze / frozen-prediction tools;
- provider-profile registry;
- CEL-backed proposition expressions with explicit profile authority;
- Dataset Card and Croissant metadata;
- P3 and SafeAct corpus/upstream-contract audits;
- machine-readable external-module license/version/semantic-boundary registry.

### Official Agent Hooks CTK receipt on the clean branch

Run **37921383519** installed `agent-hooks-sdk[ctk]==0.1.0b1` and executed the official CTK reference corpus plus the RN interceptor seam.

Official CTK reference:
- vectors: **51**
- pass: **47**
- capability-gated skip: **4**
- fail: **0**

RN interceptor cases in the same pinned SDK:
- authoritative TRUE → allow;
- authoritative FALSE → deny;
- UNKNOWN → deny / investigate;
- wrong-revision TRUE → deny / investigate.

The report explicitly states:
- `claim_type = interceptor_compatibility_not_host_conformance`
- `host_conformance_claimed = false`

Artifact:
- `agent-hooks-official-ctk-cross-contract`
- artifact id **11611399384**
- artifact zip SHA-256 `7471db9cffd173a51f79148708165fc30745c9643803494cc1116da5ff2b864a`

This is official-CTK cross-contract evidence, not an Agent Hooks §13 host-conformance claim and not upstream adoption.
