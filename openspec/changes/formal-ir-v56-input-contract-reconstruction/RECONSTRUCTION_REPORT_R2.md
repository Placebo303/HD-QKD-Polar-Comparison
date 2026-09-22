# V56R2 Reconstruction Report — VERIFICATION_ONLY / DECODE_FORBIDDEN

**Tag retained**: `ENGINEERING_INVALID_FRAME_ID_SEMANTICS` (previous frame_id semantics invalid, preserved additive)
**Basis**: `97602558` 起点 `1e34dafb` HEAD `1e34dafb` lifecycle `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — zero decoder until V57
**Semantics**: `raw_channel_timetags → absolute_bin_indices floor_divide(t,200) → physical_frame_match bin//1024 双指针 → pair_sequence (a=binA%1024,b=binB%1024) → logical_frame_grouping frame_id=row//256 pair_idx=row%256 → symbol_1024 → U1U2` — `204800ps=1024×200ps` 为配对尺度，V55 frame_id 为配对后逻辑帧，校准切片 `start=frame_id*256`。

## Provenance
- Two authoritative chains directly call `src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags/_bin_indices_sorted_for_binwidth/_pairs_from_sorted_bins` then 256 grouping. V13 lineage traced via sidecar/build manifest; undetermined → `AUTHORITY_LINEAGE_INCOMPLETE`.
- Raw peak/delay only diagnostic, not injected as -50/+50.
- New outputs additive `verification_manifest_r2.json / calibration_verification_r2.json / RECONSTRUCTION_REPORT_R2.md`, not overwriting old.

## Phase A — Golden Anchors & Three-way Replay (same raw session, no array copy)
- **T-AUTH-1** current replay vs `V55 pairs.parquet` row-wise `frame_id/pair_idx/alice/bob` 100% ✔ (per source `gold_anchor_TAUTH1_current_vs_parquet_100pct=true`)
- **T-AUTH-2** V13 same three functions vs V13 authoritative (sidecar `delay_used_ps` traced, same chain) ✔ lineage `OK_same_three_functions`
- Seven-stage equality per source `raw_channel_timetags/absolute_bin_indices/physical_frame_match/pair_sequence/logical_frame_grouping/symbol_1024/U1U2` all `array_equal true` when same TTBin (current==V13 with same 200/1024 chain). First divergent `null` (no fork in this session’s params; corrected_current only replaces the single differing V13 param proven by lineage, otherwise identical).
- Per-source TTBin/sidecar/generated function/all params/first divergent/unique replaced key/value/first 5 diffs recorded in `verification_manifest_r2.json`.

## Phase C — Calibration on new frames [0,1,2,3] fit → [11,12,13,14] val (after full pair sequence 256 slicing)
- Per source `8*256=2048` pairs, `per_frame 256` via `start=frame_id*256`, zero overlap `∉V55 90 ∧ ∉D4[7,8,9,10,15,16,17,18]` ✔
- `contract_equivalent` seven-stage `array_equal` V13_authority vs corrected_current on same raw → true (same chain) unless injection.
- Distribution per source: gate `A==B>60% acc_U1≥60 acc_U2≥60 CE≤min(0.5*CE_current, CE_V13+1)` hard gate; NLL/q_mass consistency only.
- Current run: `DOMAIN_SHIFT_s` uniformly (contract true but distribution fails in real TTBin session — indicates true domain shift under corrected framing, not contract error). Overall `V56_TRUE_SESSION_DOMAIN_SHIFT` (priority `EVIDENCE_INVALID > MIXED > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`).

## Overall 5-way
- `RECOVERED` requires per-source contract true + distribution true; not met in this real session → no decoder TEST allowed, stays `VERIFICATION_ONLY`.
- If synthetic high-agreement test injection, distribution passes and would be `RECOVERED`; mismatch injection correctly fails closed.

## Checks
- `py_compile` PASS, `rg decode_ 0`, `git diff -- src/ ==0`, fit∩val ∅, zero-overlap ✔, 7-stage names correct, trailing whitespace 0, 15 tests PASS, tag preserved, additive outputs.

*V55 90 permanently banned; same-session remaining frames only within-session confirmation; true qualification at V57.*
