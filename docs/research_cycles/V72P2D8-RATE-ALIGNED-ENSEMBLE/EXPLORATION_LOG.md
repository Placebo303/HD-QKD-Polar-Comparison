# D8 rate-aligned GF32 ensemble feasibility — EXPLORE log (append-only)

Cycle: `V72P2D8-RATE-ALIGNED-ENSEMBLE`
Change: `v72p2d8-rate-aligned-gf32-ensemble-feasibility`
Track: `EXPLORE_HEAVY` under `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`
Batch: D8 rate-aligned GF32 ensemble feasibility heavy R1
Authority: `.workbuddy/tasks/D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY_R1_TASK_PACKET.md`
+ paired prompt.
Readiness record: `READINESS_R1.md` (this directory).

This is the single append-only log for this batch. The operator appends
attempts, the preregistered engineering correction (at most one repair+rerun),
final evidence and the batch-end review here; no per-arm documents are created.

## 2026-09-13 — readiness opening / preregistration (E01–E06; no execution)

### Authorization boundary

- The readiness call authorized audit, OpenSpec, design and read-only
  verification only. It performed no production code edit, no decoder call, no
  DE scientific call, no Model-F content read beyond the accepted artifact
  metadata, no CAL/VAL/raw/real-data contact, no output-root creation, no
  commit, no push.
- The future DE sweep remains **unauthorized**. It requires a separate explicit
  user/main-thread authorization naming this batch, branch, root, candidate
  cap, seeds and budgets. No authorization key was or is set by readiness.

### Accepted predecessor route close (E01)

- Lifecycle `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`; L1
  exact/syndrome 0/40, L2-APP 5/40, L2-oracle 35/40, end-to-end APP exact
  0/120, T1 PEG-DV3 silent at n64/n128/n256. Closes only the eligible-only DV3
  topology substitution; no graph-family-impossibility claim. `next_gate`:
  `D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY`. D7-H stays not recommended and
  unauthorized.

### Frozen future sweep design (see `READINESS_R1.md` §2–§6; `design.md` §1–§6)

- Reused engine: `nonbinary_v26_mcde.run_mcde_posterior` unchanged (q=32,
  poly 37, probability-domain full vectors, coefficient-permuted WHT check
  update), plus V27-style `R=1-m/n`/`make_rho` mapping and V37
  `compute_trajectory_metrics` definitions; exact delta list in `design.md` §1.
- Channel: accepted CAL-only Model-F artifact
  `workspace/v72p2d5_model_f_input/20260907_r1` → E2 `P_F` → `P1` → floor
  `1e-15` → per-sample XOR centering; 32-ary rows preserved exactly; L1 only
  (L2 read-only comparator). No BSC/AWGN/q-SC/scalar surrogate.
- Rate conditions: f1.2 primary (R=5/64) and f1.0 secondary (R=15/64), with
  the accepted D6 row sets n64 L1 (49,59,64)/L2 (43,52,64), n128 ×2,
  n256 ×4; square excluded. DE is n-independent (identical R and channel).
- Candidates: λ support {2,3}, λ2∈{0.00,0.05,…,1.00}, 21 candidates, hard cap
  21, regular-DV3 baseline `lam_d2_0.00_d3_1.00` included; ρ derived by
  `make_rho(R,λ)`; refusals recorded; no outcome adaptation.
- Sweep: `n_samples=4000`, `max_iter=60`, `entropy_tol_bits=1e-4`,
  `streak=20`, `record_entropy=True`, `record_channel_entropy=True`; seeds
  `2026091601..2026091603`; ≤126 DE calls + ≤20 setup, wall ≤1800 s, per-call
  ≤120 s, RSS <2 GiB strict, single process, no retry/resume/seed search.
- Advancement: all seeds converged (H60<1e-4) in both conditions AND primary
  worst-seed `AUT_30` ≤ 0.95× regular-DV3 baseline; exactly one winner by
  `(primary worst-seed AUT_30 asc, primary mean AUT_30 asc, primary worst-seed
  T_0.01 asc, candidate ID lexicographic)`.
