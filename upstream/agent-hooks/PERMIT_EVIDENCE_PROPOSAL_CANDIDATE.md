# P-XXX: Preserve permit-side evidence attribution across composition

**Status:** **Downstream draft** — not submitted upstream; proposal number intentionally unassigned.
**Raised by:** downstream Agent Hooks consumer `hippoley/Residual-Necessity`, based on a reproducible Beta interoperability case.

## Gap

AGENT-HOOKS-0.1 §5.3 allows an interceptor verdict to carry an `evidence` artefact pointer.

For multi-interceptor composition, §7.3 synthesizes a combined verdict and unions selected metadata such as warnings and permit result labels. §10.3 records payload-free per-interceptor summaries in `verdicts[]`.

A real downstream interceptor can therefore return:

```json
{
  "decision": "allow",
  "reason": "current_state_justifies_action",
  "evidence": {"artefact": "sha256:..."}
}
```

and the host correctly proceeds, while the durable composed record no longer retains the evidence pointer that justified that individual permit.

The motivating downstream case is an evidence-dependent state-transition control: the action may proceed only because a current-world receipt established a required proposition. The control result is preserved as an allow, but the artefact that justified the allow is not attributable after composition.

This is an audit/record question, not an enforcement bug. The current host behavior remains fail-closed where required.

## Options

### Option A — Evidence is winning-verdict-only

Define that `Verdict.evidence` belongs only to the verdict that survives composition. Interceptor evidence on non-winning or synthesized permit results is intentionally ephemeral.

**Pros**
- no wire change;
- no additional record growth;
- simplest semantics.

**Cons**
- evidence-dependent permits become unauditable after composition;
- downstream controls must invent another attribution channel;
- a single-interceptor all-allow path can lose its evidence even though no competing verdict replaced it.

### Option B — Compose permit evidence onto the combined verdict

Extend composition so evidence from permitting interceptors is represented by the combined verdict.

**Pros**
- all permit evidence is visible in one place.

**Cons**
- current `Verdict.evidence` is singular;
- requires a new evidence collection/manifest model;
- changes verdict algebra and aggregation semantics;
- higher compatibility and implementation cost.

### Option C — Preserve evidence on per-interceptor record summaries

Extend each §10.3 `verdicts[]` summary with an optional evidence pointer:

```json
{
  "index": 0,
  "decision": "allow",
  "reason": "current_state_justifies_action",
  "evidence": {"artefact": "sha256:..."}
}
```

The combined verdict is unchanged.

**Pros**
- preserves attribution without changing enforcement or winner selection;
- reuses the existing §5.3 out-of-band evidence pointer;
- avoids inventing evidence-union semantics;
- naturally supports multiple interceptors with independent evidence.

**Cons**
- changes the record shape;
- requires spec/schema/CTK updates across all SDKs;
- increases record size slightly.

## Recommendation

**Option C.**

The record already preserves per-interceptor decision/reason summaries. Evidence attribution is the same category of provenance: it explains the basis of an individual control result without changing the aggregate decision.

Only the evidence pointer should be copied. Evidence payloads remain out of band.

## Security and privacy

- Do not inline evidence payloads.
- Apply existing evidence-pointer size/redaction requirements.
- A host must not treat the presence of an evidence pointer as trust in the referenced content.
- The change is audit-only and must not alter composition severity or enforcement.

## Conformance impact

If adopted, add a CTK vector for an all-allow multi-interceptor composition where each interceptor returns a distinct evidence artefact. The record should preserve both pointers under the corresponding `verdicts[]` entries while the combined verdict remains `allow`.

A downstream schema-valid candidate is maintained at:

`upstream/agent-hooks/AH-CTK-candidate-permit-evidence.json`

## Reproduction

Residual Necessity runs as a real Agent Hooks Beta interceptor and returns allow + receipt-digest evidence for a positively witnessed necessity receipt. The canonical emitter proceeds, but the composed all-allow record does not retain that evidence pointer on the combined verdict or per-interceptor summary.

The same repository now also exercises a real external P3 partial/final revision pair through the Agent Hooks control plane.

## Decision needed

- [ ] Is permit-side interceptor evidence intentionally ephemeral after composition?
- [ ] If not, should attribution live in the combined verdict or in `verdicts[]`?
- [ ] If per-interceptor attribution is preferred, should the optional field apply uniformly to allow/deny/transform summaries?
