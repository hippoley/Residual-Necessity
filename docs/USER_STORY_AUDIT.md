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
| US-20 | As an ACS/audit consumer, each verdict is bound to the exact receipt used for the decision. | CLOSED in bridge | Annotation includes receipt SHA-256 digest; ACS evidence artefact references it. |
| US-21 | As an external project, I can independently reproduce a real Residual-Necessity workload result. | CLOSED for one upstream evidence record | ExecSurface maintainers independently qualified one run as genuine external real-workload evidence. |
| US-22 | As a standards implementer, I can use an executable conformance pack rather than prose examples. | PARTIAL | `conformance/core-cases.json` exists and is executed in tests; Agent Hooks interoperability is green, but no upstream CTK/conformance claim exists yet. |

## Evaluation / Reality Gate

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-23 | As an evaluator, unnecessary intervention and false abstention use the correct class-conditional denominators. | CLOSED | `src/eval.py` fixed; tests lock denominators. |
| US-24 | As an evaluator, paired accuracy only scores complete ACT/ABSTAIN pairs. | CLOSED | Incomplete pairs excluded; duplicate members rejected. |
| US-25 | As a benchmark consumer, hidden gold never leaks into inference. | CLOSED for data preparation | AgentAbstain blind-slice tests and CI boundary. |
| US-26 | As a benchmark consumer, Residual Necessity actually predicts AgentAbstain outcomes from current-state observations before labels are revealed. | OPEN | No inference/probe implementation over the 97 runtime pairs yet. |
| US-27 | As a project, I can demonstrate lower unnecessary intervention without collapsing legitimate-action recall. | OPEN — primary Reality Gate | No superiority result yet. |
| US-28 | As a project, I compare against always-act, always-abstain, and at least one reasonable evidence/repair baseline. | PARTIAL | Trivial baselines implemented; meaningful baseline comparison still open. |
| US-29 | As a project, partial-fix cases are present in the real evaluation, not only synthetic fixtures. | OPEN | Current partial-fix conformance vector is synthetic; external FixedBench artifact path remains unresolved. |

## Product / dependency surface

| ID | User story | Status | Acceptance evidence |
| --- | --- | --- | --- |
| US-30 | As a third-party developer, I can install a versioned package and import a stable API. | OPEN intentionally | No `pyproject.toml` / package release yet. Do not stabilize API before Reality Gate semantics settle. |
| US-31 | As a third-party developer, schema changes are versioned and examples cannot silently drift. | CLOSED for current draft | Receipt schema bumped to 0.2; examples/conformance validated by JSON Schema in CI. |
| US-32 | As a third-party developer, the repository has a canonical license file. | CLOSED | Full canonical Apache-2.0 license text installed. |
| US-33 | As a reviewer, one PR tells one coherent story. | PARTIAL | PR #2 has been retitled/reframed as the first Reality Gate branch, but it is still broad (core + AgentAbstain + ExecSurface + ACS + standards work). Keep draft until CI and merge gate are satisfied. |
| US-34 | As a maintainer, latest commits cancel superseded CI so one PR does not accumulate stale runs. | CLOSED | Workflow concurrency + cancel-in-progress added. |

## Claims deliberately de-scoped

| ID | Former claim | Status | Reason |
| --- | --- | --- | --- |
| DS-01 | “Compute the smallest justified state change.” | DE-SCOPED | No action-effect/minimization model exists. Current project only judges whether the proposed transition is justified. |
| DS-02 | “Pre-action evidence gate” as primary novelty. | DE-SCOPED | Too crowded; overlaps ACS/OAP/TwinCheck and other runtime-governance work. |
| DS-03 | “No-op/stale/retry detection” as primary novelty. | DE-SCOPED | TwinCheck and adjacent work already cover significant portions. |
| DS-04 | “Fill ADL §8.8.” | DE-SCOPED | ADL §8.8 is record omission completeness; predicate completeness is a distinct question and must not be conflated. |

# Remaining closure order

The repository should not expand framework surface until these are resolved in order:

1. **US-26 / US-27 / US-28 / US-29 — real paired evaluation.**
   This is the project’s existential gate.
2. **Agent Hooks upstream/conformance reality.**
   Canonical runtime interoperability is now proven locally/CI; external maintainer discussion or CTK contribution is still absent.
3. **US-33 — PR/history cleanup.**
   Public history must become reviewable before merge.
4. **US-32 — canonical license hygiene.**
5. **US-30 — packaging only after semantics survive the Reality Gate.**
6. **Time-based TTL remains out of scope unless a real workload proves revision/state-token binding insufficient.**

If the real evaluation cannot beat reasonable baselines without false-abstention collapse, stop independent framework growth and upstream the useful completeness/conformance pieces.
