# Method submission contract

A benchmark method is not identified by a model name or a prose description alone.

Before any Track A holdout release, freeze a JSON Method Card conforming to
`method_submission.schema.json`. It records:

- method identity;
- exact code commit;
- benchmark manifest hash;
- frozen pair-split manifest hash;
- method configuration hash (prompt/rules/model settings or equivalent);
- proposition/provider-profile hash;
- development report hash;
- external dependencies and versions;
- the claim being tested and explicit non-claims;
- whether holdout remains sealed.

The Method Card is intentionally model-agnostic, but the exact model/prompt/rule
configuration must be materialized separately and frozen by
`method_config_sha256`. A method may use deterministic code, a model, or a
hybrid system, but evidence authority must still come from the benchmark's
tool-visible/provider contracts.

## Holdout rule

The public holdout remains sealed until a release commit identifies one frozen
Method Card. Once the candidate is scored on holdout, subsequent method tuning
requires a new benchmark/split version rather than silently reusing the same
holdout.

This contract exists to make third-party submissions independently auditable,
not to create a leaderboard platform.
