# Spec — v29_retrospective_finite_code_gate

Status: `FROZEN_P102_ACCEPTED`. P102 was accepted by the main thread on
2026-08-20 after the freeze review and the two editorial corrections. This
specification does not itself start implementation or execution.

## Requirement: frozen retrospective input

The implementation MUST read only the three V25-split `pairs.parquet` files as
scientific input data and MUST select exactly the inclusive frame ranges
1600..1999 (1M), 2213..2612
(1p5M), and 2916..3315 (2M). Every selected frame MUST contain 256 pairs.
Rows MUST be ordered by `(frame_id,pair_idx)` and grouped four consecutive
frames per 1024-symbol block, producing 100 blocks per source.

V26/V28 binding artifacts and current-run evidence MAY be read for provenance
and verification; they are not additional scientific input data. No raw
`.ttbin` or unlisted scientific data file may be read.

### Scenario: input identity pass

- **Given** the three frozen source IDs, delays, frame ranges, and V25 pair
  order.
- **When** the selector builds the block manifest.
- **Then** it contains exactly 300 blocks and no extra/missing/duplicate frame
  or pair, and records enough identity to reconstruct selection.

### Scenario: forbidden input

- **Given** a raw `.ttbin`, an unlisted parquet, or a holdout-fitting request.
- **When** execution or verification encounters it.
- **Then** the run is `implementation_blocked`; the file is not read.

## Requirement: canonical V28R Bob-only decode

The implementation MUST reuse the V28R F03 natural GF32+GF32 matrices and the
V26 train-only source/delay posterior. It MUST decode L1 before L2 with
`max_iter=200` and `streak=20`. L2 MUST receive only the actual returned L1
`x1_hat`; an L1 failure MUST make L2 `not_run`. Alice truth MAY be used only
to construct public syndromes/tags and for offline exact scoring.

### Scenario: sequential order

- **Given** a Bob block, public syndromes, and a bound V26 adapter.
- **When** the decoder runs.
- **Then** it calls L1 posterior/decode first, conditionally calls L2 with the
  returned `x1_hat`, and records both layer statuses and iterations.

## Requirement: leakage and public tag

For each block, leakage MUST be `(m1+m2)*5+64`, with 1064/1094/1104 bits for
1M/1p5M/2M. `f` MUST be computed from the `H_total` values frozen in the
current V28R configuration and remain below 1.3. Those values MUST NOT be
re-estimated, recalibrated, or recomputed from execution data. The public tag
MUST be the first eight bytes of
`SHA256(bytes(x1_true)||bytes(x2_true))`; Bob's decoded tag is independently
computed and compared.

## Requirement: evidence and metrics

The run MUST persist exactly the nine frozen evidence files. There MUST be one
per-block record for every completed block, containing source/delay/frame
identity, statuses, iterations, syndromes, tags, decoded layers, exact score,
symbol errors, and runtime. The block's L1 and conditional L2 processing MUST
finish before this single record is persisted and before the next block starts;
decoder wall-clock still accumulates the L1 and L2 calls. If L1 fails, the
record MUST contain L2=`not_run`. Per-source/global summaries MUST include L1 fail,
conditional L2 fail, tag verified, offline exact, false accept, syndrome fail,
decoder fail, and block FER.

`false_accept_count` MUST count `tag_verified=true` with `offline_exact=false`.

## Requirement: terminal gate and resource policy

Input or semantic errors MAY immediately emit `implementation_blocked`. For a
normally completed block, after L1 and conditional L2 finish and its single
block record is persisted, the runner MUST first test whether 300/300 blocks
are complete. If complete, it MUST evaluate PASS/FAIL even if cumulative
decoder wall-clock has reached 24 hours, and MUST not start a 301st call. If
completion is short and the cumulative decoder wall-clock reaches 24 hours,
the terminal MUST be `resource_blocked`, the completed prefix MUST be retained,
and no next block may start. If all blocks complete, PASS requires every
source to have at least 95 tag-verified and 95 offline-exact blocks, zero
false accepts, all accounting/bindings valid, and then emits
`retrospective_ready_for_fresh_change`; otherwise it emits
`v29_finite_gate_fail`.

After a persisted incomplete block, the runner MAY emit
`v29_finite_gate_fail` before 300/300 only under the user-authorized
irreversible-fail addendum: for a source, `false_accept_count>0`, or
`offline_exact_count+remaining_expected<95`, or
`tag_verified_count+remaining_expected<95`. It MUST persist an
`early_fail_proof` containing the source, completed count, remaining count,
observed counts, threshold, and maximum possible count. The summary MUST mark
`fer_scope=observed_prefix_only`; this terminal is a threshold-gate failure,
not a full-run FER result. The precedence is complete-300 scientific gate,
then irreversible-fail proof, then incomplete-run resource gate.

## Requirement: no-decoder-rerun verifier

The read-only verifier MUST reload only the three allowed parquet files as
scientific inputs (and MAY read V26/V28 bindings plus current-run evidence),
verify frame/block identity and no extra scientific input, rebuild V28R
matrices, verify V26 source/delay binding, recompute syndrome/tag/leakage/f and all aggregate
metrics, and re-evaluate terminal precedence without invoking a decoder. For
`resource_blocked`, it MUST verify only the completed prefix and exact unrun
suffix. For an early-fail closeout it MAY verify identity and the persisted
proof without rereading parquet, but MUST recompute the proof from persisted
prefix counters and reject a tampered proof. Tampered evidence or binding MUST
make verification fail.

## Requirement: lifecycle

V29 PASS MAY only propose a separate fresh qualification change. V29 does not
claim fresh qualification or promotion, and V29 FAIL forbids tuning/retry under
this change.
