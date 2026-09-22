# X3 independent Pre-RESULT review R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  (§7 X3, §8, §9); Addendum A1 (`## Required independent reviews`)
- Review subject: `X3_OPERATOR_RETURN_R1.md` and the immutable X3 evidence
  root `workspace/d7_r1_reference_ladder_20260913_r1` (7 files, frozen),
  read against the immutable X2 root
  `workspace/d7_r1_multigraph_20260913_r1` and the transcripts in
  `/tmp/opencode/x3_r1_20260913/`.
- Review mode: independent read-only recomputation from the raw
  `selected_records.csv` / `ladder_records.csv` / `paired_summary.csv` /
  `manifest.json` / `summary.json`; nothing was re-executed, repaired,
  retried, cleaned, staged, or committed.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD
  `278fdf0742255de0d030649965b6feffb11bc23d`.
- Recording note: the operator transcribed the independent review's frozen
  findings into this record and re-verified the raw counts below against the
  X3/X2 artifacts; the operator did not perform or accept the review.

## 1. Verdict

**`X3_PRE_RESULT_REVIEW_PASS`**

## 2. Raw recomputation summary

Command, execution identity, exit (from `/tmp/opencode/x3_r1_20260913/`):

- Exact launched command
  `timeout -k 30 3660 .venv/bin/python scripts/v72p2d7_consistency_multigraph.py --reference-ladder --x2-root workspace/d7_r1_multigraph_20260913_r1 --out-root workspace/d7_r1_reference_ladder_20260913_r1 --wall-budget-s 3600`
  from cwd `/mnt/d/Code/HD-QKD_Polar_Comparison`; one foreground attempt.
- Exit code **0**; outer wall **374622 ms** (374.622 s; watchdog disposition
  `COMPLETED_BEFORE_OUTER_WATCHDOG`, `timeout` pid **538493**); start
  `2026-09-13T13:51:53+0800` / `2026-09-13T05:51:53Z`, end
  `2026-09-13T13:58:07+0800` / `2026-09-13T05:58:07Z`.
- stdout terminal line exactly
  `terminal=X3_REFERENCE_LADDER_COMPLETED out=.../workspace/d7_r1_reference_ladder_20260913_r1 selected=156 ladder_calls=468 reconstruction_calls=4`;
  stderr empty (0 bytes).

Selector identity (recomputed from X2 `call_records.csv` and the X3
`selected_records.csv`):

- S = **156**; all rows `f = 1.2`, `invoked = true`, status not crash,
  `finite = true`, `exact = false`; no dedup or replacement.
- Per graph **51 / 54 / 51**; per role **87 `SOURCE` / 69 `TARGET`**; per
  arm `L1_MARGINAL` **39**, `L1_TO_L2_TRANSFER` **40**, `L2_MARGINAL` **48**,
  `L2_TO_L1_TRANSFER` **29** (sum 156).
- Multiset identity against the X2 root on
  `(slot_idx, graph_idx, seed, arm, role, rows)` is exact, and every
  `stored_status / stored_exact / stored_syndrome_ok / stored_iterations /
  stored_finite / stored_provenance` equals the X2 record field-by-field
  (0 mismatches).
- Graph seeds `(2026090501, 2026090502)`, `(2026091401, 2026091402)`,
  `(2026091501, 2026091502)`; stored rows f=1.2 L1=**59**, L2=**52**.

Call accounting:

- `ladder_calls` **468** (3 x 156; 156 per arm) + `reconstruction_calls`
  **4** = **472 <= 576** (frozen §P04 construction bound); PASS.
- `ladder_records.csv` 472 rows: `LADDER` 468 (`ROW_LAYERED_90` 156,
  `ROW_LAYERED_360` 156, `FLOODING_90` 156), `SOURCE_RECONSTRUCTION` 4.
- Reconstruction calls at record slots **[36, 264, 272, 300]**
  (`record_idx` 27/113/119/141, all `source_marginal_replay`); no fifth
  reconstruction, no over-ceiling path.

Baseline replay gate (hard gate before comparative interpretation):

- `ROW_LAYERED_90` replay equality against the stored X2 record:
  **156/156** LADDER rows `baseline_replay_match = True`; the **4/4**
  `SOURCE_RECONSTRUCTION` rows also `True` — **160/160 field-exact**;
  `mismatch_field` empty on every row; no mismatch token
  (`X3_BASELINE_REPLAY_MISMATCH_BLOCKED` absent); `stop: null` in
  `manifest.json` / `summary.json`.

Per-arm raw records (LADDER rows only, 156 calls each; all 472 rows finite,
`provenance = CHECK_UPDATED`, zero crash):

