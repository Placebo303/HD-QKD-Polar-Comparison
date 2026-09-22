# P0 Pre-RESULT review R1 — independent read-only verdict

Reviewer: independent session. Did not run P0, did not write P0 packet/addendum/authorization/operator return, did not execute any earlier D5 packet. No prior claim accepted on faith, including task-packet §4 paraphrases; every row re-derived from artifacts and source.
Task packet: `.workbuddy/tasks/D5_P0_PRERESULT_R1_REVIEW_PACKET.md`.
Under review: `workspace/v72p2d5_p0_cost/20260906_r1/` (4 files) + `P0_OPERATOR_RETURN_R2.md` + `P0_AUTHORIZATION_RECORD_R2.md` + `P0_EXECUTION_PACKET_ADDENDUM_A1.md`.
Governing frozen packet: `P0_EXECUTION_PACKET.md` (must be byte-identical).
HEAD `b4696273`, branch `formal-ir-v72p1-addendum-clean`, gate `next_gate: P0_PACKET_REVIEW`.
Role: read-only review. Authorization: **false**.

P0 is a cost preflight. It establishes no correctness, no rate-point performance, no FER, no leakage, no key rate. PASS here means only "the cost was measured and honestly recorded".

## 1. Numbered checks

| ID | Check | Result |
| --- | --- | --- |
| C1 | Frozen `P0_EXECUTION_PACKET.md` byte-identical to `b27f31da` | PASS |
| C2 | `cycle_state.yaml` net-zero lifecycle, only `p0_cost_execution_authorized` touched, nine keys false, `next_gate`/`scientific_promotion` intact | PASS (see note N1) |
| C3 | Exactly one invocation; no rerun, no second root, no partial leftovers; auth record carries verbatim auth + frozen + watchdog + STEP 2' | PASS |
| C4 | Output root: exactly 4 files, nothing else | PASS |
| C5 | `phase`/`block_length`/`f_list`/`seeds`/`frozen_rows` match frozen contract | PASS |
| C6 | `decoder_calls` == 12 and consistent with record structure | PASS |
| C7 | Four records cover `f` × `kind` exactly once each | PASS |
| C8 | `projected_g1_s`/`projected_g2_s` reproducible from wall × frozen call counts per source formula; `projection_blocked` follows `> 3600 s` rule | PASS (arithmetic; structural soundness is F2, separate) |
| C9 | Four files mutually self-consistent | PASS |
| C10 | No forbidden content (raw rows/matrices/priors/beliefs/syndromes/absolute paths/checksums) | PASS |
| C11 | F1 `rss_bytes` null — cause, contract status, significance | PASS with recorded limitation L1 (non-blocking; see §3) |
| C12 | F2 `projected_g2_s` structure — scaling, what it licenses, G1 vs G2 standing | PASS with recorded limitation L2 (G2 projection unusable; see §3) |
| C13 | F3 iteration-cap finding — aggregation, per-call value, meaning, G1 consequence | PASS with cost signal S1 (see §3) |
| C14 | Claim discipline of `P0_OPERATOR_RETURN_R2.md` (records without interpreting; no FER/leakage/key/method/G1-G2-readiness overstatement; `NOT_INTERPRETED` honest) | PASS |
| C15 | `py_compile` on the two core modules + two scripts | PASS |
| C16 | Three focused test files with fresh `--basetemp` | FINDINGS (7 failed / 193 passed; only 1 is the known-benign; remaining 6 are stale lifecycle guards — non-blocking for P0, must be fixed in G1 packet; see §5) |
| C17 | Protected roots re-stat afterwards, nothing changed; `workspace/v72p2d5_g2/20260906_r1` never created | PASS (checked subset; G0/structure roots NOT_VERIFIABLE, see N2) |

Notes:
- N1: `git diff f1cdf970 b4696273 -- cycle_state.yaml` is literally one line (`-p0_cost_execution_authorized: true` / `+p0_cost_execution_authorized: false`). Current file has all nine `*_execution_authorized` false, `scientific_promotion: false`, `next_gate: P0_PACKET_REVIEW`. Combined with the R1 record (pre-first-flip all-false at `b27f31da`/`299416ae` era) and the log order `299416ae -> f1cdf970 (flip true) -> b4696273 (consumed false)`, the net `false -> true -> false` on the single key is established. A direct `299416ae..f1cdf970` literal diff was not re-derived byte-for-byte in this session; the net-zero conclusion rests on the current-false read + the two authorization records + the second-leg literal diff.
- N2: re-stat verified P0 (4 files, 267/227/1197/186), G2 absent, G1 (4 files, 267/146/2593/126), Model-F (2 files, 752/208467) unchanged. G0 / G0-recovery / structure roots were not re-statted against a pre-run snapshot available to this reviewer → NOT_VERIFIABLE for those three roots (reason: no baseline snapshot in scope; no evidence of change either).

