# Landscape checkpoint

This repository treats neighboring work as constraints, not validation.

## Nearby systems

- **Microsoft Agent Control Specification / Foundry intervention points**: deterministic runtime policy and intervention points.
- **AgentAction**: action authorization, approvals, budgets, idempotency, stateful policy.
- **IntentGate**: request-derived intent consistency.
- **scorekeeper**: practical entitlement, overreach, and underreach.
- **AgentAbstain**: paired should-act / should-abstain evaluation and critical-action boundaries.
- **FixedBench**: already-fixed coding tasks and partial-fix false-abstention failures.
- **SentinelBench**: long-running monitoring tasks with explicit no-op cases.

Residual Necessity must not duplicate these.

## Surviving hypothesis

The remaining question is:

> Given that an action is authorized, intent-consistent, in entitled scope, and policy-compliant, what current violated condition still exists that makes changing state necessary now?

## Anti-LLM-obsolescence rule

A model-generated necessity score is not authoritative evidence.

Models may propose hypotheses, probes, or explanations. Authoritative inputs must come from externally inspectable current-state observations such as revision identity, tests, runtime state, device state, API state, resource identity, or timestamps.

## Graduation metrics

A real evaluation must report at least:

- unnecessary intervention rate;
- false abstention rate;
- investigate / escalate rate;
- paired accuracy where paired cases exist;
- partial-fix / residual-violation performance separately.

A system that appears safe by refusing everything has failed.

## Kill / upstream criterion

Stop treating this as an independent project if a mature neighboring system already provides all of:

1. model-external current-state necessity predicates;
2. explicit residual-violation semantics;
3. stale / unknown / conflicted evidence states;
4. pre-side-effect enforcement;
5. two-sided measurement of unnecessary action and false abstention;
6. a stable external interface adopted by real runtimes.

In that case, contribute upstream instead.


## 2026-10-08 competitive pressure update

New adjacent systems make the project boundary narrower:

- **Open Agent Passport (OAP)**: deterministic pre-action authorization with signed audit records. This occupies authorization and policy enforcement, not residual necessity.
- **AgentHook**: a general runtime-evidence envelope for agent lifecycle events. This occupies evidence transport/standardization, so Residual Necessity must not become another generic evidence schema.
- **Proof-Carrying Agent Actions (PCAA)**: runtime-neutral action certificates spanning admissibility, approval, execution and outcome closure. This occupies portable proof-carrying governance.
- **sincLLM pre-action evidence and authority gate**: explicitly treats observed start state, evidence freshness, missing/mixed evidence and human hold/escalation as first-class. This overlaps strongly with any broad "pre-action evidence gate" claim.

### Surviving seam

The project should survive only if it can demonstrate a narrower predicate that these systems do not already own:

> Given that an action is authorized, in scope, policy-compliant, and supported by runtime evidence, what currently violated condition still exists that makes this next state transition necessary now?

The differentiator is therefore **residual necessity**, especially:
- already-fixed / stale requests;
- partially-fixed states where one historical symptom disappeared but another violated property remains;
- repeated/retried actions where authority persists but necessity has expired;
- evidence that is sufficient to authorize observation but insufficient to prove necessity.

If real evaluation cannot show value beyond authorization/evidence/hold semantics already covered by adjacent systems, this project should upstream or stop rather than widen scope.
