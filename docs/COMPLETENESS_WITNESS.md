# Completeness Witness for Negative Necessity Evidence

Residual Necessity operates in an open world by default.

If a runtime observer does not report a violation, the system does **not** infer that the violation is absent. Missing evidence remains unknown unless the observer provides a bounded completeness witness for the exact predicate and target under evaluation.

This is not a new logical principle. It follows the long-standing distinction between open-world reasoning and locally justified closed-world reasoning. Database and knowledge-representation work uses completeness statements to make explicit when absence may support a sound negative conclusion.

Residual Necessity applies that idea to state-changing agent actions.

## Runtime contract

A negative authority witness is scoped to:

- one necessity predicate;
- one target identity;
- the current target revision when a revision exists;
- one explicit basis for completeness;
- one inspectable evidence reference.

Example:

```json
{
  "status": "FALSE",
  "negative_authority": {
    "scope": {
      "predicate_id": "residual_violation_exists",
      "target_identity": "service:payments",
      "target_revision": "sha256:..."
    },
    "basis": "authoritative_query",
    "evidence_ref": "sha256:..."
  }
}
```

The reference gate accepts this FALSE only when the witness scope matches the receipt being evaluated.

A witness for another target, another predicate, or an older revision has no negative authority over the current intervention.

## Why this matters

Without an explicit completeness witness:

```text
not observed
    !=
proved absent
```

Collapsing those states creates false abstention: the agent may refuse a still-required intervention merely because its observer was incomplete.

With a bounded witness:

```text
complete for predicate P
+ exact target/revision
+ P not present
----------------------
P may be admitted as FALSE
```

## Non-goals

This repository does not claim to invent:
- open-world semantics;
- closed-world reasoning;
- completeness statements;
- explicit negative information.

The experimental contribution under test is narrower:

> Can bounded completeness witnesses make intervention-necessity decisions safer and more reusable at agent runtime boundaries?

The project should survive only if that runtime application produces measurable value on stale, already-resolved, partial-fix, retry, or repeated-action cases.
