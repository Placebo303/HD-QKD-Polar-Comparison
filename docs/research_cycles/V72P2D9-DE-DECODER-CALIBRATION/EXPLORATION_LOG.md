# D9 GF32 DE-decoder calibration and threshold — EXPLORE log (append-only)

Cycle: `V72P2D9-DE-DECODER-CALIBRATION`
Change: `v72p2d9-gf32-de-decoder-calibration`
Track: readiness/OpenSpec now (C01–C06); the frozen calibration batch is
`EXPLORE_HEAVY` under `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`
(one authorization, one append-only log, one batch-end independent review).
Batch: D9 GF32 DE-decoder calibration and threshold heavy R1.
Authority: `.workbuddy/tasks/D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`
+ paired prompt.
Readiness record: `READINESS_R1.md` (this directory).

This is the single append-only log for this batch. Future arms append attempts,
the preregistered engineering correction (at most one repair+rerun), final
evidence and the batch-end review here; no per-arm documents are created. This
opening entry is the preregistration/authorization boundary for the *readiness*
call only; the calibration batch is not preregistered as executable until the
C07–C12 readiness terminal is reached and a separate explicit authorization
names the batch.

## 2026-09-14 — readiness opening / calibration contract freeze (C01–C06; no execution)

### Authorization boundary

- This call was authorized for audit, OpenSpec, design and read-only
  verification only. It performed no production code edit, no decoder call, no
  DE call (scientific or probe), no Model-F content read beyond the accepted
  artifact, no CAL/VAL/raw/real-data contact, no output-root creation, no
  commit, no push.
- The future calibration batch remains **unauthorized**. It requires a separate
  explicit user/main-thread authorization naming this batch, branch, root,
  candidate set (DV3, 0.45, 0.50, 0.55), conditions/populations, seeds and
  budgets. No authorization key was or is set by readiness.
- F1.0 was assigned `BOUNDARY_DIAGNOSTIC` from the frozen rate margin before and
  independently of the D8 outcome (`design.md` §4); the D8 terminal and
  winner=none were not reinterpreted.

### C01 accepted D8 counts (read-only)

- Root `workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`
  read but not modified: 126/126 DE calls, `call_idx` 0..125, 126 unique
  `(candidate_id, condition, seed)`, `converged` True 10; 0 candidates
  all-seeds-both-conditions; DV3 baseline 0/3 at f1.2 (worst `AUT_30`
  151.90884493578253) and 0/3 at f1.0 (worst 154.47598423886723); 0.45 and
  0.50 primary f1.2 3/3; every f1.0 row 0/3; `winner_candidate_id: null`;
  `eligible_candidate_ids: []`; terminal `D8_DE_BASELINE_NOT_CONVERGED`.
  Batch-end review `EXPLORATION_LOG.md:436-457`; acceptance `:459-479`.

### C02–C05 frozen contract (see `design.md`; no behavior)

- Full V26↔v35 stage map with path:line pointers and MATCH/APPROX/MISMATCH
  boundaries (`design.md` §2); equivalence ceiling (`§3`) limited to certified
  same-input primitives, tree posteriors and the prior chain; flooding↔row-layered
  and DE↔decoder terminals explicitly excluded.
- f1.0 role criterion and derivation (`§4`); degree/socket realization rules
  and full table (`§5`); stability matrix, stability definition, decision rules,
  terminals and routing (`§6–§7`).
- Fresh future root UUID `10076f83-d752-4bac-9161-d8b0907d951b` verified absent
  at `workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`.
  Fresh seeds `2026091801..05` verified absent in
  `docs/`, `openspec/`, `scripts/`, `.workbuddy/`,
  `comparison_bench/src`, `comparison_bench/tests`, `analysis/` and top-level
  `*.md` at freeze time. Exact future command frozen in `design.md` §6 and
  `READINESS_R1.md` §5; left absent and unauthorized.

### Claim boundary (unchanged)

- Readiness establishes only that the calibration contract is mathematically
  specified, semantically anchored, bounded and mechanically routable. It
  establishes no finite-length/FER/leakage/SKR/qualification/promotion/real-data
  claim, does not reinterpret the D8 terminal, and does not revive D7-H.

## 2026-09-14 — C07–C10 implementation, focused tests and freeze confirmation (no calibration execution)

