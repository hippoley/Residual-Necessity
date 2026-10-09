# Adversarial Internal Audit — 2026-10-09

This document is a self-audit, not a project pitch.

Its purpose is to record where Residual Necessity can still fool itself, what was corrected, what remains unproven, and which external node currently has the highest long-term value.

## 1. What the project actually is

Residual Necessity is currently a deterministic receipt evaluator for one narrow question:

> Does current, externally grounded evidence still justify this proposed state transition?

The durable candidate primitive is not the Python gate itself. It is the evidence boundary:

```text
predicate
+ target identity
+ target revision/state token
+ positive or bounded negative authority
→ justified / unnecessary / unresolved
```

The implementation is disposable if a stronger adopted system owns the same semantic boundary.

## 2. What is already real

### Core semantics

Implemented and tested:

- explicit intervention → reality-predicate justification;
- scoped positive authority for ACT;
- scoped negative authority before FALSE may justify ABSTAIN;
- revision/state-token binding;
- UNKNOWN / STALE / CONFLICTED fail closed;
- freshness/scope failure does not masquerade as “problem solved”;
- human-only resolution escalates;
- malformed / unknown core receipt fields fail closed in both schema and runtime;
- contradictory TRUE+negative / FALSE+positive authority fails closed;
- orphan observations fail closed.

### External runtime interoperability

Real public CI currently exercises:

- Agent Hooks Beta `agent-hooks-sdk==0.1.0b1`;
- Microsoft ACS `agent-control-specification==0.3.1b1`;
- ExecSurface public typed-evidence contract;
- AgentAbstain public benchmark data.

This is interoperability, not adoption.

### External human qualification

ExecSurface maintainers independently classified one preserved Residual-Necessity workload record under their own preregistered process.

This is external evidence qualification, not dependency, citation, or endorsement.

## 3. Self-deception paths found during this audit

### 3.1 Schema strictness was not runtime strictness

Before this audit, JSON Schema allowed unknown fields in most core objects and `gate.evaluate()` did not invoke the schema.

A typo such as `human_ony` could pass schema validation and be ignored by the runtime.

Correction:

- close core schema objects;
- independently reject unknown fields in the gate;
- reject malformed predicates/interventions and orphan observations.

### 3.2 Legitimate-action recall could be gamed

The evaluator previously counted only explicit `ABSTAIN` as false abstention.

A system could return `INVESTIGATE` on every required-action case and report zero false-abstention while never acting.

Correction:

- any non-ACT outcome on expected-ACT counts as missed required action;
- report `missed_required_action_rate`;
- retain `false_abstention_rate` only as a compatibility alias;
- report `act_recall`.

### 3.3 The gold firewall leaked scenario semantics through pair_id

The blind AgentAbstain view removed `category` but retained `pair_id = category/task_id`.

That did not directly reveal ACT/ABSTAIN, but it contradicted the claim that category was hidden and enabled category-aware heuristics.

Correction:

- replace inference-side pair ids with stable opaque hashes;
- retain source pair ids only in the hidden label file;
- lock this with tests and CI assertions.

### 3.4 Permit evidence disappears after Agent Hooks all-allow composition

A Residual Necessity interceptor can return `allow + evidence`.

Agent Hooks default all-permit composition synthesizes a bare combined allow and unions warnings/result labels, not evidence.

Therefore the host-level permit record can lose the evidence pointer that justified the permit.

Status:

- reproduced on the public Beta SDK;
- documented as an upstream contract question;
- not submitted upstream yet because the current GitHub integration cannot create issues in that repository;
- no downstream workaround should be normalized before upstream semantics are clarified.

### 3.5 Node documents had become stale

ADL had remained open as the stated highest-value standards node after Agent Hooks became a stronger live control/conformance surface.

Correction:

- close the ADL node checkpoint as superseded;
- preserve the reasoning and surviving record-vs-predicate completeness distinction;
- make Agent Hooks the current primary ecosystem node.

## 4. User-story maturity, not binary completion

### Semantically closed

