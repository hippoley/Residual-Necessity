# User Story Audit

Status vocabulary:

- **CLOSED** — implemented and covered by executable tests or external evidence.
- **PARTIAL** — code exists but an external/runtime acceptance test is still pending.
- **OPEN** — promised by positioning or required by Reality Gate but not yet implemented.
- **DE-SCOPED** — explicitly removed because the repository cannot currently justify the claim.

## Core decision semantics

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-01 | As a runtime, I only ACT when a current violated reality predicate is explicitly linked to the proposed intervention. | CLOSED | `intervention.justified_by` must reference required reality predicates; core tests reject unknown/non-reality justification. |
| US-02 | As a runtime, TRUE evidence from the wrong target/revision must never authorize ACT. | CLOSED | Positive authority is scoped to predicate + target + revision; wrong-target/revision tests return INVESTIGATE. |
| US-03 | As a runtime, absence alone must never become FALSE. | CLOSED | FALSE without scoped negative authority returns INVESTIGATE. |
| US-04 | As a runtime, authoritative FALSE for the exact predicate/target/revision may justify ABSTAIN. | CLOSED | Bounded negative-authority witness + conformance case `already-resolved-abstain`. |
| US-05 | As a runtime, missing / UNKNOWN / CONFLICTED / STALE required evidence must not silently authorize mutation. | CLOSED | Gate maps unresolved required evidence to INVESTIGATE. |
| US-06 | As a runtime, a human-only predicate must route to human resolution. | CLOSED | Core test + conformance vector `human-only-escalate`. |
| US-07 | As a runtime, a stale request that is already satisfied should ABSTAIN when current-state absence is authoritative. | CLOSED | Conformance vector `already-resolved-abstain`. |
| US-08 | As a runtime, a retry/repeated action should ABSTAIN when the previous transition already satisfied the invariant. | CLOSED | Conformance vector `retry-after-success-abstain`. |
| US-09 | As a runtime, a partial fix must still ACT when the historical symptom is gone but a residual violated property remains. | CLOSED | `examples/residual-act.json` + conformance vector `partial-fix-residual-act`. |
| US-10 | As a runtime, FALSE freshness/scope must not be confused with “problem solved”. | CLOSED | Freshness/scope FALSE returns INVESTIGATE; core test covers freshness. |
| US-11 | As a runtime, duplicate predicate IDs or malformed justification references must fail closed. | CLOSED | Core tests reject duplicates and unknown justification predicates. |

## Evidence-provider semantics

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-12 | As an evidence consumer, I can distinguish record/evidence completeness from proposition-level completeness. | CLOSED at reference-contract level | `docs/COMPLETENESS_WITNESS.md`; gate requires bounded negative authority. |
| US-13 | As an ExecSurface consumer, matching typed evidence can become a scoped TRUE observation without inheriting policy authority. | CLOSED in adapter tests | Adapter validates typed/raw consistency and emits `positive_authority` scoped to receipt target/revision. |
| US-14 | As an ExecSurface consumer, incomplete or unsupported evidence stays UNKNOWN. | CLOSED | Adapter tests cover incomplete collection and unsupported capability. |
| US-15 | As an ExecSurface consumer, effect absence must not become FALSE until the producer grants proposition-specific negative authority. | CLOSED by conservative contract | Absence returns UNKNOWN; external contract question is open upstream. |
| US-16 | As a consumer, contradictory typed/raw evidence must fail closed. | CLOSED | Backend, completeness, and warning-code mismatch tests. |
| US-17 | As a runtime, every decision is pinned to a current target revision/state token rather than relying on wall-clock freshness heuristics. | CLOSED for draft semantics | `target.revision` is required; positive/negative authority must match it. Wall-clock TTL is intentionally not inferred by the gate. |

## Governance/runtime integrations

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-18 | As an ACS host, policy decisions must inherit the same core gate semantics instead of trusting a naked status. | CLOSED in code/tests | ACS annotator now consumes a full receipt and calls `gate.evaluate()`. |
| US-19 | As an Agent Hooks host, scoped ACT permits while ABSTAIN/unresolved evidence blocks before the side effect. | CLOSED for canonical control contract | Agent Hooks Beta E2E is green on push and PR runs using the real InterceptionEmitter. |
| US-20 | As an ACS/audit consumer, each verdict is bound to the exact receipt used for the decision. | CLOSED in bridge | Annotation includes receipt SHA-256 digest; ACS evidence artefact references it. Released ACS 0.3.1b1 PRE_TOOL_CALL compatibility is green. |
| US-21 | As an external project, I can independently reproduce a real Residual-Necessity workload result. | CLOSED for one upstream evidence record | ExecSurface maintainers independently qualified one run as genuine external real-workload evidence. |
| US-22 | As a standards implementer, I can use an executable conformance pack rather than prose examples. | PARTIAL | `conformance/core-cases.json` exists and is executed in tests; Agent Hooks interoperability is green, but no upstream CTK/conformance claim exists yet. |