### Authorization boundary

- Authorized: C07–C10 implementation under the frozen packet (thin module,
  runner, focused tests), py_compile, focused tests, at most 6 bounded
  PROFILE_ONLY calls (never calibration evidence, never written to a root) and
  the frozen-match check. Performed: no production/finite-length decoder call
  (0), no scientific DE calibration call (0), no frozen 96-call matrix, no
  output-root creation, no CAL/VAL/raw/real-data contact, no Model-F content
  read, no D8 evidence rerun, no branch switch, no commit, no push, no
  authorization change (all flags false).
- PROFILE_ONLY calls used a synthetic true-symbol-centered 32-ary channel and
  fresh non-frozen seeds; they are engineering profiles only, not DE
  calibration evidence, and were not written to any root.

### C07 implementation

- New module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d9_de_decoder_calibration.py`:
  same-input V26↔v35 primitive certification (channel centering; coefficient
  direction; check update vs v35 and vs D7-A direct SP; variable/belief updates
  vs the log-sum algebra; star-tree equality vs exact posteriors; labelled
  loopy/schedule non-equivalence diagnostics; DE-metric-vs-decoder-terminal
  mismatch label), deterministic V37-P0 graph realization audit with clear
  refusal on unrealizable socket/forest cells, frozen matrix/stability/routing.
- New runner `scripts/v72p2d9_de_decoder_calibration_development.py`
  (`--calibrate`, `--verify`; six-file root; fresh-root refusal; single
  process; no retry/resume/seed search/adaptive stop; zero-skip verify).

### C08 focused tests

- New `comparison_bench/tests/test_v72p2d9_de_decoder_calibration.py`.
- Command: `.venv/bin/python -m pytest -p no:cacheprovider -q
  --basetemp=workspace/d9_c07c10_tests_7f3d2a91-4c5e-4b60-8a17-2e9f0c1d6b84
  comparison_bench/tests/test_v72p2d9_de_decoder_calibration.py`
  → `20 passed, 1 warning in 6.01s` (warning: unknown pytest config option
  `cache_dir`; benign).
- Coverage: channel/centering, coefficient direction, variable/check/belief
  updates, tree equality, loopy claim ceiling, degree integrality + design-table
  reproduction (all 24 frozen cells), deterministic planning, unrealizable
  socket/forest refusal, fresh-root/no-overwrite, no production-decoder entry,
  full fake 96-call sweep + verify, tamper detection, failure retention/no
  retry, blocked semantics/graph paths, stability labels and selection rank
  including lexicographic tie-break.

### C09 PROFILE_ONLY raw numbers (no root, no calibration interpretation)

- P1 `certify_primitives()` (no DE): `semantics_pass=True`, wall 1.069 s;
  equivalence max abs diffs: channel centering 0.0, coefficient direction 0.0,
  check V26↔v35 3.469e-17, v35↔D7-A direct SP 3.469e-17, variable log-sum
  1.388e-16, belief log-sum 1.943e-16, tree check 2.082e-17, tree V26 belief
  2.776e-17, tree v35 flooding 5.551e-17, tree V26-vs-v35 4.857e-17. Loopy
  diagnostics (non-equivalence, informational): flooding-vs-exact 0.99646,
  flooding-vs-row-layered 0.12931.
- P2 V26 DV3 f1.2 n_samples=100 max_iter=60 seed=2026091999:
  converged=False iterations=60 final_entropy=4.99896 wall=0.025 s.
- P3 V26 0.50 f1.2 n_samples=100 seed=2026091998: converged=False
  iterations=60 final_entropy=4.86781 wall=0.019 s.
- P4 V26 0.45 f1.0 n_samples=100 seed=2026091997: converged=False
  iterations=60 final_entropy=4.9988 wall=0.019 s.
- These reduced-population synthetic calls are not comparable with the frozen
  matrix and are not evidence for any D9 terminal.

### C10 frozen-match / freeze confirmation

- FROZEN_MATCH PASS: exact future command and root
  `workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`
  (verified absent), `--model-f-root workspace/v72p2d5_model_f_input/20260907_r1`
  (runner default), 4 frozen candidates, 8 frozen seeds, 96 planned calls
  (f1.2 64 + f1.0 32), budgets ≤96 calls + ≤12 setup, wall ≤1200 s, per-call
  ≤300 s, RSS <2 GiB, single process, retry/resume/seed-search/adaptive-stop
  all false; V26 parameters unchanged (`max_iter=60`, tol 1e-4, streak 20).
- No calibration root was created; the future root remains absent and every
  authorization flag false. `tasks.md` C07–C10 marked `[x]`; C11–C12 pending.

### Claim boundary (unchanged)

- C07–C10 implementation/tests/PROFILE_ONLY establish only that the frozen
  calibration contract is implemented, mechanically verifiable and
  frozen-match clean. No finite-length/FER/leakage/SKR/qualification/promotion/
  real-data claim; the D8 terminal and winner=none are not reinterpreted; no
  D7-H revival; next gate is the independent C11 review (readiness terminal
  only after C12).

## 2026-09-14 — C11 independent review and C12 closure

### C11 independent review

- Artifact:
  `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/INDEPENDENT_REVIEW_R1.md`.
- `EVIDENCE_ACCESS: VERIFIED`; `VERDICT: PASS_WITH_FINDINGS`; all findings
  non-blocking with no required correction. Four PASS judgments:
  SEMANTIC_EQUIVALENCE, F1_0_ROLE, GRAPH_REALIZABILITY, EXECUTION_BOUNDARY
  (packet §9 STOP conditions 1–6 all PASS). Independent focused pytest rerun
  with a reviewer-owned fresh basetemp: 20 passed.

### C12 closure (zero corrections applied)

- No correction applied; the single-correction allowance is unused because
  every finding is explicitly non-blocking. F1–F6 carried as recorded
  non-blocking notes (proposal/spec max-degree wording, one-parameter criterion
  redundancy, `Δ_min` provenance, between-call budget enforcement, unused
  `allow_partial`, one pointer-offset).
- Terminal: `D9_DE_DECODER_CALIBRATION_READY_AWAITING_EXPLICIT_AUTHORIZATION`

## 2026-09-14 — main-thread readiness acceptance

- Accepted C01–C12 and the independent `EVIDENCE_ACCESS: VERIFIED`,
  `PASS_WITH_FINDINGS` review. The reviewer-owned 20/20 focused tests,
  primitive equality bounds and 24-cell graph realization recount are trusted
  without duplicate execution.
- Accepted prospective f1.0 role `BOUNDARY_DIAGNOSTIC`: the classification is
  derived from frozen margin `mu=0.013383 bit/symbol` and not from the observed
  D8 failure. f1.0 is reported and may trigger review at >=7/8, but never gates
  candidate eligibility or ranking.
- Accepted future calibration matrix: DV3, lambda2 0.45, 0.50 and 0.55; eight
  seeds; f1.2 populations 4000 and 16000; f1.0 population 4000; <=96 DE calls.
- Carried notes F1–F6 remain non-blocking. Execution/result wording must keep
  the actual realized max check degree <=4 distinct from the normative <=8
  bound, describe the f1.0 criterion as one effective margin threshold, disclose
  the design allowance provenance, call timing as between/after-call, leave
  unused `allow_partial` outside the normal complete-root path, and treat the
  pointer offset as cosmetic.
- Lifecycle:
  `D9_DE_DECODER_CALIBRATION_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  This acceptance grants no calibration run, finite-length decoder, D7-H,
  real-data run, commit or push.
  (recorded in `READINESS_R1.md`; `tasks.md` C11/C12 marked `[x]`).

