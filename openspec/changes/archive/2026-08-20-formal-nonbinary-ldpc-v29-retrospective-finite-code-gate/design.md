# V29 Design — retrospective finite-code gate

## 1. Lifecycle and predecessor

The change is `FROZEN_P102_ACCEPTED`: the main thread recorded `P102 ACCEPT`
on 2026-08-20 after the freeze review and the two editorial corrections in
this packet. The only predecessor is the accepted V28R candidate
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`,
now closed out and archived as engineering evidence. V29 implementation and
execution remain a separate authorized action.

V29 is a retrospective finite-code gate, not fresh qualification,
qualification data collection, promotion, DE/MET work, or a public residual
release.

## 2. P0 input selection

The three scientific inputs are the already-frozen V25 `pairs.parquet` files
and their V25 source/file/frame split. The runner must fail closed if any
other scientific input data file is opened. This restriction does not prohibit
reading V26/V28 binding artifacts or evidence produced by the current V29 run;
those are provenance and verification inputs, not additional scientific data.

| label | source id | `delay_used_ps` | inclusive frame range | rows |
|---|---|---:|---:|---:|
| 1M | `type2_1M_20260121_184040` | -50 | 1600..1999 | 102400 |
| 1p5M | `type2_1p5M_20260121_183806` | +50 | 2213..2612 | 102400 |
| 2M | `type2_2M_20260121_183657` | +50 | 2916..3315 | 102400 |

Each selected frame must contain exactly 256 pairs. The normalized row order
is `(frame_id, pair_idx)`; `pair_idx` is the V25 per-frame pair order and is
not re-created from timestamps. Four consecutive frames form one
1024-symbol block, with blocks indexed 0–99 in that order.

The input identity persisted in `frame_selection.json` and
`block_manifest.json` consists of source id, relative parquet path, V25 split
identity, delay, frame range, frame IDs, pair counts, pair-index bounds, and
the ordered block/frame mapping. This is sufficient to reconstruct selection
without reading `.ttbin`; no new checksum scheme is introduced.

## 3. P1 canonical architecture and channel

Use the accepted V28R canonical config and matrices without regeneration,
search, or mutation:

- F03 natural MSB→LSB, GF(32)+GF(32);
- `n=1024`, shared L1 `m1=6`;
- source-specific L2 `m2={1M:194,1p5M:200,2M:202}`;
- L1/L2 coefficient, topology, rank, degree, source and delay bindings must
  match V28R `run_02_v28r`;
- V26 train-only `ChannelAdapter` for each source/delay; holdout rows must not
  alter the adapter.

The decoder receives Bob's complete observed 10-bit symbols. It performs:

1. `posterior_rows("L1", B)` from the V26 train model;
2. GF(32) additive centering relative to Bob's observed L1 symbols;
3. L1 error-domain FFT-QSPA with the public L1 syndrome;
4. only after L1 `success` and syndrome consistency,
   `posterior_rows("L2", B, x1_hat)` using the actual returned L1 estimate;
5. GF(32) centering relative to Bob's observed L2 symbols and L2 FFT-QSPA.

If L1 fails, L2 is `not_run`. Alice truth is permitted only in the test
harness to form the public syndrome and public tag, and in offline exact
scoring after decode. It must not enter a posterior, candidate selection,
threshold, retry, stopping decision, or decoder call.

## 4. P2 decoder and execution policy

Reuse V10 `decode_fftqspa` through V28R's posterior wrapper. The only decoder
settings are `max_iter=200` and `streak=20`. No degree, matrix, split,
iteration, threshold, posterior, or source selection search is permitted.

There is one official execution over the pre-registered 300 blocks. Each block
is processed as one unit: complete L1 and, conditional on L1 success, L2;
then persist one and only one block record before starting the next block.
Decoder wall-clock accumulates the L1 and L2 calls. If L1 fails, the block
record contains L2=`not_run`. There is no failed-call retry or
alternate-parameter rerun. Existing completed evidence is retained if
execution becomes resource-blocked.

## 5. P3 leakage and rate accounting

For every block of a source, the same public leakage applies:

`leak_bits = (m1 + m2) * 5 + 64`

| source | `m_total` | `leak_bits` | frozen `H_total` | `f=leak/(1024*H_total)` |
|---|---:|---:|---:|---:|
| 1M | 200 | 1064 | 0.801037825 | 1.2971453626425193 |
| 1p5M | 206 | 1094 | 0.825566052 | 1.2940931527063324 |
| 2M | 208 | 1104 | 0.832562722 | 1.2949474814463287 |

The `H_total` values in this table are the values frozen in the current V28R
configuration (with provenance to the V25 train contract). They are binding
constants for V29: every source must satisfy `f<1.3`, and execution MUST NOT
re-estimate, recalibrate, or recompute `H_total` from holdout or run data.

The public tag is exactly 64-bit SHA-256 truncation over the layer tuple:

`tag_true = SHA256(bytes(x1_true) || bytes(x2_true))[:8]`

Bob's decoded tag is calculated independently from `(x1_hat,x2_hat)` and is
compared with `tag_true`. The decoder is not given `x1_true` or `x2_true`.

## 6. P4 per-block and aggregate metrics

`per_block_results.jsonl` has exactly one record per completed block. The single
record is persisted only after that block's L1 and conditional L2 processing
has finished, before the next block starts. A record contains:

- source, delay, source identity, `block_index`, ordered `frame_ids`, and the
  block/frame identity fields needed to reconstruct the selected rows;
- L1/L2 statuses, iterations, public syndromes, public/decoded tags,
  `tag_verified`, `x1_hat`, `x2_hat`, and layer syndrome checks;
- offline exact flags, L1/L2 symbol error counts, block runtime and cumulative
  decoder wall-clock seconds;
- a field explicitly stating that Alice truth was used only for public input
  generation/offline scoring.

`source_summary.json` contains one summary per source and a global summary.
The required counters are:

- `l1_fail_count`: L1 did not return verified success;
- `l2_conditional_fail_count`: L1 verified but L2 did not return verified
  success;
- `tag_verified_count`: decoded tag equals the public tag;
- `offline_exact_count`: both decoded layers equal the offline truth;
- `false_accept_count`: `tag_verified=true` while `offline_exact=false`;
- `syndrome_fail_count`, `decoder_fail_count`, and block `FER`.

`FER` is block FER: `1 - offline_exact_count / completed_block_count`,
reported per source and globally. For an incomplete authorized early-fail
prefix it MUST be labeled `fer_scope=observed_prefix_only`; it is not a
full-300-block FER. A tag mismatch is not silently converted to a decoder
success.

## 7. P5 terminal gate and resource precedence

For a semantic or input/binding error, the runner may terminate immediately
with `implementation_blocked`. For a normally completed block, it must first
complete L1 and conditional L2, persist the single block record, and then
evaluate the terminal gate before starting another block. The terminal order
after that persistence point is:

1. if 300/300 blocks are complete, evaluate the scientific gate regardless of
   whether cumulative decoder wall-clock has reached 24 hours;
2. after an incomplete block is persisted, if any source has
   `false_accept_count>0`, or `offline_exact_count+remaining_expected<95`, or
   `tag_verified_count+remaining_expected<95`, emit `v29_finite_gate_fail`
   with a replayable `early_fail_proof` and `fer_scope=observed_prefix_only`;
3. if the run is incomplete and cumulative decoder wall-clock has reached 24
   hours, emit `resource_blocked`, retaining the completed prefix and starting
   no next block;
4. PASS requires, for every source, `tag_verified_count>=95` and
   `offline_exact_count>=95`, `false_accept_count==0`, all `f<1.3`, and all
   bindings/manifest checks pass → `retrospective_ready_for_fresh_change`;
5. otherwise, with 300/300 complete → `v29_finite_gate_fail`.

When 300/300 is reached, the runner must set a stop-before-next-call marker;
no 301st call may start. A resource-blocked prefix cannot be re-sampled,
retuned, or restarted under V29.

## 8. P6 evidence root and verifier

The additive run root contains exactly this frozen evidence set:

```text
RUN_MANIFEST.json
frame_selection.json
block_manifest.json
channel_model_binding.json
matrix_binding.json
per_block_results.jsonl
source_summary.json
gate.json
readonly_verify.json
```

The read-only verifier does not rerun the decoder. It reloads only the three
allowed parquet files as scientific inputs, while also reading the V26/V28
binding artifacts and current-run evidence needed for provenance and
verification. It validates exact source/frame/pair identity and no extra
frames, reconstructs V28R matrices, checks the V26 train/source/delay binding,
recomputes public syndromes/tags/leakage/f, reaggregates per-block metrics and
terminal precedence, and writes `readonly_verify.json`. If the terminal is
`resource_blocked`, it verifies only the completed prefix and confirms that
the missing suffix is exactly the unrun suffix. It must reject tampered
evidence, a changed block order, a changed tag, a false exact flag, a changed
matrix/channel binding, or any extra scientific input file.

## 9. P7 lifecycle and P8 test tiers

V29 PASS only permits proposing a separate fresh qualification change. V29
FAIL is retained and forbids tuning/retry under this change. No V29 terminal
state is a promotion claim.

Tests are additive and use a writable workspace root with
`pytest -p no:cacheprovider`:

- T0: frame selection, grouping, pair counts, accounting, matrix and channel
  binding;
- T1: tiny fake decoder, Bob-only order, L1-failure/L2-skip, tag false accept,
  tamper evidence, no holdout fitting and no `.ttbin` access;
- T2: fake 300-block PASS/FAIL/resource/replay and prefix preservation;
- T3: focused V27/V28 regression at the milestone only.
