# D11 canonical forward APP integration — EXPLORE log (append-only)

Cycle: `V72P2D11-FORWARD-APP` (successor of `V72P2D10-R3-FRESH-SCALING` route
`D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`).
Authority: `.workbuddy/tasks/D11_FORWARD_APP_INTEGRATION_READINESS_TASK_PACKET.md` §1–§4 (frozen).
This is the single append-only log root for D11 readiness. The future scientific batch
(if separately authorized) and its batch-end review append here; no per-arm documents.
Detail record: `READINESS_R1.md` in this directory.

## 2026-09-14 — D11 readiness D1101-D1110 (no execution)

### Authorization boundary

- This call was documentation-only (D1110B): two new record files in this directory
  (`READINESS_R1.md`, this log), one pointer append to the parent R3 log, and the
  D1110 checkbox update in the D11 OpenSpec `tasks.md`. It performed no code edit,
  no D11 execution, no decoder or scientific call, no root creation, no commit, no push.
- The future D11 batch remains unauthorized. It requires a separate explicit batch
  grant naming batch/branch/root
  (`workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`),
  seeds and budgets. No authorization was granted by readiness or by the R1110 review.

### D1101-D1109 evidence (trusted, not rerun)

- D1101: OpenSpec change `v72p2d11-forward-app` with equations, priorities, seeds, calls, terminals, rationale.
- D1102–D1106: thin additive plan/runner/verifier reusing D10 R2/R3 graph/decoder paths and canonical D5/D7 transfer + D6 oracle helpers (16/16 defs, 17/17 is-identical imports, no new message interface, reverse leg never invoked); default-false execution flag with pre-root/bind/Model-F refusal (exit 2, no-write); exact R3 L1 replay gate (n128 MIX `[4,4,2,5,3,5]`, n256 MIX `[6,3,5,5,6,4]`, CONTROL zeros, mismatch eng-blocked); call accounting + CHECK_UPDATED fail-close + gate priorities + conditional n256 + never-overwrite output + fail-closed read-only verifier.
- D1107–D1108: focused tests + `py_compile` in a fresh basetemp; production calls fake-injected.
- D1109: PROFILE_ONLY 36/36 (L2 12/12 + L1 24/24) A1–A6, plan 360/720, decoder 0, future root absent, 3.3 s.

### R1110 verdict/findings (trusted VERIFIED, not rerun)

- `REVIEW_ID D11-R1110`, `EVIDENCE_ACCESS VERIFIED`, `PASS_WITH_FINDINGS`, BLOCKING none.
- PASS: branch no-switch; reuse (16/16 defs, 17/17 imports, no reimplemented semantics, L1-seed-into-L2 refused, L2 DV3-only guard); replay (REPLAY_MIX verbatim, R3 shared refs, mismatch eng-blocked); isolation (one shared L2/pair across CONTROL/MIX/ORACLE, oracle once per cell riding MIX excluded from grading, exact/syndrome/joint distinct); gates (8-clause signal + both bottlenecks + ambiguous + priority + 8 terminals + conditional n256 + 360/720 identities); budgets (720/64/2400/120/2GiB/1-proc/no-retry in code+spec+manifest); no-production (v35 lazy-only, refusal precedes root/bind/Model-F-load, zero scientific calls, no D7-H). TEST_RERUN 33/33 own basetemp `/tmp/d11-r1110-review`.
- Non-blocking: (a) dirty worktree incl. 323-line v72p2d5 change adding kwargs to `_run_layered_block` that D11 depends on (`on_blocked_transfer="record"`) — reconfirm d5 tree state at Pre-EXECUTE; (b) operator `/tmp` basetemps adjudicated non-blocking (all claims independently re-verified); (c) 23 R3 tests not re-run (ceremonial per trust rule).

### Terminal