### Authorization boundary (unchanged)

- The future calibration batch remains **unauthorized**: no explicit
  authorization names it; the future root
  `workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`
  stays absent; every authorization flag false; no production decoder call, no
  scientific DE call, no root, no branch switch, no commit, no push.

## 2026-09-14 — D9 calibration A1 pre-dispatch checks (no execution yet)

Authorization A1: the paired A1 prompt authorizes exactly one frozen 96-call
invocation (`.workbuddy/tasks/D9_DE_CALIBRATION_A1_TASK_PACKET.md`; branch
`formal-ir-v72p1-addendum-clean`, not switched). This entry records the eight
pre-dispatch outcomes **before** execution. All eight PASS; no repair applied.

1. **Readiness marker / unexecuted — PASS.** `READINESS_R1.md:3` carries
   `D9_DE_DECODER_CALIBRATION_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
   and `main_readiness_acceptance: true` (`:23`). Calibration unexecuted: frozen
   root absent; no `de_records.csv` anywhere under a `d9_*` root; only prior
   task-owned pytest basetemps (`workspace/d9_c07c10_tests_…`,
   `workspace/d9_c11_review_*`) exist and contain fake test `cal_root`s only.
2. **Authorization flags false — PASS (stated explicitly).** D9 has **no machine
   flag store**: no D9 flag/authorization file exists in `workspace/` or in
   `docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/`; the runner
   `scripts/v72p2d9_de_decoder_calibration_development.py` has no flag-file gate
   (authorization appears only as help text `:752` and a manifest field `:258`).
   Recorded state is false from the readiness prose
   (`authorization_flags: all false`; `future_root_absent: true`) and from the
   absence of any root/records; execution is authorized only by the A1 prompt.
3. **Future root absent — PASS.** `test -e
   workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`
   → ABSENT.
4. **Model-F root CAL-only and unchanged — PASS.** `workspace/v72p2d5_model_f_input/20260907_r1/`:
   `model_f_input.npz` size 208467 bytes, mtime 2026-09-07 02:07:07.043698800
   +0800; `model_f_input_summary.json` size 752 bytes, same mtime. Summary raw:
   `cal_only: true`, `val_rows_read: 0`, `decoder_calls: 0`, `p0_calls: 0`,
   `formal: false`, `status: MODEL_F_INPUT_CANDIDATE`, `lambda_star:
   137.3823795883264`, `field: {q: 32, poly: 37}`, schema
   `v72p2d5_model_f_input_v1`, CAL 702..1725, 1024 frames × 256 pairs.
5. **Plan introspection — PASS.** `build_plan()`: 96 entries, 96 planned calls,
   0 refusals; four candidates (`lam_d2_0.00_d3_1.00` baseline,
   `lam_d2_0.45_d3_0.55`, `lam_d2_0.50_d3_0.50`, `lam_d2_0.55_d3_0.45`);
   eight seeds (2026091601..1603 + 2026091801..1805); f1.2 populations
   (4000, 16000), f1.0 population (4000); 12 groups × 8 seeds = 96. Two
   independent `build_plan()` builds are identical
   (`deterministic_two_builds_identical=True`); `expected_call_index` is
   96-long, unique and contiguous 0..95. Order: candidate → condition (f1.2
   then f1.0) → population ascending → seed; first key
   `(lam_d2_0.00_d3_1.00, f1.2, 4000, 2026091601)`, last
   `(lam_d2_0.55_d3_0.45, f1.0, 4000, 2026091805)`. f1.2 m=59 rate 0.078125,
   f1.0 m=49 rate 0.234375.
6. **Primitive certification — PASS.** `certify_primitives()`:
   `semantics_pass=True`, `ensemble_path_equivalence=False`. Equivalence max
   abs diffs: channel centering 0.0; coefficient direction 0.0; check
   V26↔v35 3.469446951953614e-17; v35↔direct-SP 3.469446951953614e-17;
   variable log-sum 1.3877787807814457e-16; belief log-sum
   1.942890293094024e-16; tree check 2.0816681711721685e-17; tree V26 belief
   2.7755575615628914e-17; tree v35 flooding 5.551115123125783e-17; tree
   V26-vs-v35 4.85722573273506e-17. Labelled non-equivalence diagnostics
   (informational): loopy flooding-vs-exact 0.9964571039970646;
   loopy flooding-vs-row-layered 0.1293056908797188; DE-metric-vs-decoder-
   terminal MISMATCH_DIAGNOSTIC.
7. **f1.0 role — PASS.** `CONDITION_ROLE = {"f1.2": "primary_gate", "f1.0":
   "boundary_diagnostic"}`; `F1_0_CROSSING_MIN = 7`; `CONDITION_POPULATIONS`
   f1.0 = (4000,). `s4000_f10` is read only in `aggregate_stability` reporting
   (`:419,447,458,476-478`) and sets only the reported
   `boundary_crossing_ids` (`:522-523`); the `compute_routing` eligibility and
   rank block never reads f1.0. Functional probe with otherwise-identical fake
   complete records: f1.0 0/8 vs 8/8 gives identical gate outputs
   (terminal/eligible/winner/baseline_stability unchanged; only the reported
   crossing list changes from `[]` to the three non-baseline IDs).
8. **Compile + focused tests — PASS.** Task-owned basetemp parent
   `workspace/d9_calib_a1_preflight/` pre-created. `py_compile` on module +
   runner + test file → OK. Focused run:
   `.venv/bin/python -m pytest -p no:cacheprovider -q
   --basetemp=workspace/d9_calib_a1_preflight/3bf82319-0f59-411c-a001-75c04205b02a
   comparison_bench/tests/test_v72p2d9_de_decoder_calibration.py`
   → `20 passed, 1 warning in 5.74s` (warning: unknown pytest config option
   `cache_dir`; benign). No broad suite and no D8 suite rerun.

Pre-dispatch verdict: **PASS for all eight checks**; the frozen invocation in
`.workbuddy/tasks/D9_DE_CALIBRATION_A1_TASK_PACKET.md` §4 proceeds once,
unmodified.

## 2026-09-14 — D9 calibration A1 execution

### Command, process and wall

- Exact command (run once, repo root, no modification):
  `.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py
  --calibrate --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`
- Process ownership: wrapper shell pid 984680; runner python pid 984685; one
  python process only; no retry, resume, seed extension or adaptive stop.
- Exit code: 0. Start 2026-09-13T18:37:43Z (2026-09-14 02:37:43 +0800), end
  2026-09-13T18:39:44Z (02:39:44 +0800), external wall 121.549 s; runner-internal
  `wall_s = 118.61216687600245` s.
- Runner stdout: `D9_DE_CALIBRATION terminal=D9_DE_CALIBRATION_SELECT_ONE
  winner=lam_d2_0.45_d3_0.55 de_calls=96 setup=4`.

### Calls and stages (raw)

- 96/96 scientific DE calls (`de_records.csv` 96 rows, `call_idx` 0..95
  contiguous, each with a matching `de_traces.csv` row); 0 refusals; planned 96.
- Setup units = 4 (implemented `SETUP_UNITS`: primitive certification, graph
  audit, plan build, channel load) ≤12; refused roots: none.
- All 12 groups (4 candidates × {f1.2 p4000, f1.2 p16000, f1.0 p4000})
  complete with 8/8 seeds.
- 41/96 calls `converged=True`; every call ran the full `it=60` iterations
  (no early entropy streak break); per-seed `H60` listed below.

### Per-candidate S4000/S16000 and stability classes

| candidate | S4000 f1.2 | S16000 f1.2 | S4000 f1.0 | stability | worst AUT_30 p16000 | mean AUT_30 p16000 | worst T_0.01 p16000 | ratio vs DV3 |
|---|---|---|---|---|---|---|---|---|
| `lam_d2_0.00_d3_1.00` (DV3) | 0 | 0 | 0 | `stable_unconverged` | 151.91176112222527 | 151.8804918322248 | 61 | 1.0 |
| `lam_d2_0.45_d3_0.55` | 8 | 8 | 0 | `stable_converged` | 113.22729748925664 | 109.36644017530324 | 48 | 0.7453491201260983 |
| `lam_d2_0.50_d3_0.50` | 7 | 8 | 0 | `stability_ambiguous` | 100.7969338149846 | 97.25804441845028 | 47 | 0.6635229100786036 |
| `lam_d2_0.55_d3_0.45` | 6 | 4 | 0 | `stable_unconverged` | 92.12076621342497 | 89.11686079880923 | 51 | 0.6064097047713533 |

- Per-seed convergence (f1.2 p4000 / p16000): 0.45 = 8/8 / 8/8 (all seeds);
  0.50 = 7/8 / 8/8 (only seed 2026091802 failed at p4000, H60=1.492e-3);
  0.55 = 6/8 / 4/8 (failures 2026091601, 2026091802 at p4000; 2026091601,
  2026091801, 2026091802, 2026091804 at p16000); DV3 0/8 / 0/8 with
  H60 ≈ 4.89 (no trajectory progress).
- D8 reproduction check on seeds 2026091601..03: 0.45 3/3 at both f1.2
  populations; 0.50 3/3 at both; 0.55 2/3 at both; DV3 0/3. Consistent with the
  accepted D8 primary counts at the reproduced seeds.
- Fresh seeds 2026091801..05: 0.45 5/5 both populations; 0.50 4/5 at p4000,
  5/5 at p16000; 0.55 4/5 at p4000, 2/5 at p16000. The 0.50 p4000 miss is a
  fresh-seed (2026091802) boundary fluctuation, which is what makes 0.50
  `stability_ambiguous` under the frozen 8/8 rule.

### f1.0 boundary diagnostics (reported only; never a gate)

- `S4000(f1.0) = 0/8` for all four candidates; `boundary_crossing_ids = []`.
  f1.0 `H60` stayed 4.86–5.00 bits for every candidate/seed (no approach to the
  1e-4 convergence tolerance), consistent with the frozen `BOUNDARY_DIAGNOSTIC`
  classification and the accepted `mu = +0.013383` bit/symbol margin.

### DV3 baseline comparison

- DV3 `stable_unconverged` (0/8 and 0/8; worst AUT_30 p16000
  151.91176112222527) satisfies the frozen baseline precondition for selection.
  D8 recorded DV3 worst AUT_30 151.90884493578253; the D9 value differs by
  ~2.9e-3 because the matrix adds five fresh seeds (the D8-seed subset is
  consistent).
- Candidate AUT_30 p16000 ratios vs DV3: 0.45 = 0.7453, 0.50 = 0.6635,
  0.55 = 0.6064 (all below the 0.95 margin; only stability separates them).

### Stored terminal, eligible set and rank output (report only; NOT accepted)

- `summary.json`: `terminal = D9_DE_CALIBRATION_SELECT_ONE`,
  `terminal_reason = null`, `winner_candidate_id = lam_d2_0.45_d3_0.55`,
  `eligible_candidate_ids = ["lam_d2_0.45_d3_0.55"]`,
  `baseline_stability = stable_unconverged`, `semantics_pass = true`,
  `graph_valid = true`.
- Deterministic rank output: with exactly one eligible candidate the frozen key
  `(worst AUT_30 p16000 asc, mean AUT_30 p16000 asc, worst T_0.01 p16000 asc,
  ID lexicographic)` selects `lam_d2_0.45_d3_0.55`. `lam_d2_0.50_d3_0.50` was
  **not** eligible (7/8 at S4000 ⇒ `stability_ambiguous`) despite its lower
  AUT_30; `lam_d2_0.55_d3_0.45` was `stable_unconverged`. Non-eligible
  candidates are not ranked.
- This entry reports the stored terminal; it does not accept, promote or select
  a finite-length candidate. The packet §7 independent batch-end review is
  still required before any route decision.

### Budgets and resources

| budget | limit | observed |
|---|---|---|
| scientific DE calls | ≤96 | 96 |
| setup units | ≤12 | 4 |
| total wall | ≤1200 s | 118.612 s internal / 121.549 s external |
| per-call wall | ≤300 s (checked between/after calls) | max 2.299 s |
| RSS | <2 GiB strict | peak 274210816 bytes (261.5 MiB) |
| processes | 1 | 1; no retry/resume/seed search/adaptive stop |

- The per-call cap was never approached; no partial-root stop or in-flight kill
  occurred (not an interrupting watchdog). If a call had returned over cap the
  partial root would have been retained and the run stopped before the next
  call, per packet §4.

### Root inventory (six files, complete)

`workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/`:

| file | size | mtime (+0800) |
|---|---|---|
| `manifest.json` | 4405 | 2026-09-14 02:37:46.916481700 |
| `de_records.csv` | 19696 | 2026-09-14 02:39:44.502210900 |
| `de_traces.csv` | 228456 | 2026-09-14 02:39:44.509673900 |
| `candidate_summary.csv` | 696 | 2026-09-14 02:39:44.514245000 |
| `summary.json` | 17436 | 2026-09-14 02:39:44.514245000 |
| `command_log.txt` | 16202 | 2026-09-14 02:39:44.514245000 |

- `manifest.json` records the frozen command, `l1_only: true`, field q=32/poly37,
  the frozen seeds/conditions/candidate freeze, `setup_units: 4`, no refusals
  and `authorization: "separate explicit user/main-thread authorization required
  before --calibrate"`.
