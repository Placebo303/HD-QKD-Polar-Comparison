# D6 R1d graph redirect — EXPLORE log (append-only)

Cycle: `V72P2D6-GF32-GRAPH-MOTHER`
Change: `v72p2d6-gf32-graph-mother-r1d-option-c`
Track: `EXPLORE_HEAVY` under
`TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE` (alias `TWO_TIER_WORKFLOW_ACCEPTED`;
`docs/research_cycles/WORKFLOW-TWO-TIER-R1/cycle_state.yaml`)
Batch: D6 mainline graph redirect heavy R1
Authority: `.workbuddy/tasks/D6_MAINLINE_GRAPH_REDIRECT_HEAVY_R1_TASK_PACKET.md` +
`.workbuddy/tasks/D6_MAINLINE_GRAPH_REDIRECT_HEAVY_R1_PROMPT.md`

This is the single append-only log for this batch. The operator appends attempts,
the preregistered engineering correction (at most one repair+rerun), final
evidence and the batch-end review here; no per-arm documents are created.

## 2026-09-13 — batch opening / preregistration (H01–H35; no execution)

### Authorization boundary

- One authorization covers the frozen conditional arm sequence
  canary→confirmation→scaling; this opening authorizes planning, reconciliation,
  implementation corrections, fake/injected tests, bounded fake/no-op profiling
  and Pre-EXECUTE readiness only.
- No production decoder call, no `--r1d` run, no Model-F/real/raw/VAL/G1/G2/
  D7-H/n1024 contact, no output-root creation, no commit, no push. The planned
  output root does not exist.
- The planned run remains blocked until a separate explicit user/main-thread
  authorization names this batch, branch, arms, widths and budgets.

### Predecessor route close (accepted X1–X4)

- X1–X4 accepted: X1 historical decoder returned `CHECK_UPDATED` with an
  operational provenance path; X2 forward joint exact 2/16, 2/16, 1/16 with
  reverse joint 0/16 (three n64/f1.2 graph pairs); X3 156 failed records,
  row-layered 360 rescued 1 and flooding 90 rescued 0; X4 frozen n256 G2
  1320/1320 calls with 0/600 L1/L2 syndrome-valid and grade
  `G2_CURRENT_CONFIGURATION_FAILED`.
- D5 current rate-mother configuration closed; terminal
  `G2_CURRENT_CONFIGURATION_FAILED` (earlier `DECOMPOSITION_NO_N64_RECOVERY`
  retained as superseded history); runtime 2141.9420988290076 s measured stored
  wall (`workspace/v72p2d5_g2/20260906_r1/execution_summary.json`).
- D7-H remains `NOT_AUTHORIZED / NOT_RECOMMENDED`; no D7 file edited.
- Next orthogonal variable: graph/code construction at the unchanged Model-F,
  rows, coefficients contract and decoder contract; resumed as the existing D6
  R1d Option C eligible-only route (`{B0,B1,T1}`, T1 sole new arm).
- Durable duplicate: one route-reconciliation entry in `docs/decision-log.md`.

### Frozen batch design pointers

- Readiness and frozen design:
  `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS.md`
  (transition table, terminal semantics, command/root/watchdog/budgets/evidence,
  early-negative semantics, claim ceiling).
- Accepted frozen science and thresholds:
  `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` §2–§5;
  `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md`;
  `D6_GRAPH_MOTHER_R1D_READINESS_R1C_A5.md`;
  `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv` (144 cells; 22/22 R1d cells pass).
- Planned fresh root (absent, not created):
  `workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d/`
  (UUID `141730d1-5ed4-4a60-a935-50e8f24f872d`).
- Frozen command (repo venv; requires explicit authorization):
  `.venv/bin/python scripts/v72p2d6_graph_mother_development.py --r1d
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d/
  [--workers 18]`.
- Budgets: ≤2500 total calls (worst case 552 scientific), wall 43200 s,
  per-call watchdog 120 s, aggregate RSS <2 GiB strict, chunk ≥5400 s block,
  no retry.
