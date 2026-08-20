# V29 retrospective finite-code gate — closeout report

Date: 2026-08-20  
Status: `v29_finite_gate_fail`  
Scope: retrospective finite-code gate only; no qualification or promotion.

## Canonical evidence

The canonical run is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v29_20260820/run_02/`.
It used frozen V28R F03 natural GF(32)+GF(32), V26 train-only
source/delay-conditioned posterior, Bob-only L1→L2 decoding, and the
pre-registered V25 block order. `run_01` remains retained as the superseded
0-call `implementation_blocked` run caused by the earlier selector bug; it was
not rewritten or reused.

## Stopped prefix

The user authorized stopping after a persisted block because the 1M source
could no longer satisfy its 95/100 gate. The canonical prefix contains 9
blocks, all 1M block indices 0–8:

| Metric | Result |
|---|---:|
| completed | 9 / 300 |
| decoder calls | 16 |
| decoder wall-clock | 1167.14 s |
| L1 success / fail | 7 / 2 |
| L2 success / max-iter / not-run | 1 / 6 / 2 |
| tag verified | 1 |
| offline exact | 1 |
| false accept | 0 |
| observed prefix FER | 8/9 = 0.8888888889 |

The last metric is explicitly `fer_scope=observed_prefix_only`; it is not a
full 300-block FER.

The persisted irreversible proof is:

```text
source=1M, completed=9, exact=1, tag_verified=1,
remaining=91, maximum possible exact=1+91=92<95,
maximum possible tag_verified=1+91=92<95, false_accept=0.
```

Thus the terminal is mathematically fixed at `v29_finite_gate_fail` and no
tenth decoder call was started. `readonly_verify.json` reports
`ok=true`, `recomputed_terminal=v29_finite_gate_fail`, and
`decoder_rerun=false`.

## Structural mechanism for the successor

The V28R finite-matrix audit found a construction-level defect in the shared
degree-two L1 graph:

- 15 support groups;
- maximum support-group multiplicity 69;
- 303 duplicate projective classes;
- 922 columns in duplicate projective classes;
- 1107 guaranteed proportional-column / weight-2 pairs.

For a degree-two GF(32) column, normalize by support pair and coefficient
ratio `h_b/h_a`. Equal keys are proportional columns; two such columns form a
weight-2 nullspace word, so this construction guarantees `d_min <= 2`.
This is a finite graph/construction failure of V28R, not evidence that the
channel-informed GF32×GF32 route itself is impossible. V30 is a separate
projective-safe finite-graph draft pending freeze review.