### C1 detail
`git hash-object` worktree == `git rev-parse b27f31da:...` == `git rev-parse HEAD:...` == `7a9f8fa03a3215a9e52b9d6fa1c2d492f467191d`; `git diff b27f31da HEAD -- <packet>` empty; `git diff HEAD -- <packet>` empty. Addendum A1 edits nothing in the frozen file by its own §1 statement and the empty diff confirms it.

### C5–C8 recomputed values (inline, from `results.json`, not copied from operator)
- Records: f=1.0/app wall 1.8862763999495655 iter 360 rss null; f=1.0/oracle wall 1.04731999989599 iter 180 rss null; f=1.2/app wall 3.459295800072141 iter 360 rss null; f=1.2/oracle wall 1.671841400093399 iter 180 rss null.
- `sum(records.wall_s)` = 8.064733600011096. Source rule is `per_call = total_wall / calls` with `total_wall = time.perf_counter() - t0` (phase wall, core L1999–2000), NOT the record sum, so `per_call` cannot be re-derived from records alone. Inverted from recorded projections: `161.8241519993171 / 240 = 0.6742672999971546`; `485.47245599795133 / 720 = 0.6742672999971546`; `3 × 161.8241519993171 = 485.47245599795133` exactly (`720/240 = 3`, diff 0.0e+00). Implied `total_wall = 0.6742672999971546 × 12 = 8.091207599965855`; implied overhead over record sum ≈ 0.026474 s (≈0.33%, mother build + sampling). Operator numbers match to all 16 decimals.
- `decoder_calls` 12 = per-`f` (app `calls += 2` × 2 seeds = 4; oracle `calls += 1` × 2 seeds = 2; total 6) × 2 `f` (core L1973–1992, `G0_SEEDS[:2]` L1980). Coverage `{1.0,1.2} × {app,oracle}` exactly once each.
- Frozen contract: `phase p0-cost`, width 64 (`P0_WIDTH`), `f (1.0,1.2)` (`P0_F`), seeds `[2026090510, 2026090511]` (`G0_SEEDS[:2]`), `m1 {49,59}` / `m2 {43,52}`. Formula `ceil(64×3.814742×1.0/5)=49`, `ceil(64×3.814742×1.2/5)=59`, `ceil(64×3.347605×1.0/5)=43`, `ceil(64×3.347605×1.2/5)=52` — all AGREE.
- `projection_blocked`: `485.47245599795133 > 3600.0` is False — rule applied correctly.
- Cross-file: `decoder_calls` 12 / `projected_g1_s` / `projected_g2_s` / `projection_blocked: false` / `passed: true` / `formal_root workspace/v72p2d5_p0_cost/20260906_r1` agree across `results.json` + `report.md` + `execution_summary.json`; `table.csv` `None` ×4 ≡ JSON `null` ×4 (Python csv serialisation of None); wall/iterations match to all decimals.

## 2. Pre/post stat snapshot (protected roots)

| Root | Before (frozen P01 / R2 E1 at `299416ae`) | After run (R2 operator return) | After this review's tests |
| --- | --- | --- | --- |
| `workspace/v72p2d5_p0_cost/20260906_r1` | absent | 4 files: execution_summary.json 267, report.md 227, results.json 1197, table.csv 186 | same 4 files/sizes, unchanged |
| `workspace/v72p2d5_g2/20260906_r1` | absent | absent | absent (never created) |
| `workspace/v72p2d5_g1/20260906_r1` | 4 files: 267/146/2593/126 | same | same, unchanged |
| `workspace/v72p2d5_model_f_input/20260907_r1` | 2 files: 208467/752 | same | same, unchanged |
| `cycle_state.yaml` | `p0 false`, `next_gate P0_PACKET_REVIEW` | nine false, `scientific_promotion false`, `next_gate P0_PACKET_REVIEW` | same (this review changed nothing) |

## 3. F1 / F2 / F3 — independent assessments (own reasoning from source)

**F1 — `rss_bytes` null in all four records: recorded limitation L1, non-blocking for a wall-time preflight.**
Cause (source, not author framing): `_rss_bytes()` (core L941–947) is `try: import resource; return ru_maxrss×1024; except Exception: return None`. `resource` is Unix-only and unavailable on this Windows host → `ImportError` → `None` on every call. `run_p0_cost_phase` L1995–1998 stores that `None` per aggregated record; `write_p0_cost_evidence` L2322–2331 passes `None` through (`int(rss) if rss is not None else None`). No code path on this host could have produced non-null (no `psutil`/fallback). Contract status: the frozen packet lists `rss_bytes` among recorded quantities (P03) and names peak RSS `< 2 GiB` as a downstream budget "context only". The key is present in all four records with the honest value `null`; nothing was omitted or hand-filled, and the operator claims "not assessable — no claim". That satisfies the record-what-you-measured duty; it does not satisfy a 2 GiB comparison, but no such comparison is a P0 pass criterion (OQ-P0-1 caps the decode-attributed wall sum; OQ-P0-3 makes P0 PASS independent of projection). Verdict: not a blocking defect; carry L1 into the G1 packet — G1 must re-establish a working RSS measurement (Linux host or instrumented watcher) before any `< 2 GiB` claim, and must not cite P0 as RSS evidence.

