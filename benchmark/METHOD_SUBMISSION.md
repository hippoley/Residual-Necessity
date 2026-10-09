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


## Executable submission workflow

The repository provides two small tools so a third-party method does not need
to hand-compute or copy benchmark hashes.

### 1. Freeze the development method

Materialize the exact method configuration, development report, dependency
list, and claim boundary as files, then run:

```bash
python benchmark/freeze_method.py \
  --method-id my-method-v1 \
  --code-commit <40-hex-method-commit> \
  --method-config method-config.json \
  --development-report development-report.json \
  --dependencies dependencies.json \
  --claims claims.json \
  --out method-card.sealed.json
```

The tool automatically binds:

- current Benchmark 0.2 manifest SHA-256;
- frozen pair-split SHA-256 from the sealed holdout policy;
- method-configuration SHA-256;
- current provider-profile registry SHA-256;
- development-report SHA-256.

It validates the resulting `rn-method-card/0.2` card before writing it.

### 2. Freeze holdout predictions before gold scoring

After the sealed method is run against the holdout inference surface, but
**before any holdout gold is read**, freeze the prediction artifact:

```bash
python benchmark/freeze_holdout_predictions.py \
  --sealed-card method-card.sealed.json \
  --predictions holdout-predictions.json \
  --release-commit <40-hex-release-commit> \
  --out method-card.released.json
```

The freezer:

- verifies the Benchmark manifest, split, and provider registry have not
  drifted since the sealed card was created;
- rejects gold/identity fields such as category, task type, task ID,
  execution DAG, and critical actions;
- rejects duplicate case IDs;
- freezes the holdout prediction SHA-256;
- upgrades the Method Card to `holdout_status=released`;
- does **not** load or score holdout labels.

Only after this released card and prediction hash exist may an authorized
holdout scoring step reveal gold.

This tooling intentionally does not create a leaderboard or automate holdout
release approval. Governance remains explicit; the tools only make the
evidence chain reproducible and hard to accidentally bypass.