- `D11_FORWARD_APP_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no execution).
- Decoder calls 0; scientific calls 0; future root absent; no commit/push. Pre-EXECUTE must reconfirm the d5 tree state per finding (a).

## 2026-09-14 — main-thread readiness acceptance

Accepted as `D11_FORWARD_APP_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The R1110 reviewer evidence is trusted without rerun. Its d5 dirty-tree finding
is not waived: execution preflight must inspect the current `_run_layered_block`
signature/record-on-blocked semantics and re-run the focused D11 tests before
authorization consumption. No execution is authorized by this acceptance.

## 2026-09-14 — D11 Batch A1 pre-dispatch (AUTHORIZED once)

Grant: user turn 2026-09-14, D11_FORWARD_APP_BATCH_A1 exactly once, branch
`formal-ir-v72p1-addendum-clean`, root
`workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`, frozen
seeds/gates/budgets. No repair/rerun/retune/input change.

1. READINESS marker `D11_FORWARD_APP_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` present (READINESS_R1.md:67, this log:43, decision-log:101, memory:33); `D11-R1110` VERIFIED PASS_WITH_FINDINGS, BLOCKING none — PASS.
2. Branch `formal-ir-v72p1-addendum-clean` exact, no switch. Scoped D11/R2/R3/OpenSpec/cycle-docs paths: all untracked-additive (`??`, no tracked `M`), d5 dirty `M` carried as check-5 item; unrelated dirt preserved, no repairs — PASS.
3. Future root ABSENT (`ls: No such file or directory`). Model-F root present, `cal_only true`, `decoder_calls 0`, sha256 npz `38e4bfba…280d345` summary `ca67a953…fac1a43` match R3-log record. R3 six-file root sha256 full-match (prefixes `464931ba…`/`b1c72560…`/`f5838b2c…`/`0d4b6ea4…`/`88957763…`/`e363049c…`) — PASS.
4. Dump-from-module vs design: FROZEN_COMMAND MATCH (modulo `--execution-authorized` flag form); L1 seeds `2026092401..06`/`2026092501..06`, blocks `2026092601..12`/`2026092701..12`, L2 `2026092801..06`/`2026092901..06` MATCH; REPLAY `{128:(4,4,2,5,3,5),256:(6,3,5,5,6,4)}` MATCH; plan 360/720 MATCH; gates 9/6/4/3/3/18/18/3/6 MATCH; budgets 720/64/2400/120/2147483648/1-proc/no-retry MATCH; 8 terminals MATCH — PASS.
5. d5 `_run_layered_block(decode_fn,h1,h2,p1,p2,block,oracle,*,on_blocked_transfer='raise')`: kwarg present; `"record"` returns `transfer_invoked False` + `transfer_blocked_reason UnconditionedBeliefProvenanceError` with 1 decoder call (L1 only, no mixer/L2) — live probe RECORD_BEHAVIOR_OK; `d11.run_layered_block is d5._run_layered_block` True — PASS (finding (a) closed).
6. PROFILE_ONLY: 36/36 admitted, A1–A6 all true, plan 360/720, decoder 0, replacements 0, future_root_absent True, wall ~3.2 s; root still absent after — PASS.
7. Live refusal `--forward-batch` w/o flag on tmp target: rc2, `refusing --forward-batch` pre-root/bind/Model-F, tmp target never created, future root still absent — PASS.
8. `py_compile` 3/3 OK. Focused D11(33)+R3(23) in ONE fresh task-owned basetemp `-p no:cacheprovider -o addopts=`: R3-first order `56 passed`; note: D11-first order fails R3 `test_r3_unauthorized_batch_refuses_before_write_or_bind` on `v35 in sys.modules` (cross-test import pollution, pre-existing harness artifact, not code drift); R3-alone 23/23 incl. that test — PASS (with order note).
9. Full-tree 2172 dirty entries noted, no repairs; prior evidence (Model-F/R3 roots) hashes unchanged; no writes outside this log + task basetemps + check-7 tmp (removed) — PASS.

PRE_DISPATCH 9/9 PASS. Proceeding to the single authorized command.

## 2026-09-14 — D11 Batch A1 run evidence (AUTHORIZED once, raw)