- Partial-root/no-repair semantics: not applicable — the run completed all 96
  registered calls with no error/resource terminal, so no partial-root
  retention, cleanup, repair or rerun was needed or performed. A1 authorizes
  no second scientific invocation.

### Read-only verifier (raw output)

Command:
`.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py
--verify --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b`

Raw output (`exit 0`):

```text
VERIFY checked_calls=96 agreements=96 skipped=0 groups=12/12 violations=0
VERIFY PASS
```

### Claim boundary (unchanged)

- This entry records one completed `EXPLORE_HEAVY` calibration batch under the
  frozen CAL-only Model-F channel/decoder contract. It establishes no
  finite-length/FER/leakage/SKR/qualification/promotion/real-data claim, does
  not reinterpret the D8 terminal or its winner=none, and does not revive D7-H.
  Independent batch-end review (packet §7) remains pending; the terminal above
  is stored evidence, not an accepted route decision.

## 2026-09-14 — D9 calibration A1 batch-end review and closure

REVIEW_ID: D9-DE-CALIBRATION-A1-BATCH-END
EVIDENCE_ACCESS: VERIFIED
VERDICT: PASS_WITH_FINDINGS
REVIEWED_SCOPE: A1 packet §§1–8 and prompt; D9 feasibility packet; all four OpenSpec artifacts; READINESS_R1, EXPLORATION_LOG, INDEPENDENT_REVIEW_R1; the actual root six files; module `v72p2d9_de_decoder_calibration.py` (`aggregate_stability`, `compute_routing`, graph audit) and runner `verify_command`. Read-only commands: frozen `--verify` (exit 0; raw preserved), stdlib-only recounts/recomputations over all six artifacts, scoped git/find/stat checks. No file created/modified/staged/committed; no decoder/DE/CAL/raw execution; no repair/rerun.
VERIFIER_RESULT: `VERIFY checked_calls=96 agreements=96 skipped=0 groups=12/12 violations=0` / `VERIFY PASS` (exit 0); matches operator output exactly; reviewer-side independent recount agrees with all stored values.
RECOUNT: 96 plan keys reconstructed in frozen order (candidate → f1.2 4000/16000 → f1.0 4000 → seed 1601..03,1801..05); `call_idx` 0..95 contiguous/unique, 0 duplicates/missing, no adaptive reordering; 96 traces key-identical; 12 groups × exactly 8 seeds; f1.2 labels {4000,16000} (m=59, rate 0.078125), f1.0 {4000} (m=49, rate 0.234375); per-cell reproduction 3/3 + fresh 5/5; all calls ran it=60.
STABILITY_AND_TERMINAL: Recomputed — DV3 0/8 & 0/8 → `stable_unconverged`; 0.45 8/8 & 8/8 → `stable_converged`; 0.50 7/8 & 8/8 → `stability_ambiguous`; 0.55 6/8 & 4/8 → `stable_unconverged`. Worst AUT30 p16000 = 151.91176112222527 / 113.22729748925664 / 100.7969338149846 / 92.12076621342497; ratios 1.0 / 0.745349 / 0.663523 / 0.606410. Eligibility under the frozen rule: only `lam_d2_0.45_d3_0.55` (0.50 correctly excluded despite lower AUT30 because S4000 is 7/8; 0.55 fails stability). Deterministic rank → single winner `lam_d2_0.45_d3_0.55`. Stored terminal `D9_DE_CALIBRATION_SELECT_ONE`, reason null, eligible `["lam_d2_0.45_d3_0.55"]`, baseline `stable_unconverged` — all confirmed. D8-seed consistency confirmed (seed 2026091602 p4000 DV3 AUT30 151.90884493578253 identical to D8 record); fresh-seed misses: 0.50 p4000 seed 2026091802 (H60=1.491587e-3); 0.55 p16000 seeds 1601/1801/1802/1804. f1.0: S4000 0/8 all four, no H60 near tolerance, `boundary_crossing_ids=[]`.
MARKERS_AND_BUDGETS: `semantics_pass=true`, `ensemble_path_equivalence=false`, `graph_valid=true` (24 cells, 0 violations), refusal 0; 10 certified equivalence checks + 3 labelled non-equivalence diagnostics. Code inspection confirms f1.0 enters reporting only (never eligibility/rank). Budgets: 96/96 calls at cap, setup 4 ≤12, internal wall 118.61216687600245 s ≤1200, max per-call 2.2993 s ≤300 enforced between/after calls (no in-flight kill/watchdog claim), RSS peak 274210816 B < 2 GiB strict, single sequential process, no retry/resume/seed-extension/adaptive stop.
EVIDENCE_INTEGRITY: root exactly six files with reported sizes (4405/19696/228456/696/17436/16202 B); `command_log.txt` 114 lines = 3 header + 14 stage + 96 call + 1 terminal, fields match records, monotonic timestamps; terminal line matches `summary.json`; command strings equal the A1 packet §4 command verbatim; pre-dispatch entry precedes execution entry; Model-F root untouched; only this root contains calibration records.
CLAIM_AND_AUTHORIZATION: claim ceiling consistent (DE-only synthetic ensemble-screen evidence under the frozen CAL-only Model-F channel/decoder contract; no finite-length/FER/leakage/SKR/qualification/promotion/real-data claim; no D8 reinterpretation; no D7-H revival; selection authorizes at most the next finite-length synthetic task packet). No self-acceptance (stored terminal is machine output only; log marks it report-only; no route-selection document). No commit/push; HEAD `278fdf07` unchanged; D9 artifacts untracked/ignored.
FINDINGS:
- [F1] NON-BLOCKING — log §execution states f1.0 H60 "4.86–5.00 bits"; observed 4.8641–4.9841 (conservative superset); optional wording precision. CARRIED.
- [F2] NON-BLOCKING — operator summary floors max per-call wall to 2.299 s vs record 2.2993 s; record authoritative. CARRIED.
- [F3] NON-BLOCKING (verification limit) — exit 0 / pids / external wall / single-process are operator-attested; consistent with monotonic log and mtimes. CARRIED.
- [F4] NON-BLOCKING — `summary.json` graph cells store the clamped forced-cycle rank `max(0, N2-(m-1))` (=0) while design §5 lists raw negative values; semantics correct, field juxtaposition can mislead; optional clarity note at next revision. CARRIED.
- [F5] NON-BLOCKING — `openspec/.../tasks.md:4-7` prose still says "C11–C12 pending" while the checkboxes are `[x]`; stale prose only (readiness cycle complete); no impact on A1. CARRIED.
CLAIM_CEILING: establishes that the one authorized A1 invocation ran within its frozen matrix/budgets/command/root, that all six artifacts are internally consistent and independently recomputable, and that the stored selection `lam_d2_0.45_d3_0.55` follows the frozen rules with f1.0 excluded and 0.50 correctly set aside as ambiguous. Does NOT establish DE↔decoder trajectory/terminal equivalence, finite-length/FER behavior, leakage/SKR or qualification numbers, real-data validity, mixed-degree construction feasibility, D8 reinterpretation, or D7-H revival.
TERMINAL_RECOMMENDATION: D9_DE_CALIBRATION_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION
AUTHORITY_BOUNDARY: advisory review only; result acceptance and route decision remain with the user/main thread.

## 2026-09-14 — main-thread result acceptance and route decision

- Accepted the complete A1 root, independent review and stored terminal
  `D9_DE_CALIBRATION_SELECT_ONE` under the frozen DE-only claim ceiling.
- Accepted exactly one candidate for successor construction:
  `lam_d2_0.45_d3_0.55`. It was stable-converged 8/8 at both f1.2 population
  sizes and satisfied the frozen AUT_30 margin. Lambda2 0.50 remains excluded
  as `stability_ambiguous` despite its lower AUT_30; lambda2 0.55 and DV3 are
  stable-unconverged. f1.0 remains a non-gating boundary diagnostic.
- This is selection for a finite-length synthetic task packet, not evidence of
  decoder success. DE-to-row-layered trajectory/terminal equivalence remains
  false and all finite-length claims remain open.
- Next gate: `D10_MIXED_DEGREE_L1_FINITE_READINESS`. Build a matched-constructor
  regular-DV3 control and mixed-DV23-0.45 candidate, freeze multiple graph seeds
  at n64/n128/n256 and f1.2, and test L1 only before any L2 APP or alternation.
- D7-H remains unauthorized/not recommended. Lifecycle:
  `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`. No finite decoder,
  real-data run, commit or push is authorized by this acceptance.
