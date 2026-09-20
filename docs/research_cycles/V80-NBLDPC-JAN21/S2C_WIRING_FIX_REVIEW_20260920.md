# S2C Wiring-Fix Review (2026-09-20) — EXPLORE
Verdict: PASS. Branch `formal-ir-v72p1-addendum-clean` kept; no switch/commit/push.
SWF-1 call convention: `_construct_gate` L644-645 `construct_fn(arm,seed,trials)` matches `construct_arm(arm,seed,max_trials)` L166; sole `construct_fn(` user, grep sweep clean.
SWF-2 T15 genuine: spy delegates to REAL `construct_arm` via gate, asserts `("L-A",2026092001,20)`+fc0; OLD `construct_fn(seed,trials)` would TypeError/refuse `unknown arm 2026092001`, so T15 fails pre-fix.
SWF-3 frozen contract unchanged: seed 2026092001/trials 20/pins L-A fc0/L-B fc0/L-C fc2/frame-base 2026097201; zero modified tracked files.
SWF-4 blocked-attempt integrity: `workspace/s2c_*` absent (zero roots), refused pre-decode (zero decodes), no `results/`/`outputs_comparison/` writes.
Evidence: `test_v80_s2c_campaign.py` 25 passed (3.76 s rerun here); T15 covers real L-A gate path.
Statement: three-arm re-launch may proceed under standing pre-authorization.