## Evaluation / Reality Gate

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-23 | As an evaluator, unnecessary intervention and missed required action use the correct class-conditional denominators. | CLOSED after audit fix | Expected-ABSTAIN ACTs count as unnecessary intervention; expected-ACT **any non-ACT** counts as false abstention / missed required action; `act_recall` is reported so always-INVESTIGATE cannot game the metric. |
| US-24 | As an evaluator, paired accuracy only scores complete ACT/ABSTAIN pairs. | CLOSED | Incomplete pairs excluded; duplicate members rejected. |
| US-25 | As a benchmark consumer, hidden gold never leaks into inference. | CLOSED for data preparation | AgentAbstain blind-slice tests and CI boundary. |
| US-26 | As a cross-benchmark stress test, Residual Necessity-derived evidence semantics should generalize to AgentAbstain's tool-visible runtime cases without collapsing capability/risk/support into necessity. | SUPERSEDED BY EVIDENCE | Development run 37894155290 produced 0.78% accuracy, 0% ACT recall, 0% paired accuracy and 99.2% INVESTIGATE. AgentAbstain's constraint-heavy gold is retained as falsification evidence, not an RN success gate. |
| US-27 | As a project, I can demonstrate two-sided utility on a broader external benchmark without collapsing legitimate-action recall or violating the support-vs-necessity boundary. | SUPERSEDED BY EVIDENCE | AgentAbstain broader superiority is no longer pursued as an acceptance gate. Generic probe-success caused 82.47% unnecessary intervention and the proposition-specific development candidate still had 0% ACT recall. |
| US-28 | As a project, I compare against always-act, always-abstain, and at least one reasonable evidence/repair baseline. | CLOSED for first evidence baseline | Run 37875541342 scored frozen gold-blind `failure_only` and `probe_success` runtime-evidence baselines. `probe_success` retained 88.66% ACT recall but still caused 81.44% unnecessary intervention and only 7.22% paired accuracy, falsifying generic probe-success semantics. |
| US-29a | As a project, residual/partial-fix semantics are grounded in a real external software history rather than only synthetic fixtures. | CLOSED | P3 run 37876394371 froze a pinned real-world base → two partial attempts → expected-fix sequence from `andwn/cave-story-md`; evidence hash `4a34d59c...`, artifact 11592786218. |
| US-29b | As a project, an agentic partial-fix evaluation shows the gate acts on a residual violation without false abstention after the historical symptom changes. | CLOSED for one bounded real external path | Public P3 residual-pair run 37892134518 checked real `andwn/cave-story-md` revisions: partial revision `62d8c669...` produced scoped TRUE necessity → ACT; final fix `2c11d40f...` produced scoped FALSE necessity → ABSTAIN. This is a bounded issue-derived oracle, not a claim that all residual bugs are automatically discoverable. |

