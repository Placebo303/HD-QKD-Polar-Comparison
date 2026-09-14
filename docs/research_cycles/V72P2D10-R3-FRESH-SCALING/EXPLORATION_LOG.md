# D10 R3 fresh-graph scaling — EXPLORE log (append-only)

Cycle: `V72P2D10-R3-FRESH-SCALING` (successor of `V72P2D10-MIXED-DEGREE-L1` A1).
Authority: `.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md` §1–§4 (frozen).
This is the single append-only log root for R3 readiness. The future scientific batch
(if separately authorized) and its batch-end review append here; no per-arm documents.

## 2026-09-14 — R3 readiness R301-R310 (no execution)

### Authorization boundary

- This call was documentation-only (R310B): two new record files in this directory,
  one pointer append to the parent L1 log, and R302–R310 checkbox updates in the R3
  OpenSpec `tasks.md`. It performed no code edit, no `--r3-batch`, no decoder or
  scientific call, no root creation, no commit, no push.
- The future R3 batch remains unauthorized. It requires a separate explicit
  authorization naming batch/branch/root
  (`workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`),
  seeds and budgets. No authorization was granted by readiness or by the R310 review.

### R301–R309 evidence (trusted, not rerun)

- R301: OpenSpec change `v72p2d10-r3-fresh-graph-scaling` (4 files).
- R302–R306: 3 new additive code files reusing R2 construction/decoder path;
  `--r3-batch` default-false refusal before root/decoder/Model-F; A1–A6 gate;
  144/width conditional-288 plan with A1 non-pooling; never-overwrite root with
  fail-closed verifier.
- R307–R308: 23 focused tests; `py_compile` OK; broad suites deferred per trust rule.
- R309: no-decoder PROFILE_ONLY 24/24 A1–A6, zero replacements, deterministic replay,
  future root absent (~2.2 s).

### R310 verdict/findings (trusted VERIFIED, not rerun)

- `REVIEW_ID D10-R3-R310`, `EVIDENCE_ACCESS VERIFIED`, pass-with-comments, no blocking.
- PASS: seed separation (48 fresh seeds + UUID isolated from A1/R1/R2); admission
  (independent 24/24 recompute, wall 7.07 s); gates/terminals verbatim; budgets static;
  no-production (no v35 import/load, A1 mtimes unchanged, future root absent);
  reuse (delegate to R2, additive footprint only, R2/A1 diffs empty).
- Non-blocking: (a) unrelated dirty-worktree mods — future commit scoped to additive
  paths only; (b) deferred live refusal + fresh-basetemp pytest run once at authorized
  execution.

### Terminal

- `D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no execution).
- Decoder calls 0; scientific calls 0; future root absent; no commit/push.

## 2026-09-14 — main-thread readiness acceptance

Accepted as
`D10_R3_FRESH_GRAPH_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The R310 independent review is trusted without duplicate testing. Its two
non-blocking notes are carried to execution preflight: scope any future commit
to additive paths and run the deferred live refusal plus focused pytest once.
No R3 execution is authorized by this acceptance.

## 2026-09-14 — R3 Batch A1 pre-dispatch (AUTHORIZED once)

- Grant: user authorized `D10_R3_FRESH_GRAPH_SCALING_BATCH_A1` exactly once;
  branch `formal-ir-v72p1-addendum-clean`; root
  `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`;
  n128 graphs 2026092401..06 + blocks 2026092601..12; conditional n256 graphs
  2026092501..06 + blocks 2026092701..12 iff n128 R3_REPRODUCED; budgets
  <=288 scientific / <=50 setup / <=1800s wall / <=120s per-call /
  RSS <2147483648 / one process. HEAD `278fdf07`.
