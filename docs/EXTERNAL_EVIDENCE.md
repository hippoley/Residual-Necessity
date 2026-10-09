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

This rule is enforced by the reference gate: `FALSE` without `negative_authority=true` remains unresolved and cannot produce `ABSTAIN`.


## AgentAbstain preregistered trivial baselines

Public CI run 37764233694 consumed the public AgentAbstain dataset and rebuilt the gold-hidden runtime-only slice.

Observed dataset shape:

- runtime pairs: **97**
- runtime variants: **194**
- hidden from inference: `task_type`, `abstention_trigger`, `execution_dag`, `critical_actions`, category, transformation metadata

Preregistered trivial baselines:

| Baseline | Accuracy | Unnecessary intervention | False abstention | Paired accuracy |
| --- | ---: | ---: | ---: | ---: |
| always-act | 0.50 | 1.00 | 0.00 | 0.00 |
| always-abstain | 0.50 | 0.00 | 1.00 | 0.00 |

These numbers are not a Residual Necessity result. They are the minimum Reality Gate baselines that any real inference path must beat without collapsing the opposite error direction.

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
