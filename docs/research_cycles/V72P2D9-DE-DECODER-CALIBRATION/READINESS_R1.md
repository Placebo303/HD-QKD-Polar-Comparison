# D9 GF32 DE-decoder calibration and threshold — heavy R1 readiness

Status: `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`
(docs/design readiness + C07–C10 implementation; grants no execution
acceptance; no route decision; creates no root).
Track: `EXPLORE_HEAVY` for the future calibration batch (separate explicit
authorization required); this readiness call is documentation/OpenSpec only.
Authority: `.workbuddy/tasks/D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`
(§3 hypotheses C1–C4, §4 items 1–8, §5 minimal implementation, §6 allowed
files, §7 C01–C12, §8 decision shape, §9 STOP conditions, §10 return).
Predecessor: `D8_DE_SWEEP_RESULT_ACCEPTED_ROUTE_TO_D9_CALIBRATION`.
Branch: `formal-ir-v72p1-addendum-clean` (not switched; no commit, no push).
Scope of this record: C01–C06 only. Production decoder calls: **0**. DE calls:
**0** (no DE sweep, no tiny DE probe). CAL/VAL/raw/real-data contact: **0**.
Root created: **none**. Authorization flags: all false.
independent_review_verdict: PASS_WITH_FINDINGS
independent_review_artifact: docs/research_cycles/V72P2D9-DE-DECODER-CALIBRATION/INDEPENDENT_REVIEW_R1.md
c12_correction: none applied (all findings non-blocking, no required correction)
carried_findings: F1_F2_F3_F4_F5_F6
future_root_absent: true
authorization_flags: all false
next_gate: D9_DE_CALIBRATION_BATCH_EXPLICIT_AUTHORIZATION
calibration_result_accepted: true
calibration_result_acceptance_date: 2026-09-14
accepted_terminal: D9_DE_CALIBRATION_SELECT_ONE
accepted_candidate: lam_d2_0.45_d3_0.55
main_route_decision: D10_MIXED_DEGREE_L1_FINITE_READINESS
main_readiness_acceptance: true
main_readiness_acceptance_date: 2026-09-14
batch_terminal: D9_DE_CALIBRATION_SELECT_ONE
batch_root: workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b
batch_calls: 96
batch_setup: 4
batch_exit_code: 0
batch_selected_candidate_reported_not_accepted: lam_d2_0.45_d3_0.55
batch_review_verdict: PASS_WITH_FINDINGS
batch_review_log_section: EXPLORATION_LOG.md#2026-09-14--d9-calibration-a1-batch-end-review-and-closure
main_route_decision: PENDING
next_gate: D9_DE_RESULT_MAIN_ROUTE_DECISION
memory_triage: DEFERRED_UNTIL_MAIN_ROUTE_DECISION

## 1. C01 — Accepted D8 counts and claim ceiling (read-only; no DE rerun)

Artifacts (all under `workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`):

- `summary.json`: `de_calls: 126` = `planned_de_calls: 126`; `setup_calls: 0`;
  `refusal_count: 0`; `terminal: "D8_DE_BASELINE_NOT_CONVERGED"`;
  `terminal_reason: null`; `winner_candidate_id: null`;
  `eligible_candidate_ids: []`; `baseline_converged: false`;
  `baseline_primary_worst_aut_30: 151.90884493578253`; seeds
  `[2026091601, 2026091602, 2026091603]`; conditions f1.2 primary
  (`m=59, rate=0.078125`), f1.0 secondary (`m=49, rate=0.234375`);
  `wall_s: 107.10461202799343`; `peak_rss_bytes: 251805696`.
- `manifest.json`: frozen command, budgets (`max_de_calls: 126`,
  `max_setup_calls: 20`, `per_call_s: 120`, `wall_s: 1800`, `rss_bytes:
  2147483648`, `processes: 1`, `retry/resume/adaptive_stop: false`), field
  `{q: 32, poly: 37}`, `l1_only: true`, `claim_ceiling`.
- `de_records.csv`: 126 data rows; `call_idx` 0..125 contiguous; 126 unique
  `(candidate_id, condition, seed)` keys; `converged` True 10 / False 116.
  Converged pairs (all f1.2): 0.40 1/3, 0.45 3/3, 0.50 3/3, 0.55 2/3,
  0.60 1/3. f1.0: 0 converged calls.