COMMAND: `.venv/bin/python scripts/v72p2d11_development.py --forward-batch
--execution-authorized --model-f-root
workspace/v72p2d5_model_f_input/20260907_r1 --out-root
workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`
EXIT: 0. Start 2026-09-14T11:32:33Z, end 2026-09-14T11:43:58Z (log tz shows
19:32–19:43 local, same instant).

CALLS: scientific 720/720 ceiling; setup 62/64; planned 720, call_idx 0..719.
WALL 661.145/2400 s; PER-CALL max 1.833 (n256) / 0.964 (n128) ≤120 s;
RSS 137068544 < 2147483648 B; 1 process; budget_violations [].
ADMISSION: 36/36 ok (per width: 6 CONTROL-L1 + 6 MIX-L1 + 6 shared-L2).

L1 REPLAY vs R3 (MUST-equal): n128 MIX [4,4,2,5,3,5] CONTROL 0 — EQUAL
(pooled MIX L1 23, CONTROL 0); n256 MIX [6,3,5,5,6,4] CONTROL 0 — EQUAL
(pooled MIX L1 29, CONTROL 0). No engineering block.

PROVENANCE: 144+144 non-oracle transfers all invoked=True +
CHECK_UPDATED (fail list: none); oracle rows prov ORACLE; L1 prov
CHECK_UPDATED; transfers_blocked 0/0; all_check_updated true/true; crashes 0.

n128 (JM=22 JC=0 O=43): source exact M23/C0; target L2 exact M22/C0;
joint M[4,3,2,5,3,5] C[0]*6; synd==exact everywhere (pooled 209==209);
oracle O=43. Clauses: JM>=9 T; margin 22>=6 T; wins 6/6>=4 T; ge1 6/6>=3 T;
JC<=3 T; O>=18 T; 144 CHECK_UPDATED T; no violation T → D11_FORWARD_SIGNAL.
Paired: b=22 c=0 concord 50, McNemar one-sided 2.38e-07 (descriptive only).
n256 DISPATCHED (n128 signal, iff-gate satisfied).
n256 (JM=28 JC=0 O=64): source M29/C0; target M28/C0;
joint M[6,3,5,5,5,4] C[0]*6; oracle O=64. Clauses: 28>=9 T; 28>=6 T;
6/6 T; 6/6 T; 0<=3 T; 64>=18 T; 144 CHECK_UPDATED T → D11_FORWARD_SIGNAL.
Paired: b=28 c=0 concord 44, p=3.73e-09 (descriptive only).

TERMINAL (stored): `D11_FORWARD_APP_WIDE_RECOVERY` (both-signal route).
ROOT 6 files sha256: arm_summary `c6c0682f…106e`, command_log
`42bb6b91…5423`, decoder_records `b932f7d4…5f43`, graph_records
`60801c4b…0641`, manifest `c4e0092b…719e0`, summary `930d50c0…1a19`.
GRANT_CONSUMED. No D7-H/reverse/mixed-L2/real-data/FER/commit/push.
Evidence only: no route acceptance. Next gate (main thread): independent
EXPLORE batch-end review (EVIDENCE_ACCESS VERIFIED) + memory triage.

## 2026-09-14 — D11 Batch A1 batch-end review (VERIFIED PASS_WITH_FINDINGS)

REVIEW_ID D11-B1-REVIEW condensed. EVIDENCE_ACCESS VERIFIED, branch
`formal-ir-v72p1-addendum-clean` confirmed no switch.

- EVIDENCE_ACCESS VERIFIED: root six sha256 full-match (arm `c6c0682f…`,
  cmdlog `42bb6b91…`, decoder `b932f7d4…`, graph `60801c4b…`, manifest
  `c4e0092b…`, summary `930d50c0…`); single 8-line command_log pass (n128
  SIGNAL → n256 SIGNAL → terminal, calls=720 setup=62 wall 661.145);
  timestamps 19:32:35→19:43:58 local consistent ±2s; EXIT 0 corroborated.
- IDENTITIES PASS_WITH_FINDING F1 (non-blocking): 720 rows = 360/width
  (CONTROL 72+72, MIX 72+72, ORACLE 72 per width), crash 0, batch_id
  d11-forward-app-v1 uniform; frozen seeds only; F1 = call_idx stored
  per-width 0..359 (not global 0..719; summary first/last is global row
  position) — identities intact via unique (width,call_idx).
