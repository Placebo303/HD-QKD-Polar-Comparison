# Change: formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic

Status: P1 SPECIFICATION FREEZE — planner-authored. Read-only except for creating the four OpenSpec files of this change. No production code, no runs, no evidence generation, no commit/push in this phase.

## Positioning (authoritative)

V31 is closed as `ARCHIVED_PARTIAL`: `n=1024` is a full-window negative result (300/300 blocks, `finite_graph_fail`, 0 exact/tag/syndrome); `n=2048` was only a 14-block diagnostic prefix on source `1M`. V32 is a **diagnostic bridge**. It is NOT a qualification, NOT a promotion, NOT a new reconciler, and NOT a V31 completion. Its **single purpose** is to attribute the V31 n=1024 finite-graph failure to exactly one of four mutually exclusive root causes, using paired and pre-registered B0–B5 arms.

## Goal (verbatim, frozen — authoritative here; design/tasks/spec reference this section)

> 在不修改 V31 固定 n=1024 QC packet、V26 allocation、V25/V26 empirical posterior 和 V28R decoder 的条件下，通过成对且预注册的 B0–B5 arms，区分 fixed finite graph/message-passing mismatch、L1 sequential propagation limit、real error structure mismatch 和 empirical channel model mismatch。

## Non-Goals

1. No modification of the V31 fixed n=1024 QC packet, V26 allocation, V25/V26 empirical posterior, or V28R decoder.
2. No V31 rerun, no V31 completion, no n=2048 work of any kind.
3. No new matrix construction, no new allocation, no decoder modification, no posterior retuning, no seed search, no block selection by results.
4. No qualification or promotion claims; V32 terminals are diagnostic attributions only.
5. No reading of raw `.ttbin`; all real-error inputs come from frozen V31/V25 derived artifacts.
6. No new reconciler development and no NB-Polar start (that is successor work, out of scope).
7. No overwrite of any existing output under `results/**` or `comparison_bench/outputs_comparison/**` outside the single new V32 run root.
8. No push; local commit policy follows the repository OpenSpec workflow and is decided by main after acceptance.

## Frozen Input Bindings (identical in all four V32 docs)

All inputs resolve through existing repository-relative paths and identifiers; every binding is opened read-only:

| # | Binding | Path / Identifier |
|---|---|---|
| 1 | Canonical V31 n=1024 QC packet | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/matrix_payloads.json` + `matrix_audits.json` (accepted `QC-cyclic-projective`, n=1024) |
| 2 | V31 n=1024 validation blocks/frames | `.../nbldpc_v31_20260820/run_01/validation_blocks_n1024.json`, `validation_frames_n1024.json` |
| 3 | V31 n=1024 per-block baseline | `.../nbldpc_v31_20260820/run_01/per_block_n1024.jsonl` (300 lines) |
| 4 | V25 run_04 empirical channel | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/` (`channel_counts.npz`, `data_inventory.json`, `split_manifest.json`) |
| 5 | V26 run_02 F03/A02 allocation | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/` |
| 6 | V28R decoder | `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/` (interface authority; Bob-only GF(32) FFT-QSPA `decode_error_domain`) |
| 7 | GF(32) field identity | `GF2mField.create(32)`, poly `0b100101`, `field_id=c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf` (as recorded in the V31 `RUN_MANIFEST.json`) |
| 8 | Allocation scalar | `m1=16` (V31/V30R fixed allocation) |
| 9 | Three frozen source IDs | `type2_1M_20260121_184040` (1M), `type2_1p5M_20260121_183806` (1p5M), `type2_2M_20260121_183657` (2M) |

## Arms (frozen numbers — MUST NOT be changed)

| Arm | Content | Count | Key frozen facts |
|---|---|---|---|
| **B0** noiseless control | Noiseless end-to-end plumbing control | 2 blocks/source × 3 sources = **6 total** | Requires 6/6 exact, 6/6 tag, 6/6 syndrome, 0 false accept. Any failure ⇒ STOP; no scientific attribution is made. |
| **B1** iid synthetic + oracle L1 | Matched synthetic channel, correct (oracle) L1 | 20 blocks/source × 3 = **60 total** | Seeds frozen: 1M `320101–320120`; 1.5M `320201–320220`; 2M `320301–320320`. Every block marked `truth_used=true, truth_role=oracle_l1, operational=false, qualification=false`. Tests whether the fixed QC graph + L2 decoder works at all under matched synthetic conditions. |
| **B2** Bob-only sequential | Identical to B1 in block/seed/truth/channel sample/graph/posterior | **60 total** (same blocks as B1) | The ONLY change vs B1: oracle L1 → Bob-only sequential L1. Isolates L1→L2 propagation. |
| **B3** deterministic shuffled real-error surrogate | Real errors with per-block error count/marginals preserved under deterministic permutation of EXACTLY the B4 block set (blocks 0–19/source) | 20/source × 3 = **60 total** | Rules frozen BEFORE execution: fixed real block IDs (= B4 block set); preserve per-block error count/marginals; deterministic permutation; permutation rule and seed fixed in advance; permutation never selected by results; truth may be used to construct the fixture but MUST NOT be a decoder input. |
| **B4** real retrospective oracle-L1 | Real V31 validation errors, oracle L1 | blocks 0–19/source × 3 = **60 total** | Marked `truth_used=true, truth_role=oracle_l1, operational=false, qualification=false`. Tests only whether L2 has capability under real error structure/posterior. |
| **B5** V31 baseline import | Read-only import of the V31 n=1024 300-block baseline | 300 records imported | MUST NOT invoke the V31 decoder; MUST NOT regenerate any result. Import integrity only. |

Total decoded blocks: 246 (6 + 60×4). Pairing logic: B1↔B2 isolates L1 propagation; B1↔B3 isolates error structure (iid vs permuted-real marginals); B3↔B4 isolates permutation sensitivity within real structure; B4 vs B1 separates real vs matched-synthetic under identical oracle-L1 conditions.

## Development Discriminator (frozen — NOT a qualification threshold)

- **arm pass** = every source has at least **19/20** block successes (B0: 6/6 as above).
- **block success** = `exact && tag && syndrome && !false_accept`.
- This discriminator exists only to make the B0–B5 arms decidable. It confers no qualification, promotion, or operational status.

## Terminal States (frozen set — exactly 9, nothing may be added post-run)

```
bridge_binding_fail
finite_graph_decoder_mismatch
l1_sequential_propagation_limit
real_error_structure_mismatch
empirical_channel_model_mismatch
bridge_pass_ready_for_successor
bridge_inconclusive
resource_blocked
implementation_blocked
```

Minimum decision logic (frozen):

- B0 fail → `bridge_binding_fail` 或 `implementation_blocked`
- B0 pass, B1 fail → `finite_graph_decoder_mismatch`
- B1 pass, B2 显著低于 B1 → `l1_sequential_propagation_limit`
- B1 pass, B3 pass, B4 fail → `real_error_structure_mismatch`
- B1 pass, B3 fail 且伴随真实 posterior calibration/NLL 异常 → `empirical_channel_model_mismatch`
- 多模式冲突或证据不足 → `bridge_inconclusive`

The complete truth table covering all reasonable B0–B5 combinations lives in `design.md §5`; uncovered combinations map uniformly to `bridge_inconclusive`. No terminal may be invented after results are seen.

## Forbidden (must appear consistently in all four V32 docs)

- New matrices; new allocation; decoder modification; posterior retuning; seed search; block selection by results.
- Reading raw `.ttbin`.
- V31 rerun; regenerating any V31 result; invoking the V31 decoder from V32 code paths.
- Anything `n=2048` (blocks, configs, outputs).
- Qualification/promotion statements in any V32 artifact.
- Overwriting canonical V31 `run_01`, any archive, `src/**`, `experiments/**`, `tools/**`, `results/**`, or any output root other than the single new V32 root.

## Output Root (unique)

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/`

If this path already exists when implementation starts the formal run → **STOP: implementation/output collision**. Overwriting and automatic `run_02` creation are both forbidden.

## Run Rules Pointer

The 12-hour cumulative wall-clock budget (persisted meter), the fixed execution order (`binding → B5 → B0 → B1 → B2 → B3 → B4 → terminal reconstruction`), the pre-registered exact-resume constraints, and the exhaustive 7-item early-stop whitelist are frozen in `design.md §4`, mirrored in `tasks.md §Frozen Constants`, and normative in spec SHALL-O1/R1–R3/X1–X3/E1–E2.

## Impact Scope

- `openspec/changes/formal-nonbinary-ldpc-v32-finite-de-bridge-diagnostic/**` (this change, new)
- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v32_finite_de_bridge.py` (new harness CLI, after freeze)
- `comparison_bench/tests/test_nonbinary_v32_finite_de_bridge.py` (new tests, after freeze)
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/*` (new evidence, formal run only)
- `workspace/nbldpc_v32_finite_de_bridge/*` (candidate-only handoff)

No impact on `src/**`, `experiments/**`, `tools/**`, `results/**`, canonical V31/V30R/V28R/V26/V25 roots, or any archived OpenSpec change.