- Early-negative semantics: H34 reconciliation in the readiness record §4
  (frozen §2 predicate governs; no graph-family-impossibility label).
- Claim ceiling: H35 in the readiness record §4 (exploratory graph-candidate
  evidence only; no FER/qualification/real-data claim; D7-H not revived).

### Attempts

- None (execution). This opening performed read-only verification (H01),
  documentation and additive readiness corrections only
  (H02/H03/H11–H15/H21–H24/H31–H35); no run root created.
- Readiness corrections recorded: R1d additive `residual_syndrome_weight`
  evidence column (`R1D_DECODER_FIELDNAMES`; frozen `DECODER_FIELDNAMES`
  unchanged); BP-compat focused-test isolation fix (below).
- Retained failed attempt / incident (engineering, test-only, no data): an
  exploratory *combined* pytest invocation of
  `test_v72p2d6_gf32_graph_mother_r1d.py` +
  `test_v72p2d6_bp_provenance_compat.py` in one process hit a
  module-reload identity hazard: the BP-compat worker tests patched `dev.d5`
  while `_worker_main` resolved the reloaded live package instance, so 4 tests
  reached the real `bind_historical_decoder` path (up to 8 entered historical
  decoder invocations, warmup + task, on tiny in-memory synthetic fixtures
  4×4/8×8; no Model-F/real/raw data, no writes, no roots). The four tests
  failed loudly (`len(bind_calls) == 1`), no scientific result cites them, and
  the single authorized style (per-file separate processes) was clean. Fix:
  `_run_worker` now patches both the loaded and the live sys.modules instance;
  re-proof with a detector plugin: combined run 28/28 passed, `V35_DETECTED=[]`
  (no real v35 import/decoder reachable).
- Readiness test evidence: `test_v72p2d6_gf32_graph_mother_r1d.py` 14/14,
  `test_v72p2d6_bp_provenance_compat.py` 14/14, `test_v72p2d6_gf32_graph_mother.py`
  62/62 (A4/A6 equivalence included), `test_v72p2d5_gf32_rate_mother.py`
  165/165, H12/H13 no-decoder proof transcript
  `/tmp/opencode/d6_h12_h13_proof.out`; `py_compile` OK.

### Final evidence

- Placeholder — to be filled by the authorized run (fresh root files:
  `manifest.json`, `structure_records.csv`, `selected_arms.json`,
  `decoder_records.csv`, `summary.json`, `command_log.txt`).

### Batch-end review

- Placeholder — one independent batch-end review after the frozen conditional
  sequence (or after an early terminal) covers the authorization boundary,
  machine gates, retained failures, the preregistered repair if used, final
  evidence and the claim ceiling. FAIL blocks promotion of the batch evidence
  and triggers escalation review, not another unreviewed arm.

## 2026-09-13 — H41–H44 readiness validation (T0/T1 + bounded perf smoke; no execution)

Append-only evidence; it supersedes only the readiness numbers in the opening
entry (the retained incident entry above stands). Fresh task-owned basetemps
under `workspace/d6_r1d_heavy_r1_tests/`, `-p no:cacheprovider`, zero
production decoder/CAL/VAL/real contact, no root created, no commit, no push,
`next_gate` unchanged.

- H41 T0: `py_compile` exit 0; constants `H41_CONSTANTS_OK` (exact B0/B1/T1
  arms, T1-only fallback, `r1d-v2`, `frozen-AND-I1`, 22-cell subset, 4
  refused historical roots); tiny-math subset 7 passed / 7 deselected in
  3.68 s.
- H42 T1 per file: r1d 14/14 (6.90 s); BP-compat 14/14 (3.15 s);
  graph-mother 62/62 (248.72 s); rate-mother 165/165 (25.45 s); model-f 32/32
  (6.20 s); d4 30/30 (14.12 s); d4r2 32/32 (32.49 s); nonbinary_v31 11/11
  (3.37 s); v37 11/11 (4.68 s). Literal seven-file non-perf suite 343/343 in
  338.37 s. Explicit category subset 45 passed / 77 deselected (11.24 s):
  22/22 live I1, controls/T1-only, fake decoder matrix, conditional
  canary→confirmation→scaling, crash/nonfinite/resource precedence,
  no-overwrite/historical-root protection.
