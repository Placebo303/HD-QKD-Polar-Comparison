# V72P2D5 Model-F Input Pre-EXECUTE Packet (frozen, implement-only review)

- Repository: HD-QKD_Polar_Comparison (Comparison only; never Release)
- Branch: formal-ir-v72p1-addendum-clean
- Cycle: V72P2D5-GF32-RATE-MOTHER
- Change: formal-ir-v72p2d5-model-f-input-preparation
- Lifecycle: MODEL_F_INPUT_IMPLEMENTATION_CANDIDATE / PRE_EXECUTE_REVIEW / EXECUTE_NOT_AUTHORIZED
- Date: 2026-09-07
- Role: independent pre-execute reviewer / packet author (reviewer-go with packet-author exception)
- Authorization in this task: false. Execution performed: false.

## 1. Goal

Freeze one real prepare invocation that reads frozen CAL and generates the sole formal Model-F artifact. No P0/G1/G2, no decoder, no VAL-as-model, no second command.

## 2. Exact input (frozen)

- Registry: workspace/v72p2d3_real_registry_20260904.json
  - schema v72p2d3_real_registry_v1, session 20260123_1M_600k_0dB, source 1M, used_2m false
  - cal_frame_ids exactly 1024 IDs 702..1725 sorted no dup/gap
  - val_frame_ids exactly [1726,1727,1728,1729], zero intersect CAL, reject-check only never read
  - columns exactly [frame_id,pair_idx,alice_symbol,bob_symbol]
  - parquet_path comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet (repo-root relative, inside Comparison tree)
- Parquet (read-only, no row reads in review):
  - exists at repo-root relative path, is-file, 545280 rows, 1 row-group
  - schema columns exactly frame_id/pair_idx/alice_symbol/bob_symbol
  - CAL retained after filter must be 262144 rows, 256/frame; VAL 0 rows read as model
- Loader: scripts/v72p2d5_prepare_model_f_input.py _load_cal_arrays
  - validates schema/session/CAL 702..1725/VAL 1726..1729
  - resolves parquet relative path, reads only 4 frozen cols via pd.read_parquet
  - keeps only CAL IDs via isin(cal_ids), requires len 262144
  - returns alice_symbol/bob_symbol/frame_id as injected arrays to build_model_f_input
  - never loads VAL as model, never swaps Alice/Bob, never confuses pair_idx/symbol
  - calls build_model_f_input then write_model_f_input, only 2 files, no decoder/P0

## 3. Statistical contract (frozen, D4R2 + R2_DV3)

- counts_ab[a,b] = count CAL pairs Alice=a Bob=b, shape (1024,1024) dtype int64 sum 262144
- axis0=Alice, axis1=Bob; bob_counts[b]=sum_a counts_ab; p_b=marginal/262144 shape (1024,) float64 sum 1
- full-CAL refit after lambda freeze, not outer avg nor TEST concat, no VAL
- symbol=low+32*high; U1=high; U2=low; q32 poly37
- lambda_star=137.3823795883264 (D4R2 nested-CV, refit only)
- CE_L1=3.814742 / CE_L2_oracle=3.347605 / CE_joint=7.162347 provenance only
- CAL 1024 frames x 256 pairs = 262144 symbols, session 20260123_1M_600k_0dB

## 4. Exact output (frozen, sole formal artifact)

- Formal root (must not exist pre-exec): workspace/v72p2d5_model_f_input/20260907_r1/
- Post-success exactly 2 files, no more no less:
  - model_f_input.npz keys exactly counts_ab,p_b (savez_compressed, allow_pickle=False)
  - model_f_input_summary.json UTF-8 frozen schema v72p2d5_model_f_input_v1
- Banned in artifact: raw/frame/P_F/P1/P2/VAL/beliefs/syndrome/abspath/hash/pickle-object/keys/paths/checksum
- Summary frozen: cycle V72P2D5-GF32-RATE-MOTHER, session 20260123_1M_600k_0dB, source 1M, cal 702..1725, n_frames 1024, pairs_per_frame 256, n_symbols 262144, axis [Alice,Bob], dims [1024,1024], mapping symbol=low+32*high;high=U1;low=U2, field q32 poly37, lambda_star, selection D4R2 nested-CV refit, cal_only true, val_rows_read 0, decoder_calls 0, p0_calls 0, formal false, status MODEL_F_INPUT_CANDIDATE (loader also accepts MODEL_F_INPUT_ACCEPTED), artifact_files exactly 2 names

## 5. Exact frozen commands (one prepare + one verify, no extra params)

- Prepare (single authorized invocation):
  - python scripts/v72p2d5_prepare_model_f_input.py --phase prepare --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized
- Verify (read-only, revalidates 2 files, no parquet/write/decoder/P0):
  - python scripts/v72p2d5_prepare_model_f_input.py --phase verify --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized
  - Note: CLI requires --registry even for verify (ignored by verify per help text); recorded as-is, no fix, no invented omission.
- No extra flags: no lambda/frame/output/retry/resume/seed/f-degree/family overrides. No second command.

## 6. Invocation and budgets (frozen)

- Invocation: 1 prepare only (verify is read-only follow-up, not a second prepare)
- CAL rows: 262144; VAL rows as model: 0; decoder calls: 0; P0/G1/G2 calls: 0
- Wall <=300s, RSS <2GiB
- Runner has no hard killer/watchdog framework; outer caller observes timeout (ponytail-lite). No multiprocessing/retry framework in scope.

## 7. No-overwrite / fail semantics (frozen)

- Writer validates in-mem before mkdir; root exists -> FileExistsError before any write
- No overwrite/merge/resume/retry; no P0; no auto verify->P0; no partial delete
- Ordinary failure -> PREP_FAILED (retained, no transaction/rollback machinery)
- Target root must be absent pre-exec; second write to same root refuses with first unchanged

## 8. Stop rules

- Stop on: CAL drift (IDs !=702..1725), retained rows !=262144, non-256 frame, symbol out of 0..1023, axis/marginal/sum/lambda/session mismatch, root exists, parquet missing/schema mismatch, timeout >300s or RSS >=2GiB, any VAL-as-model or decoder/P0 entry.
- No rerun/resume/tuning without new Pre-EXECUTE review + explicit re-authorization.
- No promotion on PREPARED alone.

## 9. Allowed result labels (only)

- Only: MODEL_F_INPUT_PREPARED / PREP_FAILED / RESOURCE_BLOCKED / INPUT_BLOCKED
- Banned: P0_PASS/G1_PASS/G2_PASS/FER/SKR/QUALIFIED/PROMOTED/any success-rate claim
- PREPARED requires post verify PASS + independent acceptance; verify alone is not acceptance.

## 10. Claim boundary

- This prepare generates canonical counts + P(B) only. No FER, no SKR, no rate-point performance, no qualification, no promotion, no secure-key claim.
- Full-CAL refit is not a VAL leak (no VAL claim). Future real single-point must use independent VAL/fresh.
- G0 toy/uniform/random distributions must not substitute.

## 11. Authorization isolation

- Future auth (if granted after PRE_EXECUTE_REVIEW_PASS) covers Model-F prepare only.
- p0_cost/g1/g2/synthetic/real/formal/scientific_promotion stay false; prepare auth must not imply P0.
- P0 still unauthorized in this packet. No P0/G1/G2 execution authorized here.

## 12. Preconditions to execute (all must hold)

- PRE_EXECUTE_REVIEW_PASS with PX01-PX28 all PASS, explicit user EXECUTE_AUTH for this single prepare, target root absent, focused tests PASS, parquet reachable via correct resolution.