- Terminals: `D8_DE_ADVANCE_ONE_ENSEMBLE`, `D8_DE_NO_ADVANCE`,
  `D8_DE_BASELINE_NOT_CONVERGED`, `D8_DE_EVIDENCE_INVALID`,
  `D8_DE_RESOURCE_BLOCKED`, `D8_DE_NOT_RUN`. A `NO_ADVANCE`/silent grid closes
  only the frozen support/grid and routes to a broader degree/ensemble
  proposal or an explicit channel/decoder mismatch analysis; it is never
  "NB-LDPC impossible".
- Claim ceiling: DE-only synthetic asymptotic evidence under the frozen
  CAL-only Model-F channel and decoder contract; no finite-length/FER/leakage/
  qualification/promotion/real-data claim; advancement authorizes only the
  next finite-length task packet.
- Fresh root (absent, not created):
  `workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`
  (UUID `5edf0630-f357-4a7e-b4c5-9ba955021405`).
- Frozen command (repo venv; requires explicit authorization):
  `.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`.
- Expected fresh-root files: `manifest.json`, `de_records.csv`,
  `de_traces.csv`, `candidate_summary.csv`, `summary.json`, `command_log.txt`;
  `--verify` recomputes every group from the traces (zero skip).

### Attempts

- None (execution). This opening is E01–E06 readiness/design only.

### Final evidence

- Placeholder — to be filled by the authorized sweep (fresh-root files above).

### Batch-end review

- Placeholder — one independent reviewer-go batch-end review after the frozen
  sweep (or after an early terminal) covers the authorization boundary, machine
  gates, retained failures, the preregistered repair if used, final evidence
  and the claim ceiling. FAIL blocks promotion of the batch evidence and
  triggers escalation review, not another unreviewed arm.

## 2026-09-13 — E07–E10 implementation/verification (no sweep execution)

### Authorization boundary

- Implementation-only call: adapter + runner + focused tests + bounded
  PROFILE_ONLY smoke + frozen-match verification. No production decoder call,
  no DE scientific sweep, no `--de-sweep` execution, no root creation (the
  fresh future root remains absent), no CAL/VAL/raw/real-data contact, no
  commit, no push. All authorization flags remain false.

### E07 — adapter + runner + verifier (allowed files only)

