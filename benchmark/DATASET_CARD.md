# Residual Necessity Reality Benchmark — Dataset Card

## Summary

This benchmark evaluates a narrow question:

> Does current, externally grounded evidence still justify a proposed state transition?

It is a **composite evaluation contract**, not a redistributed copy of upstream datasets. The repository keeps adapters, manifests, frozen split rules, conformance logic, evaluation code, and evidence records. Raw source data remains with its original maintainers.

## Tracks

| Track | External source | Purpose | Current status |
| --- | --- | --- | --- |
| A — Runtime necessity | AgentAbstain | Paired ACT/ABSTAIN runtime evaluation under tool-visible evidence | 97 pairs; 64 development / 33 holdout; holdout not used for candidate tuning |
| B — Residual partial fix | P3 + cave-story-md issue #169 | Verify an intermediate incomplete fix can still justify ACT while a later bounded fix supports ABSTAIN | Real external revision pair verified |
| C — Evidence/support boundary | SafeAct | Verify mature action-support evidence can be reused as constraints without becoming necessity authority | Real pinned interoperability verified |

There is intentionally **no single aggregate score** across tracks.

## Source provenance

Pinned versions live in `benchmark/manifest.json`.

The benchmark currently depends on:

- AgentAbstain runtime commit `cfc3faf7ab1cfd4892cde1158d6e43b2f312ddc3`;
- AgentAbstain dataset revision `842228426c2a703347396501af61c7890972c7ee`;
- P3 dataset commit `bfd73658`;
- SafeAct commit `841816cf1e376e6fbf8600cffac5df1736e1d369`.

Upstream data is not relicensed by this repository.

## Splits and leakage controls

AgentAbstain is split at the **pair** level:

- development: 64 pairs;
- holdout: 33 pairs.

Both ACT/ABSTAIN variants of a pair always remain in the same partition.

The split is deterministic and gold-free. Trusted audit code may inspect hidden category metadata only to verify aggregate split coverage; category is never exposed to inference.

Current split audit confirms all three runtime categories appear in both partitions:

- conflicting evidence: 17 development / 13 holdout;
- critical tool failure: 24 / 10;
- emergent risk discovery: 23 / 10.

Blind inference removes task type, abstention trigger, execution DAG, critical actions, semantic category, and transformation metadata.

## Metrics

Track A reports both action directions:

- accuracy;
- unnecessary intervention rate;
- missed required action rate;
- ACT recall;
- investigate/escalate burden;
- paired accuracy;
- probe coverage;
- provider-profile coverage;
- complete-binding coverage.

Point estimates are accompanied by deterministic **95% pair-preserving bootstrap confidence intervals** (5,000 samples, fixed seed 20261009). ACT/ABSTAIN variants are resampled together.

## Current benchmark finding

A generic `probe_success` heuristic is already falsified. It preserves high ACT recall but still causes very high unnecessary intervention. This demonstrates that tool availability/success is not proposition-level necessity evidence.

The current proposition-specific development candidate is **not holdout-ready**: provider-profile coverage remains very low. No holdout superiority claim is made.

## Intended use

Appropriate uses:

- testing proposition-specific evidence/necessity semantics;
- comparing pre-action decision rules while preserving both ACT and ABSTAIN failure costs;
- validating integrations with existing control/evidence systems;
- reproducing the project's falsification experiments.

Not appropriate:

- treating support/permission as necessity;
- training on holdout labels;
- using one aggregate score to hide a safety failure in another track;
- claiming general agent safety from these tracks;
- redistributing upstream data under this repository's Apache-2.0 license.

## Licenses

Repository benchmark code/metadata is Apache-2.0.

External source licenses remain upstream. In particular, the SafeAct repository declares MIT for code and CC BY 4.0 for data. P3 and underlying real projects retain their own source-specific licensing; consumers must preserve those terms.

## Known limitations

- Track A currently has only one narrow proposition-provider profile with very low coverage.
- The 33-pair holdout is small; confidence intervals are mandatory.
- Track B uses a bounded issue-derived oracle for one real partial-fix case and does not prove global bug absence.
- Track C proves a semantic boundary, not Residual Necessity benchmark superiority.
- Third-party adoption/dependency on this benchmark is currently zero.

## Third-party method submissions

Track A candidates use the machine-readable contract in `benchmark/method_submission.schema.json`.
A candidate must freeze its exact code commit, provider-profile hash and development-report hash before holdout release. The one-shot holdout governance lives in `benchmark/holdout_policy.json`.

## Machine-readable metadata

- Benchmark contract: `benchmark/manifest.json`
- Croissant 1.1 metadata: `benchmark/croissant.json`
- Horizontal completeness matrix: `audit/user_story_horizontal_matrix.json`
- Method submission schema: `benchmark/method_submission.schema.json`
- Holdout release policy: `benchmark/holdout_policy.json`

The Croissant file describes this composite benchmark without vendoring external raw datasets.
