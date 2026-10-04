# D7-A — tasks

- [x] T0 — Baseline/scope inventory (HEAD dfab1ed8, roadmap §12 verified,
  R1d paused, auth keys false, R1d/G2 roots absent, production modules read)
- [x] T1 — Freeze OpenSpec (proposal/design/tasks/spec) + `D7_A_PREREG_R1.md`
  BEFORE new numerical results; commit 1 (docs only) also lands roadmap §12
  verbatim; no push
- [x] T2 — Implement `v72p2d7_gf32_decoder_certification.py` oracle
  (independent mult/add/inv tables, direct check-SP deg 2/3, exact posterior,
  row-layered recurrence) + negative-control self-tests
- [x] T3 — Arithmetic + check-update certification tests (exhaustive/sampled
  matrix, per-family max-abs error, tol 1e-10)
- [x] T4 — Tree posterior + loopy per-sweep dynamics tests (tiny synthetic
  in-memory only; `max_iter` ∈ {1,2,3}; damping 1.0; cold start)
- [x] T5 — Adapter + L1→L2 soft-APP audit tests (`final_beliefs` semantics,
  `_softmax_rows`, `app_fed_l2_prior`, `_run_layered_block` with fake
  decode_fn; no historical decoder on the bridge path)
- [x] T6 — Test tiers: py_compile → focused D7-A tests → related v35/D5/D6
  fake/unit regression → established non-perf formal-IR suite once at closeout
- [x] T7 — Independent correctness review in a fresh context (source
  inspection + independent recomputation; exactly one §5 verdict)
- [x] T8 — Closeout: `D7_A_CERTIFICATION_REPORT_R1.md`,
  `D7_A_CORRECTNESS_REVIEW_R1.md`, OpenSpec task-state update, append-only
  decision-log + memory updates, scoped local commits, no push
