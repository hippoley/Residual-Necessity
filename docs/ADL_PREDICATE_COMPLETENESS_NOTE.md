# ADL Runtime Evidence: Record Completeness vs Predicate Completeness

Status: **downstream implementation note / RFC candidate**, not an ADL proposal and not an ADL-endorsed interpretation.

## Summary

ADL Runtime Protocol §8 distinguishes tamper-evidence/freshness from completeness and reserves §8.8 for a future witness/transparency-log tier that can detect omitted enforcement records.

A downstream consumer exposes a second completeness dimension:

- **record completeness** — were enforcement records/events omitted?
- **predicate completeness** — is an observation source exhaustive enough for proposition P over target T at revision R that absence may soundly support P = FALSE?

A complete record does not automatically imply predicate completeness.

## Motivating counterexample

Suppose a future §8.8 witness proves that an enforcement record sequence is omission-free.

The record contains no observation of:

`residual_violation_exists(service:payments@r42)`

That absence does not establish the predicate is false if the observer itself:
- did not monitor the relevant subsystem;
- could not observe the relevant effect class;
- observed an earlier revision;
- sampled instead of exhaustively checking;
- lost events before the governor received them.

The transparency log may be complete while the proposition-level evidence remains incomplete.

## Proposed normative clarification candidate

A future Runtime Protocol clarification could say:

> A complete enforcement record MUST NOT be interpreted as proposition-level negative evidence unless the observation source separately establishes completeness for the proposition and target scope being negated.

This is intentionally weaker than proposing new syntax.

## Possible future completeness witness

If ADL later decides that proposition-level completeness belongs in protocol scope, a witness would need at least:

- proposition/predicate identity;
- target identity;
- target revision or equivalent state pin;
- basis for completeness;
- evidence reference;
- optional validity/freshness boundary.

Residual-Necessity currently experiments with this shape, but that implementation is not proposed as normative ADL syntax.

## Conformance probes

A useful future conformance pack could include:

1. complete record + incomplete observer + absent predicate → MUST NOT infer FALSE;
2. complete record + witness for wrong target → MUST NOT infer FALSE;
3. complete record + witness for stale revision → MUST NOT infer FALSE;
4. complete record + scoped completeness witness + absent predicate → MAY admit FALSE;
5. positive observation → TRUE does not require negative completeness authority.

## Why Residual Necessity cares

Residual Necessity asks whether any currently violated condition still justifies the next state transition.

False negative evidence is dangerous because it creates false abstention: an agent may stop a still-required intervention merely because an observer failed to see the violation.

The project therefore treats bounded predicate completeness as a prerequisite for authoritative FALSE.

## Relationship to ADL §8.8

This note does **not** claim to fill §8.8.

§8.8 currently addresses third-party witnessing / transparency logs for omission detection in enforcement records. Predicate completeness is a separate semantic layer that may belong:
- in Runtime Protocol guidance;
- in a future evidence-provider profile;
- in conformance material;
- or outside ADL entirely.

That scope question should be decided by ADL maintainers, not assumed by this project.

## External implementation evidence

Residual-Necessity has a real downstream evidence consumer and has already surfaced incomplete-observation behavior in an external ExecSurface workload. ExecSurface maintainers independently qualified that run as a genuine external real-workload evidence record under their preregistered protocol.

This gives the distinction a concrete implementation basis rather than only a theoretical motivation.
