# Provider Boundary

Residual Necessity does not define a general telemetry, authorization, policy, or evidence-transport format.

Its provider boundary is deliberately narrow:

> Convert externally inspectable current-world observations into proposition evidence that is scoped to one predicate, one target identity, and one target revision/state token.

## Provider responsibilities

A provider may emit:

- `TRUE` only with scoped positive authority;
- `FALSE` only with a bounded negative-authority / completeness witness;
- `UNKNOWN`, `CONFLICTED`, or `STALE` when the observation cannot support a sound truth value.

Every authoritative TRUE/FALSE must bind to:

- predicate id;
- target identity;
- target revision/state token;
- an explicit evidence basis;
- an inspectable evidence reference.

## What providers must not do

Providers must not:

- infer policy verdicts;
- treat absence as FALSE without proposition-level completeness;
- reuse evidence from another target or revision;
- silently upgrade incomplete/unsupported observations into authoritative truth;
- use an LLM's unsupported assertion as evidence authority.

## Ownership boundaries

- OpenTelemetry or equivalent systems own telemetry transport/observability.
- Runtime observers such as ExecSurface own their own observation semantics.
- Microsoft ACS or other governors own policy/intervention enforcement.
- Residual Necessity owns only the mapping from scoped current-state evidence to a necessity receipt and deterministic ACT / ABSTAIN / INVESTIGATE / ESCALATE semantics.

## Current integration rule

Adapters must feed the same core receipt/gate path. No integration is allowed to bypass `src/gate.py` by mapping a naked provider status directly to an allow/deny decision.


## Support is not necessity

A provider may establish that an action is **supported, permitted, authorized, or has satisfied prerequisites** without establishing that the action is **necessary now**.

Receipt 0.3 makes this boundary explicit:

- `role=constraint` is for support, permission, freshness, scope, authority, and other preconditions;
- `role=necessity` is reserved for a current violated condition whose truth may justify the proposed state transition;
- `intervention.justified_by` may reference only required `kind=reality, role=necessity` predicates.

The SafeAct interoperability adapter is intentionally one-way at this boundary: SafeAct deterministic rule support is projected as constraint evidence only. A SafeAct `SUPPORTED` result cannot by itself authorize Residual Necessity `ACT`, and a SafeAct missing/defer condition does not grant proposition-level negative authority.
