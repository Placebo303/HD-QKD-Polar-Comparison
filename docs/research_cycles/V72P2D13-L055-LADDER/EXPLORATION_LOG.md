# D13 L055 failure decoder ladder — EXPLORE log (append-only)

Cycle: `V72P2D13-L055-LADDER` (decoder-dynamics diagnostic on frozen D12 failures; NOT a correction of any predecessor).
Authority: `.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md` §1–§4 (frozen).
This is the single append-only log root for D13 readiness. The future scientific batch
(if separately authorized) and its batch-end review append here; no per-arm documents.
Detail record: `READINESS_R1.md` in this directory.
Predecessor pointer: `docs/research_cycles/V72P2D12-FINITE-L1-DEGREE/EXPLORATION_LOG.md`
(D12 root read-only context; successes never enter the ladder).

## 2026-09-14 — D13 readiness D1301-D1310 (no execution)

### Authorization boundary

- This call was documentation-only (D1310B): two new record files in this directory
  (`READINESS_R1.md`, this log), one pointer append to the D12 log, and the
  D1304–D1310 checkbox update in the D13 OpenSpec `tasks.md`. It performed no code edit,
  no D13 execution, no decoder or scientific call, no root creation, no commit, no push.
- Branch `formal-ir-v72p1-addendum-clean` confirmed, no switch.
- The future D13 batch remains unauthorized. It requires a separate explicit batch
  grant naming batch/branch/root
  (`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`),
  seeds and budgets. No authorization was granted by readiness or by the R1310 review.

### D1301-D1309 evidence (trusted, not rerun)

- D1301: OpenSpec change `v72p2d13-l055-decoder-ladder` (4 files: `proposal.md`,
  `design.md`, `tasks.md`, `specs/l055-decoder-ladder/spec.md`) with packet §2 frozen
  verbatim, before behavior edits.
- D1302: selector `arm == L055 AND exact == false` over D12 `decoder_records.csv`,
  own recompute → 56 (n128 30, n256 26); all `iterations == 90`,
  `syndrome_ok == False`, `converged_no_syndrome`, `CHECK_UPDATED`; undetected 0;
  three-source corroboration (arm_summary/summary/direct audit);
  `selection_identities == FROZEN_IDENTITY_SET`, `validate_selection` empty.
- D1303: binder audit/import map in `design.md` §4 (D12 reconstruction + accepted
  D7-E RL90 / D7-D schedule binders; RL360 via `max_iter`; damping-0.7 existing
  param NOT tuned; flooding-360 accepted target); no decoder duplication.
- D1304–D1306: thin additive selector/replay/ladder/gate/verifier + runner
  (`v72p2d13_l055_decoder_ladder.py`, `scripts/v72p2d13_development.py`);
  plan-before-binding, first-mismatch block; default-false execution flag with
  pre-root/bind/Model-F refusal (rc=2); fresh never-overwrite minimal root.
- D1307–D1308: 16 focused fake tests, 16/16 PASS in own basetemp; `py_compile`
  3/3 PASS; broad suites declined per trust rule (D12+X3 88+8 adjudicated
  pre-existing/environmental, not D13-attributable).
- D1309: PLAN_ONLY ×2 rc=0 byte-identical (56 identities, plan 224, decoder 0);
  input root unchanged; future root absent before and after.

### D1310 verdict (independent reviewer-go, EVIDENCE_ACCESS VERIFIED)

- SELECTION/REPLAY/BINDINGS/GATES/BUDGETS/NO-PRODUCTION all PASS (see
  `READINESS_R1.md` evidence table).
- FINDINGS: BLOCKING none; non-blocking — (a) D1304–D1310 checkboxes flipped in
  this docs-only call after acceptance; (b) broad dirty worktree preserved, noted
  for awareness; (c) refusal-test vacuous second clause (test-isolation debt).
- VERDICT PASS_WITH_FINDINGS; recommendation
  `D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION`;
  decoder/scientific calls 0; no commit/push.

### Terminal

