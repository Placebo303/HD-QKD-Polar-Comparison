# D12 finite L1 degree refinement — EXPLORE log (append-only)

Cycle: `V72P2D12-FINITE-L1-DEGREE` (successor refinement; NOT a correction of any predecessor).
Authority: `.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md` §1–§4 (frozen).
This is the single append-only log root for D12 readiness. The future scientific batch
(if separately authorized) and its batch-end review append here; no per-arm documents.
Detail record: `READINESS_R1.md` in this directory.

## 2026-09-14 — D12 readiness D1201-D1210 (no execution)

### Authorization boundary

- This call was documentation-only (D1210B): two new record files in this directory
  (`READINESS_R1.md`, this log), one pointer append to the D11 log, and the
  D1210 checkbox update in the D12 OpenSpec `tasks.md`. It performed no code edit,
  no D12 execution, no decoder or scientific call, no root creation, no commit, no push.
- The future D12 batch remains unauthorized. It requires a separate explicit batch
  grant naming batch/branch/root
  (`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`),
  seeds and budgets. No authorization was granted by readiness or by the R1210 review.

### D1201-D1209 evidence (trusted, not rerun)

- D1201: OpenSpec change `v72p2d12-finite-l1-degree` (4 files: `proposal.md`,
  `design.md`, `tasks.md`, `specs/finite-l1-degree/spec.md`) with packet §2 frozen
  verbatim, before behavior edits.
- D1202: D9 exact realization audit + D10 R2/R3 construction, prior and decoder
  path import map; no duplicate framework or message semantics.
- D1203–D1206: thin additive plan/runner/verifier (3 new code files + R2/R3 reuse)
  with frozen tables, seeds, 432 identities, gates, ranking and terminals;
  default-false execution flag with pre-root/bind/Model-F refusal (exit 2, no-write);
  36-graph A1–A6 gate with zero replacements; never-overwrite root + fail-closed
  read-only verifier.
- D1207–D1208: focused tests + `py_compile` in fresh basetemps; production calls
  fake-injected (D12 26/26 + R2/R3 41/41).
- D1209: PROFILE_ONLY 36/36 A1–A6, plan 432, decoder 0, deterministic replay
  identical, zero replacements, future root absent, ~2.35 s.

### R1210 verdict/findings (trusted VERIFIED, not rerun)

- `REVIEW_ID D12-R1210`, `EVIDENCE_ACCESS VERIFIED`, `VERDICT PASS`, BLOCKING none.
- PASS: branch no-switch; degree math (all six cells recomputed from D9 rule, socket
  balance, min dc 2 max 3); admission (36/36 A1–A6, zero replacements, replay
  identical ~2.38 s; n128 comp1/118/118/4cyc0/girth6–10; n256 comp1/236/236;
  L050-2026093101 4cyc1/girth4 retained diagnostics-only; L055 girth ≤14);
  isolation (one shared builder, `dispatch_l1` is R2 `dispatch_l1`,
  exact/syndrome separate, exact-only tallies + `batch_id` gate, D11/A1/R3 unpoolable);
  gates (STABLE/MATERIAL-4-clause/ranking/retain/SPLIT/five terminals/eng-override,
  all edges incl. ties; McNemar descriptive-only); budgets
  (432/62/1800/120/2GiB/1-proc/no-retry in code+spec; refusal exit 2 pre-root/bind/Model-F;
  `py_compile` PASS); no-production (zero v35 import, D11 root untouched,
  additive-only, decoder/scientific 0). TEST_RERUN 67 total (D12 26/26 + R2/R3 41/41 = 18+23).
- Non-blocking: (a) broad dirty worktree (reconfirm at execution preflight);
  (b) "41" label = 18+23; (c) wall gate applies at execution.

### Terminal

- `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no execution).
- Decoder calls 0; scientific calls 0; future root absent; no commit/push.
- No execution is authorized by this readiness.

## 2026-09-14 — main-thread readiness acceptance

Accepted as
`D12_FINITE_L1_DEGREE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The D12-R1210 independent evidence is trusted without duplicate testing. The
L050/n256 seed 2026093101 four-cycle is retained as frozen diagnostic evidence,
not repaired or replaced. Execution preflight must reconfirm scoped dirty-tree
state. No execution is authorized by this acceptance.

