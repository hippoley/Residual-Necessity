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