`D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION` — no D13
execution is authorized. D7-H, L2 and real data remain out of scope.

## 2026-09-14 — Main-thread readiness acceptance

- Accepted evidence: D1301–D1310 and independent review `D13-R1310`,
  `EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, BLOCKING none.
- Accepted terminal:
  `D13_L055_DECODER_LADDER_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- Carried to batch end: dirty-tree scope awareness and the refusal-test
  isolation debt. The D12+X3 combined-suite environmental failures remain
  outside the D13 gate.
- Authorization remains false. Decoder/scientific calls remain 0/0. The future
  result root remains absent. No commit or push is authorized.

## 2026-09-14 — D13 Batch A1 pre-dispatch (AUTHORIZED once)

Grant: batch `D13_L055_DECODER_LADDER_BATCH_A1`, branch
`formal-ir-v72p1-addendum-clean`, frozen inputs
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450` +
`workspace/v72p2d5_model_f_input/20260907_r1`, fresh root
`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
only; 56 failures + RL90 replay + 3 arms; ceilings 224 sci / 8 setup /
1800 s / 120 s / RSS<2GiB / 1 proc / no-retry. Track EXPLORE.

1. PASS — accepted marker `D13_L055_DECODER_LADDER_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
   present in `READINESS_R1.md:113` + `EXPLORATION_LOG.md:69` (+ memory hit);
   `D13-R1310` `EVIDENCE_ACCESS: VERIFIED`, VERDICT `PASS_WITH_FINDINGS`
   (`READINESS_R1.md:85,106-107`), BLOCKING none (`READINESS_R1.md:85`,
   `EXPLORATION_LOG.md:52,67`).
2. PASS — branch `formal-ir-v72p1-addendum-clean` exact, no switch. Scoped
   statuses only: 3 D13 files `??` untracked, OpenSpec D13 change `??`,
   D13 cycle docs `??`; zero tracked-file modifications in scope. Broad
   unrelated dirty tree preserved as-is, no repairs.
3. PASS — future root ABSENT (`ls: No such file or directory`). D12 six
   sha256 full-match D12-log record: arm `4d337efc…468868`, cmdlog
   `a5366e67…516ae2`, decoder `ac78c362…871b60`, graph `371fbbed…9beead61`,
   manifest `2090038a…7e7d1820f`, summary `96b8a06d…19870dba1`. Model-F
   present/unchanged: `cal_only true`, `decoder_calls 0`, npz
   `38e4bfba…280d345`, summary `ca67a953…fac1a43`.
4. PASS — own CSV recompute over D12 `decoder_records.csv`: 432 rows,
   selector `arm==L055 AND exact==False` → 56 (n128 30 / n256 26); all 56
   `iterations==90`, `syndrome_ok==False`, `converged_no_syndrome`,
   `CHECK_UPDATED`, `crash==False`; undetected (`exact False + syndrome
   True`) 0; L055 successes excluded 88.
5. PASS — `--plan-only` ×2: rc=0/rc=0, `cmp` BYTE_IDENTICAL, 56 identities,
   plan 224 (replay 56 + ladder 168), `decoder_calls` 0,
   `future_root_absent` True; future root still absent after (no write).
6. PASS (observed only) — scratch target `workspace/d13_a1_refusal_probe`
   (never future root): absent before; `--d13-batch` without
   `--execution-authorized` → rc=2, stderr `refusing --d13-batch: separate
   explicit user/main-thread authorization required…`; scratch target absent
   after; future root absent after.
7. PASS — `py_compile` 3/3 PASS; focused `pytest -p no:cacheprovider -o
   addopts=` with `--basetemp workspace/d13_a1_predispatch_tmp`
   (fresh, absent before): 42 passed (D13 16 + D12 26), `.venv/bin/python`.
   Adjudicated D12+X3 combined suite not rerun (no focused conflict).
8. PASS — frozen command string equals packet §5; arms RL360 a1 / RL360
   a0.7 / flooding-360 in frozen order; gates/budgets per packet §6 + spec
   (224/8/1800/120/RSS<2GiB/1-proc/no-retry); grant unconsumed (future root
   + refusal probe both absent; no D13 root content).

Pre-dispatch: 8/8 PASS. Proceeding to single authorized `--d13-batch`
invocation. No repair/clean/retry/substitution performed.

## 2026-09-14 — D13 Batch A1 run evidence (AUTHORIZED once, evidence only)

COMMAND (exact, once):
`.venv/bin/python scripts/v72p2d13_development.py --d13-batch
--execution-authorized --model-f-root
workspace/v72p2d5_model_f_input/20260907_r1 --out-root
workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
EXIT 0. Start 2026-09-14T14:31:32Z, select 2026-09-14T22:31:35 local
(`selected 56 frozen L055 failures (n128=30 n256=26)`), end
2026-09-14T14:46:36Z. GRANT_CONSUMED at command start; no second run, no
repair/rerun/resume/retry/seed-search/tuning/input change.