## 2026-09-14 — D12 Batch A1 pre-dispatch (AUTHORIZED once)

Grant: user one-time grant this turn; batch A1; branch
`formal-ir-v72p1-addendum-clean`; root
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`;
arms L045/L050/L055; n128 graphs 2026093001..06 + blocks 2026093201..12;
n256 graphs 2026093101..06 + blocks 2026093301..12; budgets
432/62/1800s/120s/RSS<2147483648/1-proc. 8/8 PASS, grant consumed at
Phase-2 command start.

1. ACCEPTED marker present: `rg` hits READINESS_R1.md:138 +
   EXPLORATION_LOG.md:65
   (`D12_FINITE_L1_DEGREE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`);
   D12-R1210 `EVIDENCE_ACCESS VERIFIED`, `VERDICT PASS`, BLOCKING none
   (READINESS_R1.md:87, EXPLORATION_LOG.md:41). PASS.
2. Branch exact `formal-ir-v72p1-addendum-clean`, no switch. Scoped status:
   3 D12 files + R2/R3 modules/runners/tests + OpenSpec D12 change + D12
   cycle docs all `??` untracked (readiness additive, uncommitted, no commit
   requested); zero tracked-file modifications in scope; broad unrelated dirt
   preserved as-is, no repairs. PASS (matches R1210 non-blocking finding a).
3. Future root ABSENT (`ls: No such file or directory`). Model-F root
   present: `cal_only true`, `decoder_calls 0`, sha256 npz
   `38e4bfba…280d345` summary `ca67a953…fac1a43` match R3-log record. D11
   six sha full-match log prefixes (`c6c0682f…106e`/`42bb6b91…5423`/
   `b932f7d4…5f43`/`60801c4b…0641`/`c4e0092b…719e`/`930d50c0…1a19`); R3 six
   sha full-match (`464931ba…bf91`/`b1c72560…93892`/`f5838b2c…6731d`/
   `0d4b6ea4…f6ea5`/`88957763…fee61c7`/`e363049c…896ecb018`). PASS.
4. Module-vs-OpenSpec MATCH per item: DEGREE_TABLE six cells EXACT
   (L045-128 71/57/313 2^41+3^77; L050-128 77/51/307 2^47+3^71; L055-128
   83/45/301 2^53+3^65; L045-256 141/115/627 2^81+3^155; L050-256
   154/102/614 2^94+3^142; L055-256 166/90/602 2^106+3^130); GRAPH_SEEDS
   2026093001..06/2026093101..06; BLOCK_SEEDS 2026093201..12/2026093301..12;
   432 identities (216/width); ARMS L045/L050/L055; D12_WIDTHS (128,256);
   gates STABLE 18/5+, MATERIAL margin 6/pair-wins 4, SPLIT beat 6/trail 2,
   ranking total→worst-width→smaller-λ2, five terminals incl.
   `D12_FINITE_DEGREE_SPLIT_AMBIGUOUS`; budgets 432/62/1800.0/120.0/RSS-reuse;
   FROZEN_COMMAND string equals grant command; FUTURE_ROOT equals grant root.
   PASS.
5. PROFILE_ONLY: 36/36 admitted, all six A1–A6 true ×36; two consecutive runs
   identical (excl. wall); seed_replacements [] / 0; frozen_seed_failures [];
   plan_calls 432 (216/width); decoder_calls 0; future_root_absent True;
   wall ~2.4–2.5 s; L050/256/2026093101 four_cycles=1 retained; root still
   absent after. PASS.
6. Unauthorized `--d12-batch` (tmp target `workspace/d12_tmp_refusal_probe`,
   never future root): stdout refusal pre-auth, RC=2, tmp target still absent
   after (no write/bind/Model-F-load). PASS.
7. py_compile PASS (3 D12 files) + 67 passed in ONE fresh basetemp
   `workspace/d12_a1_predispatch_tmp` (`-p no:cacheprovider -o addopts=`,
   `.venv/bin/python`): D12 26/26 + R2 18 + R3 23 (41 labeled 18+23). PASS.
8. `--d12-batch` store_true default false; `--execution-authorized`
   store_true default False; HEAD unchanged `278fdf0`; future root +
   refusal tmp both absent; D11/R3/Model-F roots untouched (no status
   lines); no other writes. PASS.

## 2026-09-14 — D12 Batch A1 run evidence (AUTHORIZED once, evidence only)

COMMAND (exact, once):
`.venv/bin/python scripts/v72p2d12_development.py --d12-batch
--execution-authorized --model-f-root
workspace/v72p2d5_model_f_input/20260907_r1 --out-root
workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
EXIT 0. Start 2026-09-14T12:49:56Z, end 2026-09-14T12:54:54Z (local log
20:49:57→20:54:54; UTC+8). GRANT_CONSUMED at command start; no second run,
no repair/rerun/replacement-search/tuning/input change.