**F2 — `projected_g2_s` is structurally unsound for any width-dependent decision; `projection_blocked: false` licenses nothing about G2. `projected_g1_s` stands on firmer (same-width) ground only.**
Source: `per_call = total_wall / calls` (L1999–2000); `proj_g1 = per_call × (100×2 + 20×2 = 240)`; `proj_g2 = per_call × (200×3 + 40×3 = 720)` (L2001–2004). Grep over L1999–2004: no reference to width, `n`, rows, or `m` — zero scaling. Constants: `P0_WIDTH = G1_WIDTH = 64`, `G2_WIDTH = 256` (L68–70); G2 frozen rows at n=256 are `ceil(256×CE×f/5)` = L1 {196, 215, 235} / L2 {172, 189, 206} for f {1.0, 1.1, 1.2} — roughly 4× the P0 rows (49→196, 59→235, 43→172, 52→206). A per-call cost measured on 64-wide / ~43–59-row blocks therefore cannot price 256-wide / ~172–235-row blocks; FFT-QSPA row-layered work grows with rows and width, so the G2 number is at best uncalibrated and plausibly a substantial underestimate. What the two numbers actually license: pure call-count arithmetic — "IF per-call cost stayed at the P0 value, 240 calls cost 161.82 s and 720 calls cost 485.47 s". `projected_g1_s` shares P0's width and row counts (`G1_F = P0_F`, same `_rows_required` inputs), so its only extrapolation is call count — firmer, usable as a same-width cost indicator subject to the F3 cap caveat. Explicit answer: **the G2 projection must not be relied upon for any decision** — no G2 authorization, no G2 budget clearance, no "G2 fits in 3600 s" claim. `projection_blocked: false` is the same unscaled arithmetic compared against 3600 s and is equally uninformative about G2. Carry L2 into the G1 packet: G1 must re-measure per-call cost at its own width and must include an explicit row/width-scaling disclaimer for any G2 mention.

**F3 — every decode ran to the iteration cap (360 = 4×90, 180 = 2×90). Cost signal S1 for G1; not a failure result.**
Aggregation (source): `_run_layered_block` returns `iterations = it1 + it2` (L1280, two layered decodes summed); P0 app branch `calls += 2` per seed, oracle `calls += 1` per seed (L1986/L1992), over `G0_SEEDS[:2]` = 2 seeds (L1980). At cap (`MAX_ITER = 90`, L89): app `2×2×90 = 360`, oracle `2×1×90 = 180` — exact match to all four records. Historical `decode_row_layered_fftqspa` returns `iterations = max_iter` on the non-converged fall-through (v35 module, loop `for it in 1..max_iter`, `iterations = max_iter` at the cap return). So each of the 12 single decodes consumed the full 90-iteration budget without early convergence at these 64-wide prefixes. Means: the measured per-call wall is worst-case-at-cap cost, a conservative basis for budgeting. Does NOT mean: failure, non-convergence verdict, method defect, or rate-point performance — P0 records no `exact`/`syndrome_ok` by design, and none is present in the four files. G1 consequence (S1, mandatory): the G1 packet must budget per-call cost at the cap (not at a converged average), must record `exact`/`syndrome_ok`/finite per block so the persistence of cap-running can be interpreted, and must not cite P0 iterations as evidence for or against the method.

## 4. Claim discipline (operator return R2)
PASS. The return quotes the verbatim command, exit 0, operator wall 8.6278899 s, empty stdout/stderr, root listing, and literal scalars including the non-cost context (`block_length`, `f_list`, `frozen_rows`, `seeds`). Resource accounting computes `sum(records.wall_s) = 8.064733600011096 s` vs the OQ-P0-1 1440 s cap, max single record 3.459 s vs 120 s, `RESOURCE_OVERRUN: NO`; RSS is "not assessable — no claim"; watchdog "did not fire". Post-run state (auth false ×9, promotion false, gate unchanged, root untouched after run) is stated factually. The `NOT_INTERPRETED` section draws no correctness / rate-point / FER / leakage / key-rate / method / G1-G2-readiness conclusion and defers acceptance and G1 authorization to independent review. No overstatement found. Stays inside the P02 claim boundary.

## 5. Static and test evidence