| Arm | exact | syndrome_ok | changed_vs_current | status |
|---|---|---|---|---|
| `ROW_LAYERED_90` | 0 | 0 | 0 | `converged_no_syndrome` 156 |
| `ROW_LAYERED_360` | 1 | 1 | 1 | `converged_no_syndrome` 155, `converged_exact` 1 |
| `FLOODING_90` | 0 | 0 | 0 | `converged_no_syndrome` 156 |

- The single rescue is `record_idx` **29**, record slot **40**, graph **0**,
  arm `L1_MARGINAL`, role `SOURCE`, seed **2026091310**, iterations **231**,
  status `converged_exact`, wall 1.1202 s.
- The 4 `SOURCE_RECONSTRUCTION` rows are a separate row kind (baseline-arm
  re-decodes of stored SOURCE marginals; 4 exact) and are not merged into
  the per-arm ladder counters above.
- `paired_summary.csv` 156 rows: `arm_360_exact` True **1** / False 155,
  `arm_360_changed` True **1** / False 155 (the one changed record is
  graph 0), `flooding_exact` False 156, `flooding_changed` False 156, all
  `baseline_replay_match` True.

Budgets:

- Stored wall **372.2475444819138 s** (<= 3600 s); max per-call `wall_s`
  **1.7975539110047976 s**; max recorded RSS **134381568 B** (~0.1252 GiB
  < 2 GiB); outer wall 374.622 s < 3660 s watchdog.
- Claim ceiling: `STRONG_REFERENCE_DIAGNOSTIC`, `scope`
  `STRONG_REFERENCE_DIAGNOSTIC` in `summary.json`; no ML,
  information-theoretic, qualification, or promotion claim.

## 3. Boundary confirmations

- Terminal `X3_REFERENCE_LADDER_COMPLETED` is a scientific/coverage
  terminal with full coverage of the 156 selected failed f=1.2 records and
  no stop reason — not engineering/resource/crash/incomplete. Exactly one
  X3 process start; no rerun/resume/replacement/tuning/cleanup.
- Fresh root created by the run; exactly the 7 frozen X3 evidence files;
  `manifest.no_overwrite: true`; pre/post `git status --porcelain | sort`
  byte-identical (both md5 `df682a08b9d224e9999ef7f1b23033c5`, 2104
  entries; `status_diff.txt` 0 lines); independent file-window scan found
  zero other modified repo files; X2 root mtimes unchanged; Model-F input
  root untouched.
- `x3_reference_ladder_authorized` restored **false** after the attempt
  (verified 13:59:35); all execution flags false; X4 unconsumed
  (`x4_authorization_consumed: false`); X4 frozen root absent at review
  time; no commit, no push; `historical_evidence:
  RETAINED_BYTE_IDENTICAL`.
- Independent test rerun (fresh basetemp
  `workspace/v72p2d7_x1x4_test_x3post_1789279418_4411`):
  `.venv/bin/python -m pytest -p no:cacheprovider -q .../test_v72p2d7_r1_x1x4_entrypoints.py`
  → **57 passed**, exit 0.

## 4. Advisories (non-blocking, for the next boundary)

1. Plan wording imprecision: `manifest.json` labels the 576 bound as
   `ladder_call_ceiling` and carries a separate `reconstruction_call_ceiling:
   96`; the binding frozen rule is the §P04 construction bound
   `ladder_calls + reconstruction_calls <= 576` from actual records, which
   holds (472). Field names are non-binding labels.
2. Flag-restore snapshot ordering: `flag_restore.txt` (13:59:35) shows
   `x3_authorization_consumed: false` because that snapshot preceded the
   additive consumption bookkeeping; `cycle_state.yaml` now records `true`.
   The authorization flag itself (`x3_reference_ladder_authorized`) is
   false in both.
3. `/tmp/opencode/x3_r1_20260913/repo_files_touched.txt` is vacuous
   (0 bytes; `find -newer` compared against a pre-run `meta.txt`); the
   no-write case rests on the byte-identical status diff, the explicit file
   window scan, and the X2 mtime check, all of which passed.
4. Per-call telemetry limitation: per-call walls are recorded per row
   (max 1.7976 s), but the 480 s per-call watchdog is externally owned and
   not enforced in-process; it is not machine-observable in the frozen
   evidence beyond the stored per-row walls. The outer 3660 s watchdog and
   the operator's process ownership are the binding execution guards.
5. Memory/troubleshooting updates (X3 outcome, advisory items) are deferred
   to memory triage at the phase boundary.

## 5. Disposition

X3 independently reviewed as `X3_PRE_RESULT_REVIEW_PASS`. X3 is complete
and verified; state advances to `X3_COMPLETE_VERIFIED` with `next_gate:
X4_EXECUTION`. This record grants no authorization, accepts no scientific
claim, and does not consume any phase authorization.