- H42 H12/H13 re-proof: `H12_H13_PROOF_OK`; 22/22 live I1 min degree 2 /
  0 below; B0/B1 support == D5, B0 coeffs == D5 stream, T1 differs 6/6;
  decoder contract unchanged; transcript
  `workspace/d6_r1d_heavy_r1_tests/h42_h12_h13_proof_r1.out`.
- Combined-order re-proof (r1d + BP-compat in one process with the
  `d6_v35_detect` plugin): 28/28 passed, `V35_DETECTED=[]`; the earlier
  incident (retained above) stays fixed, no production decoder reachable.
- H43 bounded perf smoke: A4/A6 equivalence subset 5/5 (237.28 s; n256
  211.23 s / n64 12.70 s / n128 8.60 s / A4 n64 2.51 s / A4 scaling-fb
  1.02 s); structure-build timing n64 seq 0.074 s, n64 par2 0.076 s,
  n128 par2 0.204 s; old 10,897 s benchmark not rerun; perf-v38 skipped with
  recorded rationale (no scoped dependency changed).
- H44: basetemps listed in the readiness record §7; nothing deleted; legacy
  pytest roots and the R1c immutable root unchanged; planned R1d root still
  absent.
- H41–H44 complete; H45–H46 remain. No terminal, authorization key or
  `next_gate` change.

## 2026-09-13 — readiness review (H45) and closure (H46)

- Independent H45 readiness review artifact:
  `D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS_REVIEW.md`
  (`REVIEW_ID: D6-R1D-HEAVY-R1-H45`), verdict `PASS_WITH_FINDINGS`.
- Terminal: `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION` (H46).
- Findings actioned: F1 (crashes/nonfinite/invariant force the blocking terminal
  when the final terminal is composed; only resource gates stop dispatch) and F3
  (the `V35_DETECTED=[]` detector covers the importlib bind path; it proves the
  real bind path was not reached, not that no v35 import is reachable by any
  route) applied in the readiness record; F2 (`heavy_r1_phase`/Status/§6
  completion state) applied here; F4 (exact entered-invocation count not
  retained; log keeps "up to 8") carried.
- Retained incident (the pre-fix combined pytest invocation that transiently
  reached the real `bind_historical_decoder` path on tiny in-memory synthetic
  fixtures) is explicitly carried to the future batch-end review; adjudicated
  `NON-BLOCKING` by H45, with the residual honesty note on the exact
  entered-invocation count (F4).
- Authorization boundary unchanged: nothing was executed; no production
  decoder/Model-F/real/raw contact; the planned output root
  `workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d/` remains
  absent; all authorization keys false; `evidence_root`/`terminal` null; no
  commit, no push.