## Product / dependency surface

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-30 | As a third-party developer, I can install a versioned package and import a stable API. | BLOCKED — external consumption/reviewability first | Packaging remains intentionally deferred until US-22 has an independent external consumer and US-33 yields a reviewable public checkpoint. It no longer depends on superseded AgentAbstain utility goals. |
| US-31 | As a third-party developer, schema changes are versioned and examples cannot silently drift. | CLOSED for current draft | Receipt schema bumped to 0.3; examples/conformance validated by JSON Schema in CI. |
| US-32 | As a third-party developer, the repository has a canonical license file. | CLOSED | Full canonical Apache-2.0 license text installed. |
| US-33 | As a reviewer, one PR tells one coherent story. | PARTIAL, materially improved | PR #2 is now reframed around one Reality Gate foundation: receipt semantics + benchmark boundary + canonical runtime/evidence interoperability + explicit node migration. It remains a large 90+ commit draft until latest-head CI is green and it is squash-merged. |
| US-34 | As a maintainer, latest commits cancel superseded CI so one PR does not accumulate stale runs. | CLOSED | Workflow concurrency + cancel-in-progress added. |
| US-35 | As a runtime integrator, unknown or misspelled control fields cannot silently change semantics even when JSON Schema validation is bypassed. | CLOSED after audit fix | Schema core objects are closed and `gate.evaluate()` independently fails closed on unknown fields, malformed predicates/interventions, and orphan observations. |
| US-36 | As an Agent Hooks audit consumer, evidence supporting a permit remains attributable after verdict composition. | OPEN upstream-contract gap | Real Beta E2E shows interceptor permit evidence is not preserved on synthesized combined allow; reproduction is frozen in `docs/AGENT_HOOKS_PERMIT_EVIDENCE_NOTE.md`. No upstream acceptance yet. |
| US-37 | As a Reality Gate runner, I can obtain AgentAbstain observations while keeping probe selection/prediction blind to hidden initial state and gold task metadata. | CLOSED for process-isolated boundary | Run 37875541342 used separate minimal-env subprocesses for selector and predictor, read-only lookup/verify tools only, frozen 194 predictions before gold scoring, and source firewalls; trusted harness knowledge remains explicit. This closes isolation, not predictive value. |
| US-38 | As an evidence consumer, external action-support evidence cannot masquerade as residual necessity, and schema-valid/defaulted tool calls cannot become proposition evidence until required semantics are bound. | VERIFIED CLOSED | Probe artifacts now carry arguments, provenance, bound/unbound fields, and `binding_complete`; incomplete binding is forced to UNKNOWN. This was added after development evidence showed blank/default verify calls for fleet/date/account/portfolio tasks. |
| US-39 | As a control runtime, a real external residual predicate distinguishes a partial state that still requires action from the final fixed state, while positive evidence for one sub-intervention cannot authorize unrelated work. | VERIFIED CLOSED | Provider profiles declare `decision_scope.intervention` and `task_coverage`. Partial FALSE may block a required sub-action; partial TRUE remains INVESTIGATE. Only complete task coverage can map TRUE to ACT. |
| US-40 | As a benchmark researcher and maintainer, Verified Closed requires vertical closure plus ten-dimensional horizontal closure, and candidate-development scoring cannot consume holdout labels accidentally. | VERIFIED CLOSED | Development scorer re-checks the frozen hash partition and rejects any pair assigned to holdout. |
| US-41 | As a third-party benchmark consumer, I can discover, reproduce, interpret, and submit methods against the benchmark without reading implementation internals or silently contaminating holdout. | PARTIAL — latest full Reality Gate rerun pending | Dataset Card + Croissant 1.1 metadata are present; official `mlcroissant==1.1.0` validation passed; benchmark manifest, pair-bootstrap CI, split/category audit, sealed holdout policy, and Method Card schema are machine-verifiable. Full current-head AgentAbstain rerun is the remaining cross-system check before horizontal closure. |

## Claims deliberately de-scoped

| ID | Former claim | Status | Reason |
| --- | --- | --- | --- |
| DS-01 | “Compute the smallest justified state change.” | DE-SCOPED | No action-effect/minimization model exists. Current project only judges whether the proposed transition is justified. |
| DS-02 | “Pre-action evidence gate” as primary novelty. | DE-SCOPED | Too crowded; overlaps ACS/OAP/TwinCheck and other runtime-governance work. |
| DS-03 | “No-op/stale/retry detection” as primary novelty. | DE-SCOPED | TwinCheck and adjacent work already cover significant portions. |
| DS-04 | “Fill ADL §8.8.” | DE-SCOPED | ADL §8.8 is record omission completeness; predicate completeness is a distinct question and must not be conflated. |

# Remaining closure order

The repository should not expand framework surface until these are resolved in order:

1. **P0 — CLOSED, but continuously regression-gated.**
   US-38 SafeAct semantic-boundary interop, US-39 real P3 residual pair, and US-40 horizontal-closure enforcement are the current semantic P0. Any regression reopens P0 immediately.
2. **US-41 — benchmark asset horizontal closure.**
   Standardized metadata, uncertainty reporting, split governance, holdout sealing, and Method Card submission now exist. Close only after the latest full AgentAbstain Reality Gate reruns successfully on the same head.
3. **US-36 / US-22 — Agent Hooks upstream/conformance reality.**
   Canonical runtime interoperability is green; external maintainer discussion, CTK vector, or accepted conformance artifact is still absent.
4. **US-33 — PR/history cleanup.**
   Latest-head CI must remain green, then squash-merge the Reality Gate foundation so main has one reviewable checkpoint.
5. **US-30 — package only after independent conformance consumption + reviewable public checkpoint.**
   Do not freeze an API merely because local integrations work.
6. **US-26 / US-27 — superseded cross-benchmark hypothesis.**
   AgentAbstain remains a falsification/stress benchmark. Re-open only if a new proposition-specific external contract changes the semantic mismatch; do not tune profiles simply to chase its labels.
7. **Time-based TTL remains out of scope unless a real workload proves revision/state-token binding insufficient.**

If future real-world evidence shows the narrow necessity primitive adds no value beyond mature support/policy/control contracts, stop independent framework growth and upstream only the useful conformance/evidence pieces.
