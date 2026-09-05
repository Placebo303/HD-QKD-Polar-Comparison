# V72P2D4R1 IMPLEMENTATION_REVIEW (CAL-only, frame-blocked nested)

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `a7a6ec62` (`HEAD == origin/formal-ir-v72p1-addendum-clean`)
- Cycle: `V72P2D4R1-CAL-GF32-MODEL-RATE`
- Review kind: `R1_IMPLEMENTATION_REVIEW_CAL_ONLY`
- Verdict: `R1_IMPLEMENTATION_ACCEPTED`
- Date: `2026-09-05`

## 1. Review binding (exactly 3 files, no baseline change)

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d4r1_cal_gf32_model_rate_audit.py`
2. `scripts/v72p2d4r1_cal_gf32_model_rate_audit.py`
3. `comparison_bench/tests/test_v72p2d4r1_cal_gf32_model_rate_audit.py`

No `src/`, `experiments/`, `tools/`, `results/`, or existing comparison output changed. Old Attempt-0 files (`v72p2d4_*` module/CLI/test/outputs) untouched, not reviewed, not committed.

## 2. Logic evidence (CAL-only, decoder 0)

- `py_compile` PASS on all three files.
- `pytest comparison_bench/tests/test_v72p2d4r1_cal_gf32_model_rate_audit.py -p no:cacheprovider -q`: **30 passed** (T0 10 + T1 15 + T2 5) in ~22s.
- Constants frozen: `Q=1024/Q_SUB=32/N=1024/CAL702..1725/SESSION 20260123_1M_600k_0dB`, `FLOOR=1e-300/NORM 1e-12/CHAIN 1e-10`, `M1_LAM=1.0/LAMBDA_GRID 30/M3_EXIT_AMBIGUOUS/UNIFORM 10.0 descriptive`, `SELECT_DELTA=0.02/STABILITY 0.10/0.20`, `F 1.0/1.1/1.2/1.3`, `H1 16/L2 200/Total 216 rows`, budgets `300/300/600s/RSS 2GiB`.
- CV mechanics: `outer_folds` TEST256/TRAIN768 deterministic frame blocks, four TESTs partition `702..1725`; `inner_folds_for_outer` 3×(512/256) partition outer TRAIN, pairwise disjoint, no `permutation/shuffle/default_rng`; `inner_select_lambda` never reads outer TEST (T1 tamper: perturbing outer TEST leaves selection unchanged).
- Models: M0 train-marginal pin, M1 canonical `P(A|B)` frozen `lam=1.0`, M2 hierarchical `P(U1|B)*P(U2|U1,B)` grid-30 inner-selected, M3 direct `M3_EXIT_AMBIGUOUS` excluded from selection/budget/route; floor-then-normalize only protects log; chain `<1e-10` enforced in `ce_m0/ce_m1/ce_m2`.
- R5 gate: same-fixture synthetic (`seed=20260905/n=4096/lam=1.0`) repro `6.422161237462124/5.083351288530697/11.50551252599282`, `|Δ|<1e-6`, chain `<1e-10`, `passed=true`, `real_cal_exact_match=false`; failure raises `BLOCKED`, never tunes to fit.
- Selection/budget/route: `select_model` fold-mean minimal + delta-0.02 simple priority + unstable downgrade; `budget_rows=ceil(N*CE*f/5)` vs `16/200/216`; `route_from_selection` A/B/C mutually exclusive on selected-model mean.
- Prohibitions: module/runner contain no `decode_row_layered/history_decode/run_g_layer/compute_tag/hashlib/sha256/md5/checksum/zeros((16,1024))/VAL1726/val_bundle/mock/stub`; CLI only `--registry/--out-dir`, no `--execute-real/--lam/--val`; `validate_output_target` allows only the pre-registered root or fresh `workspace/` dir, refuses existing dirs and any `run_01`.
- Summary scalars only: banned keys (`alice_symbols/bob_symbols/prior_logp/syndrome_*/candidate/messages/...`) probed; `decoder_calls=0/published_bits=0/formal=false/cal_only=true`.

## 3. Boundaries

No VAL read for fitting, no decoder call, no new matrix, no checksum/hash/tag, no formal `run_01`. Old Attempt-0 output root stays untracked and is not evidence.

*Implementation acceptance only. Result interpretation is in RESULT_SUMMARY.md.*
