# D15 Paired Finite-Length Margin Curve — EXPLORE log (append-only)

- Authority: `.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md` (§§1–§7, sole authority; §7 return contract).
- Track: documentation-only (no code, no execution, no D15 batch, no decoder/scientific calls, no root creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This is the single append-only log root for D15. Detail record: `READINESS_R1.md` in this directory.
- Predecessor pointer: `docs/research_cycles/D14_VALIDITY_RESET/EXPLORATION_LOG.md` (D14N accepted `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`; routes to margin curve).
- This call (D1510B): documentation-only close (two new record files in this directory, one pointer append to the D14 log, D15 OpenSpec `tasks.md` D1503–D1510 checkbox update). No code, no execution, no decoder/DE/real-data calls, no staging/commits, no push.

## 2026-09-15 — D15 readiness R1 close (no execution)

### Authorization boundary

- This call performed no code edit, no D15 execution, no decoder or scientific call, no root creation, no commit, no push.
- The frozen 288-call margin-curve batch remains unauthorized. It requires a separate explicit batch grant. No authorization was granted by readiness or by D15-R1510.
- No-execution-authorized statement: **no D15 execution is authorized by this close; the future root remains absent and the frozen command remains an unauthorized string.**

### D1501–D1509 evidence (trusted VERIFIED, do not rerun)

- Arithmetic: loads 548.700215065776 / 412.508145233200; factors L1 1.00237/1.03882/1.07527 + L2 1.00604/1.04240/1.07877; pairing gaps +0.00367/+0.00359/+0.00350; sockets L045 313 / L055 301 / L2 384; all nine allocs count-sum=m + socket-sum=E.
- Admission 36/36 (A1–A6, replay, 1 component, srank==m, gf32==m; L1 min_dc 2, L2 min_dc 4); replacements 0; wall ~2.39 s double-build.
- Seeds: 36 graph + 8 blocks 3901–08 exact, disjoint from priors; plan 288 (9×32, point-major) + batch-tag d15-margin-curve-v1.
- Reuse is-identical, no copied kernels; No-APP 0 hits, ARMS len 3, oracle diagnostic-only ungraded.
- Tests 25/25 + py_compile 3/3; PROFILE_ONLY 36 graphs + 288 plan, decoder 0; fake summary setup 46/calls 288; budgets 288/46/1800/120/2GiB/1-proc.
- Refusal rc=2 pre-write/bind/load (reviewer ran); future root absent pre/post; FROZEN_COMMAND verbatim.

### D1510 verdict/findings (trusted VERIFIED)

- EVIDENCE_ACCESS VERIFIED; VERDICT PASS_WITH_FINDINGS; BLOCKING none.
- D14N-3FAIL adjudication: ENVIRONMENTAL NON-BLOCKING, out of D15 scope.
- Non-blocking: stale runner comment (flag wording contradicts actual — code correct, later docs touch); additive-clean scope.

### Terminal

`D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`. Next gate: separate explicit batch grant. No route/investment/D7-H/FER claims.
- 2026-09-15 main-thread readiness acceptance: accept D1501–D1510 and
  `D15-R1510` (`EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, BLOCKING
  none) as `D15_MARGIN_CURVE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  The materialized D14N result-root failures are stale-world-state outside the
  D15 gate. Acceptance freezes readiness only; the 288-call batch remains
  unauthorized and D7-H remains closed.

## 2026-09-15 — D15 Batch A1 pre-dispatch (AUTHORIZED once)

- Grant: user turn 2026-09-15, `D15_MARGIN_CURVE_BATCH_A1` once, branch
  `formal-ir-v72p1-addendum-clean`, root
  `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`,
  n128 matrix, budgets 1800s/120s/RSS<2GiB/1CPU. Consumed at command start.
- 1. Marker `D15_MARGIN_CURVE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
  present: decision-log + memory + log:38 + packet:10 (rg 4 hits). D15-R1510
  VERIFIED PASS_WITH_FINDINGS, BLOCKING none. PASS.
- 2. Branch `formal-ir-v72p1-addendum-clean` exact; `614a0e81` ancestor of HEAD
  (ANCESTOR_YES). Scoped D15 paths clean: runner/module/tests/OpenSpec unchanged
  (no status entries); log diff = +6 acceptance lines only (explained). Other
  worktree dirt (formal_ir misc, scripts misc) preserved untouched. PASS.
- 3. Official root absent (`ls`: No such file). Model-F present: `model_f_input.npz`
  + summary; `cal_only true`, `decoder_calls 0`; sha256
  `38e4bfba74d06234af22e931d43d00e51e4a3c61825c59f02c1ed00b6280d345` matches
  D14 log:159 + V72P2D10 log:480 records. PASS.
- 4. Own recompute (`.venv` python, not trusting spec): LOAD_L1=548.700215065776,
  LOAD_L2=412.508145233200 (12dp exact); factors L1 1.00237/1.03882/1.07527, L2
  1.00604/1.04240/1.07877 (5dp); gaps 0.00367190/0.00358504/0.00349818 (≈packet
  0.00367/0.00359/0.00350); nine socket tables all count-sum=m + socket-sum=E
  (L045 E313, L055 E301, L2 E384). Exact agreement. PASS.
- 5. Own reconfirm: 36 graph seeds exactly 2026093801..3836 in frozen per-cell
  4-sets; 8 blocks 2026093901..3908; plan 288 call_idx 0..287, 9 cells x 32;
  no predecessor overlap (own pool 129 seeds, disjoint; module import asserts
  fail-closed). Seed-leak rg outside D15 files: zero hits. PASS.
- 6. PROFILE_ONLY rc=0 once: admitted 36/36, A1-A6 all true (sample seed 3801:
  1 component, srank 110, gf32 110, replay true), replacements 0, plan 288,
  decoder 0, wall 1.07 s, future_root_absent True; official root still absent
  after. Cosmetic note: `plan_per_cell` summary collapses to one key (built from
  `plan[:9]`, all L045:m110 by point-major order); plan_calls=288 + own 9x32
  counter confirm the matrix. PASS.
- 7. Adapter probe: `d15.dispatch_l1 is r2.dispatch_l1` (accepted L1);
  `d15.oracle_l2_prior` resolves to `d5.oracle_l2_prior` (true-L2 oracle);
  ARMS len 3, no APP arm; static `transfer` hits 0 (only no-cross-layer doc
  lines); zero calls, zero Model-F loads. PASS.
- 8. Live unauthorized vs `/tmp/d15_check8_scratch`: `refusing --d15-batch...`,
  rc=2, target absent after. Refusal before root/bind/load. PASS.
- 9. `py_compile` 3/3 OK; 25/25 focused D15 tests PASS in fresh
  `workspace/d15_check9_tmp` basetemp (`-p no:cacheprovider -o addopts=`,
  4.44 s; cache warning benign). D14N suites not run (no focused D15 conflict).
  Basetemp removed after. PASS.
- 10. Command/matrix/terminals/budgets match frozen (FROZEN_COMMAND verbatim,
  6 terminals first-match order, 288/46/1800/120/RSS enforced `>=2GiB→FAIL`);
  official root absent; batch-content rg outside D15 files: zero hits. Grant
  unconsumed until Phase 2. PASS.
- PRE_DISPATCH: 10/10 PASS. Proceeding to single Phase-2 execution.

## 2026-09-15 — D15 Batch A1 run evidence (AUTHORIZED once, consumed)

- COMMAND: `.venv/bin/python scripts/v72p2d15_margin_curve_development.py --d15-batch
  --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`
- START 2026-09-15T06:56:08Z, END 2026-09-15T06:59:36Z, EXIT 0. Single invocation;
  no retry/resume/repair/rerun.
- CALLS 288/288 (idx 0..287 contiguous, own `csv` tally); SETUP 46/46 (=36+8+2);
  WALL 201.705 s (summary) vs 1800 ceiling; PER-CALL-MAX 1.319 s vs 120 ceiling;
  PEAK RSS 139161600 B vs strict <2147483648; 1 process; budget_violations [].
- ADMISSION 36/36 (graph_records.csv: 36 rows, all `ok`/`admitted`); statuses
  `converged_exact` 61 / `converged_no_syndrome` 227; crashes 0; iters max 90.
- NINE cells (own tally, exact/syndrome/undetected separate; exact==syndrome every
  row; undetected 0 everywhere):
  - L045 m110: pool 0, vec (0,0,0,0), synd 0, und 0
  - L045 m114: pool 6, vec (3,0,3,0), synd 6, und 0
  - L045 m118: pool 19, vec (5,5,4,5), synd 19, und 0
  - L055 m110: pool 1, vec (1,0,0,0), synd 1, und 0
  - L055 m114: pool 13, vec (3,3,4,3), synd 13, und 0
  - L055 m118: pool 22, vec (6,7,4,5), synd 22, und 0
  - L2_ORACLE m83/m86/m89: pool 0, vec (0,0,0,0), synd 0, und 0 (all three)
  - Totals: exact 61, syndrome 61, undetected 0. Matches summary.json exactly.
- L2 records: n=96, all `oracle True`, `graded False`, provenance `ORACLE`,
  exact 0. L1: n=192, provenance `CHECK_UPDATED`, `graded True`. No APP path.
- MONOTONICITY (pools over rows, retained as-is): L045 0→6→19 non-decreasing;
  L055 1→13→22 non-decreasing; L2_ORACLE 0→0→0 non-decreasing; violations [].
- CLASSES (frozen rules, own application): WEAK = L045 m110, L045 m114,
  L055 m110, L055 m114, L2 m83, L2 m86, L2 m89 (7 cells); MIDDLE = L045 m118
  (19), L055 m118 (22) (pool >16, not adequate); ADEQUATE = none (best pool 22
  <24). No cell adequate.
- TERMINAL first-match: 1 eng-blocked no (violations []); 2 L1-specific no (L1
  high cells MIDDLE, not weak); 3 L2-specific no (L1 high not adequate);
  4 finite-backoff no (high cells not adequate); 5 both-weak no (2 MIDDLE);
  → 6 `MARGIN_CURVE_AMBIGUOUS` (stored; evidence only, no route claim).
- WILSON (descriptive): L045 m110 [0,0.10718]; m114 [0.08889,0.35309];
  m118 [0.42260,0.74481]; L055 m110 [0.00554,0.15745]; m114 [0.25519,0.57740];
  m118 [0.51433,0.82048]; L2 all [0,0.10718]. Paired L045/L055 discordance
  (descriptive): m110 challenger_only 1/concordant 31; m114 7/25; m118 3/29
  (reference_only 0; trials 1/7/3; cells 32). No threshold fit.
- ROOT (six files, D11/D12 convention): manifest.json
  `3bee2a398d7ea104a979d2d056336d3494fe27cc85099e5ccda7163648eb3282`;
  decoder_records.csv
  `3f6a528b062f73f58511bf6cf2c7fc4e3ef18d209506cada6f8f1da9b02b15d8`;
  graph_records.csv
  `3e5293e8d61e3daad041a7ea33df44ef286da8e23bba7a1d7ec296896dea727b`;
  arm_summary.csv
  `a20140b641ea12da425af437a42c295a1ed2ef6e6ed870d2baf0d6b2359ac915`;
  summary.json
  `5fd26c29394d6daf6a667c67df5c621d8b5e2372c82a2378c15a08d77de95f36`;
  command_log.txt
  `7ea1386b158ac4f910532a2d02fa4fda081b7624c136dbe68d1e37237990b848`.
  Manifest command/created_utc `2026-09-15T06:59:36Z` match frozen run.
- VERIFIER: `--verify --out-root <official>` → `checked_calls=288 violations=0`,
  `VERIFY PASS`, exit 0 (read-only; no new root).
- Model-F post-run sha256 unchanged:
  `38e4bfba74d06234af22e931d43d00e51e4a3c61825c59f02c1ed00b6280d345`.
- GRANT_CONSUMED (one-shot used at 06:56:08Z). No commit/push (none requested).
  Terminal is evidence awaiting main-thread route adjudication + batch-end review.

## 2026-09-15 — D15 Batch A1 batch-end review (VERIFIED PASS_WITH_FINDINGS)

- REVIEW_ID D15-B1-REVIEW. EVIDENCE_ACCESS VERIFIED (direct reads, own recounts,
  own read-only --verify rc=0, Model-F re-hash, branch HEAD 614a0e81 + ancestor YES).
  No edits/reruns/root-modification/commit/push.
- AUTHORIZATION PASS: manifest command == frozen string verbatim; command_log single
  7-line pass (prior load 06:56:10Z → 36 graphs → dispatched=288 → terminal AMBIGUOUS);
  START 06:56:08Z/END 06:59:36Z/EXIT 0 consistent; one-shot consumed.
- INVENTORY PASS: six files, hashes match (manifest 3bee2a39…/decoder 3f6a528b…/
  graph 3e5293e8…/arm a20140b6…/summary 5fd26c29…/cmdlog 7ea1386b…); 289/37/46/7
  line counts.
- LOADS/FACTORS/GAPS PASS (own recompute, 16dp): LOAD 548.700215065776 /
  412.508145233200; factors 1.00237/1.03882/1.07527 + 1.00604/1.04240/1.07877;
  gaps 0.00367190/0.00358504/0.00349818; nine socket tables close.
- ADMISSION/SEEDS PASS: 36/36 ok/admitted, A1-A6 true all rows; seeds 3801-3836 +
  3901-3908 exact, zero predecessor overlap.
- IDENTITIES PASS: 288 unique keys, idx 0..287 (point-asc 96+96+96, L045→L055→L2
  per point, graphs/blocks asc); batch_id uniform; setup 36+8+2=46. Cosmetic:
  point_idx 1-based vs prose 0-based, ordering correct.
- RECOUNT PASS (own): L045 0/6/19 [0,0,0,0]/[3,0,3,0]/[5,5,4,5]; L055 1/13/22
  [1,0,0,0]/[3,3,4,3]/[6,7,4,5]; L2 0/0/0; totals 61=61, undetected 0, mismatches 0;
  converged_exact 61 + no_syndrome 227; crash 0; iters max 90.
- ORACLE/NO-APP PASS: L1 oracle=False/graded=True/CHECK_UPDATED; L2 oracle=True/
  graded=False/ORACLE; provenance set exactly {CHECK_UPDATED, ORACLE}; L2 cell tallies
  enter rules 2-4 per design §7 (identical thresholds; "ungraded" = excluded from
  transfer/arm grading); numerically moot (L2 pools 0). No APP path.
- CLASSES/MONO/TERMINAL PASS: WEAK×7 + MIDDLE×2 (L045-m118 19, L055-m118 22),
  ADEQUATE none; monotonicity 0→6→19 / 1→13→22 / 0→0→0, violations []; first-match
  R6 MARGIN_CURVE_AMBIGUOUS (stored); Wilson own-recomputed exact match ([0,0.10718]
  etc); paired 1/31, 7/25, 3/29 descriptive-only, no fit.
- BUDGETS/NO-RETRY PASS: 288/288, 46/46, wall 201.7046/1800, per-call-max 1.3191/120,
  RSS 139161600<2GiB, 1 proc, violations []; single pass, unique identities.
- MODEL-F/CLAIM PASS: npz hash unchanged; CAL-only; ceiling intact; L2-ORACLE-zero
  recorded as evidence ONLY (zero interpretation).
- VERIFIER OWN PASS (288/0 rc=0, no new root). TRUST: R1510 + 10/10 cited per trust
  rule (provenance only; batch numbers recomputed).
- FINDINGS: BLOCKING none; non-blocking (point_idx cosmetic; dirty-tree preserved).
- VERDICT PASS_WITH_FINDINGS; recommendation
  D15_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION; no route/D7-H/commit-push.
- Close: grant consumed, no second run, no commit/push, memory triage pending.
- 2026-09-15 main-thread result acceptance: accept D15-B1 VERIFIED
  PASS_WITH_FINDINGS and literal `MARGIN_CURVE_AMBIGUOUS` as
  `D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR`. The result is
  monotonic but has no ADEQUATE cell: L1 high-point L045/L055 are 19/22 of 32,
  while true-conditioned L2 is 0/32 through m89. This does not select a layer.
   Route to one matched effective-factor point near 1.139 (L1 m125, L2 m94),
   not another broad scan. D7-H remains closed because L2 oracle currently has
   zero recovery at every matched point.

## 2026-09-15 — D16 readiness R1 close pointer (no execution)

- D16 readiness R1 closed as `D16_MATCHED_BACKOFF_READY_AWAITING_EXPLICIT_AUTHORIZATION` (docs-only; decoder 0; root `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a` absent; no batch authorized).
- Records: `docs/research_cycles/V72P2D16-MATCHED-BACKOFF/READINESS_R1.md` + `EXPLORATION_LOG.md`; D16 OpenSpec `tasks.md` D1603–D1609 marked [x]. D1608 VERIFIED `PASS_WITH_FINDINGS` + R1608A scoped re-verify PASS (trusted, not rerun).