US-01 through US-20 are largely closed at reference/runtime-contract level, subject to the explicit scopes in `docs/USER_STORY_AUDIT.md`.

### Externally grounded but not adopted

- US-21 — one external ExecSurface evidence qualification;
- US-19/20 — real Agent Hooks / ACS runtime interoperability.

These are not third-party dependency.

### Existentially open

- US-26 — blinded AgentAbstain inference from tool-visible current state;
- US-27 — measurable improvement without ACT-recall collapse;
- US-28 — meaningful non-trivial baseline;
- US-29 — real partial-fix evaluation;
- US-36 — upstream permit-evidence composition semantics.

### Intentionally blocked

US-30 packaging is blocked until the existential benchmark result survives. Publishing a stable API now would optimize distribution before proving value.

## 5. Highest-value node now

Current valuation:

1. **Agent Hooks control / conformance ecosystem**
2. bounded predicate completeness / evidence authority
3. AgentAbstain paired Reality Gate
4. external runtime evidence providers such as ExecSurface
5. ACS compatibility
6. ADL as a secondary standards option

Why Agent Hooks is first:

- framework-neutral control contract;
- Beta normative spec;
- five SDKs;
- language-agnostic CTK;
- conformance-claim process;
- governance/proposal process;
- existing `extensions` and evidence seams;
- multiple frameworks can consume one interceptor contract.

The project should seek to become useful to that ecosystem rather than make another framework.

## 6. Immediate closure sequence

### A. Tool-visible AgentAbstain probe boundary

Required invariant:

- environment may internally mount benchmark initial state;
- Residual Necessity probe logic MUST NOT read raw environment state;
- probe logic MAY use only tool-visible lookup/verify results;
- commit-class tools are forbidden during observation collection;
- inference view receives no task type, trigger, execution DAG, critical actions, transformation metadata, or semantic category identifier.

A real CI probe is being added against the public executable sandbox.

### B. Blinded prediction

After probe evidence is available:

- define explicit current-state predicates without reading gold;
- freeze predictions;
- reveal hidden labels only in scoring;
- report unnecessary intervention, missed required action, ACT recall, investigate/escalate burden, and paired accuracy.

### C. Reasonable baseline

At minimum compare against:

- always ACT;
- always ABSTAIN;
- always INVESTIGATE;
- a simple evidence-only runtime heuristic that does not use Residual Necessity receipt semantics.

### D. Real partial fix

FixedBench establishes the partial-fix false-abstention failure mode, but a directly consumable public partial-fix executable corpus is not currently integrated.

Do not mark US-29 closed with a synthetic fixture.

### E. Upstream control/conformance contribution

After a concrete cross-SDK semantic question is reproducible:

- prefer a small CTK/vector/spec clarification upstream;
- do not pitch a competing standard;
- require a real maintainer response before counting external discussion.

## 7. Merge / history hygiene

PR #2 is intentionally a Reality Gate foundation branch, but it is large.

Before merge:

- latest-head CI must be green;
- user-story audit must match code;
- README and PR body must match external evidence;
- no known metric self-deception remains.

Then squash-merge so `main` receives one coherent checkpoint rather than preserving exploratory commit noise as the primary history.

## 8. Kill / upstream decision

Stop standalone growth if any of these becomes true:

1. real paired evaluation does not beat reasonable baselines without ACT-recall collapse;
2. a mature external system adopts equivalent predicate-scoped positive/negative evidence authority;
3. the only surviving novelty is vocabulary for stale/no-op/retry behavior;
4. third-party value comes from the conformance/evidence pieces rather than the standalone gate.

In those cases, preserve the public evidence and move the useful semantics upstream.

## 9. Current honest status

- third-party dependency on this repository: **0**
- third-party adoption: **0**
- third-party citation: **0**
- external semantic/evidence interaction: **yes**
- canonical runtime interoperability: **yes**
- benchmark superiority: **not proven**
- real partial-fix result: **not proven**
- standards contribution accepted upstream: **0**

The project is improving, but it has not yet crossed from “credible participant with externally grounded artifacts” to “infrastructure others must rely on”.