- ADMISSION PASS: 36/36 ok, A1-A6 true; L2 tables match; shared-L2 via one
  h2 per pair + identical cell keys (F4 non-blocking: no L2-seed column in
  decoder CSV; index-map + key equality is strongest schema permits).
- REPLAY PASS: n128 MIX [4,4,2,5,3,5]/C0 + n256 MIX [6,3,5,5,6,4]/C0 EQUAL
  R3; joint differs by one transfer loss per width (interpretation, not
  mismatch).
- PROVENANCE PASS: 288/288 non-oracle invoked+CHECK_UPDATED, fail list
  empty, blocked 0; oracle 144/144 ORACLE excluded from grading.
- ISOLATION PASS: own recount n128 CONTROL 0/0 MIX-L1 23 MIX-L2 22 ORACLE
  43; n256 0/0 29/28 64; pooled exact 209 == syndrome 209;
  exact-without-syndrome 0; joint n128 J_M22 [4,3,2,5,3,5] J_C0; n256 J_M28
  [6,3,5,5,5,4] J_C0; McNemar b22/c0 p2.38e-07 + b28/c0 p3.73e-09
  descriptive-only; undetected never success.
- GATES PASS: 8 clauses TRUE both widths (n128 22≥9/22≥6/6/6/6/6/0≤3/43≥18/
  144; n256 28≥9/28≥6/6/6/6/6/0≤3/64≥18/144); bottlenecks FALSE; priority
  yields SIGNAL/SIGNAL.
- DISPATCH PASS: n128 SIGNAL logged before n256 executed; widths [128,256]
  complete.
- TERMINAL PASS: D11_FORWARD_APP_WIDE_RECOVERY valid, follows; claim ceiling
  verbatim.
- BUDGETS PASS: 720/720, 62/64, wall 661.145/2400, per-call-max 1.833/120,
  iters ≤90, RSS 137068544<2GiB, 1 proc, violations [].
- NO-RETRY CONFIRMED; R3 ROOT UNTOUCHED (six sha full-match pre-dispatch
  record).
- CHECK-8 adjudication: R3-first 56-pass valid; D11-first pollution
  pre-existing harness order artifact, non-blocking.
- F2 (latent): verify_root global-vs-per-width index basis misaligned for
  future --verify — align when verify next touched; F3: manifest.command
  omits flag form by design; F5: document R3-first test ordering.
- VERDICT PASS_WITH_FINDINGS; recommendation
  D11_FORWARD_APP_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION; no
  edits/route/D7-H.

Close: grant consumed, no second run, no commit/push, memory triage pending.

## 2026-09-14 — main-thread D11 result acceptance and route

Accepted as `D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`.
The stored `D11_FORWARD_APP_WIDE_RECOVERY` remains immutable. MIX joint exact
tracks MIX L1 exact almost one-for-one (22/23 at n128; 28/29 at n256), all 288
transfers are CHECK_UPDATED, and oracle L2 is 43/72 and 64/72. The canonical
forward interface works; the dominant remaining loss is L1 failure, not a
reason to add reverse alternation.

Next is a small finite L1 degree refinement comparing only the D9-supported
λ2 values 0.45/0.50/0.55 on fresh graphs at n128/n256. D7-H remains closed;
mixed L2 and real-data claims remain out of scope. No D12 execution authorized.

## 2026-09-14 — D12 readiness pointer (no execution)

D12 readiness D1201–D1210 recorded its own log root at
`docs/research_cycles/V72P2D12-FINITE-L1-DEGREE/` (`READINESS_R1.md`,
`EXPLORATION_LOG.md`). Reviewer `D12-R1210`: `EVIDENCE_ACCESS VERIFIED`,
`VERDICT PASS`, BLOCKING none; terminal
`D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no
execution). D11 evidence stays immutable and is never pooled into D12 gates.
No D12 execution authorized.
