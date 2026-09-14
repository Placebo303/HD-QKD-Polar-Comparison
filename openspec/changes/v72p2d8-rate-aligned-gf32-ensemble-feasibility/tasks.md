# Tasks — V72P2D8 rate-aligned GF32 ensemble feasibility (L1-first)

Packet: `.workbuddy/tasks/D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY_R1_TASK_PACKET.md`
(E01–E06 completed in the readiness call; E07–E12 future, no authorization).

- [x] E01 Re-read and record the accepted D6 claim ceiling and route close
  (no D6 rerun): lifecycle `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`,
  L1 0/40, L2-APP 5/40, L2-oracle 35/40, end-to-end APP 0/120, T1 silent at
  n64/n128/n256; closes only the eligible-only DV3 topology substitution.
  Recorded in `READINESS_R1.md` §1. No D6/D7 file edited.
- [x] E02 Inventory and rank historical DE engines by mathematical
  compatibility (GF32/poly 37, probability vs LLR, check-update convention,
  Model-F prior consumption, degree parameterization, accepted evidence vs
  age) with module path / function / line anchors; rejected alternatives with
  reasons. `READINESS_R1.md` §2.
- [x] E03 Trace the Model-F L1 marginal channel into the selected DE input and
  enumerate every transformation (artifact → E2 `P_F` → `P1` → `1e-15` floor →
  XOR centering); state exact 32-ary preservation; no surrogate substitution.
  `READINESS_R1.md` §3 + `design.md` §2.
- [x] E04 Derive rate/degree/check-row equations and validate arithmetically on
  regular DV3 plus two tiny hand-checkable ensembles (exact fractions);
  numeric tests land in E08. `design.md` §3.
- [x] E05 Freeze the bounded deterministic candidate enumeration/selection
  rule: support {2,3}, step 0.05, 21 candidates, hard cap 21, baseline regular
  DV3 included, canonical IDs, no outcome adaptation; graph/coefficient
  compatibility constraints. `design.md` §4.
- [x] E06 Create this complete OpenSpec change (proposal/design/tasks/spec)
  before any behavior edit, plus `READINESS_R1.md`, `EXPLORATION_LOG.md`, the
  decision-log entry, the fresh root UUID (verified absent) and the exact
  future command (left absent/unauthorized). No production code.
- [x] E07 Implement the minimum adapter + runner + verifier required for the
  frozen future sweep: Model-F L1 sampler, rate/ρ mapping, candidate grid,
  `scripts/v72p2d8_rate_aligned_ensemble_development.py` `--de-sweep`/`--verify`,
  fresh-root refusal. No V26/V27/V37/v35 edits. (2026-09-13; adapter
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d8_rate_aligned_ensemble.py`,
  T0 import check PASS.)
- [x] E08 Focused tests: tiny exact/normalization, rate/ρ hand checks, baseline
  reproduction, deterministic enumeration, invalid-distribution refusal,
  fresh-root/no-overwrite, fake-runner isolation, cross-kernel exact check.
  (2026-09-13; `comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py`,
  T1 14 passed / 0 failed.)
- [x] E09 Run T0/T1 focused tests and a bounded no-production-decoder
  performance smoke; no broad suite rerun. (2026-09-13; T0 py_compile + import
  constants PASS, T1 14 passed; PROFILE_ONLY 4 DE calls: wall 0.801–1.987 s,
  peak RSS 239.3 MiB, future root untouched.)
- [x] E10 Freeze/confirm exact future command, root, maximum candidates, seeds,
  DE iterations/population, wall/RSS budget and stop rules (already frozen in
  `design.md` §5–§6; E10 verifies the implementation matches). (2026-09-13;
  FROZEN_MATCH PASS: command/root/budget/seeds/grid identical to design §5–§6,
  future root absent.)
- [x] E11 Obtain one independent reviewer-go implementation + readiness review
  with `EVIDENCE_ACCESS` and explicit mathematical/claim-boundary findings.
  (2026-09-13; `EVIDENCE_ACCESS: VERIFIED`, `VERDICT: PASS_WITH_FINDINGS`;
  artifact `INDEPENDENT_REVIEW_R1.md`.)
- [x] E12 Apply at most one scoped non-scientific correction, re-review only
  the affected scope, and stop at
  `D8_RATE_ALIGNED_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
  (2026-09-13; F1 applied — realized-max-check-degree test, scoped re-review
  `F1_STATUS: RESOLVED`, `VERDICT: PASS`, 15/15 tests.)

Gate: the future DE sweep remains unauthorized until a separate explicit user
authorization names this batch, branch, root, candidate cap, seeds and budgets.
