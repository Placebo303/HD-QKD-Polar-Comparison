# V29 Tasks — retrospective finite-code gate

## Freeze status and predecessor

Status: `ARCHIVED_LOCAL_CLOSEOUT`.  `P102 [x]` — the main thread recorded
`P102 ACCEPT` on 2026-08-20 after the freeze review and the two editorial fixes
in proposal/design/spec.  V28R `run_02_v28r` is the closed-out predecessor and
is archived as engineering evidence.  V29 was executed once on canonical
run_02 and is now closed out locally after read-only verification.

Implementation correction note: the initial retained `run_01` stopped at
`implementation_blocked` with zero decoder calls because the selector treated
the full V25 parquet frame set as if it contained only the selected 400-frame
range.  The selector contract is now corrected: train/validation and other
unselected frames in the same parquet are permitted; only the selected range
must be complete and satisfy the 256-pair frame contract.  The old run remains
invalid/superseded and is not rewritten or reused.

## Stable planning IDs

### P001 — P0 input inventory and split audit

Read only V25 inventory/manifests and record the three allowed parquet paths as
scientific inputs, source IDs, delays, frame ranges, schema, 256-pair frame
contract, and the 100-block mapping per source. V26/V28 bindings and current
run evidence remain permitted provenance inputs; do not open holdout rows
during the draft.

**Acceptance:** the inventory is sufficient to select exactly the prescribed
400 frames/source and names no raw `.ttbin` input. **Status: [x]** —
specification-level audit bound to `workspace/nbldpc_v25_p0/data_inventory.json`;
holdout rows were not opened.

### P002 — V28R predecessor and channel contract audit

Read-only check that V28R `run_02_v28r` is the accepted predecessor, that its
canonical config/matrix/tag/manifest/channel semantics are bound, and that
V26 train-only adapters are source/delay identified.

**Acceptance:** V29 points to the V28R candidate without regenerating or
mutating matrices; any V28R closeout gap blocks P102. **Status: [x]** —
`run_02_v28r/readonly_verify.json` is `ok=true` and its gate is the sole
`engineering_ready_for_retrospective_gate` state.

### P102 — user/main-thread freeze review

Review and accept the complete V29 four-piece OpenSpec packet, including this
task list, the ambiguity audit below, exact gate precedence, and the nine-file
evidence contract.

**Acceptance:** explicit `P102 ACCEPT` is recorded by the main thread. **Status:
[x]** — accepted in the 2026-08-20 main-thread freeze-review decision.

## Implementation IDs (after P102)

- **I01 [x]** — freeze the V29 config and predecessor binding, including the
  current V28R `H_total` constants; no execution-time re-estimation or
  parameter search (`nonbinary_v29.frozen_v29_config`).
- **I02 [x]** — implement the three-source, inclusive 400-frame selector.
- **I03 [x]** — validate `(frame_id,pair_idx)` order and exactly 256 pairs/frame.
- **I04 [x]** — group four consecutive frames into 100 ordered 1024-symbol
  blocks.
- **I05 [x]** — bind the V26 train-only posterior contract by source and delay
  (the default adapter path); injected adapters are test-only and declare
  `holdout_fit=false`.
- **I06 [x]** — wire the Bob-only empirical L1→L2 V28R decoder with
  `max_iter=200`, `streak=20`, and L1-failure L2 skip.
- **I07 [x]** — generate public syndromes/tags and retain truth only for offline
  scoring; after each block completes L1 and conditional L2, persist one block
  record before starting the next block (L1 failure records L2=`not_run`).
- **I08 [x]** — implement one-shot execution, cumulative 24-hour wall-clock
  gate, prefix preservation, and block-level persistence. After a normal block
  record is persisted, check 300/300 first; only an incomplete run can become
  `resource_blocked` before the next block. Never start a 301st call.
- **I09 [x]** — implement source/global aggregation and exact terminal precedence.
- **I10 [x]** — write the first eight frozen evidence files in an additive run
  root; `readonly_verify.json` remains the I11 follow-on deliverable.
- **I11 [x]** — implement the no-decoder-rerun read-only verifier.  The
  `verify_v29` replay rebuilds the selected parquet blocks and V28R matrices,
  recomputes syndromes/tags/metrics/accounting/terminal precedence, rejects
  tampered frame/block/matrix/summary/record evidence and extra files, and
  persists `readonly_verify.json` with `decoder_rerun=false`.
- **I12 [x]** — implement the user-authorized irreversible-threshold early
  stop after a persisted block, including a replayable `early_fail_proof` and
  prefix-only FER scope. Canonical run_02 stopped after 9 blocks because
  `1+91=92<95`; no next decoder call was started.

## Test IDs

- **T0-01..T0-04 [x]** — frame ranges, pair counts/order, four-frame grouping,
  and leakage/f accounting covered by `test_nonbinary_v29.py`. Matrix and
  channel binding remain I05/I06 follow-on checks.
- **T1-01..T1-06 [x]** — fake Bob-only order, oracle-input sealing, L1
  failure/L2 not-run, tag mismatch/false-accept accounting, no holdout
  fitting/raw `.ttbin` access, and strict binding rejection are covered by the
  injected-run tests.
