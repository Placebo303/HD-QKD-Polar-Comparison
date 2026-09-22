# V72P2D4R1 CAL GF32 model rate audit (CAL-only, frame-blocked nested)

Descriptive only; not a lower bound; not a failure verdict.

- cycle: `V72P2D4R1-CAL-GF32-MODEL-RATE`
- session: `20260123_1M_600k_0dB`
- outer: `702..957 / 958..1213 / 1214..1469 / 1470..1725` (TEST256/TRAIN768)
- inner: `3 deterministic folds, no shuffle`
- r5_repro_passed: `True` (REAL_CAL_EXACT_MATCH=false)
- selected: `M2` (ranking ['M2', 'M1', 'M0'])
- reason: `mean-minimal within 0.02: M2`
- route: `C` (mismatch@1.0 some layer)
- M0 mean_joint `9.999677` std `0.000309` range `0.000849` unstable `False`
- M1 mean_joint `9.991036` std `0.025195` range `0.067051` unstable `False`
- M2 mean_joint `6.978821` std `0.018226` range `0.047530` unstable `False`
- M3: `M3_EXIT_AMBIGUOUS` (excluded)
