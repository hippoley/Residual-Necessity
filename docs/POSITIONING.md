# Positioning

Residual Necessity exists only if **necessity** is distinct from authorization, entitlement, intent consistency, and generic policy.

| Layer | Question | Example |
| --- | --- | --- |
| Authorization | May this actor use this capability/resource? | May the agent write this repository? |
| Intent consistency | Is this action consistent with the user's request? | Does this tool call match the requested objective? |
| Entitlement / scope | Did the request license this amount or area of work? | Did "fix the typo" license rewriting the parser? |
| Necessity | Does current reality still require this state transition? | Is the reported parser failure still violated on current main? |

A proposed action can be authorized, intent-consistent, in entitled scope, and policy-compliant while still being unnecessary.

## Residual necessity

Residual necessity asks:

> What violated condition still exists in the current state, and does it justify this proposed state transition now?

This matters in partially resolved cases. The historical symptom may be gone while a residual property is still violated.

The project should not claim novelty merely because this vocabulary is convenient. Its novelty claim must be earned by a real runtime or benchmark result that existing control layers cannot reproduce without adding an equivalent current-state necessity predicate.


## Explicit non-goal: intervention minimization

The current reference gate does **not** prove that an allowed intervention is the smallest possible mutation. It only checks whether the proposed intervention names current reality predicates that justify acting and whether the supporting evidence is scoped to the current target/revision.

Minimal-change optimization requires an additional action-effect model or counterfactual comparison layer. Until such a layer is implemented and measured, this repository must not claim to compute the smallest justified state change.
