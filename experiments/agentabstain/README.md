# AgentAbstain runtime reality test

This experiment uses the public AgentAbstain dataset as an **external source of runtime cases**.

It deliberately excludes the five pre-execution categories. The initial target is only the three runtime scenarios:

- critical tool failure;
- conflicting evidence;
- emergent risk discovery.

These are the cases where the agent must learn something from the environment before deciding whether a state-changing action remains justified.

## Gold firewall

The inference view MUST NOT contain:

- `task_type`;
- `abstention_trigger`;
- `execution_dag`;
- `critical_actions`;
- category / transformation metadata.

The labels are written to a separate file used only after predictions are frozen.

The repository is not allowed to claim a benchmark result if the inference path reads the labels file.

## Why runtime-only

Residual Necessity is not intended to compete with intent/scope/ambiguity classifiers.

Runtime AgentAbstain cases are a cleaner falsification test because the decisive information is discovered through tool/environment state.

## Current milestone

The first milestone is intentionally modest:

1. consume the external public dataset directly in CI;
2. verify the blind runtime slice can be produced without gold leakage;
3. freeze an inference interface;
4. obtain tool-visible runtime observations through a trusted harness while keeping the selector blind to task type, gold metadata, and raw state;
5. convert those observations into frozen necessity predictions;
6. only then compare against hidden labels.

The trusted benchmark harness necessarily knows which dataset variant it starts; the **selector does not**. The blind selector receives only a sanitized read-only tool catalog. Direct reads of benchmark initial state or gold task fields are not a valid inference path.

Until step 5 exists, this is **runtime interoperability plus a probe firewall**, not evidence that Residual Necessity improves abstention.