- New thin adapter
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d8_rate_aligned_ensemble.py`:
  L1-only Model-F sampler (accepted artifact → `pb = p_b/p_b.sum()` → E2
  `P_F` (λ*=137.3823795883264) → `P1` marginalization → per-sample
  `floor_renorm(...,1e-15)` → `c[e] = pr1[u XOR e]` XOR centering); rate/ρ
  helper `R = 1 - m/n`, `ρ = make_rho(R,λ)`; deterministic 21-candidate grid
  `lam_d2_<λ2:.2f>_d3_<λ3:.2f>` ascending with recorded `make_rho` refusals;
  V37 `compute_trajectory_metrics` reuse; recorded-only V37-P0 `N2`/`gamma_2`
  forest diagnostics; unchanged V26 `run_mcde_posterior` wrapper with
  `q=32, n_samples=4000, max_iter=60, entropy_tol_bits=1e-4, streak=20,
  record_entropy=True, record_channel_entropy=True`; frozen advancement/rank
  key and terminals.
- New runner `scripts/v72p2d8_rate_aligned_ensemble_development.py`:
  `--de-sweep`/`--verify`, six-file fresh root, protected/existing-root
  refusal, budgets (≤126 DE + ≤20 setup, wall ≤1800 s, per-call ≤120 s,
  RSS <2 GiB strict, single process, no retry/resume/adaptive stop), seeds
  `2026091601..2026091603`, conditions f1.2 (primary) / f1.0 (secondary),
  L1 only, `--verify` zero-skip recomputation from `de_traces.csv`.
- V26/V27/V37/V14/V9/v35 and all other existing modules untouched (import
  only).

### E08/E09 — tests and profiling

- `py_compile` on adapter + runner: PASS. Import/constants check: PASS
  (21 candidates, 42 pairs, 126 calls, 6 terminals).
- `.venv/bin/python -m pytest
  comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py -q
  -p no:cacheprovider --basetemp=workspace/d8_tests_<uuid>`: **14 passed,
  0 failed** (sampler exact XOR/mass-1 on a synthetic tiny fixture; five
  rate/ρ hand checks; baseline DV3 reproduction; 21-ID enumeration; invalid-λ
  refusal; recorded ρ refusal; cross-kernel `_check_update_coeff_jit` == V14
  `_check_update_jit` with unit coefficients; fresh/protected-root refusal;
  fake-runner isolation with zero kernel and zero decoder calls; `--verify`
  self-check and tamper detection).
- PROFILE_ONLY (bounded, 4 DE calls, never sweep evidence, no root written):
  channel load 0.050 s; per-call wall 1.987 / 0.840 / 0.801 / 0.815 s; peak
  RSS 239.3 MiB; future root absent after profiling.

### E10 — frozen-match verification

- FROZEN_MATCH PASS: the implemented command
  `.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py
  --de-sweep --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`
  matches `design.md` §6; flags/defaults, seeds, 21-candidate grid (hard cap
  21), and budgets 126/20/1800 s/120 s/2 GiB strict are verified in code. The
  fresh future root is verified **absent** and was not created.

### Batch-end review

- Placeholder — this E07–E10 implementation call ends before E11 (independent
  reviewer-go review) and E12 (at most one scoped correction). No sweep
  evidence exists yet; the batch-end review remains pending and the DE sweep
  remains unauthorized.

## 2026-09-13 — E12 correction (F1 applied)

### Authorization boundary

- Scoped correction call: one test assertion added and this log appended. No
  branch switch, no commit, no push, no decoder call, no DE sweep, no root
  creation, no CAL/VAL/raw/real-data contact. All authorization flags remain
  false; the DE sweep remains unauthorized.

### F1 applied (E11 PASS_WITH_FINDINGS)

- Finding: `design.md` §4 ("E08 asserts the actual maximum ≤ 4 at both
  conditions") and `spec.md` claimed a realized-max-check-degree assertion that
  no test performed.
- Change: added `test_realized_max_check_degree_le_4_at_both_conditions` to
  `comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py` (only change).
  It computes the realized maximum check degree over the full frozen
  `build_candidate_plan()` grid (21 candidates × both conditions = 42 entries,
  positive-weight ρ keys from the implemented `make_rho` binding) and asserts
  `<= 4` (design.md:141 / spec.md:38) and `<= 8` (spec.md:37). No other test
  was modified.
- F2–F4 (E11 findings): carried as no-action for this correction and as
  notes for the next packet; not addressed here.

### Raw test result

- Command: `.venv/bin/python -m pytest
  comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py -q
  -p no:cacheprovider
  --basetemp=workspace/d8_e12_fix_69157c6f-edd2-417d-bd8d-c88679f289b5/`
- Result: **15 passed, 0 failed**, 1 warning (`Unknown config option:
  cache_dir`, benign), 6.63 s, exit 0 (14 pre-existing tests + 1 new).

### Batch-end review

- Still pending; the frozen DE sweep remains unauthorized and no sweep evidence
  exists.

## 2026-09-13 — independent review (E11/E12) and closure

### Review

- Artifact:
  `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/INDEPENDENT_REVIEW_R1.md`
  (`REVIEW_ID: D8-RATE-ALIGNED-ENSEMBLE-E11`).
- `EVIDENCE_ACCESS: VERIFIED`; `VERDICT: PASS_WITH_FINDINGS`. Independent
  Fraction re-derivation 56 PASS/0 FAIL; channel chain reproduced exactly
  (maxdiff 0; sampler rows `np.array_equal`); runner/verifier frozen-match;
  evidence boundary respected (zero decoder/scientific-DE calls, no root).
- Findings: **F1** applied at E12 (new
  `test_realized_max_check_degree_le_4_at_both_conditions`, 21×2 grid, asserts
  ≤4 and ≤8; scoped re-review `F1_STATUS: RESOLVED`, `VERDICT: PASS`, 15/15
  tests). **F2–F4** carried as non-blocking notes for the next packet
  (partial-root `--verify` fail-closed; between/after-call budget enforcement +
  hard-coded `setup_calls`; coefficient-stream seed wording).

### Terminal

- `D8_RATE_ALIGNED_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`
  (confirmed by the E12 scoped re-review).

### Authorization boundary (unchanged)

- The DE sweep remains **unauthorized**; the future root
  `workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`
  is **absent**; no commit, no push, no branch switch. All authorization flags
  remain false. The sweep still requires a separate explicit user/main-thread
  authorization naming this batch, branch, root, candidate cap, seeds and
  budgets.

## 2026-09-13 — main-thread readiness acceptance

- Accepted the D8 implementation/readiness evidence after independent
  `EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, the F1 correction and
  scoped re-review `PASS`. The 56 mathematical checks, exact Model-F channel
  reconstruction and focused 15/15 tests are trusted without duplicate rerun.
