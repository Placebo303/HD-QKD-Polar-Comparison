# D3 — Existing DE evidence (read-only inspection)

- gate status: `pass_target_f13` best_passing_f: `{'A01': 1.6, 'A02': 1.3}`
- new_DE_change_required: **True**

## Code facts

```python
comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_channel.py L10-13
Semantics (V26 design section 1):...
```

## Minimal DE questions

1. What is the DE threshold f for the QC-cyclic-projective packet per source under the corrected matched generator law Q_B1 (uniform alice, Bernoulli(raw_ser) substitution with uniform nonzero delta mod 1024) at n=1024 for the A02 L1/L2 layers?
2. Does the empirical-channel pass point (gate.json best_passing_f A01=1.6, A02=1.3) remain a pass when the channel sampler draws from Q_B1 instead of the V25 train joint?
