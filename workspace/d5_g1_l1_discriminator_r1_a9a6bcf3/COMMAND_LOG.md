# D5 L1 discriminator command log (development-only, CAL-TRAIN, no VAL)

Root: `workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/`
Prereg: `G1_L1_ESTIMATOR_DISCRIMINATOR_PREREG_R1.md` (committed alone as
`f0e4a1c` before any command below).

1. `python workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/c1_cal_estimator_compare.py`
   Phase C, 0 decoder calls, wall ~0.7s, peak RSS 182894592 B.
   Result: winner E2 (mean held-out L1 NLL 3.771651 vs E1/E3 3.814742),
   kap* 62.10169418915616 unanimous across folds.
2. `python workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/d2_n64_frontier.py`
   Phase D n64, 25 decoder calls (S0 1 + {E2,E1} x {49,59,64} x 4 seeds),
   wall ~13.6s, peak RSS 105095168 B. Result: 0/24 exact/syndrome (S0 pass).
3. `python workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/d3_block_scale.py`
   Phase D scaling (triggered: n64 0/4 everywhere m<64), 50 decoder calls,
   wall ~63.6s, peak RSS 106958848 B. Result: n128 NO_RECOVERY (nonzero-rate
   0/4; square 1/4), n256 NO_RECOVERY (nonzero-rate 0/4; square 2/4).
4. `python -m pytest -p no:cacheprovider
   comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py
   comparison_bench/tests/test_v72p2d5_model_f_input.py
   comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py
   comparison_bench/tests/test_v72p2d4r2_cal_gf32_model_rate_audit.py -q`
   Four-file D5 suite: 259 passed, 0 failed, 60.05s (benign cache_dir warning).

Totals: 75/1500 decoder calls, max per-call wall 2.41s (watchdog 120s),
peak RSS 182894592 B (<2GiB). No formal-root write, no VAL, no push.