- `next_gate` set to `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION`;
  `heavy_r1_phase` set to `H01_H46_COMPLETE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

## 2026-09-13 — A1 pre-dispatch checks (D6 R1d EXPLORE execution A1)

Authority: `.workbuddy/tasks/D6_R1D_EXPLORE_EXECUTION_A1_TASK_PACKET.md` and the
paired prompt sent verbatim by the user (explicit authorization for exactly one
frozen R1d invocation). Branch `formal-ir-v72p1-addendum-clean` (not switched;
no commit, no push). Task-owned preflight root:
`workspace/d6_r1d_exec_a1_preflight/b6e01e19-c70f-4ca2-a131-889d3af6f114/`
(check transcripts in `checks/`). These checks performed no decoder call, no
Model-F content read, and created no output root.

1. Workflow marker — PASS. Raw (`WORKFLOW-TWO-TIER-R1/cycle_state.yaml`):
   `state=TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`,
   `terminal=TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`,
   `accepted_terminal=TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`,
   `accepted_alias=TWO_TIER_WORKFLOW_ACCEPTED`, `main_acceptance=true`,
   `main_acceptance_marker_in_effect=TWO_TIER_WORKFLOW_ACCEPTED`,
   `main_acceptance_date=2026-09-13`, `d6_prerequisite=SATISFIED`.
2. D6 authorization state — PASS. Raw (`V72P2D6-.../cycle_state.yaml`): all 12
   boolean authorization/promotion keys (`implementation_authorized`,
   `structure/g0/g0_recovery/p0_cost/g1/g2/synthetic/real/formal_execution_authorized`,
   `scientific_promotion`, `development_decoder_authorized`) are `false`
   (grep count `any true: 0`); `evidence_root: null`; `terminal: null`.
   `development_authorization_basis` is a provenance string, not a boolean flag.
3. Planned root absence — PASS. Raw: `ls -d
   workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d` →
   `No such file or directory` (exit 2); no `workspace/d6_graph_mother_r1d_*`
   root exists.
4. Dispatch arms — PASS. Raw (read from module constants): `R1D_ARMS=[
   'B0_D5_DV3_NATIVE','B1_D5_DV3_COMMON_LABELS','T1_PEG_DV3']`,
   `R1D_NEW_ARM='T1_PEG_DV3'`, `R1D_SCALING_FALLBACKS=['T1_PEG_DV3']`,
   `len(R1D_VALID_SUBSET)=22`, `dispatch_arms_exact=True`.
5. Model-F root — PASS. Raw: `cal_only=true`, `val_rows_read=0`,
   `status=MODEL_F_INPUT_CANDIDATE`; `model_f_input.npz` size 208467 /
   mtime_ns 1788718027043698800 and `model_f_input_summary.json` size 752 /
   mtime_ns 1788718027043698800 both match the accepted values in
   `MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md` A01/A09 (size_match=True,
   mtime_match=True); unmodified since acceptance.
6. H45 verdict — PASS. Raw
   (`D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS_REVIEW.md`): `VERDICT:
   PASS_WITH_FINDINGS`; F1 FIXED, F2 FIXED, F3 FIXED, F4 CARRIED;
   `TERMINAL_RECOMMENDATION:
   D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION`; closure consistent in
   this log (F4 "up to 8" upper-bound wording carried).
7. Focused drift preflight — PASS. Raw: `py_compile
   scripts/v72p2d6_graph_mother_development.py` → `PY_COMPILE_EXIT=0`;
   `test_v72p2d6_gf32_graph_mother_r1d.py` → `14 passed ... in 6.95s`
   (`PYTEST_R1D_EXIT=0`); `test_v72p2d6_bp_provenance_compat.py` → `14 passed
   ... in 2.68s` (`PYTEST_BP_COMPAT_EXIT=0`); both with `-p no:cacheprovider`
   and fresh task-owned basetemps `.../pytest_r1d`, `.../pytest_bp_compat`.
   The 343-test suite was NOT rerun.

Runner-required authorization state (A1 active). Guard inspection of
`scripts/v72p2d6_graph_mother_development.py` found no authorization-state read
anywhere on the R1d path (no `cycle_state.yaml`/key access); the pre-work gates
are L1907–L1923 (`--model-f-root` required L1907–1908, `assert_no_formal_write`
L1910, `assert_r1d_out_root` L1912–1919, fresh-root refusal L1920–1922), plus
in-loop `R1D_VALID_SUBSET`/live-I1 guards L810–816. The D5 `--phase`
authorization gate (`scripts/v72p2d5_gf32_rate_mother.py:87`) belongs to the D5
entrypoint and is not invoked by the frozen command. Minimum runner-required
key set = none (∅); per "set ONLY the minimum ... the runner actually requires",
no D6 cycle_state field was changed. A1 authorization is ACTIVE per the paired
verbatim prompt (recorded here); all 12 boolean keys remain false and
`evidence_root`/`terminal` remain null.

## 2026-09-13 — A1 execution result (D6 R1d EXPLORE, single frozen invocation)

Exact command (once, from repository root, repo venv, no pipe/modification):

```text
.venv/bin/python scripts/v72p2d6_graph_mother_development.py --r1d \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d \
  --workers 18
