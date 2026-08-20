# V29 — retrospective finite-code gate for V28R GF32×GF32

## Status

`FROZEN_P102_ACCEPTED`.  `P102` was explicitly accepted by the main thread in
the 2026-08-20 freeze-review decision (the two requested editorial fixes are
included in this packet).  This document is now the frozen execution contract;
implementation and execution remain separate follow-on actions.

The predecessor is the accepted V28R candidate `run_02_v28r`, now closed out and
archived as engineering evidence.  V29 execution may begin only as a separate
authorized implementation action after this freeze; it is not started by this
document update.

## Objective

Measure the finite-code behavior of the canonical V28R F03 architecture on a
pre-registered retrospective holdout.  The gate uses exactly 300 blocks: 100
blocks for each of the three sources, with no data fitting, calibration,
parameter search, or fallback rerun.

The result is a finite-code gate only:

- `retrospective_ready_for_fresh_change` — all gates pass;
- `v29_finite_gate_fail` — 300 blocks complete but a scientific gate fails;
- `implementation_blocked` — input, binding, or semantic implementation error;
- `resource_blocked` — the 24-hour cumulative decoder wall-clock limit is
  reached before all 300 blocks complete.

V29 does not qualify a fresh experiment, promote a production method, run DE or
MET, or authorize public residual disclosure.

## Frozen input contract

Only the three V25-split `pairs.parquet` files may be read as scientific input
data.  V26/V28 binding artifacts and evidence from the current V29 run may be
read as provenance/verification inputs; that allowance does not expand the
scientific data set.  For each source,
the selected frame range is inclusive and contains exactly 400 frames:

| source | source identity | holdout frames | pairs/frame | blocks |
|---|---|---:|---:|---:|
| 1M | `type2_1M_20260121_184040` | 1600–1999 | 256 | 100 |
| 1p5M | `type2_1p5M_20260121_183806` | 2213–2612 | 256 | 100 |
| 2M | `type2_2M_20260121_183657` | 2916–3315 | 256 | 100 |

Rows are sorted by `(frame_id, pair_idx)`.  Four consecutive frames form one
1024-symbol block; blocks are indexed 0–99 in that order.  No raw `.ttbin` is
allowed, and the selected holdout may not be used to fit or tune a channel
model, threshold, matrix, split, or decoder parameter.

## Frozen acceptance boundary

The canonical V28R matrices/config, V26 train-only source/delay posterior, and
Bob-full sequential L1→L2 decoder are reused exactly.  `max_iter=200` and
`streak=20` are fixed.  Each source must have at least 95/100
`tag_verified` blocks and at least 95/100 offline-exact blocks, with zero
false accepts.  All 300 blocks are required for a scientific PASS; a normal
scientific FAIL is also evaluated at 300/300.  As an explicit 2026-08-20
user-authorized addendum, an incomplete run may instead terminate early after
the current block record is persisted when `false_accept>0`, or when
`exact+remaining<95`, or `tag_verified+remaining<95` for a source.  Such a
`v29_finite_gate_fail` MUST persist an `early_fail_proof` and MUST label FER as
observed-prefix-only, never as full-run FER.  Each block completes L1 and,
conditional on L1 success, L2 before a single block record is persisted; only
then may the next block start.  Decoder wall-clock accumulates the L1 and L2
calls.  If L1 fails, the persisted block record contains L2=`not_run`.  After
a normally completed block is persisted, 300/300 completion is checked first,
then the irreversible-fail proof, then the 24-hour resource gate.

The `H_total` values and the resulting `f` values are bound to the current
V28R frozen configuration shown in the design.  They are not re-estimated,
recalibrated, or otherwise recomputed from execution data.

## Evidence and review

The additive V29 evidence root is frozen to the nine files listed in the
design and spec.  The read-only verifier reloads the selected parquet rows,
reconstructs block identities and matrices, recomputes public syndromes/tags,
reaggregates all metrics and the terminal state, and never reruns the decoder.
The formal execution and archive remain separately authorized after freeze
review.
