# Node Valuation

Residual Necessity is a vehicle, not a destination.

The project should continuously move toward the highest-value external node where existing work can compound into durable identity, dependency, citation, governance influence, or standards position.

## Current node stack

### N0 — standalone gate/framework
Value: low.

A self-contained pre-action gate is crowded and easy to absorb into larger agent runtimes.

Do not optimize for framework surface area.

### N1 — residual-necessity runtime primitive
Value: medium.

Distinct question:
> What current violated condition still exists that makes any further state transition necessary?

Useful, but adjacent work such as abstention benchmarks and action-repair systems substantially overlaps stale/no-op/retry behavior.

### N2 — bounded predicate completeness / evidence authority
Value: high.

Core question:
> When may an observation soundly support TRUE or FALSE for a specific predicate, target, and revision?

This is model-external, reusable across runtimes, and directly affects both unnecessary action and false abstention.

Current implementation:
- predicate-scoped positive and negative authority;
- target/revision binding;
- explicit completeness/evidence basis;
- inspectable evidence reference;
- absence without bounded negative authority remains unresolved.

### N3 — Agent Hooks control / conformance ecosystem
Value: **highest currently observed**.

External surface:
`responsibleai/agent-hooks` — AGENT-HOOKS-0.1.

Why this node outranks framework-specific integration:

- framework-neutral host/interceptor control contract;
- Beta specification with five-language SDKs;
- language-agnostic Conformance Test Kit;
- formal third-party conformance-claim process;
- explicit governance and design-proposal process;
- namespaced `extensions.<namespace>` seam for optional interoperable data;
- standard verdict `evidence` pointer;
- explicit acknowledgement that interception points do not prove complete mediation;
- ACS is itself only one conformant interceptor on this contract.

Residual Necessity therefore has a natural role as a **specialized interceptor / evidence-semantics profile**, not another host framework or policy engine.

The current experimental adapter:
- reads a Residual Necessity receipt from `extensions.residual_necessity.receipt`;
- evaluates it through the same core gate;
- maps ACT / ABSTAIN / unresolved outcomes into the standard Agent Hooks verdict model;
- binds the receipt digest through standard Agent Hooks evidence.

This path is higher value because any conformant host can potentially consume the primitive without Residual Necessity owning framework glue.

### N4 — canonical ACS policy-engine interoperability
Value: high, but below Agent Hooks.

External surface:
`responsibleai/agent-control-spec`.

ACS owns policy decision semantics behind Agent Hooks. Residual Necessity should interoperate with it, but should not bend its core abstraction around one ACS SDK wrapper.

The legacy Microsoft `agent-control-specification==0.3.1b1` compatibility test remains useful as evidence, but it is no longer the strategic center.

### N5 — ADL standards / predicate-completeness discussion
Value: high-optionality, secondary.

ADL Runtime Protocol remains relevant because it has a completeness/witness design surface, but its reserved completeness is record-level omission detection rather than proposition-level completeness.

The important distinction remains:

> record completeness does not automatically imply predicate completeness.

ADL should be pursued only if maintainers confirm that this semantic distinction belongs in its protocol or conformance scope.

## Evidence supporting the current pivot

- ExecSurface independently qualified a Residual-Necessity workload run as a genuine external real-workload evidence record under its preregistered protocol.
- Real downstream consumption exposed the difference between successful workload execution and sufficient observation authority.
- AgentAbstain provides 97 runtime pairs / 194 variants and shows that static task text is insufficient; actual runtime state/execution logs are required for a valid result.
- TwinCheck substantially overlaps evidence-grounded action repair, stale arguments, retries, and no-op behavior; those cannot remain the primary novelty claim.
- Agent Hooks now provides the broadest live control/conformance surface that can host the primitive without requiring a parallel runtime standard.

## Pivot rules

Move upward when:
- an external standard/spec has an explicit interoperable seam;
- our existing evidence gives us a non-speculative contribution;
- entering that seam creates durable public contribution history;
- the node is harder for a larger model to absorb than a standalone implementation;
- one integration can reach multiple frameworks rather than one wrapper.

Move sideways when:
- another project owns the broader primitive but lacks our narrow evidence semantics;
- interoperability can create mutual dependency faster than competition.

Move downstream when:
- standards scope intentionally excludes the concept;
- conformance/value can still be demonstrated as implementation infrastructure.

Kill or upstream when:
- a mature adopted system already owns scoped proposition-level evidence authority/completeness;
- real paired evaluation shows no value beyond generic HOLD/repair/abstention;
- the project survives only by renaming existing concepts.

## Current decision

As of 2026-10-09:

> Prioritize Agent Hooks interoperability / conformance over standalone framework expansion and over framework-specific ACS glue.

Near-term code should exist only if it directly advances:
- a canonical Agent Hooks interceptor/conformance path;
- the AgentAbstain Reality Gate;
- an external evidence-provider contract;
- or a falsification case for bounded predicate completeness.

Do not add broad SDK, UI, dashboard, orchestration, or generic policy features before the real paired Reality Gate result exists.

This file should be updated whenever a materially higher-value node appears.
