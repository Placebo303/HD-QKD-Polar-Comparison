# Tasks — V72P2D9 GF32 DE-decoder calibration and threshold (R1)

Packet: `.workbuddy/tasks/D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`.
C01–C06 completed in the docs/design readiness call (2026-09-14; no decoder,
no DE, no root, no commit, no push). C07–C10 completed in the C07–C10
implementation call (2026-09-14; no production decoder, no scientific DE, no
root, no commit, no push; frozen-match PASS). C11–C12 pending.

- [x] C01 Verify and record the accepted D8 counts/claim ceiling from the raw
  artifacts (no DE rerun): 126/126 calls; DV3 baseline 0/3 at f1.2 and 0/3 at
  f1.0; no candidate all-seeds-both-conditions; winner none; terminal
  `D8_DE_BASELINE_NOT_CONVERGED`; lambda2 0.45/0.50 primary f1.2 3/3
  descriptive only. Exact paths/fields recorded in `READINESS_R1.md` §1.
- [x] C02 Stage-by-stage V26↔v35 semantic map with exact code pointers and
  match/approximation/mismatch boundaries: channel centering + prior/floor
  chain; coefficient permutation direction and syndrome/coset centering;
  variable-node update; check-node update; posterior/belief metric versus
  decoder output; flooding DE versus row-layered sweep; stopping metric.
  Equivalence ceiling and STOP resolution recorded. `design.md` §2–§3.
- [x] C03 Derive the prospective f1.0 role from a rate/information argument
  independent of the D8 outcome: frozen criterion (`mu >= 0.05` bits/symbol and
  `R_ent - R >= 0.01`), numeric derivation (`mu(f1.0)=+0.013383`,
  `mu(f1.2)=+0.794633`), role `BOUNDARY_DIAGNOSTIC`. `design.md` §4.
- [x] C04 Derive deterministic edge-to-node degree realization and
  socket-balance rules; enumerate baseline/0.45/0.50/0.55 at n64/n128/n256 for
  f1.2 and f1.0; flag non-integer nominal socket counts with exact fractions;
  verify min check degree >= 2, realized max <= 4 (<=8 bound), forest
  feasibility. `design.md` §5.
- [x] C05 Freeze the minimal stability/control matrix: DV3 + 0.45 + 0.50 + 0.55
  control; 8 seeds (3 D8 reproduction + 5 fresh); populations 4000/16000
  (f1.2) and 4000 (f1.0 diagnostic); iteration/tolerance frozen; budgets
  <=96 DE + <=12 setup, wall <=1200 s, per-call <=300 s, RSS <2 GiB; stability
  definition and decision rules; §8 routing hooks. `design.md` §6–§7.
- [x] C06 Create this complete OpenSpec change (proposal/design/tasks/spec)
  before any behavior edit, plus
  `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/{READINESS_R1.md,
  EXPLORATION_LOG.md}`, one decision-log entry, the fresh future root UUID
  `10076f83-d752-4bac-9161-d8b0907d951b` (verified absent) and the exact future
  command (left absent/unauthorized). No production code.
- [x] C07 Implement the thin calibration module + runner + verifier: V26/v35
  primitive same-input certification (channel/centering, coefficient direction,
  variable/check/belief updates, tree equality, loopy non-equivalence labels);
  graph-realization audit via accepted V37P0 helpers; future stability runner
  with no production decoder; fresh additive root; read-only verify.
- [x] C08 Focused tests: channel/centering, coefficient direction,
  variable/check/belief updates, tree equality, loopy claim ceiling, degree
  integrality, deterministic planning, failure retention and
  no-production-decoder entry.
- [x] C09 Run focused tests and bounded PROFILE_ONLY calls (never sweep
  evidence, no scientific root); no D8 evidence reuse as a new result.
- [x] C10 Freeze/confirm the exact future command/root and strict
  call/wall/RSS budgets; root absent and all authorization false.
- [x] C11 Obtain one independent reviewer-go review separately judging semantic
  equivalence, f1.0 role, graph realizability and execution boundary.
- [x] C12 Apply at most one scoped non-scientific correction and stop at
  `D9_DE_DECODER_CALIBRATION_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

Gate: no behavior edit before C06 (done); the future calibration batch remains
unauthorized until a separate explicit user/main-thread authorization names this
batch, branch, root, candidate set, seeds and budgets.
