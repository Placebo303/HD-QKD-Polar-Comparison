# V72P2D4R2 CAL GF32 model rate audit (CAL-only, frame-blocked nested, U/G/F/L)

Descriptive only; not a lower bound; not a failure verdict.

- cycle: `V72P2D4R2-CAL-GF32-MODEL-RATE`
- session: `20260123_1M_600k_0dB`
- outer: `702..957 / 958..1213 / 1214..1469 / 1470..1725` (TEST256/TRAIN768)
- inner: `3 deterministic folds, no shuffle`
- r5_repro_passed: `True` (REAL_CAL_EXACT_MATCH=false)
- U: `5/5/10 exact (uniform_reference_descriptive)` (reference, not in selection)
- selected: `F` (ranking ['F', 'L', 'G'])
- reason: `mean-minimal within 0.02: F`
- route: `C` (mismatch@1.0 some layer)
- G mean_joint `9.999677` std `0.000309` range `0.000849` unstable `False`
- F mean_joint `7.162347` std `0.015850` range `0.042319` unstable `False`
- L mean_joint `7.343949` std `0.013794` range `0.035372` unstable `False`
- U->G `0.000323` G->F `2.837330` F->L `-0.181602` U->selected `2.837653`
- M3: `M3_EXIT_AMBIGUOUS` (excluded)
- circulant: `CIRCULANT_DEFERRED` (excluded)