```

- Exit code: `0`. Start `2026-09-13T19:43:47+08:00` (epoch 1789299827); end
  `2026-09-13T19:44:03+08:00` (epoch 1789299843); outer wall 16 s; runner-stored
  wall `13.547724741016282 s` (`manifest.json`/`summary.json` `wall_s`).
- Process ownership: wrapper pid 810359; runner python pid 810364; 18 decoder
  worker pids 810393–810410 (`manifest.json` `worker_pids`; decoder rows carry
  exactly this set), zero respawns (`respawn_pid` empty 120/120). No task-owned
  process remains (verified after exit).
- Workers: requested 18, effective 18 (pilot_rss=104386560, main_rss=155660288);
  the allowed RSS downgrade 18→14→12→8 was not triggered.
- Stages/calls: canary ran fully (24 cells / 72 calls: B0,B1,T1 × n64 × 4 canary
  seeds × {f1.2,square} × L1+APP-L2+oracle-L2); T1 did not advance
  (`advancing=[]`, canary `f12_exact=0` for all three arms < 1/4), so
  confirmation was NOT entered (`confirmation_counts={}`). Scaling canary ran
  T1-only at n128 (8 cells / 24 calls) and n256 (8 cells / 24 calls), silent at
  both widths (`f12_exact=0`, `sq_exact=0`); scaling confirmation not entered.
  Scientific calls 120, setup calls 18, total 138 (call_idx 1..120 continuous).
  Per-mode decoder outcome: L1 exact/syndrome 0/40; L2-APP 5/40 (B0 1/8, B1
  1/8, T1 n64 0/8, n128 0/8, n256 3/8); L2-oracle 35/40; end-to-end APP exact
  (L1∧L2-APP) 0/120 cells. `exact`/`syndrome_ok` identical on all 120 rows
  (zero disagreements); crash 0, nonfinite 0, timeout 0; all 40 exact rows have
  `residual_syndrome_weight=0` (zero exact-with-nonzero-residual).
- Stored terminal: `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` (scientific negative;
  no blocking/resource/engineering terminal; `rss_block_terminal=null`,
  `chunk_wall_blocked=false`, `budget_stop=false`). Per the frozen early-negative
  semantics this is a valid completed EXPLORE result, not graph-family
  impossibility; route interpretation remains the main thread's.
- Limits: calls 138 total ≤2500 and 120 scientific ≤552 PASS; wall 13.5 s
  ≤43200 s PASS; max per-call wall 2.7687 s ≤120 s, watchdog_ok True 120/120,
  watchdog fires 0 PASS; aggregate RSS `aggregate_rss_bytes=2023432192` /
  `peak_aggregate_rss_bytes=2049343488` <2147483648 strict PASS
  (`rss_semantics` fail-closed, no zero substitution); chunk walls canary
  4.507 s / n128 2.919 s / n256 4.576 s <5400 s; no retry, no resume, no
  seed search, no second root.
- Output-root inventory (all six, fresh root; no file renamed/deleted):
  `manifest.json` 2484 B; `structure_records.csv` 2631 B (30 rows; header
  carries frozen columns + `row_degree_min`,`rows_below_degree_2`);
  `selected_arms.json` 357 B; `decoder_records.csv` 22711 B (120 rows; header
  carries `residual_syndrome_weight` additively); `summary.json` 1557 B;
  `command_log.txt` 3374 B. Schema markers present: `structure_schema=r1d-v2`,
  `eligible_semantics=frozen-AND-I1`, `r1d_arms=[B0,B1,T1]` in manifest and
  summary; `selected_arms.json` selected = B0/B1/T1, fallback_T=T1,
  fallback_M=null, structural_order_new=[T1].
- Authorization restore (raw before → set → after): before dispatch all 12
  boolean keys false, `evidence_root`/`terminal` null (check 2); "set" = ∅
  (runner requires no key; no cycle_state field was ever written — file mtime
  19:08:16 predates the 19:43:47 run start); after exit all 12 boolean keys
  still false, `evidence_root`/`terminal` still null. No commit, no push
  (HEAD unchanged `278fdf07`; nothing staged).
- Carried disclosure: the previously disclosed pre-fix test-machinery incident
  (exploratory combined pytest invocation that transiently reached the real
  `bind_historical_decoder` path on tiny in-memory synthetic fixtures before
  the scoped fix; adjudicated NON-BLOCKING by H45) and the H45 F4 upper-bound
  wording ("up to 8 entered historical decoder invocations"; exact count not
  retained) are carried forward to the batch-end review without revision.
- Result state: unreviewed and unaccepted; the single independent batch-end
  review (packet §6) remains pending. `evidence_root`/`terminal` in
  `cycle_state.yaml` intentionally unchanged by the operator (no authorization
  key was set; advancement to
  `D6_R1D_EXPLORE_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` awaits the
  independent reviewer verdict).

## 2026-09-13 — batch-end review (A1)

- Independent batch-end review artifact:
  `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_R1D_EXPLORE_A1_BATCH_END_REVIEW.md`
  (`REVIEW_ID: D6-R1D-EXPLORE-A1-BATCH-END`), `EVIDENCE_ACCESS: VERIFIED`,
  `VERDICT: PASS_WITH_FINDINGS`.
- Verifier: `VERIFY PASS` (exit 0), 20/20 mechanical+I1 checks PASS; stored
  vs recomputed terminal agreement `True` (recomputed governs and equals
  stored).
- Recount: 120 decoder rows = 40 cells × {L1, L2-APP, L2-oracle}; canary 24
  cells/72 rows, scaling n128 8/24 and n256 8/24 (T1 only), confirmation 0
  rows; `advancing=[]`; `L1` 0/40, `L2-APP` 5/40, `L2-oracle` 35/40,
  end-to-end APP exact 0/120; scientific 120 + setup 18 = 138 calls.
- Findings (all NON-BLOCKING): [F1] preflight `CHECK2_ALL_AUTH_FALSE=False`
  from counting the non-boolean `development_authorization_basis` key
  (presentation only; all 12 booleans false; no cycle_state write). [F2]
  `cycle_state.yaml` still read the pre-execution gate/`evidence_root`/
  `terminal` null by design; closure applies the reviewed terminal now. [F3]
  H45 F4 carried: exact pre-fix incident entered-invocation count not
  retained, "up to 8" upper bound kept, no count reconstructed. [F4]
  observation: `structure_records.csv` has 8 built-but-never-dispatched f1.0
  contingency cells outside `R1D_VALID_SUBSET` (all 120 dispatched cells
  inside); expected build-all/dispatch-subset behavior, not a guard violation.
- Incident/F4 carried statement: the previously disclosed pre-fix
  test-machinery incident remains carried with H45 `NON-BLOCKING`
  adjudication and the F3 importlib-path qualification; F4 `NON-BLOCKING`
  remains carried.
- `TERMINAL_RECOMMENDATION:
  D6_R1D_EXPLORE_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`. Advisory
  review only: the result remains unaccepted and the route decision remains
  with the user/main thread.

## 2026-09-13 — main-thread result acceptance and route decision

- Accepted the independently reviewed A1 root and stored terminal
  `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` under the exact frozen synthetic
  B0/B1/T1 DV3 contract. The batch was scientifically valid and within all
  registered call, wall, watchdog, RSS, no-retry and no-overwrite limits.
- Accepted facts: L1 exact/syndrome 0/40; L2-APP 5/40; L2-oracle 35/40;
  end-to-end APP exact 0/120; T1 silent at n64, n128 and n256; exact and
  syndrome-valid agreed on every record.
- Interpretation: close the eligible-only DV3 topology redirect. PEG-DV3 did
  not restore the base L1 recovery needed before cross-layer alternation can be
  informative. This does not establish graph-family impossibility or behavior
  of T2/T3/T4/M1/M2, other degree distributions, n>256, real data, FER,
  leakage, qualification or promotion.
- Route: `D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY`. Audit and reuse the nearest
  accepted GF32 density-evolution/ensemble machinery, then design a
  rate-aligned degree-distribution discriminator before another finite-length
  decoder batch. D7-H remains not recommended and unauthorized.
- Lifecycle: `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`. All
  authorization flags remain false; no commit or push is implied.