- `py_compile` (4 files: core `v72p2d5_gf32_rate_mother.py`, core `v72p2d5_model_f_input.py`, `scripts/v72p2d5_gf32_rate_mother.py`, `scripts/v72p2d5_prepare_model_f_input.py`): all exit 0. PASS.
- Focused pytest (three files, fresh `--basetemp=workspace/preresult_r1_40f3432c-0254-4d9f-b6cc-1eac4ca91fc2`, `-p no:cacheprovider`), literal summary: `7 failed, 193 passed, 1 warning in 24.31s`. Failing ids: (1) `test_v72p2d5_gf32_rate_mother.py::test_T1_22_openspec_history_zero_mod` — the known-benign line-ending-only failure (content-change count 0; non-blocking per packet); (2) `test_R1_B2_all_exec_false_formal_absent_and_budgets`; (3) `test_P0G1G2_f_no_holdout_or_file_access`; (4) `test_P0G1G2_g_four_file_no_overwrite`; (5) `test_M20_d5_authorized_fake_load_reaches_runner`; (6) `test_v72p2d5_model_f_input.py::test_M24_formal_roots_absent`; (7) `test_P12_formal_roots_absent`. Items (2)–(7) each contain `assert not (ROOT / mod.P0_FORMAL_ROOT).exists()` (verified in source at L2136, L2941, L3007, L3200, and the two Model-F guards); they are pre-execution lifecycle guards written when the P0 root was absent, now legitimately falsified by the authorized P0 existence at `b4696273`. They show no numeric mismatch, no forbidden content, no extra file, and no production write by the tests. Per the packet ("any other failure is a finding") they are recorded as findings, judged non-blocking for P0 fitness, with a mandatory carry: the G1 packet must update these six guards to be lifecycle-aware (assert tmp-output isolation + formal-root snapshots rather than absolute P0 absence) instead of re-litigating P0.
- Re-stat afterwards: P0/G1/Model-F sizes unchanged, G2 still absent, only the permitted basetemp dir added. No workspace evidence modified.

## 6. What was and was not executed

Executed: full reads of the frozen packet, R2 operator return, R2 authorization record, A1 addendum, R1 return/record, pre-execute review R1, `cycle_state.yaml`, all four P0 evidence files, and the core source regions (`_rss_bytes`, `run_p0_cost_phase`, writers, projection, `_run_layered_block`, constants, historical-decoder iteration semantics); read-only delegated evidence gathering (git log/status/show/diff, recomputation, cross-file and forbidden-content scans, `py_compile`, the three-file pytest with a fresh `workspace/` basetemp).
NOT executed: no decoder call; no P0/G1/G2 phase invocation; no `v72p2d5_prepare_model_f_input.py`; no `pandas.read_parquet` and no CAL/VAL/raw row reads; no workspace modify/delete/move/rename/overwrite/normalize/hash beyond the single permitted pytest basetemp; `workspace/v72p2d5_g2/20260906_r1` never created; no `cycle_state.yaml` change, authorization, acceptance, or promotion; no `.py`/`.md`/OpenSpec edit; no git write operation. Nothing was fixed; findings are reported only. Items that could not be checked are marked NOT_VERIFIABLE with reasons (C17/N2; C2/N1 partial basis stated).

## 7. Verdict

`P0_PRE_RESULT_REVIEW_PASS` — the P0 result is fit to be recorded as the P0 outcome, subject to the limitations below. The cost was measured on the frozen command and honestly recorded: four files self-consistent, frozen parameters exact, call counts exact, projections arithmetically reproducible, no forbidden content, claim discipline intact, iteration-cap and RSS-null facts disclosed rather than hidden.

Conditions that must be carried forward into any G1 packet (non-negotiable):
- L1 (RSS): no RSS evidence exists; G1 must re-establish RSS measurement before any 2 GiB claim.
- L2 (G2 projection): `projected_g2_s` / `projection_blocked: false` must not support any G2 decision; G1 may use `projected_g1_s` as a same-width call-count indicator only, with the F3 cap caveat stated.
- S1 (iterations): G1 must budget at cap cost and must record exactness/syndrome/finite to interpret continued cap-running.
- T1 (tests): the six stale P0-absence guards must be made lifecycle-aware; `test_T1_22` line-ending noise stays non-blocking (content diff 0).

This is not an acceptance, not a G1 authorization, and not a scientific qualification. `p0_cost_execution_authorized` stays `false`; `next_gate` stays `P0_PACKET_REVIEW`; G1 remains unauthorized.

Strongest claim the evidence supports: the single authorized `p0-cost` invocation ran to completion on the frozen command and wrote four self-consistent scalar-only files whose wall/iteration/call/projection payload reproduces from the frozen source formula.
Explicitly not claimed: no FER, no leakage, no key rate, no qualification, no method verdict, no prediction about G1 or G2 outcomes.

(End of file)