CALLS/RESOURCES vs ceilings: scientific 432/432; setup 62/62 (=36 graph
builds + 24 block samples + 2); wall 290.154 s ≤1800; per-call max 1.689 s
(mean 0.666) ≤120; peak_rss 128274432 B <2147483648; 1 process; no
retry/resume/repair/seed-search; budget_violations []. ADMISSION 36/36
(log `built 36 graphs admitted=36`).

EXACT pools (72 each): n128 L045 26 / L050 39 / L055 42; n256 L045 33 /
L050 35 / L055 46; total exact 221/432. Per-graph exact vectors: n128 L045
[6,3,2,5,4,6] L050 [7,4,5,7,7,9] L055 [7,7,5,8,7,8]; n256 L045
[6,6,4,6,5,6] L050 [6,6,6,6,4,7] L055 [7,9,7,8,8,7]. SYNDROME_OK pools
identical cell-for-cell (221 total; exact==syndrome every cell).
UNDETECTED 0 in all six cells (syndrome_ok & ~exact = 0). Status:
converged_exact 221 + converged_no_syndrome 211; crash 0; batch_id
`d12-finite-l1-degree-v1` uniform 432/432; block pairing 12/block-set per
(width,graph,arm) enforced by verifier.

PAIRED challenger-vs-L045 discordances: n128 L050 17/4 (concord 51,
trials 21) / L055 20/4 (concord 48, trials 24); n256 L050 5/3 (concord 64,
trials 8) / L055 13/0 (concord 59, trials 13); pooled L050 22/7 / L055
33/4. McNemar p descriptive-only (no gating).

CLAUSES (module-gate recompute, booleans): STABLE all six True (n128
26/6,39/6,42/6; n256 33/6,35/6,46/6 — pool/graphs≥2). MATERIAL clauses:
n128-L050 T/T/T/T (margin 13, cord 17>4, wins 6); n256-L050
stable-T/margin-2-F/cord-5>3-T/wins-2-F; n128-L055 T/T/T/T (margin 16,
cord 20>4, wins 6); n256-L055 T/T/T/T (margin 13, cord 13>0, wins 6).
MATERIAL_BETTER L050 False / L055 True. SPLIT_WIDTH_CONFLICT False
(no ≥6-beat with >2-trail; both widths prefer L055). Ranking clause not
triggered (single winner). ROUTE recompute `D12_SELECT_L055` = stored
terminal. TERMINAL: `D12_SELECT_L055` (evidence only; selects nothing
forward, authorizes no next route).

VERIFY (read-only): `checked_calls=432 agreements=432 skipped=0
violations=0`, VERIFY PASS, RC=0.

ROOT six files sha256: arm_summary `4d337efc…468868`, command_log
`a5366e67…516ae2`, decoder_records `ac78c362…871b60`, graph_records
`371fbbed…9beead61`, manifest `2090038a…7e7d1820f`, summary
`96b8a06d…19870dba1`.

NOTE (raw, non-blocking, D11-F1 pattern): `call_idx` stored per-width
0..215; 432 unique (width,call_idx) keys; summary call_idx_first/last
0/431 are global plan positions. Identities intact (216/width,
frozen seeds only, 12 paired blocks per pair, uniform batch_id).

Next gate (main thread): one independent EXPLORE batch-end review with
`EVIDENCE_ACCESS: VERIFIED` before any use. No forward/L2, D7-H,
real-data, claim-calc, commit or push performed.

## 2026-09-14 — D12 Batch A1 batch-end review (VERIFIED PASS_WITH_FINDINGS)

