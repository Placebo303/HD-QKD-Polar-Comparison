# V31 deterministic finite-graph redesign gate — report

Date: 2026-08-21 (production run finalized)
Canonical evidence:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`
Terminal: **`finite_graph_fail`** (read-only verifier `ok=true`, `problems=[]`)

## Executive result

The V31 deterministic finite-graph redesign gate did not produce a finite code
that passes the pre-registered per-source validation thresholds. The result is
a valid, bounded negative result for the tested deterministic constructions:

- `q=32`, F03 GF(32)+GF(32), V25 source/delay-conditioned channel;
- fixed `m1=16`, n=1024 and n=2048;
- family 1 `PEG-capacity-aware` (projective-capacity-aware, occupancy<=31);
- family 2 `QC-cyclic-projective` (deterministic QC control);
- V28 Bob-only sequential decoder, tag/leakage accounting.

It is not a route-wide impossibility theorem. V25's empirical-channel PASS, V26
channel-informed DE PASS, and the V27 budget-layer PASS remain valid within
their own scopes. The failure is at the finite graph/decoder conversion layer
tested here.

## Frozen scope (as executed)

- GF(32), primitive polynomial `0b100101`, field_id
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`.
- F03 natural MSB→LSB GF32+GF32 factorization.
- V25 validation frames: 1M 1200..1599, 1p5M 1660..2059, 2M 2187..2586.
- m1=16; m_total per n: n=1024 {200,206,208}, n=2048 {413,426,430};
  m2=m_total-16; leak_total=5*m_total+64; f_total<1.3 all cells.
- M1: 60 pre-registered DE confirmation calls (30 per n,
  5 seeds x 3 sources x 2 layers, n_samples=2000, max_iter=200, tol=0.01,
  streak=20), m1=16.
- M3: full Bob-only windows (n=1024 100 blocks/source; n=2048 50
  blocks/source; max_iter=200). Per-source pass requires exact>=95% and
  tag>=95% and false_accept==0; V31 pass requires each n to have a passing
  family.

## M1 — DE confirmation: PASS

- n=1024: 30/30 calls converged, worst final entropy ~3e-296.
- n=2048: 30/30 calls converged, worst final entropy ~3e-296.
- Terminal `de_allocation_pass`; 60/60 total.

## M2 — deterministic constructions

| n | family | result | note |
|---|---|---|---|
| 1024 | PEG-capacity-aware | REJECT | L2 matrices not full GF(32) rank (e.g., m=184/190/192 -> rank-deficient); construction hard gate. |
| 1024 | QC-cyclic-projective | OK | full rank, projective-safe, max support occupancy 9 <= 31. |
| 2048 | PEG-capacity-aware | REJECT | L2 matrices rank-deficient (e.g., m=397/410/414); construction hard gate. |
| 2048 | QC-cyclic-projective | OK | full rank, projective-safe, max support occupancy <= 31. |

PEG L2 rank deficiency is deterministic and reproducible (m=200 -> rank 199;
m=414 -> rank 413), so both PEG packets are hard-rejected; no replacement or
seed change is permitted.

## M3 — Bob-only validation

Only the QC-cyclic-projective packets entered M3 (PEG packets rejected in M2).

### n=1024 — full window (100 blocks/source)

| source | blocks | exact | tag | false_accept | l1_ok | l2_ok | syndrome conv. | exact/tag FER |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1M | 100 | 0 | 0 | 0 | 98 | 0 | 0.00 | 1.00 / 1.00 |
| 1p5M | 100 | 0 | 0 | 0 | 99 | 0 | 0.00 | 1.00 / 1.00 |
| 2M | 100 | 0 | 0 | 0 | 99 | 0 | 0.00 | 1.00 / 1.00 |

All 300 blocks are failure positions: L1 syndrome converges (with 3-5
iterations) but L2 always ends `converged_no_syndrome`; exact=0 and tag=0
everywhere. Threshold 95/100 per source is never met.

### n=2048 — bounded prefix (1M 14 blocks, design §5 contingency)

| source | blocks | exact | tag | false_accept | l1_ok | l2_ok | syndrome conv. | exact/tag FER |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1M | 14 | 0 | 0 | 0 | 13 | 0 | 0.00 | 1.00 / 1.00 |

Every n=2048 block run repeats the same L2 `converged_no_syndrome` pattern.
The n=2048 window was closed on this bounded 1M prefix because non-converging
n=2048 L2 decodes are pathologically slow (a single block can take tens of
minutes to hours); the global terminal is already fixed by the complete n=1024
failure. 1p5M/2M at n=2048 were not run.

### Comparison

- Waterfall: cumulative exact/tag success is identically 0 at both n for every
  completed source; no waterfall "turn" occurs.
- Syndrome convergence: 0.00 at both n (L1 converges, L2 never).
- Exact/tag FER: 1.00 at both n for all completed sources.
- Failure positions: all completed blocks; L2 decoder reports
  `converged_no_syndrome` (fail-closed, no false accepts).

## Gate classification

- `finite_graph_fail` — no family passes the 95% per-source thresholds at
  n=1024; n=2048 confirms the same failure.

## Independent verification

`readonly_verify.json`:

```text
ok=true
problems=[]
recomputed_terminal=finite_graph_fail
persisted_terminal=finite_graph_fail
no_de_rerun=true
no_decoder_rerun=true
```

The verifier rebuilds allocation tables, M1 registries, matrix audits
(occupancy<=31, zero duplicate/proportional keys, full-rank checks, label
replay), validation frame/block identity, per-block registration (full n=1024;
bounded n=2048 prefix per design §5 contingency), per-source
FER/syndrome/waterfall/failure positions, and terminal equality without
rerunning DE or the decoder.

## Scientific interpretation

1. The deterministic `QC-cyclic-projective` control gives full-rank, sparse,
   projective-safe finite matrices, but its L2 decoding never converges to the
   syndrome on the V25 channel => exact/tag FER = 1.0.
2. The `PEG-capacity-aware` family is rank-deficient at these L2 sizes, so it
   fails the construction gate deterministically; it cannot be the mechanism
   that transfers the V26 DE success to finite FER at these sizes.
3. Therefore the V31 result isolates the finite graph/decoder conversion again:
   neither the capacity-aware PEG nor the structured QC-cyclic control converts
   the DE success into a finite-code validation pass at the tested parameters.

## Closeout and successor boundary

V31 is closed with terminal `finite_graph_fail`. Prohibited and unchanged:
no V30R packet rerun, no random matrix-library search, no seed tuning, no
V29 holdout/raw `.ttbin`, no qualification/promotion, no push. A future
successor would require new user authorization and a new OpenSpec change; the
failure mechanism (L2 non-convergence on the empirical channel, and PEG L2
rank deficiency) is the primary diagnostic to address.
