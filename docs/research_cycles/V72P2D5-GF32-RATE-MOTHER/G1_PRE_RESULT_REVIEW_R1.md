# G1 Pre-RESULT Review R1 — independent review of the sole authorized attempt

- Role: independent Pre-RESULT reviewer for D5-G1. Did not execute the G1 run, did not write the implementation, packet, authorization, or operator return. No operator PASS or arithmetic accepted on faith; every check below re-derived from direct reads of the frozen packet, both execution commits (via read-only git inspection), current source, `cycle_state.yaml`, and the four files in the new G1 root.
- Evidence baseline: repo `D:/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (verified `git branch --show-current`), baseline `6494b623`, authorization commit `f4d577fb6b53cc58a23ada532331a5df3fac357f`, consumed-attempt return commit `58c68961a1dedad58f52145e9f23942f2c476e4a` (= current HEAD, verified `git rev-parse HEAD`), accepted implementation `cf61ee63f5b76b0223838717b1344e0e7c3867ee`, new result root `workspace/v72p2d5_g1/20260907_r2`.
- Task packet: `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_PRE_RESULT_REVIEW_R1_TASK_PACKET.md` (§1→§8 followed; any STOP would have been reported verbatim with raw evidence and no repair).
- Non-acceptance: this review accepts no result, grants no scientific qualification, authorizes no rerun/retry/resume, no second G1, and no G2. A PASS below means only that the recorded "completed but no-signal failure" record is internally coherent and ready for a separate main-thread result-acceptance decision. PASS does not convert the outcome into trend pass, FER, leakage, key rate, method success, qualification, promotion, G2 readiness, or rerun permission.
- VOID hygiene: retained `workspace/v72p2d5_g1/20260906_r1/` was never opened. No file inside it was listed, read, hashed, interpreted, or cited as evidence anywhere below. Parent `workspace/v72p2d5_g1/` membership (`20260906_r1`, `20260907_r2`) is the only VOID-related fact used, for root-hygiene only.

## 1. R01–R09 verdict table

| ID | Check | Verdict | Concrete evidence |
|----|-------|---------|-------------------|
| R01 | Authorization & attempt lifecycle | PASS | `git log --oneline 6494b623..HEAD` = exactly `f4d577fb` + `58c68961`, nothing else. `f4d577fb` stat = 3 paths (`G1_AUTHORIZATION_RECORD_R1.md` 57 lines new, `G1_PRE_EXECUTE_REVIEW_R1.md` 100 lines new, `cycle_state.yaml` 1-line change); cycle_state diff = single line `g1_execution_authorized: false→true`, no other key touched. `58c68961` stat = 2 paths (`G1_OPERATOR_RETURN_R1.md` 101 lines new, `cycle_state.yaml` 1-line change); diff = single line `true→false`. Verbatim user authorization present in both record §1 and return §1 (Chinese one-attempt text, attempt-consumed, no-retry, no-G2). Operator return records exactly one frozen-command invocation, exit 0, outer wall 239.110 s. Current `cycle_state.yaml` L30 `g1_execution_authorized: false`; all nine `*_execution_authorized` false (L8/L11/L12/L29/L30/L31/L32/L33/L34); `scientific_promotion: false` (L35); `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW` (L47) unchanged; no G1 result-accepted/qualified/promoted field added. Attempt consumed, key false now. |
| R02 | Immutable run identity | PASS | Packet §4.1 vs code vs artifacts: phase `g1` (results.json L63, report L2, summary L15); root `workspace/v72p2d5_g1/20260907_r2` (results.json L9, report L10, summary L9; core L78 `G1_FORMAL_ROOT` identical); width 64 (results.json L2; core L68 `G1_WIDTH=64`); f `[1.0, 1.2]` (results.json L5–L8; core L61 `G1_F=(1.0,1.2)`); frozen rows `1.0→49/43, 1.2→59/52` (results.json L10–L19) match packet L1 49/59, L2 43/52; graph seeds 2026090501/02 (core L52–L53, matches packet); block seeds `2026090600..2026090699` 100 ordered ints listed literally results.json L64–L165 (core L59 `range(2026090600,2026090700)`); oracle first-20 diagnostic-only (core L66 `G1_ORACLE_SUBSET=20`, L2082–L2103 oracle gated on `t < oracle_subset`, stored under separate `oracle_*` keys); cold historical GF32 max_iter 90 damping 1.0 (core L89–L90); Model-F accepted input identity `workspace/v72p2d5_model_f_input/20260907_r1` (core L85; cycle_state L21); L1→L2 order (core `_run_layered_block` L1307–L1330: L1 decode, feed-forward prior, L2 decode); exactly 440 calls (core L2092 `calls += 2` per block + L2100 `calls += 1` for oracle subset); exact watchdog command byte-identical in packet L33–L35, auth record §4, operator return §2; invocation count 1; exactly four no-overwrite files (core `_write_stage_evidence` L2414–L2430 raises `FileExistsError` if dir exists, writes exactly `results.json/table.csv/report.md/execution_summary.json`; root listing = exactly those 4). G2 never appears: `Test-Path workspace/v72p2d5_g2` = False; no G2 commit/phase. |
| R03 | Artifact structure & cross-file coherence | PASS | Root listing = exactly `execution_summary.json, report.md, results.json, table.csv`, no subdirectory. JSON finite (all numbers plain decimals, no NaN/Inf/None; wall `238.86517630005255` finite). Schema fields present in both JSONs (phase/formal_root/decoder_calls/monotonic/nonfinite/outcome/passed/peak_rss_bytes/wall_seconds + per_f detail in results.json). CSV = header + exactly 2 `f` rows, 13 columns matching writer header (core L2564–L2568); row scalars identical to JSON per_f (§2 table). Report 10 lines and execution summary 10 keys restate same outcome/passed/counts/wall/RSS/formal_root, no contradiction. Prohibited-payload scan over all four file contents: no `prior`, `beliefs`/`final_beliefs`, `symbol`, `counts_ab`/`p_b`, `syndrome_weight`, per-block `seed,exact` rows, `CAL`/`VAL`, `secret`, `key`, decoder traces, or absolute-path machine references; seeds list is the 100 frozen identity ints, not decode samples. All `formal_root` strings point only to the new valid root; no VOID-root citation inside any of the four files. |
| R04 | Count & iteration arithmetic | PASS | Recomputed manually from literals (§3): attempted 100/f ✓; APP 100×2×2=400, oracle 20×1×2=40, total 440 = `decoder_calls` ✓; `1−0/100=1.0`, `0/100=0.0` both f ✓; all exact/syndrome counts 0 within 100 ✓; `app_iterations_max 180 ≤ 180` ✓ (= 2×90); APP totals `18000 ≤ 100×180 = 18000` ✓ equality; oracle `1800 ≤ 20×90 = 1800` ✓ equality; cross-identity `18000/180=100` blocks, `1800/90=20` oracle ✓; run peak `max(114167808,115142656)=115142656` ✓ equals stored run peak. |
| R05 | Exact/syndrome/oracle isolation | PASS | Current source: `_decode_block` (L1007–L1018) defines `exact` purely as `x_hat == x_true` and `syndrome_ok` as decoder-reported AND recomputed-syndrome-match — separate outputs, no merge. `_run_layered_block` (L1320–L1329) stores `app_exact = e1 and e2` vs `app_syndrome_ok = s1 and s2` vs `oracle_exact`/`oracle_syndrome_ok` under distinct keys. `_run_rate_scan` (L2086–L2124) counts APP rate/failure only from `app_exact` (`rate = app_ok/n_blocks`, `app_failure_fraction = 1−rate`); syndrome counters (`app_syn_ok`) and oracle counters recorded alongside, never subtracted from failure. `write_g1_evidence` (L2486–L2539) persists all four counters separately. `_classify_g1_outcome` (L2139–L2160) uses only `nonfinite`, wall, RSS, `app_exact_count` monotonicity/top>0 — syndrome/oracle absent from the decision. Stored record keeps literal zeros: exact 0, syndrome 0, nonfinite 0 — no relabeling as FER/undetected/correctness/data-quality. No conflation found; blocking gate clear. |
| R06 | Signal & terminal outcome | PASS | Frozen signal recomputed: zero-nonfinite (`0`, TRUE) AND rates nondecreasing (`0.0≥0.0`, TRUE) AND top APP exact `>0` (`0>0`, FALSE) AND fourth clause (short-circuit, FALSE) → signal FALSE. Stored `outcome=G1_COMPLETED_NO_SIGNAL_FAIL`, `passed=false` required and present in all four files + operator return. Seven-outcome precedence (packet §4.5) checked: (1) no pre-execution block — normal bundle; (2) exit 0, not watchdog 124; (3) nonfinite 0; (4) stored wall 238.865 ≤ 900 and operator wall 239.110 ≤ 900; (5) RSS known and < 2 GiB; (6) signal FALSE so not TREND_PASS; (7) `G1_COMPLETED_NO_SIGNAL_FAIL` correct terminal. `passed=true iff G1_TREND_PASS` (core L2204) → false consistent. No 50%/90% threshold present in the G1 path (those literals live only in G2 `_grade_g2` L2208–L2215, unused by `run_g1_phase`); no oracle decision role; no post-hoc reinterpretation. |
| R07 | Time & resource gates | PASS | Stored entrypoint wall `238.86517630005255 s` finite and ≤ 900 ✓ (in results.json L166, report L9, summary L16, operator return §4). Operator outer wall `239.110 s` finite and ≤ 900 ✓ (return §2). Exit 0, not watchdog 124 ✓. Overhead `239.110 − 238.86517630005255 = 0.24482369994745 ≈ 0.245 s`, nonnegative and plausible wrapper-only ✓. Run peak RSS `115142656` known (not None), positive, equals max per-f peak ✓, `< 2147483648` (≈109.8 MiB, far below 2 GiB) ✓. Resource success does not and cannot override the no-signal outcome — classification checked wall/RSS before signal but returns NO_SIGNAL_FAIL on signal-false regardless of resource pass; report correctly keeps `passed=false`. Operator wall ≤ 900 so no stored-pass override question arises (and stored outcome is fail in any case). |
| R08 | Frozen-output/no-overwrite & protected roots | PASS | New G1 root: exactly 4 files, read twice (pre-write listing + full content reads), unchanged throughout this read-only review. Parent `workspace/v72p2d5_g1/` = exactly `[20260906_r1, 20260907_r2]` — no second valid G1 root, no partial/retry root. VOID interior never opened or listed by reviewer or evidence assistant. G2 `workspace/v72p2d5_g2` absent (`Test-Path False`) at pre-review snapshot; re-confirmed post-review (see §7). Tracked diff `git diff --numstat` empty (stdout empty, exit 0); staged `git diff --cached --numstat` empty (exit 0) — no tracked/staged change introduced by the reviewer. Working-tree `status --porcelain` `M` entries are the known pre-existing CRLF churn (informational, same class as disclosed in Pre-EXECUTE review §1/§9); reviewer wrote only the single allowed untracked review file. |
| R09 | Claim boundary | PASS | Strongest permissible claim (packet-bounded) stated in §8; all nonclaims explicitly rejected. Report and artifacts claim no real-data FER, decoder correctness, leakage, efficiency, key rate, qualification, promotion, method success, G2 readiness, or further-attempt permission. |

## 2. Complete literal scalar table (direct reads of `20260907_r2`)

Run level (`results.json` L2–L30/L166, `execution_summary.json`, `report.md`):

| Key | results.json | execution_summary.json | report.md |
|---|---|---|---|
| phase | `g1` | `g1` | `g1` |
| formal_root | `workspace/v72p2d5_g1/20260907_r2` | `workspace/v72p2d5_g1/20260907_r2` | `workspace/v72p2d5_g1/20260907_r2` |
| block_length | `64` | — | — |
| f_list | `[1.0, 1.2]` | — | — |
| frozen_rows | `1.0→m1 49/m2 43; 1.2→m1 59/m2 52` | — | — |
| seeds | `2026090600..2026090699` (100 ordered ints, L64–L165) | — | — |
| decoder_calls | `440` | `440` | `440` |
| crashes | `0` | — | — |
| nonfinite | `0` | `0` | `0` |
| monotonic | `true` | `true` | `True` |
| outcome | `G1_COMPLETED_NO_SIGNAL_FAIL` | `G1_COMPLETED_NO_SIGNAL_FAIL` | `G1_COMPLETED_NO_SIGNAL_FAIL` |
| passed | `false` | `false` | `False` |
| wall_seconds | `238.86517630005255` | `238.86517630005255` | `238.86517630005255` |
| peak_rss_bytes | `115142656` | `115142656` | `115142656` |
| output_files/files | `[results.json, table.csv, report.md, execution_summary.json]` | same 4 | — |

Per-f (`results.json` L31–L62 = `table.csv` L2–L3 exactly):

| f | attempted | app_exact_count | app_exact_rate | app_failure_fraction | app_syndrome_ok_count | app_iterations_total | app_iterations_max | oracle_exact_count | oracle_syndrome_ok_count | oracle_iterations_total | nonfinite_count | peak_rss_bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 100 | 0 | 0.0 | 1.0 | 0 | 18000 | 180 | 0 | 0 | 1800 | 0 | 114167808 |
| 1.2 | 100 | 0 | 0.0 | 1.0 | 0 | 18000 | 180 | 0 | 0 | 1800 | 0 | 115142656 |

Operator-only scalars (from `G1_OPERATOR_RETURN_R1.md` §2, not in the four files): invocation count `1`, exit `G1_EXIT=0`, outer wall `G1_WALL_S=239.110 s`, stdout empty, stderr empty, watchdog not fired (exit ≠ 124). No value silently coerced; every scalar above is a literal file read.

## 3. Independent count/iteration/failure/RSS/wall arithmetic (manual, no execution)

1. Attempted: `100` per f (both rows) ✓.
2. APP calls: `100 blocks × 2 levels × 2 f = 400`. Oracle calls: `20 × 1 × 2 = 40`. Total `400 + 40 = 440 = decoder_calls` ✓.
3. Iteration cross-identity: APP `18000 / 180 = 100` blocks per f ✓; oracle `1800 / 90 = 20` per f ✓; per-f total calls `100×2 + 20 = 220`; `220 × 2 = 440` ✓.
4. Failure fractions: `1 − 0/100 = 1.0` both f ✓; rates `0/100 = 0.0` ✓.
5. Denominator bounds: every exact/syndrome count `0`, `0 ≤ 100` ✓.
6. Max bound: `app_iterations_max 180 ≤ 180` (= 2 mothers × 90) ✓.
7. Total bounds: APP `18000 ≤ 100 × 180 = 18000` ✓ (equality — every block ran full iterations, consistent with zero exact, no contradiction); oracle `1800 ≤ 20 × 90 = 1800` ✓ (equality, same reading).
8. RSS: `max(114167808, 115142656) = 115142656` = run `peak_rss_bytes` ✓; `115142656 < 2147483648` ✓; positive and known (not None) ✓.
9. Walls: `238.86517630005255 ≤ 900` ✓; `239.110 ≤ 900` ✓; overhead `239.110 − 238.86517630005255 = 0.24482369994745 ≈ 0.245 s ≥ 0`, plausible wrapper-only ✓.
10. No missing/invalid/nonfinite value anywhere in the four files; JSON numbers all finite.

## 4. Exact/syndrome/oracle/nonfinite isolation findings

- `_decode_block` (core L1007–L1018): `exact ⟺ x_hat == x_true`; `syndrome_ok ⟺ decoder-reported-ok ∧ recomputed-syndrome == target`. Independent definitions; a syndrome-satisfied wrong codeword cannot become exact (requires array equality), and an exact block is counted exact regardless of the syndrome flag path.
- `_run_layered_block` (L1320–L1329): `app_exact = e1∧e2`, `app_syndrome_ok = s1∧s2`, `oracle_exact`/`oracle_syndrome_ok` on a separate diagnostic prior — four distinct keys, no shared counter.
- `_run_rate_scan` (L2086–L2124): APP `app_exact_count/rate/failure` derive solely from `app_exact`; `app_syndrome_ok_count`, `oracle_*`, `nonfinite` accumulate in parallel and never decrement failure.
- `_classify_g1_outcome` (L2139–L2160) + `run_g1_phase` return (L2188–L2205): decision inputs are `nonfinite, wall_seconds, peak_rss_bytes, per_f[].app_exact_count, monotonic`; syndrome/oracle keys are not read. `passed ⟺ outcome == G1_TREND_PASS`.
- Stored zeros stay literal zeros: exact 0, syndrome 0, oracle exact/syndrome 0, nonfinite 0, crashes 0. Nothing relabeled as FER, undetected success, correctness, or data quality.
- Result: isolation holds in source and in record. Syndrome never merged into exact, never reduced failure; oracle purely diagnostic; nonfinite/crash never counted as exact.

## 5. Signal recomputation and seven-outcome consistency

- Frozen signal (packet §4.6): `zero-nonfinite ∧ APP-rates-nondecreasing ∧ top-exact>0 ∧ (top>low ∨ both==attempted)`.
- Substitution: `0==0 (T) ∧ (0.0≥0.0) (T) ∧ (0>0) (F) ∧ short-circuit (F)` → signal FALSE. Monotonicity alone (`true`) is insufficient because `top>0` is false — exactly the packet Note for `0,0` counts.
- Precedence walk (packet §4.5): (1) normal bundle, not pre-execution-blocked; (2) exit 0, not 124; (3) nonfinite 0; (4) both walls ≤ 900; (5) RSS known < 2 GiB; (6) signal FALSE → not TREND_PASS; (7) `G1_COMPLETED_NO_SIGNAL_FAIL` with `passed=false`. Stored outcome/passed match in all four files.
- No 50%/90% threshold in the G1 path; the only such literals are G2 `_grade_g2` (L2211–L2213), unreachable from `run_g1_phase`. No oracle decision role. No reinterpretation.

## 6. Four-file cross-coherence and prohibited-payload scan

- Structure: root contains exactly the four names, no subdirectory (direct listing). `_write_stage_evidence` (L2414–L2430) structurally guarantees exactly these four scalar files and refuses to overwrite an existing dir (`FileExistsError`).
- Coherence: every shared scalar (phase/outcome/passed/monotonic/nonfinite/decoder_calls/peak_rss/wall/formal_root + all 12 per-f columns) is identical across `results.json`, `table.csv`, `report.md`, `execution_summary.json` (§2 table). CSV header matches the writer header string (L2564–L2568); two data rows, values match JSON per_f field-for-field.
- VOID citation: none of the four files names or numbers any other root; all `formal_root` strings are the new valid root.
- Prohibited payload: full-content scan of all four files finds no raw symbols, priors, beliefs, decoder traces, per-block samples, `syndrome_weight` rows, CAL/VAL rows, counts tables, secret material, or key matter. The 100-int `seeds` array in `results.json` is the frozen run identity (packet §4.1/§4.7), not per-block decode output.

## 7. Pre/post protected-root and lifecycle equality

- Pre-review (read-only evidence assistant + direct reads): branch `formal-ir-v72p1-addendum-clean`; HEAD `58c68961a1dedad58f52145e9f23942f2c476e4a`; `6494b623..HEAD` exactly two commits; `diff --numstat` empty (exit 0); `diff --cached --numstat` empty (exit 0); `Test-Path 20260907_r2` True; `Test-Path v72p2d5_g2` False; parent `v72p2d5_g1/` exactly `[20260906_r1, 20260907_r2]`; `cycle_state.yaml` nine authorizations false, promotion false, next gate unchanged (quoted §R01).
- Post-review: this review performed zero writes to `workspace/`, source, docs (other than this file), OpenSpec, state, decision-log, or memory, and zero git operations. The sole created path is this review file (untracked, uncommitted, unpushed). Lifecycle file re-read after all content reads: `g1_execution_authorized: false`, all nine false, `scientific_promotion: false`, `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW` — identical. G2 remains absent. No second G1 root appeared during the review (parent membership re-listed identical).
- Equality holds except the single allowed untracked review file.

## 8. Commands run and explicitly not run

- Ran (read-only): direct file reads of packet, pre-execute review, authorization record, operator return, `cycle_state.yaml`, all four new-root files, parent/root directory listings (except VOID interior), current-source ranges (L50–L99 constants, L992–L1025 decode isolation, L1307–L1330 layered block, L2061–L2205 scan/classify/G1 phase, L2414–L2569 evidence writer), targeted greps; plus a read-only evidence assistant that executed only `git branch --show-current`, `rev-parse HEAD`, `log --oneline`, `show --stat/--name-only/diff` for the three commits, `log 6494b623..HEAD`, `diff --numstat`, `diff --cached --numstat`, `status --porcelain` (head), and two `Test-Path` existence checks. No output was modified by any of these.
- Explicitly NOT run (all true): no decoder invocation; no CLI `--phase` of any kind; no retry/rerun/resume/replacement-root/parameter change; no Model-F prepare/verify; no CAL/VAL/parquet/raw-row read; no VOID-interior open/hash/interpret/citation; no `workspace/` modify/delete/move/rename/overwrite/normalize/hash; no `.py`/existing-`.md`/OpenSpec/cycle-state/decision-log/memory edit; no git add/commit/push/reset/stash/checkout/clean/rebase/revert/amend; no pytest/compile/probe/watchdog rehearsal; no repair, no acceptance, no G2/again-G1 authorization.

## 9. Findings

- Blocking: none.
- Non-blocking (disclosed, not verdict-changing):
  1. Working-tree `status --porcelain` shows pre-existing CRLF-churn `M` entries across many files; `diff --numstat`/`--cached` are empty (exit 0), so content is clean — same informational class as Pre-EXECUTE review §9.1. No normalization performed (correct).
  2. Per-f iteration totals sit exactly at their maxima (`18000 = 100×180`, `1800 = 20×90`), i.e. every APP and oracle block consumed full iterations. Arithmetically consistent with zero exact and a cold-start non-converging regime; it is a readout of the recorded scalars, not a new claim about decoder quality.
  3. Operator return §8 hygiene stats for protected roots were relied on only for pre/post sameness of membership, not as interior evidence; VOID interior numbers are deliberately not repeated here.

## 10. Strongest permissible claim and nonclaims

- Strongest permissible conclusion (and no stronger):
  > The sole authorized frozen synthetic G1 attempt completed within the frozen wall and RSS gates, produced an internally coherent four-file scalar record, and correctly classified zero APP exact successes at both f values as `G1_COMPLETED_NO_SIGNAL_FAIL` with `passed=false`.
- Explicitly rejected: real-data FER, decoder correctness, leakage, efficiency, key rate, qualification, promotion, method success, G2 readiness, permission for another G1 attempt, and any result acceptance — none follows from this review.

## 11. Verdict

`G1_PRE_RESULT_REVIEW_PASS`

(PASS = the recorded completed-but-no-signal-failure outcome is internally coherent and ready for a separate main-thread result-acceptance decision. It is not acceptance, not trend pass, and authorizes nothing.)
