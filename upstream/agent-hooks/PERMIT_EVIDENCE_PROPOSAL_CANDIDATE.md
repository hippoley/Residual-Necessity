# Agent Hooks upstream candidate: preserve per-interceptor permit evidence

Status: **downstream candidate only**. This is not an Agent Hooks proposal number, not a CTK vector, and not an upstream-accepted interpretation.

## Problem

AGENT-HOOKS-0.1 permits an interceptor verdict to carry `evidence` (§5.3).

Composition (§7.3) selects one winning verdict and unions only:

- `warnings`;
- permit `result_labels`.

For multi-verdict profiles, §10.3 records payload-free per-interceptor summaries in `verdicts[]`.

A downstream interoperability test found that an interceptor may return:

```json
{
  "decision": "allow",
  "reason": "current_state_justifies_action",
  "evidence": {"artefact": "sha256:..."}
}
```

while the synthesized all-allow combined verdict does not preserve that evidence pointer.

This means the host correctly proceeds but the durable record cannot later identify the evidence that caused an individual permitting interceptor to allow the action.

## Why not union evidence onto the combined verdict

`Verdict.evidence` is singular. Combining multiple unrelated evidence artefacts into one pointer would require a new container/manifest semantics and would change the verdict algebra.

That is unnecessary for the audit requirement.

## Minimal candidate

Extend each per-interceptor `verdicts[]` summary with an optional payload-free evidence pointer:

```json
{
  "index": 0,
  "decision": "allow",
  "reason": "current_state_justifies_action",
  "evidence": {"artefact": "sha256:..."}
}
```

Properties:

- does not change the winning/combined verdict;
- does not change enforcement obligations;
- does not require evidence contents to be understood by Agent Hooks;
- preserves the existing offline-verification pointer model from §5.3;
- allows permit-side justification to remain attributable after composition;
- applies equally to allow/deny/transform if the project prefers uniform summaries.

## Security / privacy constraint

Only the evidence pointer should be copied. Evidence payloads remain out of band. The same limits/redaction expectations that already apply to §5.3 evidence should apply to the record summary.

## Candidate CTK behavior

For a multi-interceptor all-allow emission:

- interceptor 0 returns allow + evidence A;
- interceptor 1 returns allow + evidence B;
- action proceeds;
- combined verdict remains allow;
- `verdicts[0].evidence.artefact == A`;
- `verdicts[1].evidence.artefact == B`.

This candidate intentionally does **not** require `verdict.evidence` on the combined allow.

## Downstream reproduction

Residual Necessity's Agent Hooks Beta interoperability test already demonstrates the motivating case:

- a current-state receipt is positively witnessed;
- the interceptor returns allow + receipt-digest evidence;
- `InterceptionEmitter` proceeds;
- the combined pure allow does not retain the receipt digest.

See `docs/AGENT_HOOKS_PERMIT_EVIDENCE_NOTE.md`.

## Upstream decision still required

Agent Hooks maintainers may instead decide that permit-side evidence is intentionally ephemeral or that only the winning verdict's evidence belongs in the record. If so, the specification should state that explicitly and downstream controls must not assume permit evidence survives composition.
