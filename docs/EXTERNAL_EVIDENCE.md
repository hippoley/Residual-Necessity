# External Evidence Ledger

This file records third-party evidence that may strengthen or falsify Residual Necessity. It deliberately separates **evidence qualification** from adoption, citation, endorsement, and dependency.

## ExecSurface real-workload record

- Upstream: AETHERXGLOBAL/execsurface
- Intake: issue #140, P9.5 / P8-A4 external real-workload evidence
- Residual-Necessity report: comment 6056218704
- Upstream qualification: comment 6056888111
- Workload: Residual-Necessity PR #2, Python 3.11, `python -m pytest -q`
- ExecSurface artifact: public v0.1.0-alpha.6 release binary with checksum verification
- Environment: GitHub-hosted Ubuntu x86_64
- Preserved initial result:
  - `doctor`: PASS
  - target workload: 15 tests passed
  - `learn`: exit 2
  - observation incomplete; no baseline or downstream PASS/REVIEW/BLOCK verdict manufactured
- Upstream scientific classification:
  - genuine external real-workload evidence record
  - provisional family: `PARTIAL_OR_UNSUPPORTED / INCOMPLETE`
  - root cause intentionally left open pending collection-health / warning diagnostics

### What this establishes

A third-party project has independently reviewed and retained a Residual-Necessity workload result under its own preregistered evidence protocol.

The record supports one concrete distinction:

> target workload success does not imply that observation is sufficient to authorize a baseline or a state transition.

### What this does not establish

It does **not** establish:
- adoption of Residual Necessity;
- a dependency on this repository;
- endorsement;
- a citation in scientific literature;
- superiority over another runtime-governance system;
- that ExecSurface has a defect;
- that Residual Necessity improves abstention metrics.

## ExecSurface consumer-contract discussion

- Upstream: AETHERXGLOBAL/execsurface
- Thread: issue #155
- Residual-Necessity feedback: comment 6056614778
- Question under discussion: whether complete/supported observation authorizes proposition-level negative evidence from effect absence, or whether an explicit negative-evidence guarantee is required.

Residual Necessity currently chooses the conservative contract:

- positive matching evidence may support `TRUE`;
- incomplete/unsupported evidence becomes `UNKNOWN`;
- effect absence does not become `FALSE` without explicit negative authority.

This rule is enforced by the reference gate: `FALSE` without `negative_authority=true` remains unresolved and cannot produce `ABSTAIN`.
