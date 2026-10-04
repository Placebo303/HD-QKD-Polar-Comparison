# NB-LDPC GF32 edge-label update — EXPLORE result

2026-10-01. Track **EXPLORE**. State **CLOSED / MAIN ACCEPTED**.
Batch UUID `1efed423-10c8-4c51-a119-844f2b922ab5`.
Machine root: `workspace/gf32_edge_label_1efed423/`.
Frozen authority: `PREREG_AND_AUTH.md`; OpenSpec change:
`explore-gf32-edge-label-update`.

## Frozen execution and outcome

The fixed p0=0.55 synthetic iid marginal-shape experiment completed all six
n=128, m=52, E=256 GF(32) graphs, 192 paired holdout frames, and 384 decoder
calls. There was no pilot. The control reconstructed accepted deep H0D; the
candidate made one row-major absolute edge-label sweep. All graph and
candidate support, degree, connectivity, structural-rank, and GF(32)-rank
checks passed (rank 52).

The frozen marginal had p(0)=0.55 and nonzero aggregate counts
{1:2295, 3:1126, 7:557, 15:304, 31:146} out of 4428. Graph seeds were
2026093901–2026093906. Holdout seeds used namespace
`gf32-edge-label-v1`; each pair shared the sampled error and prior, each arm
used its own syndrome, and arm order alternated by frame. The decoder was
unchanged (90 iterations, damping 1). Frozen caps were 1800 s total, 120 s
per call, 4 GiB RSS, and 384 calls.

Control exact-and-syndrome successes were 150/192; edge-label candidate
successes were 155/192, so Δ=+5. Paired states were both=140,
candidate-only=15, control-only=10, neither=27. Per-graph counts and J
diagnostics were:

| Graph seed | Control → edge successes | Δg | Control sweeps | Edge ΔJ (bits) | Changed labels | Nonunit chord residuals |
|---|---:|---:|---:|---:|---:|---:|
| 2026093901 | 28 → 24 | −4 | 4 | +0.491884 | 113 | 73 |
| 2026093902 | 22 → 27 | +5 | 5 | +0.576324 | 115 | 76 |
| 2026093903 | 24 → 26 | +2 | 6 | +0.500889 | 107 | 70 |
| 2026093904 | 25 → 25 | 0 | 5 | +0.443839 | 98 | 72 |
| 2026093905 | 25 → 26 | +1 | 4 | +0.543601 | 109 | 74 |
| 2026093906 | 26 → 27 | +1 | 4 | +0.542335 | 95 | 77 |

Every control deep search ended `NO_CHANGE`. Each edge pass increased J;
complete J versus accumulated-row-increment drift was at most 4.55e-13 bits.
Every candidate left the full row+column gauge class: all six had 179 tree
edges and 77 chord residuals, with at least one nonunit residual per graph.
The cycle-change count was 6/6; the positive-Δ count was 4/6.

The frozen screen is `NO_SUFFICIENT_SIGNAL`: control=150 is within [39,153],
positive Δg passes at 4/6, the cycle-residual gate passes at 6/6, and
integrity/resource/authorization violations are zero; only Δ=+5 misses the
required +12. This is the mechanical result for this batch, not a route or
family decision.

## Accounting and resources

The 384 calls disclosed 99,840 syndrome bits (260 per attempt); tag bits=0.
One syndrome-consistent wrong row occurred in control at call 156, graph
2026093903, stream 0, frame 13: the decoder reported `converged_exact` and
syndrome acceptance, but the saved truth comparison was not exact. It remains
an isolated wrong row and is not counted as success. Candidate wrong rows=0.
Verification is `NOT_IMPLEMENTED`; `undetected` is `NOT_MEASURED`.

Batch wall time was 121.451 s, maximum call time 0.565175 s, and maximum RSS
103,452,672 bytes. Integrity, resource, and authorization violations were
all zero. FER, `f_eff`, and SKR are null and are not claims.

The source was the frozen historical 2M aggregate nonzero shape used as an
iid marginal proxy; there were no empirical-input reads. The four machine
artifacts do not store truth/prior arrays. Review could verify seed roles,
formula, arm order and saved outputs, but cannot replay those arrays
value-by-value.

## Independent review, acceptance, and limits

Independent reviewer `faithful_scope` returned batch-end P1–P7 PASS and was
not the operator. The reviewer independently reconstructed the row/column
gauge potentials and 77 residuals from saved edge updates and checked J
results; the recomputed values agreed. Main accepted this batch only as the
frozen synthetic marginal-shape observation with terminal
`NO_SUFFICIENT_SIGNAL`.

Do not pool or rank this batch against other label/search batches. It does not
establish a conditional-channel reconstruction, causal mediation, FER,
`f_eff`, SKR, throughput, qualification, publication, or route conclusion.
The batch execution is closed: no retry, repair, extra frames, or rerun.

Ongoing bounded synthetic EXPLORE authority is documented at
`docs/research_cycles/NBLDPC-CONTINUOUS-EXPLORE-20261001.md`; any successor
needs its own packet, independent review, and main dispatch. The separate
`NBLDPC-GF32-SHORT-CYCLE-CENSUS-20261001` packet remains unexecuted pending
its own implementation review and dispatch. The source-aware
`W_cycle` overlap diagnostic discussed after this batch is a proposal only;
no census or source-overlap computation is claimed here.

No commit, push, merge, archive, or new scientific execution was performed
as part of this closeout.