- 1. READINESS MARKER PASS: exact string
  `D10_R3_FRESH_GRAPH_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
  present 1x each in READINESS_R1.md, AGENT_PROJECT_MEMORY.md,
  docs/decision-log.md; R310 `REVIEW_ID D10-R3-R310 EVIDENCE_ACCESS VERIFIED`
  pass-with-comments, no blocking.
- 2. BRANCH/SCOPE PASS: branch `formal-ir-v72p1-addendum-clean`; zero tracked
  modifications in scope (all scoped R3/R2/OpenSpec/cycle-doc/packet paths are
  untracked-additive `??`, no `M`); unrelated dirt preserved untouched
  (e.g. pre-existing `M workspace/pytest-evidence-test/output/...`).
- 3. ROOTS PASS: future root ABSENT (`ls: cannot access ... No such file or
  directory`); Model-F root present, `cal_only true`, `decoder_calls 0`,
  sha256 npz `38e4bfba...280d345` summary `ca67a953...fac1a43`; A1 root
  unchanged — all six sha256 match A1 log record
  (`26bd36d2… dbe271b8… c678d00e… 87c4837a… bc2ac507… 98f0f75a…`).
- 4. FROZEN-CONTRACT MATCH: ARMS `(PEG_DV3_MATCHED, PEG_DV23_LAM2_045)`;
  GRAPH 128 `2026092401..06` / 256 `2026092501..06`; BLOCK 128
  `2026092601..12` / 256 `2026092701..12`; degree cells DV3-n128 m118 E384
  `3^88+4^30`, DV3-n256 m236 E768 `3^176+4^60`, MIX-n128 n2=71 n3=57 E313
  `2^41+3^77`, MIX-n256 n2=141 n3=115 E627 `2^81+3^155`; decoder max_iter=90
  damping=1.0 (r2 reuse); gates `(18,12,5,4,6)+(6,3)` verbatim; plan 144/144
  max 288, n128-first, MATCHED-first, call_idx 0..143/0..287; budgets
  288/50/1800/120/2147483648/1-proc; terminals six frozen names; FROZEN_COMMAND
  matches packet command (packet adds `--execution-authorized`).
- 5. PROFILE_ONLY PASS: 24/24 admitted (6 per arm x width), all A1–A6 true,
  `replacement_seeds_used 0`, `seed_replacements []`, `frozen_seed_failures []`,
  stdout only; future root still absent after.
- 6. REFUSAL PASS: `--r3-batch --out-root /tmp/d10_r3_refusal_probe_4d39ed0e`
  (no `--execution-authorized`) → `refusing --r3-batch: ...` rc=2; tmp target
  absent after; future root still absent.
- 7. TESTS PASS: `py_compile` OK (R3 module/runner/test); pytest
  `test_v72p2d10_r3_fresh_scaling.py` (23) +
  `test_v72p2d10_mixed_degree_l1_r2.py` (18) = 41 passed in fresh basetemp
  `workspace/d10_r3_predispatch_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
  (`-p no:cacheprovider -o addopts=`).
- 8. NO-TOUCH PASS: `--r3-batch`/`--execution-authorized` both default false;
  only writes: this log append + gitignored basetemp; HEAD unchanged
  `278fdf07`; no commit/push.
- PRE-DISPATCH 8/8 PASS. Proceeding to single authorized execution.

## 2026-09-14 — R3 Batch A1 authorized run evidence (raw)