- **T2-01..T2-05 [x]** — fake 300-block PASS, scientific FAIL, resource prefix,
  stop-before-call/301st-call behavior, clean verifier replay, and semantic
  evidence tamper/file-set rejection are covered without the official decoder.
- **T3-01 [x]** — focused V28 regression passed; no broad fresh-data rerun is
  implied.
- **T3-02 [x]** — early-stop state machine, prefix finalization, proof tamper,
  and no-parquet finalizer tests passed on synthetic evidence.

## Evidence IDs

- **E01** — `RUN_MANIFEST.json` with frozen config, input boundary, call count,
  resource state, terminal, and no-extra-file declaration.
- **E02** — `frame_selection.json` with exact source/frame/file identity.
- **E03** — `block_manifest.json` with the 300 ordered four-frame blocks.
- **E04** — `channel_model_binding.json` with V26 train path/model identity,
  source IDs, delays, and no holdout fit.
- **E05** — `matrix_binding.json` with V28R config, dimensions, rank, edges,
  topology, coefficients, and source-specific L2 mapping.
- **E06** — `per_block_results.jsonl`, one persisted record per completed block.
- **E07** — `source_summary.json` with per-source/global metrics and observed
  prefix FER scope.
- **E08** — `gate.json` with terminal precedence, counters, user stop, and
  `early_fail_proof` when a threshold is mathematically irreversible.
- **E09** — `readonly_verify.json` with no-decoder-rerun reconstruction result.

## Verifier IDs

- **V01** — reject non-exact frame ranges, extra frames, duplicate rows, or
  wrong pair order/count.
- **V02** — rebuild and verify V28R matrices, dimensions, rank, degrees, and
  source-specific L2 binding.
- **V03** — verify V26 train/source/delay binding and no holdout calibration.
- **V04** — recompute public syndromes, true/decoded tags, leakage, and f.
- **V05** — recompute block/source/global metrics, observed-prefix FER,
  false accepts, and terminal precedence without invoking a decoder.
- **V06** — verify resource-blocked completed-prefix semantics and that no
  next call began after 300/300.
- **V07** — reject tampering in any required evidence file and reject extra
  input files.
- **V08** — for an authorized early stop, recompute the threshold proof from
  the persisted prefix and reject a tampered proof without treating prefix FER
  as full-run FER.

## Gate/closeout IDs

- **C01 [x]** — independent read-only verifier returns `ok=true` for canonical
  run_02.
- **C02 [x]** — canonical terminal is `v29_finite_gate_fail` with a valid
  irreversible threshold proof; it is not a full-300 FER result.
- **C03 [x]** — archived after main-thread review; FAIL forbids tuning/retry
  in V29 and does not authorize qualification or promotion.

## Freeze-review ambiguity audit (15 items)

All items below are resolved in this draft; none is an execution blocker. They
must remain explicit in the accepted packet.

| # | question | frozen answer |
|---:|---|---|
| 1 | Are frame endpoints inclusive? | Yes: 1600..1999, 2213..2612, 2916..3315. |
| 2 | Which source identities bind the files? | The three exact V25 `type2_*` source IDs in design §2. |
| 3 | Which delays apply? | 1M=-50 ps; 1p5M=+50 ps; 2M=+50 ps. |
| 4 | How many rows per frame? | Exactly 256 pairs; otherwise implementation_blocked. |
| 5 | What is pair order? | V25 `pair_idx`, sorted by `(frame_id,pair_idx)`. |
| 6 | How are blocks formed? | Four consecutive selected frames, 1024 symbols, block 0–99/source. |
| 7 | Which factorization/labels apply? | F03 natural MSB→LSB GF32+GF32. |
| 8 | Which channel model is allowed? | V26 train-only, source/delay-conditioned; no holdout fitting. |
| 9 | What does Bob provide to the decoder? | Full observed B plus Bob layer observations and public syndromes. |
| 10 | What conditions L2? | Only the actual returned L1 `x1_hat`; L1 failure makes L2 not_run. |
| 11 | How are truth and tags separated? | Truth creates public syndrome/tag and offline score; decoder sees neither truth. |
| 12 | Which decoder settings/searches are allowed? | max_iter=200, streak=20; no search or retry. |
| 13 | What are exact/verified/false-accept metrics? | Exact means both layers equal truth; false accept means tag pass but nonexact. |
| 14 | How does resource precedence work? | Persist one record after L1 plus conditional L2 for the block; check 300/300 first (even at 24 h), then apply the 24 h gate only to an incomplete run before the next block. |
| 15 | What does verifier do on incomplete runs? | No decoder rerun; verify only completed prefix and exact unrun suffix. |
| 16 | May an irreversible threshold fail stop before 300 blocks? | Yes, only after the current block record is persisted and only when `false_accept>0`, `exact+remaining<95`, or `tag_verified+remaining<95`; persist a proof and report FER as observed-prefix-only. |

## Scope stop condition

The V29 worker returned after I01–I12 and the frozen tests/evidence were
complete. Canonical run_02 is retained under the additive output root;
run_01 remains the superseded 0-call `implementation_blocked` evidence. V30 is
a separate draft and must pass a new freeze review before execution.
