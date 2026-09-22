# Tasks: v72p2d5-g1-information-recovery-r2

- [x] T1 (OpenSpec): proposal/design/tasks/specs written before code (this change).
- [x] T2 (implement): add `build_f_model_concentration` +
  `prepare_model_f_prior_candidate` to `v72p2d5_gf32_rate_mother.py`
  (additive only; frozen symbols untouched).
- [x] T3 (tests): extend `test_v72p2d5_gf32_rate_mother.py` with defect,
  numerical-limit, axis/normalization, CAL-selection-basis, and
  formal-root-isolation tests.
- [x] T4 (validate): compile + focused tests + exact three-file D5 suite +
  candidate development diagnostics green; record evidence.
- [x] T5 (deliver): logical commits (proposal/evidence vs implementation
  separated); no push; return review-ready candidate.
  Evidence 20260908: acceptance `G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`
  landed on review `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS` (chain
  `88053563→a93106f5→21576add→1d4fa912`); cycle `next_gate` moved to
  `G1_L1_ESTIMATOR_DISCRIMINATOR_IN_PROGRESS`; scoped six-file commit, no push.
- [x] T6 (D5_G1_R2_STALE_GUARD_FIX_R1): replaced stale
  `assert _snapshot_dir(ROOT / mod.G1_FORMAL_ROOT) is None` in
  `test_G1R01_fresh_root_literal_and_old_barred` with start-of-test snapshot
  invariance (`_g1_before` + `_assert_formal_roots_unchanged` +
  `assert _snapshot_dir(_g1_root) == _g1_before`); extended
  `test_T1_23_no_formal_root_absence_assertion` to flag
  `_snapshot_dir(<formal-root expr>) is/== None`. Evidence: focused
  `2 passed, 1 warning in 1.68s`; full three-file D5 suite
  `227 passed, 1 warning in 23.03s` (fresh basetemp
  `workspace/v72p2d5_g1r2_staleguard_r1_20260908`, `-p no:cacheprovider`).
  No production or scientific behavior change.