- `candidate_summary.csv`: 42 rows (21x2); DV3 f1.2 `seeds_converged=0`,
  `worst_aut_30=151.90884493578253`, `worst_t_001=61`; DV3 f1.0
  `seeds_converged=0`, `worst_aut_30=154.47598423886723`; 0.45 f1.2 3/3
  (worst 116.8714999864904), 0.50 f1.2 3/3 (worst 101.81987960461223);
  every f1.0 row 0/3; `eligible=False` for all 42.
- `de_traces.csv`: 126 rows, columns `candidate_id, condition, seed,
  entropy_trace_bits, channel_entropy_trace_bits`.
- `command_log.txt`: 126 `call=` lines and the terminal line
  `terminal=D8_DE_BASELINE_NOT_CONVERGED reason=None winner=None de_calls=126
  wall=107.105s peak_rss=251805696`.
- Reviews: batch-end review `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/EXPLORATION_LOG.md:436-457`
  (`EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, 126/126 recomputation,
  42/42 summaries, 0 violations); main-thread acceptance `:459-479`;
  `INDEPENDENT_REVIEW_R1.md` E11/E12.

Recorded ceiling: no candidate met the frozen all-seeds-both-conditions rule;
winner remains none; lambda2 0.45 and 0.50 primary f1.2 3/3 is descriptive
successor-design evidence only, not retroactive advancement; D9 must not
reinterpret the D8 terminal.

## 2. C02 — V26↔v35 semantic map summary and equivalence ceiling

Full map with pointers: `openspec/changes/v72p2d9-gf32-de-decoder-calibration/design.md`
§2 (seven stages) and §3. Summary:

| stage | verdict | key pointers | DE-as-screen impact |
|---|---|---|---|
| (a) channel centering / prior / floor | MATCH (+ i.i.d. population APPROX) | D6 `:817`; D5 `:48,275-306,309-321,346-351,1415`; D8 adapter `:281-290`; V26 `:252-254,293` | DE row = decoder prior row XOR-reindexed by true symbol; fresh draws per iteration |
| (b) coefficient permutation / coset | MATCH incoming + zero-syndrome centered; APPROX outgoing coefficient | V26 `:59-61,73-75,109-113`; v35 `:472-475,503-504`; D7-A report `:16-23` | no per-iteration message-path equivalence; entropy observable invariant per message, not for variable products |
| (c) variable update | MATCH flooding algebra; APPROX row-layered schedule | V26 `:142-153`; V14 `:120-152`; v35 `:742-766,856-885` | iteration counts not comparable |
| (d) check update | MATCH certified primitive; APPROX outgoing coeff + floor difference | V26 `:48-90`; v35 `:453-513`; D8 test `:289-302`; D7-A `:16-23` | same-input probability equality certifiable; ensemble path separate |
| (e) posterior/belief vs decoder output | MISMATCH | V26 `:300,117-120`; v35 `:888-890,923-936` | DE convergence is not decoder exact/syndrome success |
| (f) flooding DE vs row-layered | APPROX / no equivalence | V26 `:292-311`; v35 `:856-885`; D7-A `:24-31` | tree equality only; loopy and schedule comparisons are diagnostics |
| (g) stopping metric | MISMATCH | V26 `:303-310`; V37 `:337`; v35 `:890`; D7-A prereg `:42-48` | `H60<1e-4` never substitutes for syndrome/exact stop |

Equivalence ceiling: certified same-input check kernel + coefficient direction +
tree posteriors + prior chain; NOT established: flooding↔row-layered
trajectories, DE↔decoder terminals, finite-length/FER. STOP condition "same-input
semantics require modifying v35/V26 or the channel" is **not** triggered: the
outgoing-coefficient absorption is an inherited V26 ensemble convention;
`design.md` §3 records it as an approximation with the exact inference impact and
no decoder tuning is performed.

## 3. C03 — Prospective f1.0 role (rate/information argument, outcome-independent)

`H_L1 = 3.814742` (`v72p2d5_gf32_rate_mother.py:49`); disclosure `d = 5m/n`;
`mu = d - H_L1`; `R_ent = 1 - H_L1/5 = 0.2370516`.

| condition | `5m/n` | `mu` (bits/symbol) | `R` | `R_ent - R` | role |
|---|---|---|---|---|---|
| f1.2 (m=59) | 4.609375 | **+0.794633** (20.83 % of `H_L1`) | 0.078125 | 0.1589266 | primary gate |
| f1.0 (m=49) | 3.828125 | **+0.013383** (0.35 % of `H_L1`) | 0.234375 | 0.0026766 | **`BOUNDARY_DIAGNOSTIC`** |

Frozen criterion: a condition may be `HARD_GATE` only if `mu >= 0.05`
bits/symbol and `R_ent - R >= 0.01`; otherwise `BOUNDARY_DIAGNOSTIC`.
`Δ_min = 0.05` is a frozen design allowance (~1.31 % of `H_L1`, ~3.7x the f1.0
margin) because the accepted `H_L1` carries no accepted uncertainty interval, so
a hard gate must not be decidable by sub-percent model error. The f1.0
classification does not use the D8 counts: at the boundary both C1 (threshold)
and C2 (mismatch) predict non-convergence, so an f1.0 hard gate discriminates
almost nothing while it would veto an f1.2-valid ensemble. f1.0 is reported
(`S4000(f1.0)` per candidate; crossing `>=7/8` routes to main-thread review) and
never gates.

## 4. C04 — Degree/socket realization (full table in `design.md` §5)

Rules reused read-only from `v37_degree_feasibility.py`
(`edge_to_node_distribution:118-139`, `largest_remainder_counts:142-165`,
`calculate_node_degree_counts:168-187`, `calculate_total_sockets:190-192`,
`calculate_check_degree_allocation:205-261`, `analyze_degree2_subgraph:264-297`):
largest-remainder node counts `n2+n3=n`; sockets `E=2n2+3n3=3n-n2`; check
allocation `dc_floor=floor(E/m)`, `c_ceil=E mod m`, `c_floor=m-c_ceil`
(exact socket balance); realized rate exactly `R=1-m/n` by
`Σ_j λ̂_j/j = n/E`, `Σ_i ρ̂_i/i = m/E`.

Enumerated (baseline, 0.45, 0.50, 0.55; n64/128/256; f1.2 and f1.0):

| case | n | n2 | n3 | E | λ̂2 | check alloc | realized max dc | N2-(m-1) |
|---|---|---|---|---|---|---|---|---|
| DV3 f1.2 | 64/128/256 | 0 | n | 3n | 0 | f1.2 `3^44+4^15` / `3^88+4^30` / `3^176+4^60` | 4 | -58/-117/-235 |
| 0.45 f1.2 | 64 | 35 | 29 | 157 | 0.44586 | 2^20+3^39 | 3 | -23 |
| 0.45 f1.2 | 128 | 71 | 57 | 313 | 0.45367 | 2^41+3^77 | 3 | -46 |
| 0.45 f1.2 | 256 | 141 | 115 | 627 | 0.44976 | 2^81+3^155 | 3 | -94 |
| 0.50 f1.2 | 64 | 38 | 26 | 154 | 0.49351 | 2^23+3^36 | 3 | -20 |
| 0.50 f1.2 | 128 | 77 | 51 | 307 | 0.50163 | 2^47+3^71 | 3 | -40 |
| 0.50 f1.2 | 256 | 154 | 102 | 614 | 0.50163 | 2^94+3^142 | 3 | -81 |
| 0.55 f1.2 | 64 | 41 | 23 | 151 | 0.54305 | 2^26+3^33 | 3 | -17 |
| 0.55 f1.2 | 128 | 83 | 45 | 301 | 0.55150 | 2^53+3^65 | 3 | -34 |
| 0.55 f1.2 | 256 | 166 | 90 | 602 | 0.55150 | 2^106+3^130 | 3 | -69 |
| DV3 f1.0 | 64/128/256 | 0 | n | 3n | 0 | `3^4+4^45` / `3^8+4^90` / `3^16+4^180` | 4 | -48/-97/-195 |
| 0.45 f1.0 | 64 | 35 | 29 | 157 | 0.44586 | 3^39+4^10 | 4 | -13 |
| 0.45 f1.0 | 128 | 71 | 57 | 313 | 0.45367 | 3^79+4^19 | 4 | -26 |
| 0.45 f1.0 | 256 | 141 | 115 | 627 | 0.44976 | 3^157+4^39 | 4 | -54 |
| 0.50 f1.0 | 64 | 38 | 26 | 154 | 0.49351 | 3^42+4^7 | 4 | -10 |
| 0.50 f1.0 | 128 | 77 | 51 | 307 | 0.50163 | 3^85+4^13 | 4 | -20 |
| 0.50 f1.0 | 256 | 154 | 102 | 614 | 0.50163 | 3^170+4^26 | 4 | -41 |
| 0.55 f1.0 | 64 | 41 | 23 | 151 | 0.54305 | 3^45+4^4 | 4 | -7 |
| 0.55 f1.0 | 128 | 83 | 45 | 301 | 0.55150 | 3^91+4^7 | 4 | -14 |
| 0.55 f1.0 | 256 | 166 | 90 | 602 | 0.55150 | 3^182+4^14 | 4 | -29 |

Flags: all cells integer and socket-balanced; min check degree 2 (f1.2 mixed)
or 3; realized max 4 <= 8; all `N2 <= m-1` (no forced degree-2 cycle component).
Exact nominal-λ socket counts are non-integers for every mixed point
(0.45: `E = 7680/49, 15360/49, 30720/49`; 0.50: `768/5, 1536/5, 3072/5`;
0.55: `2560/17, 5120/17, 10240/17`), so the apportioned `λ̂` is the realization
of record (`|λ̂2 - λ2| <= 6.96e-3`); realized rate is unaffected. No unrealizable
socket count exists under the frozen rule.

## 5. C05 — Frozen future matrix / command / root / budgets

Candidates: DV3 baseline + 0.45 + 0.50 (mandatory) + 0.55 upper-flank control
(D8 primary 2/3 adjacent to the 3/3 plateau; tests the plateau edge).
Seeds: `2026091601..03` (D8 reproduction) + `2026091801..05` (fresh, verified
absent). Populations: f1.2 primary {4000, 16000}; f1.0 boundary diagnostic
{4000}. V26 unchanged: `max_iter=60`, `entropy_tol_bits=1e-4`, `streak=20`,
entropy + channel-entropy recording.

Stability: `S4000(c)`/`S16000(c)` = seeds with `H60 < 1e-4`;
`stable_converged` ⇔ 8/8 and 8/8; `stable_unconverged` ⇔ <=6 and <=6; else
`stability_ambiguous`. Selection requires semantics PASS, graph valid, DV3
`stable_unconverged`, and `stable_converged` with 16000-sample worst-seed
`AUT_30 <= 0.95x` DV3; one winner by
`(worst AUT_30 p16000 asc, mean AUT_30 p16000 asc, worst T_0.01 p16000 asc,
ID lexicographic)`. Terminals/routing: `design.md` §6–§7.

Budgets: <=96 DE calls (f1.2 64 + f1.0 32) + <=12 setup; wall <=1200 s;
per-call <=300 s; RSS <2 GiB strict; single process; no retry/resume/seed
extension/adaptive stop; six-file evidence root with fresh-root refusal.

Fresh future root (verified absent):
`workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/`.
Exact future command (do not run; unauthorized):

```text
.venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py --calibrate \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b
```

## 6. State

C01–C06 complete (docs/design readiness). C07–C10 complete in the C07–C10
implementation call (2026-09-14): module + runner + `--verify`, focused tests
`20 passed`, bounded PROFILE_ONLY calls (3 reduced-population synthetic V26
calls + 1 primitive certification; no root, no calibration evidence),
FROZEN_MATCH PASS (exact command/root, 4 candidates, 8 seeds, 96 planned calls,
budgets, absent root). C11 (independent reviewer-go review) and C12 (at most one
scoped correction, then the readiness terminal) pending.
No production decoder call, no scientific DE call, no root, no commit, no push;
all authorization flags false. Next gate: independent C11 review, then C12; the
future calibration batch still requires
`D9_DE_CALIBRATION_SEPARATE_EXPLICIT_AUTHORIZATION`.

## 7. C07–C10 implementation pointers (2026-09-14)

- Module:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d9_de_decoder_calibration.py`
- Runner: `scripts/v72p2d9_de_decoder_calibration_development.py`
  (`--calibrate`, `--verify`)
- Tests: `comparison_bench/tests/test_v72p2d9_de_decoder_calibration.py`
  (20 passed)
- Record: `EXPLORATION_LOG.md` §"C07–C10 implementation, focused tests and
  freeze confirmation".
- Implementation/tests write no decoder/DE/root evidence; the future root
  remains absent and all authorization flags false.
