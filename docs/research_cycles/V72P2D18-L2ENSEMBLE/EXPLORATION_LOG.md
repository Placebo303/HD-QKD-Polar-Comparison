# D18 Current-Channel L2 Ensemble DE — EXPLORE log (append-only)

- Authority: `.workbuddy/tasks/D18_L2_ENSEMBLE_DE_READINESS_R1_TASK_PACKET.md`
  (§§1–10, §10 return contract).
- Track: documentation-only (no code, no DE/decoder execution, no root
  creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This is the single append-only log root for D18. Detail record:
  `READINESS_R1.md` in this directory.
- Predecessor pointer: `docs/research_cycles/V72P2D16-MATCHED-BACKOFF/EXPLORATION_LOG.md`
  (D16 accepted `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`;
  route pauses L1 construction/decoder investment for current-channel L2 ensemble DE).
- This call (D18 close-docs): documentation-only close (two new record files
  in this directory, one pointer append to the D16 log, D18 OpenSpec
  `tasks.md` E02–E09 checkbox update). No code, no execution, no
  DE/decoder/scientific calls, no staging/commits, no push.

## 2026-09-15 — D18 readiness R1 close (no execution)

### Authorization boundary

- This call performed no code edit, no D18 execution, no DE/decoder or
  scientific call, no root creation, no commit, no push.
- The frozen ≤456-call two-stage ensemble DE batch remains unauthorized. It
  requires one later explicit user grant plus Pre-EXECUTE. No authorization
  was granted by readiness or by D18-R108.
- No-execution-authorized statement: **no D18 execution is authorized by this
  close; the future root remains absent and the frozen command remains an
  unauthorized string.**

### E01–E07 evidence (trusted VERIFIED, do not rerun)

- E01: OpenSpec freeze (proposal/design/tasks/delta spec, packet §§1–6
  verbatim in effect). E02: thin module importing corrected D17/D9/V26
  helpers; rejected-duplication real. E03: 21-candidate table
  (`lam_d2_<x:.2f>_d3_<1-x:.2f>`), Stage-S 168 deterministic (idx 0..167),
  verbatim rank + ties, Stage-C 320 selected-4 with 32-overlap set-equal
  (288 new, 456 total, no-rerun in code), 4 terminal edges,
  eligibility `0.5077488653656221` exact.
- E04: runner gates (`--profile-only`, `--de-sweep`, default-false
  `--execution-authorized`, fresh-root refusal, read-only `--verify`). E05:
  seeds `2026094301..4308` / fresh root / command / budgets frozen;
  predecessor seeds disjoint; future root absent. E06: 26/26 focused tests;
  D17 42+3 environmental. E07: PROFILE_ONLY arithmetic only, zero
  DE/decoder calls, root absent after.
- Frozen numbers: grid `{89,94,99,104,109}`; DV3 baseline
  `0.5468113653656221` (== D17 A2 recomputed); sample deltas
  `+0.25384/+0.44916/+0.64447/+0.83978/+1.03509`; budgets ≤456/≤16 /
  1800s/300s/2GiB/1-proc/no-retry; refusal rc=2 pre-write/bind/load.

### E08 verdict/findings (D18-R108, trusted VERIFIED)

- EVIDENCE_ACCESS VERIFIED, VERDICT `PASS_WITH_FINDINGS`, BLOCKING none.
- CHANNEL/REUSE/FEASIBILITY/PLANS/RANK/BUDGETS/NO-PRODUCTION/CEILING all
  PASS. Tails `T(p_lo)=0.2730308351705778` /
  `T(p_hi)=3.3394200787523175e-07` description-only. Non-blocking:
  predecessor hit-count note; pytest.ini Windows basetemp note; D16-root
  hygiene note.

### Terminal

`D18_L2_ENSEMBLE_DE_READY_AWAITING_EXPLICIT_AUTHORIZATION`. Next gate: one
later explicit grant + Pre-EXECUTE. No DE/finite-L2/D7-H/real-data/FER/
leakage/SKR/qualification/optimality/publication claims. DE/decoder calls
this call: 0. COMMIT_PUSH: none.

(End of file)

## 2026-09-15 — Main-thread readiness acceptance and Sweep A1 authorization

- Accepted marker:
  `D18_L2_ENSEMBLE_DE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- D18-R108 accepted within scope: `EVIDENCE_ACCESS VERIFIED`,
  `PASS_WITH_FINDINGS`, blocking none.
- Sole execution authority:
  `.workbuddy/tasks/D18_L2_ENSEMBLE_DE_SWEEP_A1_TASK_PACKET.md` and its
  companion authorized prompt.
- One grant covers Stage S and mechanically selected Stage C. No manual
  selection, rerun, finite L2 construction, APP, D7-H, or route/FER claim.

## 2026-09-15 — D18 readiness acceptance + Sweep A1 authorization

- Acceptance marker:
  `D18_L2_ENSEMBLE_DE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
  (formalizes the preceding acceptance entry; same single grant, no second
  grant, no scope change). D18-R108 accepted: `EVIDENCE_ACCESS VERIFIED`,
  `PASS_WITH_FINDINGS`, no blocker.
- One-shot grant: batch `D18_L2_ENSEMBLE_DE_SWEEP_A1`, track
  `EXPLORE_HEAVY`, branch `formal-ir-v72p1-addendum-clean`, root
  `workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901`.
- Scope: Stage S (21 candidates × m{94,104} × seeds 2026094301..4304 ×
  pop4000, ≤168 calls) + mechanically selected Stage C (selected-4 × full
  5-m grid × seeds 2026094301..4308 × pops {4000,16000}; 32 Stage-S
  overlap identities reused and never rerun; ≤288 new; ≤456 total).
  Budgets: setup ≤16, wall ≤1800s, per-call ≤300s, RSS <2GiB, one CPU.
- Consumption rule: this single grant is consumed at the start of the one
  frozen command; no second invocation, retry, resume, manual candidate
  replacement, extra seed/grid, adaptive search, or repair. Any failure
  retains evidence and STOPs for one main-thread decision.

## 2026-09-15 — Sweep A1 pre-dispatch checks 1–10 (raw evidence)

No `--execution-authorized` used in this section; zero DE/decoder calls.

- 1 ACCEPTANCE/MARKER PASS: marker recorded in the section above; D18-R108
  `EVIDENCE_ACCESS VERIFIED` / `PASS_WITH_FINDINGS`, blocking none (log
  §E08 lines 54–59). Pre-dispatch added no new grant.
- 2 BRANCH/SCOPE PASS: `git branch --show-current` →
  `formal-ir-v72p1-addendum-clean`. Scoped status raw:
  ` M docs/research_cycles/V72P2D16-MATCHED-BACKOFF/EXPLORATION_LOG.md`
  (197-line documented readiness pointer append, no D16 run) and `??` for
  the three new files + D18 OpenSpec change + D18 cycle docs + A1
  packet/prompt. Unrelated worktree dirt preserved; nothing staged; no
  repairs; no unexplained scoped drift.
- 3 ROOTS/INPUTS PASS: future root absent (`ls`: No such file or
  directory). Model-F `workspace/v72p2d5_model_f_input/20260907_r1`
  present (2 files): npz sha256
  `38e4bfba74d06234af22e931d43d00e51e4a3c61825c59f02c1ed00b6280d345`,
  summary
  `ca67a95305e97fc85dfeae1fd7e3262be9e84771dda5540c9185a3a78fac1a43` ==
  canonical V72P2D15 record. D17-A2 root six files: all sha256
  prefix+suffix match the D17-log record (`2ee23120…54a2c4`, `4837bd52…263917`,
  `d60ab78d…68e40a26`, `b3b4d3b5…f04cec2e`, `1aecf2d2…bb433d9`,
  `53ec0fdc…7db79`). D16 root: all six 8-hex prefixes match the D16-log
  record and every recorded tail fragment is contained in the current
  sha256 (D16-log tails are truncated screen reads); all six mtimes
  2026-09-15 21:54:12 +0800, single-write. Spot hashes PASS.
- 4 OWN RECOUNT PASS: 21 candidates, IDs equal module enumeration, DV3
  `lam_d2_0.00_d3_1.00` present; 105 cells; own rho-normalization +
  min/max-degree recheck infeasible `[]`; module 105/105 executable, 0
  refused. Stage-S 168 calls, idx 0..167 unique, 0 refused flags;
  selected-4 Stage-C 320 identities, idx 0..319 unique; overlap set-equal
  32 (`selected × m{94,104} × seeds 2026094301..4304 × pop4000`), new 288,
  total 456, reused flags 32; module `stage_counts` identical.
- 5 SEEDS PASS: module `verify_seed_disjointness()` passed=True, hits
  prior/banned/d17/d9 all `[]`; D18 seeds `2026094301..4308`. Own
  `rg --hidden "20260943"` outside `workspace/`: hits only D18-owned files
  (module, test, OpenSpec D18, D18 cycle docs, D18 packet). No D16/finite
  fit outcome enters DE: module import surface is only d17/d9/v37f (d16 is
  imported solely to union banned seed sets in `collect_prior_seeds`).
- 6 PROFILE_ONLY PASS: rc=0, stderr empty (stdout 41243 B);
  executable_cells 105, refused_cells 0, counts
  `{stage_s_max:168, stage_c_identities:320, overlap_reused:32,
  stage_c_new_max:288, total_ceiling:456}`, de_calls 0, decoder_calls 0,
  future_root_absent true; official root still absent after (ls: No such
  file or directory).
- 7 ZERO-CALL PRODUCTION PROBE PASS: bind resolves the V26 spy as
  `de_call`; `build_production_channels` → keys `['L045','L055','L2']`,
  L1≠L2 with tags L1/L1/L2; `resolve_sampler` returns the L2 callable
  (`_d17_layer='L2'`); profiles `L1/L045/L055/APP/joint` all refused with
  `D18 is L2-only`; `verify_reuse_identity` passed all 9 checks; spy calls
  0. Bind+inspect only — no DE call, no decoder path.
- 8 REFUSAL PASS: `--de-sweep` without `--execution-authorized` on fresh
  scratch `workspace/d18_a1_check8_scratch_3b7f1c92`: rc=2 with the
  fail-closed message, before root/bind/load (bind/channel/run stubs would
  have raised); scratch absent after; official root absent; no write.
- 9 COMPILE/TESTS PASS: `py_compile` rc=0 (runner, module, test);
  `.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d18_l2_ensemble_de.py
  -p no:cacheprovider -o addopts= --basetemp=workspace/d18_a1_predispatch_tests_5e2b8d41 -q`
  → `26 passed, 1 warning in 6.11s`, rc=0 (warning: `cache_dir` option
  unknown without cacheprovider — benign). D17 fit/DE and broad suites not
  rerun (no concrete conflict).
- 10 FROZEN RECONFIRM + UNUSED GRANT PASS: `FROZEN_COMMAND` char-equal to
  packet §3 / prompt Phase-2 command; budgets 456 DE / 16 setup / 1800 s /
  300 s / 2147483648 B / 1 process; terminals exactly the four labels;
  eligibility `0.5077488653656221` = `0.5468113653656221 − 0.0390625`;
  DE 60/1e-4/20; grid m `{89,94,99,104,109}`; Stage-S m `{94,104}`;
  pops `{4000,16000}`; runner gates `--profile-only` / `--de-sweep` /
  default-false `--execution-authorized` / fresh-root refusal / read-only
  `--verify`. Grant unused: official root absent; no prior D18 DE content;
  authorization unconsumed.

### Pre-dispatch verdict

10/10 PASS. Grant remains unconsumed; the single frozen execution may
proceed once. Evidence-only; no scientific claim.

## 2026-09-15 — Sweep A1 execution (single one-shot run, raw evidence)

- COMMAND (char-exact frozen): `.venv/bin/python
  scripts/v72p2d18_ensemble_development.py --de-sweep
  --execution-authorized --model-f-root
  workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901`
  (external `/usr/bin/time -v` wrapper for RSS/wall only).
  START `2026-09-15T15:50:36Z`, END `2026-09-15T15:58:27Z`, EXIT rc=0.
  Stdout: `DE terminal=D18_L2_DE_SELECT_ONE_ENSEMBLE calls=456 setup=4
  winner=lam_d2_0.20_d3_0.80`.
- RESOURCES: internal wall_s `466.3569358550012` ≤ 1800;
  external elapsed `7:50.75` (470.75 s); max RSS `279660 KiB` =
  286371840 B < 2147483648; CPU 99 % (user 455.65 s + sys 11.84 s), one
  process, swaps 0. `budget_violations: []`. (Internal
  `peak_rss_bytes` is the unset-default 0; RSS evidence is the external
  `/usr/bin/time -v` reading.)
- CALLS: Stage S 168, Stage C new 288, total 456 (== ceiling), all 456
  record identities unique (no duplicate/rerun); setup_calls 4 ≤ 16;
  per-call max `2.815421 s` < 300 s; per-call min `0.353410 s`; sum of
  per-call walls `466.322 s`.
- STAGE-S RANK (own recompute from `de_records.csv`): top three non-DV3
  `lam_d2_0.15_d3_0.85`, `lam_d2_0.20_d3_0.80`, `lam_d2_0.25_d3_0.75`
  (S94=4/4, S104=4/4, worst H94/H104 = 3.089393128245247e-296; the
  rank-4..6 candidates 0.30/0.35/0.40 tie on all four keys and lose on
  `candidate_id ASC`). Selected four (module `select_stage_s` ==
  `summary.selected`): `[lam_d2_0.15_d3_0.85, lam_d2_0.20_d3_0.80,
  lam_d2_0.25_d3_0.75, lam_d2_0.00_d3_1.00]`.
- OVERLAP PROOF: `de_plan.csv` 168 S + 320 C rows, 320 unique C
  identities; 32 `reused=True` identities set-equal to
  `selected × m{94,104} × seeds 2026094301..4304 × pop4000`; those 32
  appear in `de_records.csv` exactly once each, all `stage=S`; all 288
  Stage-C-new identities recorded; 456 unique record identities.
- PER-SELECTED convergence counts (x/8, pop4000 then pop16000):
  - `lam_d2_0.15_d3_0.85`: m89 0/8, 0/8 | m94 8/8, 8/8 | m99 8/8, 8/8 |
    m104 8/8, 8/8 | m109 8/8, 8/8
  - `lam_d2_0.20_d3_0.80`: identical counts to 0.15 (all m≥94 8/8)
  - `lam_d2_0.25_d3_0.75`: identical counts to 0.15 (all m≥94 8/8)
  - `lam_d2_0.00_d3_1.00` (DV3): m89 0/8, 0/8 | m94 0/8, 0/8 |
    m99 8/8, 8/8 | m104 8/8, 8/8 | m109 8/8, 8/8

  pop16000 brackets (D17 rules, recomputed == summary.decision):
  - DV3 `lam_d2_0.00_d3_1.00`: lo94/hi99, h=0.09765625,
    `delta_de=0.5468113653656221`, flag `DE_BRACKET`, flags
    `[DE_BRACKET]`
  - 0.15 / 0.20 / 0.25: lo89/hi94, h=0.09765625,
    `delta_de=0.35149886536562214` (= baseline − 5/128), flag
    `DE_BRACKET`, flags `[DE_BRACKET]`
- DV3 COMPARISON PASS: m94/m99 and `delta_DE ==
  0.5468113653656221` reproduced exactly; clean stable `DE_BRACKET`, no
  `POP_UNSTABLE`; `baseline_drift=false` → no `BASELINE_DRIFT`.
- ELIGIBILITY/WINNER/TERMINAL: all three non-DV3 selected candidates are
  eligible (clean stable bracket + no refusal +
  `delta_DE=0.35149886536562214 ≤ 0.5077483653656221`); rank
  `(delta_DE ASC, worstH_hi ASC, max_dc ASC, id ASC)` → winner
  `lam_d2_0.20_d3_0.80` (0.20 and 0.25 tie at max_dc 4, 0.20 wins on id
  ASC; 0.15 has max_dc 5). Terminal
  `D18_L2_DE_SELECT_ONE_ENSEMBLE` (evidence only, no route claim).
- VERIFIER (read-only): `.venv/bin/python
  scripts/v72p2d18_ensemble_development.py --verify --out-root …` →
  `VERIFY PASS violations=0`, rc=0; root mtimes unchanged after verify.
- ROOT (six files, sha256):
  `manifest.json 50f5fd9661daadc6ab4aae8d8fc17fb2bf7d5cd58ff2a0fa7e95b0eb566b8aa0`;
  `de_plan.csv 920392190c476f3467324a0a6161a80c888d10ff255fa31dfdbbdb374bd1b43f`;
  `de_records.csv 7b8abea955e0641a8190091b273163a94e947108a63d0d63de097e6652bb8331`;
  `de_traces.csv a7ecbadf90e50686b875c674b5781fa0ad63b92ce2365320446d227f93c324ab`;
  `summary.json 293fcc47905617e69d0462dc0547f30e01e0866a445f0765a15e3d17c4f05434`;
  `command_log.txt 47e0ac6590795590bc08953181025fac0fead26197d718c858757b707cd9fbc0`.
- GRANT: consumed once at command start; no second run/retry/resume/
  repair/search/manual substitution; no APP/L1/decoder/real-data; no
  commit/push. Terminal is evidence-only and self-authorizes nothing.

## 2026-09-15 — D18 Sweep A1 batch-end review (VERIFIED PASS_WITH_FINDINGS)

REVIEW_ID `D18-A1-REVIEW` (condensed). Independent batch-end review of the
Sweep A1 evidence above; evidence-only, no route/optimality/FER claim.

- EVIDENCE_ACCESS VERIFIED: direct artifact access; reviewer wrote its own
  recomputation script; the reviewer's own read-only `--verify` run returned
  `VERIFY PASS violations=0`, rc=0; root re-hash after review identical; the
  reviewer's probes were zero-call; no edits/reruns/refits/commit/push.
- ONE-SHOT PASS: `command_log.txt` has one line
  `terminal=D18_L2_DE_SELECT_ONE_ENSEMBLE calls=456`
  (sha `47e0ac65…`); the six files appear as a single-write burst
  `23:58:27.38–.42 +0800` (= `15:58:27Z` END); root absent before; a second
  invocation is structurally refused; git reflog shows the last commit
  before the run; nothing staged; grant consumed once.
- INVENTORY PASS: 6 files, all hashes match
  (`manifest 50f5fd96…`, `de_plan 92039219…`, `de_records 7b8abea9…`,
  `de_traces a7ecbadf…`, `summary 293fcc47…`, `command_log 47e0ac65…`);
  plan 488 rows (168 S + 320 C), records 456, traces 456.
- FEASIBILITY PASS: reviewer's own edge→node reconstruction matches all
  21×5 cells (0 mismatches); 105/105 executable; refusal gate exists and
  records refusals without replacement; samples `x=0 {3:128}` E384
  maxdc5 / `x=0.20 {2:35,3:93}` E349 maxdc4 / `x=1.00 {2:128}` E256
  maxdc3; rho sums = 1.
- STAGE-S PASS: 168 unique idx 0..167; reviewer's own H60/converged
  recompute matches all 456 records, 0 mismatches; reviewer's own rank →
  selected `[0.15, 0.20, 0.25, DV3]`; tie verified — six candidates share
  `S94=S104=4` plus worst-H `3.089393128245247e-296` (held fixed point),
  resolved by pre-registered id ASC; next-ranked 0.50 (wH94 8.67e-12) then
  0.45 (2.57e-9).
- OVERLAP PASS: 320 C identities unique; exactly 32 `reused=True`
  set-equal to selected × {94,104} × 4301-4304 × pop4000; each present
  once, all stage S; C-new 288; 456 unique total.
- STAGE-C/DV3/ELIGIBLE/WINNER PASS: selected m89 0/8, m94-m109 8/8 on both
  pops; DV3 m89 0/8, m94 0/8, m99+ 8/8; brackets lo89/hi94 h=0.09765625
  `delta_de=0.35149886536562214` `[DE_BRACKET]` + DV3 lo94/hi99
  `delta_de=0.5468113653656221 == D17 baseline` (<1e-18) →
  `baseline_drift=false`; 3 eligible; rank tie-break (delta/worstH tie;
  0.20/0.25 maxdc4 < 0.15 maxdc5 → id ASC) → winner
  `lam_d2_0.20_d3_0.80`; terminal SELECT_ONE consistent.
- SAMPLER PASS: `resolve_sampler` refuses APP/L1/non-L2; zero-call probe
  channels `{L045:L1, L055:L1, L2:L2}` (L045 is L055, L2 distinct);
  spy `run_de_call` count 0; `verify_reuse_identity` 9/9; records contain
  no APP/L1/L045/L055/joint/exact/syndrome/undetected/decoder tokens;
  seeds exactly 4301-4308; D16 used only for the banned-seed union.
- VERIFIER/INPUTS PASS: the `--verify` run performed by the reviewer
  PASS/0; Model-F + D17-A2 sha match; D16 root mtimes unchanged; calls
  456/456, wall 466.36/1800, per-call min/max/sum
  0.353410/2.815421/466.322/300, `violations []`, terminal singular.
- NO-RETRY: no rerun/repair/refit/second invocation; probes were zero-call
  read-only; root post-review hash identical.
- FINDINGS: BLOCKING none. NON-BLOCKING:
  - N1: `peak_rss_bytes=0` is a placeholder; RSS evidence is external-only
    (286371840 B < 2 GiB); `setup_calls=4` is a declared constant — both
    accepted definitions.
  - N2: screen saturation fixed point; six-way tie is by design on id ASC.
  - N3: `command_log.txt` is thinner than D17 A2; the one-shot proof rests
    on fresh-root/no-overwrite plus a single root.
  - N4: rank-4..6 are screen-indistinguishable (0.30/0.35/0.40 under the
    frozen pop4000 / 4-seed screen) — main thread owns interpretation.
- VERDICT `PASS_WITH_FINDINGS`; recommendation
  `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`;
  evidence-only (no route/optimality/FER claims).
- CLOSE: grant consumed, no second run, no commit/push, memory triage
  pending.

## 2026-09-16 — D19 readiness STOP pointer (docs-only, no D18 change)

- D19 (`docs/research_cycles/V72P2D19-L2FINITE/READINESS_R1.md`) closed as
  STOP: frozen n256 DV3 seed `2026094408` deterministically fails graph
  construction (23/24 cells admit); D19-BLOCKER-REVIEW PASS with the blocker
  correctly retained. No D19 authorization may issue against the as-frozen
  seed set.
- ONE main-thread decision pending: amend the frozen n256 DV3 seed set under
  a new packet amendment OR formally accept terminal
  `D19_L2_FINITE_ENGINEERING_BLOCKED`. This entry changes no D18 evidence,
  grant, or terminal. D19 detail: `docs/research_cycles/V72P2D19-L2FINITE/EXPLORATION_LOG.md`.
