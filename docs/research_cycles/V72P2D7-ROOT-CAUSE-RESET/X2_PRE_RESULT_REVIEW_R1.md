# X2 independent Pre-RESULT review R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Packet: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
  (§7 X2, §8, §9); Addendum A1 (`## Required independent reviews`)
- Review subject: `X2_OPERATOR_RETURN_R1.md` and the immutable X2 evidence
  root `workspace/d7_r1_multigraph_20260913_r1` (7 files, frozen).
- Review mode: independent read-only recomputation from the raw
  `call_records.csv` / `manifest.json` / `across_graph_summary.json`; nothing
  was re-executed, repaired, retried, cleaned, staged, or committed.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD
  `278fdf0742255de0d030649965b6feffb11bc23d`.
- Recording note: the operator transcribed the independent review's frozen
  findings into this record and re-verified the raw counts below against the
  X2 artifacts; the operator did not perform or accept the review.

## 1. Verdict

**`X2_PRE_RESULT_REVIEW_PASS`**

## 2. Raw recomputation summary

Coverage / matrix identity (all from `call_records.csv`, 384 data rows):

- Slots: **384/384 unique and complete**; no missing, duplicated, or
  replaced slot.
- Per graph: **128 / 128 / 128** (g0/g1/g2).
- Per f: **192 / 192** (f1.2 / f1.0); per `(graph, f)` cell: **64** (6 cells).
- Per arm: **96** each of `L1_MARGINAL`, `L1_TO_L2_TRANSFER`, `L2_MARGINAL`,
  `L2_TO_L1_TRANSFER`.
- Graph seeds and block seeds exact:
  `(2026090501, 2026090502)`, `(2026091401, 2026091402)`,
  `(2026091501, 2026091502)`; block seeds `2026091300..2026091315` (16).
- Rows: f1.2 L1=**59**, L2=**52**; f1.0 L1=**49**, L2=**43**.
- Decoder identity frozen: `max_iter` **90**, `damping_alpha` **1.0**.

Outcome separation and integrity:

- Exact / syndrome columns separated, no merges: `exact=True` **36**,
  `syndrome_ok=True` **36**; statuses `converged_exact` **36** and
  `converged_no_syndrome` **348**; per graph f=1.2: exact 13/10/13,
  syndrome_ok 13/10/13 with **0** exact-only and **0** syndrome-only rows.
- Provenance `CHECK_UPDATED`: **384/384**.
- crash **0**, blocked **0**, non-finite **0**; `invoked=True` 384/384.
- Per-graph f=1.2 paired discordant vectors (forward_only, reverse_only,
  both, neither): **(2, 0, 0, 14)** / **(2, 0, 0, 14)** / **(1, 0, 0, 15)**;
  f=1.0: (0, 0, 0, 16) for all three graphs.
- Terminal **`GRAPH_SENSITIVITY_OBSERVED`** with scope
  **`EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`**; `stop_reason: None`.

Budgets:

- Stored wall **131.5423 s** (<= 900 s); max per-call wall **0.4907 s**
  (<= 120 s); max recorded RSS **133185536 B** (~0.1240 GiB < 2 GiB);
  outer wall 134.5 s < 960 s watchdog.

Claim ceiling:

- No pooled claim. Per-graph descriptive paired discordant counts and exact
  two-sided McNemar p only; no pass/fail inferred from p-values; no
  qualification, promotion, ML, or information-theoretic claim; single
  synthetic implementation; exact/syndrome separation preserved.

## 3. Boundary confirmations

- Terminal is a coverage/scientific terminal, not
  engineering/resource/crash/incomplete; exactly one X2 process start and no
  rerun/resume/replacement/tuning/cleanup.
- Fresh root created by the run; `manifest.no_overwrite: true`; pre/post
  `git status --porcelain | sort` byte-identical; independent file-window
  scan found zero other modified repo files; Model-F input root untouched.
- All execution flags false after the attempt; X3/X4 unconsumed
  (`x3/x4_authorization_consumed: false`); X3/X4 frozen roots absent at
  review time; no commit, no push; `historical_evidence:
  RETAINED_BYTE_IDENTICAL`.
- The X3 selector will operate on the immutable root only: eligible failed
  f=1.2 records are 156 (87 SOURCE + 69 TARGET) by raw recomputation
  (recorded here as a pre-X3 expectation, not a result).

## 4. Advisories (non-blocking, for the next boundary)

1. Stale tests: `test_cycle_state_marker_and_all_flags_false` and
   `test_frozen_execution_roots_remain_absent` in
   `test_v72p2d7_r1_x1x4_entrypoints.py` still pin the pre-X2 lifecycle and
   root absence; they will fail until the scoped post-attempt update at the
   next state-changing boundary (no production effect).
2. `repo_files_touched.txt` in `/tmp/opencode/x2_r1_20260913/` is vacuous
   (0 bytes; `find -newer meta.txt` executed before the root files'
   timestamps settled relative to `meta.txt`); no-write evidence rests on
   `status_diff.txt` (0 lines) and the independent file-window scan, which
   both passed.
3. `PER_CALL_WATCHDOG_S = 120.0` is defined in the module but not enforced
   in-process; the per-call watchdog is owned externally by this operator
   and per-call walls are recorded in `call_records.csv`;
   max observed 0.4907 s.
4. Memory/troubleshooting updates (X2 outcome, advisory items) are deferred
   to memory triage at the phase boundary.

## 5. Disposition

X2 independently reviewed as `X2_PRE_RESULT_REVIEW_PASS`. X2 is complete and
verified; state advances to `X2_COMPLETE_VERIFIED` with `next_gate:
X3_EXECUTION`. This record grants no authorization, accepts no scientific
claim, and does not consume any phase authorization.