- COMMAND: `.venv/bin/python scripts/v72p2d10_r3_development.py --r3-batch
  --execution-authorized --model-f-root
  workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
  (exact frozen command, run once).
- EXIT 0. START_UTC 2026-09-14T08:37:35Z (epoch 1789375055) → END_UTC
  2026-09-14T08:43:01Z (epoch 1789375381). Runner wall_s 316.629 (<=1800).
- CALLS scientific 288/288; SETUP 50/50 (=24 graph builds + 24 width-block
  samples + Model-F load + plan build); PER-CALL-MAX 1.9954 s (<=120);
  PEAK_RSS 125063168 B (<2147483648); processes 1; `budget_violations []`;
  no retry/resume/repair/seed-search/adaptation.
- ADMISSION: 24/24 graphs admitted (6 per arm x width), zero replacements;
  Model-F prior loaded from CAL-only root; 12 matched blocks sampled per width.
- N128 EXACT pools: M=23 C=0; per-pair MIX [4,4,2,5,3,5], DV3 [0,0,0,0,0,0];
  wins 6/6, graphs>=2 6/6. Gate clauses: (1) 23>=18 T; (2) 23>=12 T;
  (3) 6>=5 T; (4) 6>=4 T; (5) 0<=6 T; (6) no-eng-violation T →
  `R3_REPRODUCED(n128)`.
- N256 DISPATCHED (n128 REPRODUCED, iff-condition met). N256 EXACT pools:
  M=29 C=0; per-pair MIX [6,3,5,5,6,4], DV3 [0,0,0,0,0,0]; wins 6/6,
  graphs>=2 6/6. Clauses: (1) 29>=18 T; (2) 29>=12 T; (3) 6>=5 T; (4) 6>=4 T;
  (5) 0<=6 T; (6) T → `R3_REPRODUCED(n256)`.
- SYNDROME-VALID pools (separate, never substituted): n128 MIX 23 / DV3 0;
  n256 MIX 29 / DV3 0; total exact 52 = syndrome-valid 52; statuses
  `converged_exact` 52 + `converged_no_syndrome` 236; crash 0; rows 288
  (call_idx 0..143 per width, batch_id `d10-r3-fresh-v1` uniform).
- TERMINAL stored: `D10_R3_WIDE_L1_SIGNAL_REPRODUCED` (both REPRODUCED;
  evidence only, no route acceptance, no D7-H, claim ceiling unchanged).
- ROOT files + sha256 (six-file evidence root):
  `arm_summary.csv 464931ba…bf91`, `command_log.txt b1c72560…93892`,
  `decoder_records.csv f5838b2c…6731d`, `graph_records.csv 0d4b6ea4…f6ea5`,
  `manifest.json 88957763…fee61c7`, `summary.json e363049c…896ecb018`.
- GRANT_CONSUMED (single authorized invocation; no second run, no repair/rerun).
  No commit/push. Next required: one independent EXPLORE batch-end review with
  `EVIDENCE_ACCESS: VERIFIED` before any use of this evidence.

## 2026-09-14 — R3 Batch A1 batch-end review (VERIFIED PASS)

- REVIEW_ID `D10-R3-B1-REVIEW`; EVIDENCE_ACCESS VERIFIED; branch
  `formal-ir-v72p1-addendum-clean` confirmed, no switch.
- Six root files sha256 full-match operator hashes: arm_summary
  `464931ba…`, command_log `b1c72560…`, decoder_records `f5838b2c…`,
  graph_records `0d4b6ea4…`, manifest `88957763…`, summary `e363049c…`;
  single 8-line command_log pass (n128 REPRODUCED M=23 C=0 → n256 REPRODUCED
  M=29 C=0 → terminal, calls=288 setup=50 wall 316.629); timestamps
  consistent (2s startup delta benign); EXIT 0 corroborated.
- IDENTITIES PASS: 288 rows = 144/width, call_idx 0..143/width, crash 0,
  batch_id `d10-r3-fresh-v1` uniform, 288/288 unique keys, MATCHED-first
  order, paired blocks 12 rows per (width,block); frozen 36 seeds only.
- ISOLATION PASS: R3 seeds absent from A1 root and vice versa; A1 six sha256
  unchanged.
- ADMISSION PASS: stored 24/24 + independent rebuild with own
  union-find/Kuhn/GF32/replay 24/24 all-true; degree cells match frozen tables.
- SEPARATION PASS: per-graph exact==syndrome every cell; pools n128 23/0 n256
  29/0; exact 52 = syndrome 52; converged_exact 52 + no_syndrome 236;
  residual 0; undetected never success.
- GATES PASS: N128 clauses Tx6 (M23, margin 23, wins 6/6, >=2 6/6, C0) →
  REPRODUCED; N256 Tx6 (M29, margin 29, 6/6, 6/6, C0) → REPRODUCED; McNemar
  descriptive-only (1.19e-07/1.86e-09); A1 non-pooling holds (boundary + no A1
  tags; "A1" strings are predicate names/decl only).
- DISPATCH PASS: n128 classified before n256 executed; widths [128,256]
  complete; conditional satisfied.
- TERMINAL PASS: `D10_R3_WIDE_L1_SIGNAL_REPRODUCED` valid both-REPRODUCED
  term; claim L1-only synthetic.
- BUDGETS PASS: 288/288, 50/50, wall 316.629/1800, per-call-max 1.9954/120,
  RSS 125063168<2GiB, 1 process, violations [].
- NO-RETRY: single pass, unique identities, frozen seeds, empty
  failure_reasons, frozen decoder settings.
- FINDINGS: BLOCKING none; non-blocking (48-vs-36 seed wording benign;
  manifest.command omits flag by design; wall deltas both under ceiling;
  unrelated dirt untouched).
- VERDICT PASS; recommendation
  `D10_R3_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; no
  edits/route/D7-H.
- Close: grant consumed, no second run, no commit/push, memory triage pending.

## 2026-09-14 — main-thread R3 result acceptance and route

Accepted as `D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`.
The stored `D10_R3_WIDE_L1_SIGNAL_REPRODUCED` remains the immutable machine
terminal. Across fresh graphs, MIX recovered 23/72 at n128 and 29/72 at n256,
versus DV3 0/72 at both widths; all frozen gates and independent review passed.

The next orthogonal question is whether this established L1 signal survives a
single canonical forward L1→L2 APP integration. D11 must pair a mixed-L1 arm
against a DV3-L1 control while holding one connected full-rank DV3 L2 graph
fixed within each graph/block pair, and include a shared L2-oracle diagnostic.
D7-H remains closed: alternation is not interpretable before ordinary forward
transfer and the L2 code ceiling are separated. No D11 execution is authorized.

## 2026-09-14 — D11 forward-APP readiness pointer (no execution)

- D11 readiness D1101–D1110 recorded in `docs/research_cycles/V72P2D11-FORWARD-APP/`
  (`READINESS_R1.md` + `EXPLORATION_LOG.md`); R1110 VERIFIED PASS_WITH_FINDINGS,
  BLOCKING none; terminal `D11_FORWARD_APP_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- This append is a pointer only; R3 evidence above is unchanged. Pre-EXECUTE must
  reconfirm the v72p2d5 dirty-tree state carried by R1110 finding (a).
