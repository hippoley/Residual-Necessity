# Residual Necessity

**A model-external control primitive for deciding whether a state-changing intervention is still justified by current reality.**

Residual Necessity asks a narrower question than authorization, policy, intent consistency, or entitlement:

> **What violated condition still exists right now that makes this state transition necessary?**

This repository is intentionally small. It exists to test whether **necessity** is a distinct runtime primitive, not to become another generic agent-governance framework.

## The boundary

An action can be:

- authorized;
- consistent with the user's intent;
- within the request's entitled scope;
- policy-compliant;

and still be unnecessary because the reported condition is already satisfied.

Example:

```text
authorized?          yes
intent-consistent?   yes
within entitlement?  yes
policy-compliant?    yes
current violation?   no
------------------------
ABSTAIN
```

The harder case is partial resolution:

```text
historical symptom?  fixed
residual violation?  yes (P2)
------------------------
ACT only on P2
```

That second case is why this project is about **residual** necessity rather than simple "reproduce first" abstention.

## Runtime shape

```text
proposed intervention
        |
        v
current-state probes
        |
        v
residual violation?
   /       |        \
 yes     unknown      no
  |         |          |
 ACT   INVESTIGATE   ABSTAIN
```

A separate authority boundary may produce `ESCALATE`.

The core invariant is:

> **Missing, stale, conflicted, or unknown evidence never silently becomes permission to mutate state.**

## What this is not

Residual Necessity is **not**:

- an authorization framework;
- a request-scope / entitlement checker;
- an intent-consistency classifier;
- a generic pre-tool-call security guard;
- an LLM prompt asking "should I act?";
- a benchmark result claiming solved abstention.

Models may propose hypotheses or probes. The authoritative inputs must come from inspectable current-world evidence: revision identity, test/runtime results, service state, device state, API state, timestamps, or equivalent external observations.

## Current status

**Research prototype. External adoption: none yet. External evidence qualification: one third-party real-workload record accepted for upstream scientific review.**

ExecSurface maintainers reviewed the preserved Residual-Necessity workload run under their preregistered P8-A4 protocol and classified it as a genuine external real-workload evidence record in the provisional `PARTIAL_OR_UNSUPPORTED / INCOMPLETE` family. This is external scientific qualification of an execution record, not adoption, endorsement, citation, or dependency.

See `docs/EXTERNAL_EVIDENCE.md`.

The project is currently gated by [Reality Gate #1](https://github.com/hippoley/Residual-Necessity/issues/1): no benchmark or runtime-value claim graduates until it is supported by a non-self-referential external result.

The repository does not currently claim that Residual Necessity improves a real benchmark. The first graduation requirement is a paired evaluation that measures both:

- unnecessary intervention: acting when the correct outcome is abstention;
- false abstention: refusing when action is still required.

A system that refuses everything has failed.

## Minimal receipt

A necessity receipt records:

- proposed intervention plus explicit `justified_by` reality predicates;
- current target identity **and revision/state token**;
- required necessity predicates;
- observations scoped to the same predicate + target + revision;
- positive authority for evidence that can justify ACT;
- bounded negative authority / completeness witness before FALSE may justify ABSTAIN;
- unresolved evidence state;
- verdict: `ACT | ABSTAIN | INVESTIGATE | ESCALATE`.

See `schema/necessity.schema.json`.

## Run the reference gate

```bash
python src/gate.py examples/residual-act.json
```

Expected:

```text
ACT: all required evidence is scoped and intervention justification is currently witnessed
```

## Evaluate paired outcomes

```bash
python src/eval.py examples/paired-eval.json
```

The evaluator reports:

- `unnecessary_intervention_rate`
- `false_abstention_rate`
- `investigate_rate`
- `escalate_rate`
- `paired_accuracy`

## External anchors

This project treats neighboring work as constraints, not validation:

- **AgentAbstain** provides paired should-act / should-abstain evaluation and a critical-action boundary.
- **FixedBench** demonstrates already-fixed coding tasks and the partial-fix false-abstention failure mode.
- **scorekeeper** focuses on entitlement / overreach / underreach.
- **Microsoft Agent Control Specification** and related runtimes focus on policy enforcement at intervention points.

Residual Necessity should survive only if it remains distinct from those layers and produces independent measurable value.

See `docs/POSITIONING.md`, `docs/LANDSCAPE.md`, and `docs/USER_STORY_AUDIT.md`.

## Conformance vectors

Draft executable cases live in `conformance/core-cases.json`. They currently cover:

- residual violation after a partial fix → ACT;
- already-resolved request → ABSTAIN with bounded negative authority;
- retry after a successful prior transition → ABSTAIN;
- positive evidence from the wrong revision → INVESTIGATE;
- absence without negative authority → INVESTIGATE;
- human-only resolution → ESCALATE.

These are draft conformance vectors, not a stable standard or released compatibility promise.

## Kill criterion

Do not preserve this project merely because the abstraction is elegant.

If a mature neighboring system already provides all of the following, the right move is to contribute upstream instead:

1. model-external current-state necessity predicates;
2. explicit residual-violation semantics;
3. stale / unknown / conflicted evidence handling;
4. pre-side-effect enforcement;
5. two-sided measurement of unnecessary action and false abstention;
6. a stable external interface adopted by real runtimes.

## License

Apache-2.0.