CALLS/RESOURCES vs ceilings: scientific 224/224 (replay 56 + ladder 168);
setup 2/8; wall 869.161 s ≤1800 (external 15:04.12 incl. interpreter);
per-call max 8.297 s (mean 3.880) ≤120; peak_rss 125267968 B
<2147483648 (external max RSS 122332 kB); 1 process; `budget_violations []`.
`blocked: null`, `engineering_reason: ""`.

REPLAY (strict RL90, `replay_records.csv` 56 rows): `match True` 56/56,
mismatches 0, `mismatch_field` empty all rows; all replays `exact False`,
`syndrome_ok False`, `iterations 90`, `CHECK_UPDATED` (sample: 128 /
2026093001 / 2026093206 / 149, wall 0.765 s). First-mismatch gate never
triggered; all 168 ladder calls proceeded.

RESCUES (`ladder_records.csv` 168 rows; `is_rescue = exact AND syndrome
AND CHECK_UPDATED`; exact/syndrome/undetected kept separate; all 168 rows
`CHECK_UPDATED`, non-CHECK_UPDATED 0):
- `ROW_LAYERED_360_ALPHA_1`: 56 calls, rescues 3 (n128 1 / n256 2):
  (128,2026093006,2026093201,204,iter289), (256,2026093101,2026093308,151,
  iter254), (256,2026093106,2026093303,206,iter210). exact&syn(any prov) 3;
  undetected 0. Class MODEST_RESCUE (3 in 3..11, ≥1 each width).
  `mean_iter` 251.0 (stored).
- `ROW_LAYERED_360_ALPHA_0_7`: 56 calls, rescues 1 (n128 0 / n256 1):
  (256,2026093101,2026093308,151,iter295). exact&syn 1; undetected 0.
  Class NO_RESCUE (total ≤2). `mean_iter` 295.0 (stored).
- `FLOODING_360_ALPHA_1`: 56 calls, rescues 0 (0/0). exact&syn 0;
  undetected 0. Class NO_RESCUE. `mean_iter` null (stored).
RANKING: `[]` (no MATERIAL arm; frozen rule ranks MATERIAL only).
TERMINAL (stored): `D13_MODEST_DECODER_RESCUE` (evidence only; selects no
forward route, authorizes nothing further).

