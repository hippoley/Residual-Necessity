# Agent Hooks permit-evidence composition note

Status: downstream interoperability finding; **not submitted upstream yet** because the current GitHub integration cannot create issues in `responsibleai/agent-hooks`.

## Finding

With `agent-hooks-sdk==0.1.0b1`, an interceptor may return:

```json
{
  "decision": "allow",
  "reason": "current_state_justifies_action",
  "evidence": {"artefact": "sha256:..."}
}
```

Under the default `sequential/first_deny` composition profile, an all-permit result is synthesized as a new combined `allow` verdict.

The current composition code unions:
- warnings;
- permit `result_labels`.

It does not union `evidence`.

Therefore:
- the action correctly proceeds;
- the per-interceptor summary preserves the interceptor `reason`;
- the combined permit verdict does not preserve the interceptor evidence pointer.

## Why this matters

Some interceptors permit an action only because current evidence proves that the state transition is justified.

For those interceptors, evidence supporting `allow` can be as audit-relevant as evidence supporting `deny`.

Residual Necessity is one example:
- a current predicate is positively witnessed;
- the witness is scoped to predicate + target + revision;
- ACT is allowed;
- the receipt digest is returned as Agent Hooks §5.3 evidence.

Today that digest exists on the interceptor verdict but is lost when the host synthesizes the combined pure-allow verdict.

## Upstream contract question

Which behavior is intended?

1. **Winning-verdict-only evidence** — evidence belongs only to the selected combined verdict and pure synthesized allow intentionally has none.
2. **Permit evidence preservation** — evidence from permit verdicts survives composition under a deterministic rule.
3. **Per-interceptor evidence recording** — combined verdict remains unchanged, but each `verdicts[]` summary may carry an evidence pointer.

The project should not invent a downstream workaround using `result_labels` or unrelated context fields until Agent Hooks maintainers clarify the intended contract.

## Reproduction path

The Residual Necessity Agent Hooks interoperability experiment:
- returns allow + reason + receipt-digest evidence;
- passes through `InterceptionEmitter`;
- observes the combined allow;
- inspects the per-interceptor summary.

A minimal cross-SDK conformance vector can be contributed if the upstream project decides that permit evidence should survive composition.
