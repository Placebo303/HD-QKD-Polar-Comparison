# R2 command log (operator wall, calls, RSS)

Budgets: <=1200 decoder calls, <=6h wall, 120s/call watchdog, RSS < 2GiB.
Boundary: no CLI --phase, no formal rerun, CAL-TRAIN only, no VAL use,
no formal-root write, paired frozen seeds 2026090600..03, predeclared
square-mother seed 2026090801. One duplicate W4c invocation (operator
double-run, deterministic identical results, +16 calls) is logged honestly.

| # | command | calls | wall | peak RSS | notes |
|---|---|---|---|---|---|
| 1 | `python workspace/..._r2_.../w1_recompute.py` | 0 | 0.27s | 98975744 | W1 R2-01/R2-03 inputs |
| 2 | `python workspace/..._r2_.../w2_square_frontier.py` | 5 | 4.45s | 112816128 | W2 S0 + SQ-oracle x4 |
| 3 | `python workspace/..._r2_.../w3_contract_audit.py` | 0 | 0.18s | 85442560 | W3 five answers |
| 4 | `python workspace/..._r2_.../w4a_estimator_calibration.py` | 0 | 0.8s | 240963584 | W4a CAL-only folds; parquet CAL-filtered read |
| 5 | `python workspace/..._r2_.../w4b_decoder_matrix.py` | 16 | 6.0s | 130162688 | W4b C1 matrix |
| 6 | `python workspace/..._r2_.../w4c_frontier_bisect.py` (run 1) | 16 | 7.8s | 112508928 | W4c frontier |
| 7 | `python workspace/..._r2_.../w4c_frontier_bisect.py` (run 2 duplicate) | 16 | 7.8s | 112349184 | accidental re-run; identical deterministic output |
| 8 | `python -m py_compile ...` + `pytest -k R2_` | 0 | 0.64s | n/a | 16 passed |
| 9 | `pytest -k test_R2_ --co` | 0 | 0.11s | n/a | 15 collected (7 prior + 8 new) |
| 10 | `pytest -k <8 new tests>` | 0 | 0.13s | n/a | 8 passed |
| 11 | 3-file D5 suite (rate_mother + model_f_input + d4 audit) | 0 | 22.4s | n/a | 226 passed 1 pre-existing fail (G1R01 stale absence assertion) |
| 12 | `python workspace/..._r2_.../w6_candidate_check.py` | 0 | 0.08s | 63881216 | committed-path diagnostics PASS |

Totals: decoder calls 53/1200; script wall ~27.4s + tests ~23.3s << 6h;
per-call max ~1.5s <= 120s; peak RSS 240963584 B < 2GiB.
Formal roots: no write/hash/delete/move/rename (verified via git status).