REVIEW_ID D12-B1-REVIEW. EVIDENCE_ACCESS VERIFIED, branch confirmed no switch
(`formal-ir-v72p1-addendum-clean`).
- Six root files sha256 full-match operator hashes (arm `4d337efc…`,
  cmdlog `a5366e67…`, decoder `ac78c362…`, graph `371fbbed…`, manifest
  `2090038a…`, summary `96b8a06d…`); single 8-line linear command_log pass
  20:49:57→20:54:54 local; EXIT 0 operator-reported, corroborated by complete
  artifacts (no exit stored in root).
- COMPLETENESS/IDENTITIES PASS: 432 rows = 216/width = 72/arm/width; unique
  (width,arm,graph,block) 432/432; crash 0; batch_id
  `d12-finite-l1-degree-v1` uniform; call_idx per-width 0..215 (summary
  first/last 0/431 global positions; D11-F1 pattern, identities intact);
  frozen 36 seeds only (12 graph + 24 block; "48" brief label arithmetic-only).
- DEGREE/ADMISSION PASS: 36/36 admitted A1-A6 true; six cells EXACT vs frozen;
  L050/n256-2026093101 four-cycle retained (diagnostics-only).
- ISOLATION PASS: exact 221 = syndrome 221 cell-for-cell; undetected 0 all
  cells; converged_exact 221 + no_syndrome 211; undetected never success.
- PAIRED PASS (own recompute, all match): vectors n128 L045 [6,3,2,5,4,6]=26
  L050 [7,4,5,7,7,9]=39 L055 [7,7,5,8,7,8]=42; n256 L045 [6,6,4,6,5,6]=33
  L050 [6,6,6,6,4,7]=35 L055 [7,9,7,8,8,7]=46; total 221; discordances n128
  L050 17/4 L055 20/4, n256 L050 5/3 L055 13/0, pooled 22/7 + 33/4; margins
  +13/+16/+2/+13; wins n128 6/6+6/6, n256 2/6+6/6; McNemar descriptive-only.
- SELECTION PASS: STABLE all six True; MATERIAL n128-L050 TTTT, n256-L050
  T/F/T/F, n128-L055 TTTT, n256-L055 TTTT → L050 False, L055 True; ranking
  correctly skipped; SPLIT False; terminal routing → D12_SELECT_L055 = stored.
- TERMINAL/BUDGETS PASS: 432/432, 62/62, wall 290.154/1800, per-call-max
  1.689/120 mean 0.666, RSS 128274432<2GiB, 1 proc, violations []; frozen
  decoder settings; claim ceiling finite-L1 only.
- PREDECESSORS untouched: D11/R3 six-hash full-match; Model-F sha match.
- NO-RETRY: single pass, unique identities, zero replacements, setup exactly 62.
- FINDINGS: BLOCKING none; non-blocking (48-vs-36 seed label; 1s start skew;
  manifest.command omits flag by design; call_idx per-width already logged).
- VERDICT PASS_WITH_FINDINGS; recommendation
  D12_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION; no
  route/forward-L2/D7-H.

Close: grant consumed, no second run, no commit/push, memory triage pending.

## 2026-09-14 — main-thread D12 result acceptance and route

Accepted as `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`; stored terminal
`D12_SELECT_L055` remains immutable. L055 is MATERIAL_BETTER at both widths
(42/72 vs 26/72 at n128; 46/72 vs 33/72 at n256). L050 is not selected.

All 56 L055 failures reached iteration 90, while successes converged in 7--50
iterations. Before broadening the degree grid, D13 will replay only these frozen
failures and test three stronger decoder dynamics. This isolates decoder
truncation/schedule from code construction at ≤224 calls. D7-H, L2 and real
data remain out of scope; no D13 execution is authorized.

## 2026-09-14 — D13 readiness pointer (docs-only, no execution)

D13 readiness D1301–D1310 is recorded in
`docs/research_cycles/V72P2D13-L055-LADDER/READINESS_R1.md` (+ log root entry in
that directory's `EXPLORATION_LOG.md`). Independent R1310 review:
EVIDENCE_ACCESS VERIFIED, VERDICT PASS_WITH_FINDINGS, BLOCKING none; terminal
`D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
This D12 log is unchanged context (root read-only, `D12_SELECT_L055` immutable,
successes never enter the ladder); the future D13 batch needs a separate
explicit grant. No D13 execution authorized; no commit/push.
