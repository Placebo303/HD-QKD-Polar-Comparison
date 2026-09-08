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
- [ ] T5 (deliver): logical commits (proposal/evidence vs implementation
  separated); no push; return review-ready candidate.
