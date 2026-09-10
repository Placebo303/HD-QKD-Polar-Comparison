# D7-B easy-regime — tasks (R1 T0–T6 under A1)

- [ ] T0 — Baseline/read-only audit (reuse prior T0 per A1.3 after fresh recheck:
  HEAD f98dde08, branch formal-ir-v72p1-addendum-clean, D7-A PASS present, auth
  keys false, formal/dev/VOID metadata unchanged, G2/R1d/D7-B roots absent;
  SOP/workbuddy paths excluded; no decoder call; no VOID content read)
- [ ] T1 — Freeze OpenSpec (proposal/design/tasks/spec) + `D7_B_PREREG_R1.md` +
  `D7_B_EXECUTION_PACKET_R1.md` + `cycle_state.yaml` BEFORE any new
  production-decoder observation; nine A1 feasibility proofs + 7<8 negative
  proof recorded; active docs/code use ONLY A1 topology; scoped local commit
  (plan); no push
- [ ] T2 — Minimal implementation (`v72p2d7_gf32_easy_regime.py`, focused test
  file, runner script): deterministic builders, priors, tree-exact dual calc,
  cap ladder + 420 stop, recomputation, budget/resource guards, five-file
  writer + verify, lazy-bind + DI; v35/D5 read-only; D7-A oracle reused
- [ ] T3 — Qualification: py_compile → focused D7-B → D7-A regression →
  related D5/v35 fake → one non-perf milestone suite (no perf-v38); covers B03–
  B14 incl. 64-cell/420 accounting, priors, rank/degree, D7-A reuse, ladder/
  early-stop, terminals/boundaries, proxy equivalence on tiny fixtures, fake
  success/partial/no-region/crash/nonfinite/timeout/budget, schema/verifier,
  unauthorized-no-root, no-data-access, protected-root guards
- [ ] T4 — Independent implementation review (source inspection + independent
  recomputation; confirm zero scientific decoder calls); verdict
  `D7_B_IMPLEMENTATION_REVIEW_PASS`; one narrow rework max
- [ ] T5 — Independent Pre-EXECUTE review (branch/commits, D7-A dep, 64 cells/
  seeds/priors/caps, 420/1500/1800/120/2GiB, out-of-repo reachability probe
  with repo-off-sys.path + sentinel + probe-tempdir-empty + zero scientific
  call, live RSS positive-int, timeout.exe + 3 s rehearsal exit 124, UUID
  absence, no-overwrite, unauthorized refusal, protected roots, exact future
  command, Pre-RESULT boundary); verdict
  `D7_B_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
- [ ] T6 — Closeout: scoped local commits (plan → impl → reviews → closeout),
  decision-log/memory appends only if not already represented, no
  result/attempt/completed update; gate
  `D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` only after both PASS; then STOP
