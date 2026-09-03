# V72P1 Synthetic Qualification Acceptance Record — 20260903_h90q

**Repository**: `HD-QKD_Polar_Comparison`
**Branch**: `formal-ir-v72p1-addendum-clean`
**Cycle ID**: `V72P1-ADP`
**Record Kind**: `SYNTHETIC_QUALIFICATION_ACCEPTANCE` (transcribed, synthetic-only)
**Reviewed Implementation SHA**: `ff88696f3c242cfb441dc9c82720e4fa6a371968`
**SHA Verification**: `HEAD == origin/formal-ir-v72p1-addendum-clean == ff88696f3c242cfb441dc9c82720e4fa6a371968` (verified via `git rev-parse HEAD` / `git ls-remote`, see operator S1)

---

## 1. Authority — Transcribed User Independent Conclusion (No Re-review This Turn)

This record **only transcribes** the user-provided independent dual-PASS conclusion for the candidate below. This round **did not re-run tests/qualification, did not re-review code, and does not mark itself as reviewer**.

- **IMPLEMENTATION_REVIEW**: `PASS` — transcribed from user (covers `ff88696f` implementation on `formal-ir-v72p1-addendum-clean`, candidate directory `workspace/v72p1_baseline_check/20260903_h90q/`)
- **PRE_RESULT_REVIEW**: `PASS` — transcribed from user (covers same implementation SHA and same candidate directory, synthetic qualification only)
- Scope of transcribed PASS: **synthetic qualification only** (`development_execution_scope: synthetic_qualification_only`). Does not authorize formal decoder, real data, `run_01`, or scientific promotion.

---

## 2. Candidate and Solidified Paths

| role | path | files |
|---|---|---|
| reviewed candidate (read-only, preserved) | `workspace/v72p1_baseline_check/20260903_h90q/` | `v72p1_results.json` (18008 B), `v72p1_manifest.json` (2051 B), `v72p1_table.csv` (610 B), `v72p1_compact_report.md` (11031 B) |
| solidified accepted output (byte copy) | `comparison_bench/outputs_comparison/v72p1_synthetic_accepted_20260903_h90q/` | same four files, byte-identical (SHA256 verified, no rename, no content change) |

Prior evidence directory `v72p1_synthetic_qual/` (if any) and candidate directory are retained untouched.

---

## 3. Frozen Command, Seed and Registry (Per EXECUTION_PACKET_ADDENDUM.md)

- **Seed**: `20260902` (global single seed; P1B derived `seed_p1b = 20260902 + k*100 + n*10 + trial`)
- **Registry**: `v72p0_data_registry_synthetic.json` (data_sha `84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1`, `used_2m false`)
- **Frozen specs**: `FrozenMotherSpec Q1024 N1024 Nbit10240 M9036 r0160 delta8 max_rows9036 f_planning1.3 column_mapping sym*10+bit`; `SoftJointConfig checkpoint_rows 72 points 160..9036, max_iter_per_checkpoint10, max_total_iterations720, llr_clip20.0, convergence_tol1e-6, warm_start true, dtype float64, tag_bits64`
- **P1 commands (synthetic-only, additive)**:
  - P1A: `python scripts/v72p1_soft_joint_synthetic.py --phase P1A --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json`
  - P1B: `python scripts/v72p1_soft_joint_synthetic.py --phase P1B --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json`
  - P1C: `python scripts/v72p1_soft_joint_synthetic.py --phase P1C --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json`
  - P1D: `python scripts/v72p1_soft_joint_synthetic.py --phase P1D --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json`
  - Pre: `python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py scripts/v72p1_soft_joint_synthetic.py`

---

## 4. P1A–P1D Main Results (Transcribed from v72p1_results.json, seed 20260902)

- **P1A plumbing**: `pack_ok true, prefix1111 true, Rs_len 1111, checkpoint72 true, incremental true, tag_ok true (sha256(bits.tobytes())[:8], tag_bits64), deterministic true, pass true`
- **P1B tiny exhaustive**: `k 2→n6 / 3→n9, trials 8 per pair (16 total), worst 1.9984014443252818e-15 <1e-9, per_pass true, tree_flags all true, observed_zero true, observed_one true, overall_pass true, wall 0.094s, used_2m false, no_run_01 true`
- **P1C full mother synthetic** (`9036x10240 nnz49620 CSR284248`): `outs 1/3/10 all finite true, maxLLR 0.179859..., residual 7.81e-06→4.20e-10, 72 per_checkpoint all iterations2 residual ~1e-11..3e-10 converged true (tail 4.48e-13), total_iters144, wall46.31s, nonzero true, hard_bits_ok true, pass true, wall thresholds <1/<5/≤30s met`
- **P1D small loopy** (`n12 k3 12bits 4096 exhaustive`): `is_tree false, finite true, worst 0.008958298305150495 descriptive, wall0.062s, pass true (loopy 1e-9 not hard gate)`
- **Overall**: `overall true, five_state true, wall_s 53.125, peak_MiB 126.94437789916992`

See `v72p1_table.csv` summary rows: P1B_tiny / P1C_iter1,3,10 / P1D_loopy.

---

## 5. Non-blocking Findings (Transcribed, Isolated)

1. **Old qual head inconsistency isolated**: prior synthetic qual evidence outside this candidate (if any) carries stale head; isolated, not merged into this accepted snapshot.
2. **Fallback redundancy**: fallback artifacts / untracked files remain as redundancy; not deleted in this solidification (per forbidden `清理fallback/未跟踪文件`).
3. **Peak caliber**: `peak_MiB 126.94` is process-level `tracemalloc`/WSS caliber as in results.json; not a hard gate failure, recorded as descriptive for `tracemalloc peak <2 GiB` bound.

None block synthetic acceptance; all tracked as non-blocking.

---

## 6. Scope and Lifecycle Boundary (Synthetic-only)

- This acceptance is **synthetic-only**: validates `ff88696f` adapter plumbing, tiny exhaustive `1e-9`, full-mother finite/clip/residual, loopy descriptive against frozen `llr_clip 20.0 / convergence_tol 1e-6 / seed 20260902 / data_sha 84d62779`.
- **Real-data capability not verified**: `2M/TEST/holdout`, `formal decoder`, any `run_01`, FER/threshold/SKR claims remain unverified and unauthorized.
- **Lifecycle**: `implementation_sha ff88696f...`, synthetic qualification accepted, solidified path above. `accepted_plan_sha 73efd91f...` and `accepted_addendum_sha b0d55105...` unchanged. `formal_execution_authorized false`, `scientific_promotion false`, `development_execution_scope synthetic_qualification_only`. Formal execution still requires explicit user `EXECUTE_AUTH` + pre-EXECUTE/pre-RESULT gates.

*Record time: 2026-09-03, operator transcription only, no new hash/audit framework added.*
