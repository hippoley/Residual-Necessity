# Residual Necessity conformance pack

This directory is intentionally implementation-neutral.

## External evaluator protocol

For each vector, the runner starts a fresh evaluator process.

- **stdin:** one JSON receipt object.
- **stdout:** exactly one JSON object containing `{"verdict":"ACT|ABSTAIN|INVESTIGATE|ESCALATE"}`.
- **exit 0:** a protocol response was produced.
- **non-zero / timeout / invalid JSON:** conformance failure.

No Residual Necessity Python module import is required. An implementation in Go, Rust, Java, JavaScript, or another language can participate by exposing this small stdio contract.

Run the reference implementation:

```bash
python conformance/run_external.py \
  --evaluator "python conformance/reference_stdio.py"
```

The vectors are semantic compatibility tests, not a claim that this project is an industry standard.