- Frozen sweep accepted for authorization: 21 deterministic `{2,3}` lambda
  candidates, two rate conditions, three seeds, 126 scientific DE calls,
  regular-DV3 baseline and the registered convergence/AUT_30 advancement rule.
- Carried execution semantics: a partial root fails normal `--verify` and must
  be retained/adjudicated without rerun; the 120 s per-call cap is checked
  between/after calls rather than interrupting a call; `setup_calls=0` is the
  implemented value; DE uses the V26 random nonzero-coefficient ensemble and
  does not exercise finite-length coefficient-stream seeds.
- Lifecycle:
  `D8_RATE_ALIGNED_ENSEMBLE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  This acceptance grants no sweep, decoder, real-data, commit or push.

## 2026-09-13 — D8 DE sweep A1 pre-dispatch (raw results; no execution yet)

### Authorization boundary

- The user sent the paired A1 prompt verbatim, authorizing exactly one frozen
  `--de-sweep` invocation. No branch switch, no commit, no push, no
  retry/resume/tuning, no finite-length decoder, no D7-H, no CAL/VAL/raw/real
  data, no n1024. All checks below run read-only except the authorized focused
  preflight (py_compile + the 15 D8 tests).

### Raw checks (fail-stop; checks 1–7)

1. **Accepted readiness marker present; sweep unexecuted.**
   - `READINESS_R1.md:3`:
     `Status: D8_RATE_ALIGNED_ENSEMBLE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`;
     `:12` `main_readiness_acceptance: true`.
   - `EXPLORATION_LOG.md` §"main-thread readiness acceptance" records the
     main-thread acceptance (lifecycle marker, `:249-250`).
   - Unexecuted evidence: `test -e workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405` → `ABSENT`;
     `find workspace -maxdepth 1 -name 'd8_rate_aligned_ensemble*' -o -name 'd8_sweep*'` → no output;
     `find workspace -maxdepth 2 -name de_records.csv -o -name de_traces.csv` → no output.
   - PASS.
2. **All execution/promotion authorization flags false (no machine-readable
   flag store for D8; prose + absence check).** D8 has no flag-store file;
   verified from `READINESS_R1.md:153` "All authorization flags remain false;
   the sweep is unexecuted and unauthorized" and `:198` "All authorization keys
   false; no root created", plus the absence of any execution/root records
   above. State explicitly: **no authorization flag is set anywhere; the sweep
   is unexecuted and unauthorized.** PASS.
3. **Exact future root absent.** `workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`
   → `ABSENT`; no other D8 roots or partial records. PASS.
4. **Model-F root accepted CAL-only and unchanged.**
   `workspace/v72p2d5_model_f_input/20260907_r1/`:
   `model_f_input.npz` size 208467, mtime 2026-09-07 02:07:07.043698800 +0800;
   `model_f_input_summary.json` size 752, mtime 2026-09-07 02:07:07.043698800 +0800;
   summary `cal_only: true`, `val_rows_read: 0`,
   `lambda_star: 137.3823795883264`, `field: {poly: 37, q: 32}`,
   `cycle: V72P2D5-GF32-RATE-MOTHER`, `decoder_calls: 0`. PASS.
5. **Implemented plan exactly 21 candidates × 2 conditions × 3 seeds (raw
   introspection of the runner plan; no DE call).**
   - `candidates=21 conditions=('f1.2', 'f1.0') seeds=(2026091601, 2026091602, 2026091603)`
   - `plan_entries=42 refusals=0 planned_de_calls=126`
   - IDs: `lam_d2_0.00_d3_1.00` … `lam_d2_1.00_d3_0.00` (21 ascending).
   - Constants: `max_de_calls=126 max_setup=20 wall=1800.0 per_call=120.0 rss=2147483648`.
   - PASS.
6. **F1 resolved; F2–F4 explicitly carried.**
   - `READINESS_R1.md:10`: `e12_correction: F1 applied (realized max check
     degree 4 ≤4/≤8 asserted; 15/15 tests)`; `:11`: `carried_findings: F2_F3_F4`.
   - `INDEPENDENT_REVIEW_R1.md:25-29`: E12 scoped re-review `F1_STATUS: RESOLVED`,
     `VERDICT: PASS`; `:16-18` F2/F3/F4 marked `CARRIED` (non-blocking).
   - PASS.
7. **Focused drift preflight (authorized scope only).**
   - `.venv/bin/python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p2d8_rate_aligned_ensemble.py scripts/v72p2d8_rate_aligned_ensemble_development.py`
     → `PY_COMPILE PASS`.
   - Focused test attempt 1 (operator path-scaffold error, raw): command
     `.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py -q -p no:cacheprovider --basetemp=workspace/d8_sweep_a1_preflight/2a92f150-8047-4260-8d8e-844c290d40d1/`
     → `12 passed, 3 errors in 9.44s`, exit 1; errors were
     `FileNotFoundError: .../workspace/d8_sweep_a1_preflight/2a92f150-8047-4260-8d8e-844c290d40d1`
     from the `tmp_path` fixture because the basetemp parent
     `workspace/d8_sweep_a1_preflight/` did not exist (pytest 9 `basetemp.mkdir`
     without `parents=True`). No code/test/artifact fault; no file was edited.
   - Operator scaffold correction: created `workspace/d8_sweep_a1_preflight/`
     (task-owned, additive) and reran with a fresh UUID (no code change, not a
     scientific rerun).
   - Focused test attempt 2 (fresh task-owned basetemp):
     `.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py -q -p no:cacheprovider --basetemp=workspace/d8_sweep_a1_preflight/2e0bbf56-625b-428c-a008-044a0f8a55f4/`
     → **15 passed, 0 failed, 1 benign warning (`Unknown config option:
     cache_dir`), exit 0**. PASS.
   - No unrelated suite and no 56-check audit rerun.

### Gate decision

- All checks 1–7 PASS after the documented operator basetemp-parent scaffold
  fix (no implementation/test change). Proceeding to exactly one authorized
  invocation of the frozen sweep command. Repo state: branch
  `formal-ir-v72p1-addendum-clean` (unchanged), HEAD
  `278fdf0742255de0d030649965b6feffb11bc23d` (unchanged); no commit, no push,
  nothing staged.

## 2026-09-13 — D8 DE sweep A1 execution

### Command and execution

- Exact command (once, repo root, no branch switch):
  `.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`
- Exit code: **0**; stdout final line:
  `D8_DE_SWEEP terminal=D8_DE_BASELINE_NOT_CONVERGED winner=None de_calls=126`.
- Start `2026-09-13T23:52:43+0800` (15:52:43Z); end `2026-09-13T23:54:35+0800`
  (15:54:35Z); process wall **112 s** (runner-internal `wall_s` =
  107.10461202799343 s).
- Process/pid ownership: one foreground process, `SWEEP_PID=919649` (subshell
  pid exec-replaced by `.venv/bin/python`; no background jobs, no other
  process launched). No retry, no resume, no overwrite.

### Calls and stages

- `de_calls=126 / 126` (≤126 limit) = 21 candidates × 2 conditions × 3 seeds;
  `setup_calls=0` (implemented value, ≤20 frozen ceiling); `refusal_count=0`;
  per condition `21×3 = 63` calls. `de_records.csv`: 126 rows, `call_idx`
  0..125 contiguous, 126 unique `(candidate_id, condition, seed)` keys;
  `command_log.txt` has exactly 126 `call=` lines. No adaptive stop.
- Per-candidate convergence (raw recount from `de_records.csv`):
  - candidates with all 3 seeds converged in both conditions: **0**;
  - candidates with any converged seed: **5**;
  - f1.2 (primary): all-3 converged = `lam_d2_0.45_d3_0.55`,
    `lam_d2_0.50_d3_0.50`; partial = `lam_d2_0.40_d3_0.60` (1/3),
    `lam_d2_0.55_d3_0.45` (2/3), `lam_d2_0.60_d3_0.40` (1/3);
  - f1.0 (secondary): 0 candidates converged, 0 partial.

### Terminal, baseline, advancement (report only; not accepted)

- Stored terminal: **`D8_DE_BASELINE_NOT_CONVERGED`** (`summary.json`
  `terminal`; `terminal_reason: null`; log:
  `terminal=D8_DE_BASELINE_NOT_CONVERGED reason=None winner=None`). Per
  `design.md` §5 this routes to mismatch analysis first; it is a valid EXPLORE
  outcome, not an engineering failure.
- DV3 baseline `lam_d2_0.00_d3_1.00` (`baseline_converged: false`):
  f1.2 primary 0/3 seeds converged, worst-seed `AUT_30` =
  151.90884493578253, mean 151.88961564440865, worst `T_0.01` = 61;
  f1.0 secondary 0/3 converged, worst `AUT_30` = 154.47598423886723,
  `aut30_ratio_baseline` = 1.0168992088918187.
- Advancing candidates: **none** (`eligible_candidate_ids: []`); deterministic
  winner: **none** (`winner_candidate_id: null`). No winner is accepted here.

### Budgets / resources

- Max per-call wall: **1.975 s** (call 1, includes first-call JIT); mean
  0.849 s; min 0.799 s; all calls ≤120 s (post-call check only — no call
  exceeded the cap, so no post-call resource terminal was triggered and no
  in-flight interruption is claimed).
- Wall: 107.105 s ≤1800 s. RSS: `peak_rss_bytes` = **251805696** (240.1 MiB)
  < 2147483648 (2 GiB strict); stage logs peak 240.1 MiB.
- No retry/resume/seed search/adaptive stop evidence: 126/126 planned calls,
  contiguous indices, unique keys, `budgets` block
  `retry:false, resume:false, adaptive_stop:false, processes:1`.
- DE coefficient semantics: V26 random nonzero-coefficient ensemble; no
  finite-length coefficient-stream seeds used or tested.

### Root inventory (complete; retained; no repair/delete/rerun)

`workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/` —
exactly the six frozen evidence files:

| file | bytes |
|---|---|
| `manifest.json` | 2818 |
| `de_records.csv` | 24858 |
| `de_traces.csv` | 295382 |
| `candidate_summary.csv` | 6025 |
| `summary.json` | 2215 |
| `command_log.txt` | 18781 |

Markers present: `change_id = v72p2d8-rate-aligned-gf32-ensemble-feasibility`,
`track = EXPLORE_HEAVY`, `claim_ceiling` (manifest+summary); frozen command,
seeds, conditions, budgets and `l1_only: true` recorded in `manifest.json`.
- Partial-root/no-repair semantics: not applicable — the run completed
  (exit 0, 126/126 calls, six files). Nothing was repaired, deleted or rerun;
  normal `--verify` output follows below.

### Read-only verification (raw)

Command:
`.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --verify --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`

Raw output:

```text
VERIFY checked_calls=126 agreements=126 skipped=0 groups=42/42 violations=0
VERIFY PASS
```

Exit code 0. Zero skipped groups; stored == recomputed for all 126 traces.

### Claim boundary (unchanged)

- This execution produced DE-only synthetic asymptotic evidence under the
  frozen CAL-only Model-F channel and decoder contract. It establishes no
  decoder improvement, no ensemble superiority, and no
  finite-length/FER/leakage/SKR/qualification/promotion/real-data claim. The
  `D8_DE_BASELINE_NOT_CONVERGED` terminal routes to mismatch analysis first.
  No winner is self-accepted; advancement to any next finite-length task packet
  requires the batch-end independent review and main-thread decision.

## 2026-09-13 — D8 DE sweep A1 batch-end review

REVIEW_ID: D8-DE-SWEEP-A1-BATCH-END
EVIDENCE_ACCESS: VERIFIED
VERDICT: PASS_WITH_FINDINGS
REVIEWED_SCOPE: A1 packet §§1–7; D8 feasibility packet; READINESS_R1; EXPLORATION_LOG; INDEPENDENT_REVIEW_R1; frozen OpenSpec change; actual root six files; read-only code (runner, adapter, V26/V37 pieces, D5 artifact summary, pytest tmpdir); commands: `--verify --out-root` (exit 0), independent self-contained recount of all raw CSVs (own V37 metric re-implementation; 0 mismatches over 126 calls; 42/42 candidate rows), plan introspection, filesystem/mtime scans, scoped git checks. No repo file created/staged/committed.
VERIFIER_RESULT: `VERIFY checked_calls=126 agreements=126 skipped=0 groups=42/42 violations=0` / `VERIFY PASS` (exit 0); matches the operator's retained output exactly.
RECOUNT: 21 candidates × 2 conditions × 3 seeds = 126 records/traces; call_idx 0..125 contiguous; 126 unique keys; order == frozen plan (candidate-major ascending, f1.2 before f1.0, seeds ascending); traces finite length 60. Independent metric recomputation equals every stored field (0 mismatches); candidate_summary matches for 42/42; gamma2 formula holds. Convergence: 0 all-3-seeds-both-conditions candidates; 5 with any primary convergence (`0.40` 1/3, `0.45` 3/3, `0.50` 3/3, `0.55` 2/3, `0.60` 1/3; f1.0 all 0/3); 10 converged calls. DV3 baseline f1.2 0/3 worst AUT_30 151.90884493578253 mean 151.88961564440865 worst T_0.01 61; f1.0 0/3 worst 154.47598423886723; `aut30_ratio_baseline` 1.0168992088918187. Advancement threshold 0.95×151.90884493578253 = 144.3134026889934; eligible ∅; rank key present/correct in code; winner none. Stored terminal `D8_DE_BASELINE_NOT_CONVERGED` is the frozen-correct terminal (baseline fails; routes to mismatch analysis first per design §5); no NO_ADVANCE/EVIDENCE_INVALID/RESOURCE_BLOCKED path applies.
MARKERS_AND_BUDGETS: field {q:32,poly:37}; l1_only true; channel string = accepted CAL-only Model-F → E2 P_F → P1 → floor_renorm(1e-15) → XOR centering; λ*=137.3823795883264; f1.2 59/64 rate 0.078125 primary; f1.0 49/64 rate 0.234375 secondary; baseline ρ {3:11/16,4:5/16} / {3:1/16,4:15/16}. Grid 21 unique ascending IDs, 0 refusals, cap 21. No adaptive search/stop; all 126 frozen calls; de_parameters 4000/60/1e-4/streak 20. Budgets: 126/126 calls; wall 107.1046 s ≤1800; per-call max 1.974549 s (JIT) / mean 0.848853 s / min 0.798606 s — post-call check only, no interruption claimed or triggered; RSS peak 251805696 B < 2 GiB; processes 1; retry/resume/adaptive false; setup 0; command_log 126 call lines, no error/restart markers.
COEFFICIENT_SEMANTICS: V26 random nonzero-coefficient ensemble (seeded draw per slot/sample) correctly described; no finite-length coefficient-stream seeds used or claimed.
PREFLIGHT_INCIDENT: NON-BLOCKING. Attempt-1 pytest 12 passed/3 errors from a missing `--basetemp` parent (pytest 9.1.1 `tmpdir.py` mkdir without parents); exactly the 3 tmp_path tests errored; operator created the task-owned additive parent and reran with a fresh UUID → 15 passed; zero code/test change; retained in the log. Next-packet note: pre-create the basetemp parent.
EVIDENCE_INTEGRITY: root = exactly six regular files (2818/24858/295382/6025/2215/18781 B); no partial-root ambiguity; no writes outside the root during the run window (only authorized log append + pre-sweep pycache); no cleanup/deletion; protected roots (Model-F/D6/D7/A2/G2, results/, outputs_comparison/, src/, experiments/) untouched; HEAD `278fdf07…` unchanged; nothing staged; no commit.
CLAIM_AND_AUTHORIZATION: DE-only synthetic asymptotic evidence under the frozen CAL-only Model-F channel/decoder contract; no finite-length/FER/leakage/SKR/qualification/promotion/real-data claim; no winner self-accepted (`winner_candidate_id: null`); no route self-closed; D7-H not revived; single A1 invocation consumed; authorization flags false (prose; no D8 machine flag store); no promotion/qualification grant.
FINDINGS:
- [F1] NON-BLOCKING — preflight attempt-1 scaffold error (missing basetemp parent), independently explained, zero impact; no correction needed this batch; next-packet note retained.
- [F2] NON-BLOCKING (carried E11-F2) — `--verify` fails closed on legitimately partial roots; not exercised (complete root, PASS); next-packet note.
- [F3] NON-BLOCKING (carried E11-F3) — `setup_calls` hard-coded 0 and per-call/RSS budgets enforced between/after calls, not an interrupting watchdog; log describes correctly; next-packet note.
- [F4] NON-BLOCKING (carried E11-F4) — design.md:139 finite-length coefficient-stream wording vs DE random-ensemble semantics; wording fix in the next finite-length packet.
- [F5] NON-BLOCKING — `candidate_summary.csv` secondary-condition `aut30_ratio_baseline` uses the primary baseline worst AUT_30 (baseline f1.0 row 1.0168992088918187); informational only, never used by the frozen rank key; optional clarity note next packet.
CLAIM_CEILING: establishes that the one authorized 126-call DE-only synthetic asymptotic sweep ran exactly as frozen (exit 0, 21×2×3, no setup/refusals, budgets/no-retry/no-resume/no-adaptive respected, single fresh six-file root), evidence internally consistent and independently recomputed (126/126, 42/42, 0 violations), DV3 baseline failed the frozen gate, no candidate met the advancement predicate, stored terminal `D8_DE_BASELINE_NOT_CONVERGED` frozen-correct routing to mismatch analysis first. Establishes no decoder improvement, FER/leakage/SKR, superiority, impossibility, finite-length behavior, qualification, promotion or real-data suitability; no route decision; advancement would have authorized only the next finite-length task packet and does not revive D7-H.
TERMINAL_RECOMMENDATION: D8_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION
AUTHORITY_BOUNDARY: advisory review only; result acceptance and route decision remain with the user/main thread.

## 2026-09-14 — main-thread result acceptance and route decision

- Accepted the complete six-file A1 root, independent batch-end review and
  stored terminal `D8_DE_BASELINE_NOT_CONVERGED` under the frozen D8 claim
  ceiling. The 126-call execution was complete, within budget and internally
  reproduced with zero metric mismatch.
- No candidate satisfies the frozen two-condition advancement predicate and no
  winner is promoted. In particular, the post-run route does not relabel
  lambda2 0.45 or 0.50 as D8 winners.
- Descriptive successor evidence is retained: lambda2 0.45 and 0.50 converged
  3/3 at the primary f1.2 condition, while every candidate failed the f1.0
  condition. This pattern warrants calibration, not immediate finite-length
  execution and not an NB-LDPC impossibility conclusion.
- Next gate: `D9_DE_DECODER_CALIBRATION_AND_THRESHOLD`. It must certify the
  DE-to-decoder semantics beyond the already checked check-update kernel,
  assess Monte-Carlo stability, verify finite graph realizability of the
  `{2,3}` mixtures, and preregister whether f1.0 is a hard advancement gate or
  a boundary diagnostic. D7-H remains unauthorized/not recommended.
- Lifecycle: `D8_DE_SWEEP_RESULT_ACCEPTED_ROUTE_TO_D9_CALIBRATION`. This
  acceptance grants no new DE sweep, finite-length decoder, real-data run,
  commit or push.