ROOT `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
(6 files) sha256: command_log `7821fb54…89b4abe`, ladder_records
`638bbf19…6a7fd`, manifest `41754964…24c2ce35`, replay_records
`24f05215…3db1888`, selection `0163f543…04df7613b`, summary
`da7afdfd…c7f93ba8729`. D12/Model-F inputs unmodified (read-only; no
status lines touched). No L2/D7-H/real-data path ran (`l1_only true`,
`batch_id d12-finite-l1-degree-v1`).

Next gate (main thread): one independent batch-end review with actual
artifact access (`EVIDENCE_ACCESS`) before any use. No commit or push
performed.

## 2026-09-14 — D13 Batch A1 batch-end review (VERIFIED PASS_WITH_FINDINGS)

REVIEW_ID `D13-B1-REVIEW`. EVIDENCE_ACCESS VERIFIED, branch confirmed no
switch.

- EVIDENCE: six root files sha256 full-match (command_log `7821fb54…`,
  ladder_records `638bbf19…` (169 lines = 168+header), manifest
  `41754964…`, replay_records `24f05215…` (57 = 56+header), selection
  `0163f543…` (57), summary `da7afdfd…`); single pass, timestamps
  22:31:35/22:46:36 local = 14:31:32–14:46:36Z consistent; EXIT 0
  corroborated; grant consumed, no resume/repair/rerun (blocked null,
  engineering_reason `""`).
- AUTHORIZATION PASS: frozen command run once; manifest.command omits
  runtime flag by design (FROZEN_COMMAND constant; D11/D12 precedent); no
  second root.
- IDENTITIES PASS: own D12 recompute 56 (30/26), all iter90/syndromeFalse/
  CHECK_UPDATED/converged_no_syndrome, undetected 0, 88 successes excluded;
  D12-set == selection.csv == each arm set (3×56).
- REPLAY PASS: 56/56 match True, 0 mismatch_field; all exact False/syndrome
  False/iter 90/CHECK_UPDATED; first-mismatch gate never triggered.
- RECOUNTS PASS (rescue = exact AND syndrome AND CHECK_UPDATED): RL360_a1
  56 calls rescues 3 (1/2): (128,3006,3201,204,i289),
  (256,3101,3308,151,i254), (256,3106,3303,206,i210), mean 251.0;
  RL360_a0.7 56 calls rescues 1 (0/1): (256,3101,3308,151,i295), mean
  295.0; FLOOD360 56 calls 0; undetected 0 all arms; all 224 rows
  CHECK_UPDATED; ladder non-rescue iters all 360 (164/164).
- CLASSES PASS: a1 MODEST, a0.7 NO, FLOOD360 NO, 0 MATERIAL/AMBIGUOUS;
  ranking `[]` correct; terminal D13_MODEST_DECODER_RESCUE ∈ frozen 7-set,
  follows.
- BUDGETS PASS: 224/224 (56+168), setup 2/8, wall 869.161/1800,
  per-call-max 8.297/120 mean 3.880, RSS 125267968<2GiB, 1 proc,
  violations `[]`.
- INPUTS/CEILING PASS: D12 six + Model-F sha full-match pre-dispatch;
  cal_only true, decoder_calls 0, l1_only true; claim ceiling intact; no
  L2/D7-H/real-data.
- NO-RETRY: single pass, unique identities, no dups, frozen order.
- FINDINGS: BLOCKING none; non-blocking (a) manifest.command flag omission
  by design (precedent family).
- VERDICT PASS_WITH_FINDINGS; recommendation
  D13_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION; no route/L2/
  D7-H/commit-push.

Close: grant consumed, no second run, no commit/push, memory triage
pending.

## 2026-09-14 — Main-thread result acceptance and route decision

- Accepted `D13-B1-REVIEW` (`EVIDENCE_ACCESS: VERIFIED`,
  `PASS_WITH_FINDINGS`, BLOCKING none) and stored result
  `D13_MODEST_DECODER_RESCUE` as valid L1-only synthetic evidence.
- Scientific interpretation: RL360 alpha=1 rescued 3/56; damping 0.7 rescued
  1/56; flooding-360 rescued 0/56. Longer iteration/schedule dynamics are a
  secondary effect, not the dominant explanation of the remaining L055
  failures. No decoder arm is selected and no rerun is authorized.
- Route: close the D13 ladder. Before further L1 or L2 optimization, correct
  the legacy production prior wiring, issue the immutable G2/X4 corrigendum,
  and reconcile row budgets with the actual synthetic generator entropy for
  both layers. D7-H remains closed because its alternating-transfer question
  is downstream of the unresolved channel/rate calibration and cannot repair
  the non-material L1 decoder rescue.
- Accepted terminal: `D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER`.
