# D10 mixed-degree L1 finite discriminator — EXPLORE log (append-only)

Cycle: `V72P2D10-MIXED-DEGREE-L1`
Change: `v72p2d10-mixed-degree-l1-finite-discriminator`
Track: readiness/design now (F01–F05); the frozen future L1 batch is
`EXPLORE_HEAVY` under `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE` (one
authorization, one append-only log, one batch-end independent review).
Batch: D10 mixed-degree L1 finite discriminator heavy R1.
Authority: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_FINITE_READINESS_R1_TASK_PACKET.md`
+ paired prompt.
Readiness record: `READINESS_R1.md` (this directory).

This is the single append-only log for this batch. Future F06–F12 work,
attempts, the preregistered engineering correction (at most one repair+rerun,
unchanged scientific inputs/seeds/thresholds/data roles/hypothesis), the
scientific batch (if separately authorized) and the batch-end review append
here; no per-arm documents are created.

## 2026-09-14 — readiness opening / discriminator contract freeze (F01–F05; no execution)

### Authorization boundary

- This call was authorized for audit, OpenSpec, design and read-only
  verification only. It performed no behavior-code edit, no decoder call, no
  scientific L1 call, no graph-construction execution, no Model-F content read
  beyond the accepted CAL-only artifact, no CAL/VAL/raw/real-data contact, no
  output-root creation, no commit, no push.
- The future L1 batch remains **unauthorized**. It requires a separate
  explicit user/main-thread authorization naming this batch, branch, root
  (`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`), the
  two arms, widths, graph/block seeds and budgets. No authorization key was or
  is set by readiness.
- The frozen thresholds, degree tables, seeds and coefficient rule were fixed
  before any decoder result exists and may not be changed after execution
  begins; no seed search, retry, resume or adaptive stop is permitted.

### F01 accepted D9 evidence (read-only)

- D9 terminal `D9_DE_CALIBRATION_SELECT_ONE`; unique accepted candidate
  `lam_d2_0.45_d3_0.55`; stability DV3 0/8 & 0/8 `stable_unconverged`, 0.45
  8/8 & 8/8 `stable_converged`, 0.50 7/8 & 8/8 `stability_ambiguous`, 0.55
  6/8 & 4/8 `stable_unconverged`; lifecycle
  `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`; DE-only ceiling (no
  decoder/FER). Exact paths/fields in `READINESS_R1.md` §F01.

### F02–F05 frozen contract (see `design.md`; no behavior)

- Two-arm isolation contract and the selected minimal deterministic
  degree-sequence PEG `build_degree_sequence_peg` (builder inventory and
  rejected alternatives in `design.md` §2).
- Exact f1.2 degree tables, three graph seeds per width, eight block seeds per
  width (all verified fresh), deterministic coefficient rule, paired call
  order and structural gates G1–G10 (`design.md` §3–§5).
- Thresholds (POSITIVE/NEGATIVE/AMBIGUOUS/ENGINEERING_BLOCKED), conditional
  n64 -> n128 -> n256 progression, terminals/routing and claim ceiling
  (`design.md` §6–§7).
- Fresh future root UUID `b2dd13e4-6600-4e27-90df-5c9038cf2c34` (verified
  ABSENT) and the exact future command (`design.md` §8); budgets <=144
  scientific L1 calls + <=44 setup units, wall <=1800 s, per-call <=120 s,
  RSS <2 GiB strict, single process, no retry/resume/seed search.

### Claim boundary (unchanged)

- Readiness establishes only that the two-arm L1 discriminator is
  mathematically specified, construction-bounded, structurally gated,
  threshold-frozen and mechanically routable. It establishes no decoder
  success or finite-length/FER/leakage/SKR/qualification/promotion/real-data
  claim, no DE-to-decoder equivalence, does not reinterpret the D9 terminal
  and does not revive D7-H.

## 2026-09-14 — F06–F10 implementation, focused tests, profile, frozen-match (no decoder, no batch)

### Authorization boundary

- This call was authorized for implementation, focused fake/tiny tests,
  bounded pre-decoder profile and read-only frozen-match verification only.
  It performed no production decoder call (0), no scientific L1 call (0), no
  `--batch` invocation, no CAL/VAL/raw/real-data contact, no output-root
  creation and no commit/push. `BATCH_AUTHORIZED` remains `False`; the
  runner refuses `--batch` before any read while it is false.
- Changed files (implementation call):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`
  (new), `scripts/v72p2d10_mixed_degree_l1_development.py` (new),
  `comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py` (new), this log,
  `READINESS_R1.md` and the D10 OpenSpec `tasks.md` F06–F10 checkboxes.
  No V10/V26/v35/D5–D9 module, Model-F artifact, baseline or protected root
  was modified.

### F06–F07 implementation

- B8 `build_degree_sequence_peg`: exact variable/check degree sequences,
  decreasing-degree index assignment, B1 placement policy by read-only reuse
  (`_tie_pick`, `_bfs_distance`, `_ace_score`, `v10_seed`), one deterministic
  attempt per seed, socket infeasibility raises before placement, dead-end
  placements return `construction_failed` with no partial graph.
- Structural gates G1–G6 with reported (never repaired) rank, components,
  largest-component fraction, degree-2 diagnostics, four-cycle count and
  girth; coefficient rule `v10_seed(d10:coeff:{width}:{graph_seed})`;
  injected-decoder `execute_plan`/`dispatch_l1`; `--verify` read-only
  recomputation with zero skip; `--profile-only` stdout profile.
- F07 boundary: the module never imports the production decoder; the
  admission gate raises before any decoder binding; tests inject fakes.

### F08 focused tests

```text
.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py \
  -p no:cacheprovider -o addopts= \
  --basetemp=workspace/d10_f08_f09_tests_9e4d2c71-6b3f-4a58-9c0d-7e21f4b8a6d3 -q
# 26 passed
```

Coverage: frozen constants/command/defaults, exact degree tables, exact
degree/socket/gate checks at all 18 real graphs, builder determinism and
multi-graph variation, fail-loud infeasible sequences, construction-failure
retention, seed-namespace separation, coefficient range and same-rule check,
rank/four-cycle/girth metrics, plan matrix and order, threshold
classification boundaries, terminal routing, progression stop, paired
identical blocks, exact/syndrome separation with residual weight and
provenance, invalid-graph fail-before-decoder, full fake-batch root plus
tamper detection in `--verify`, profile seed-replacement clause, root
refusal and subprocess decoder-import isolation.

### F09 `--profile-only` (raw numbers)

Command: `.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py
--profile-only`; total wall 0.481 s; 18/18 `ok`+admitted; replacements 0;
frozen-seed failures 0.

| width | arm | wall s (3 seeds) | rank | components | largest frac | N2 | 4-cycles | girth |
|---|---|---|---|---|---|---|---|---|
| 64 | `PEG_DV3_MATCHED` | 0.0149/0.0063/0.0058 | 58/58/59 | 16/15/17 | 0.125/0.141/0.125 | 0 | 148/137/174 | 4 |
| 64 | `PEG_DV23_LAM2_045` | 0.0050/0.0046/0.0046 | 59/58/58 | 9/11/9 | 0.281/0.250/0.297 | 35 | 60/54/49 | 4 |
| 128 | `PEG_DV3_MATCHED` | 0.0174/0.0168/0.0171 | 118/118/118 | 32/35/33 | 0.125/0.086/0.094 | 0 | 325/369/333 | 4 |
| 128 | `PEG_DV23_LAM2_045` | 0.0141/0.0135/0.0134 | 118/118/116 | 19/19/21 | 0.141/0.156/0.117 | 71 | 102/107/98 | 4 |
| 256 | `PEG_DV3_MATCHED` | 0.0626/0.0615/0.0631 | 233/233/235 | 67/68/64 | 0.051/0.039/0.039 | 0 | 690/685/617 | 4 |
| 256 | `PEG_DV23_LAM2_045` | 0.0541/0.0529/0.0534 | 234/235/234 | 37/36/42 | 0.078/0.059/0.066 | 141 | 207/203/210 | 4 |

Diagnostics retained for the batch-end review: girth 4 everywhere; min check
degree 3 (DV3) / 2 (mixed); degree-2 cycle-rank lower bound 0 everywhere;
rank below `m` in several graphs (58/59, 116/118, 233–235/236); many
connected components (9–68) with largest-component fraction 0.039–0.297.
These are reported metrics, not gate failures; the frozen admission gates
G1–G6 all pass.

### F10 frozen-match check

`FROZEN_COMMAND_MATCH=True` against the design §8 command; runner defaults
`--model-f-root workspace/v72p2d5_model_f_input/20260907_r1`, `--out-root`
required; budgets 144 scientific calls / 44 setup / 1800 s / 120 s per call /
2147483648 B RSS; `BATCH_AUTHORIZED=False` (all authorization flags false);
future root `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
ABSENT. Degree-table cross-check against the D9 root `summary.json`
`graph.cells` (f1.2) matches on all six cells.

### Claim boundary (unchanged)

Implementation/profiling evidence only: no decoder success, no
finite-length/FER/leakage/SKR/qualification/promotion/real-data claim, no
DE-to-decoder equivalence; the D9 terminal is not reinterpreted and D7-H is
not revived. The scientific L1 batch remains unauthorized.

## 2026-09-14 — F11 independent review and F12 closure

- Review artifact:
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/INDEPENDENT_REVIEW_R1.md`;
  verdict `PASS_WITH_FINDINGS`; terminal recommendation
  `D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- Four PASS judgments: graph mathematics (all 18 graphs independently
  recomputed, degree/socket balance, rank/components/4-cycle, determinism, seed
  variation, coefficient re-derivation); isolation (one construction/tie
  family, arm-independent seeds, one decoder/syndrome pair, only the forced
  degree profile differs); decoder-entry boundary (admission gate precedes
  decoder binding, zero production decoder entries, `--batch` refuses while
  `BATCH_AUTHORIZED=False` with no root, injected fakes only); pre-frozen
  thresholds/progression and frozen command/root/budgets consistency.
- F12 correction (the single permitted scoped correction): F2 applied —
  replacement seeds `2026092210..2026092215` enumerated in `design.md` §4.1 and
  `spec.md`; scoped re-review `F2_STATUS: RESOLVED`, `VERDICT: PASS`.
- Carried non-blocking findings: F1 (BATCH_AUTHORIZED constant flip vs the
  `--execution-authorized` convention), F3 (`--verify` zero-skip mid-width
  engineering-blocked root expected FAIL), F4 (arm-asymmetric connectivity/rank
  interpretation caveat), F5 (pre-existing D9 record hygiene).
- Authorization boundary unchanged: the L1 batch remains unauthorized; the
  future root
  `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` is
  absent; no commit, no push; all authorization flags false.

## 2026-09-14 — main-thread route decision

R1 readiness is `REVISE_REQUIRED_CONNECTIVITY_AND_RANK`; no batch authorization
was granted. The reviewer evidence is accepted, but F4 is scientifically
blocking because the proposed treatment/control comparison is confounded by
9--68 Tanner components and, in several cells, deficient GF32 row rank. The
failed readiness candidate and profile evidence remain immutable. R2 may
change construction/admission mechanics only; it may not run a decoder, search
or replace graph seeds, change degree tables, thresholds, blocks, priors, or the
tested hypothesis.

## 2026-09-14 — R202–R210 connectivity-first implementation, focused tests, PROFILE_ONLY (no decoder, no batch)

### Authorization boundary

- Implementation/readiness only: no decoder/DE/CAL/VAL/real-data call, no
  scientific root, no commit, no push. `--execution-authorized` kept false
  and unused; `BATCH_AUTHORIZED`/`PROFILE_REPLACEMENT_SEEDS` source
  constants removed (no constant-flip authorization path remains).
- Changed files (this call only):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`,
  `scripts/v72p2d10_mixed_degree_l1_development.py`,
  `comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py` (targeted R2
  updates), `comparison_bench/tests/test_v72p2d10_mixed_degree_l1_r2.py`
  (new, additive), this log. No baseline, Model-F artifact, D5–D9 module,
  openspec, or protected root touched. Unrelated dirty worktree files
  preserved untouched.

### Constructor delta (R202, 5 lines of idea)

- Phase A backbone: seeded permutation orders
  (`rng = default_rng(v10_seed("d10:backbone:{seed}"))`) then a path
  `c_q0–v_p0–c_q1–v_p1–…–c_q{m-1}–v_p{m-1}` plus one seeded
  max-remaining-capacity attachment (`_tie_pick` in the backbone namespace)
  per leftover variable → connected spanning tree (`n+m-1` edges, every
  backbone degree ≤ exact target since all targets are ≥ 2).
- Phase B fill: unchanged R1 PEG/ACE rule over remaining sockets (max BFS
  depth → max ACE → `_tie_pick` over sorted candidates). One constructor +
  tie policy shared by both arms; only the forced degree sequence differs.
- Fail-closed: parallel edge, degree overshoot, socket mismatch or dead end
  → `construction_failed`, no partial graph. Zero replacement seeds.
- R203: Kuhn maximum bipartite matching, fixed order (checks `0..m-1`,
  sorted neighbours), no randomness; require `structural_rank == m`.
- R204: frozen R1 coefficient rule unchanged; exact GF32/poly-37 row rank
  via fresh local log/exp-table elimination (no new dep); require
  `gf32_rank == m`; failure records the cell, no seed change.
- R205: admission A1–A6 before decoder binding (degrees/sockets, simple
  graph, 1 component over `n+m` nodes, structural `m`, GF32 `m`, replay
  equality); G1–G6 retained as measurement base; 4-cycle/girth/ACE
  diagnostics only. R206: `--execution-authorized` (default false) refuses
  `--batch` before root creation/decoder binding. R207: `--verify`
  fail-closed on any non-admitted graph or engineering-blocked width.

### R209 focused tests (fresh task-owned basetemp, no cache provider)

```text
.venv/bin/python -m pytest \
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py \
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1_r2.py \
  -p no:cacheprovider -o addopts= \
  --basetemp=workspace/d10_r2_tests_7f3a9c2e-1b44-4d88-9e0a-2c5f6d8e9a01 -q
# 44 passed (T0/T1 only; no broader tier: no focused failure)
```

```text
.venv/bin/python -m py_compile <module> <runner> <both test files>
# COMPILE_OK
```

Coverage: A1–A6 positive on all 18 frozen cells + deliberate violator per
predicate (histogram/socket, empty check, block-diagonal disconnected,
Hall-violator structural deficiency, proportional-row GF32 deficiency,
replay equality), local GF32 rank cross-checked against `d5._gf32_rank` on
all 18 cells, shared-constructor spy (both arms route through one builder),
unauthorized `--batch` refusal (rc 2, no root, no v35 import), fail-closed
`--verify` on tampered non-admitted graph and engineering-blocked width,
retired-replacement profile behavior, fake-decoder entry boundary (0 calls).

### R210 PROFILE_ONLY (exactly the original 18 cells; stdout only)

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --profile-only
# rc 0; 18 graphs, 0 seed replacements, 0 frozen-seed failures, wall ~1.2 s
```

| arm | width | seeds comp/largest | struct | gf32 | 4cyc | girth | wall s |
|---|---|---|---|---|---|---|---|
| `PEG_DV3_MATCHED` | 64 | 1/1.000 ×3 | 59 ×3 | 59 ×3 | 0/1/1 | 6/4/4 | 0.012/0.012/0.012 |
| `PEG_DV23_LAM2_045` | 64 | 1/1.000 ×3 | 59 ×3 | 59 ×3 | 0/0/1 | 8/10/4 | 0.007 ×3 |
| `PEG_DV3_MATCHED` | 128 | 1/1.000 ×3 | 118 ×3 | 118 ×3 | 0 ×3 | 6/8/8 | 0.038/0.041/0.042 |
| `PEG_DV23_LAM2_045` | 128 | 1/1.000 ×3 | 118 ×3 | 118 ×3 | 0 ×3 | 10/10/8 | 0.027/0.027/0.024 |
| `PEG_DV3_MATCHED` | 256 | 1/1.000 ×3 | 236 ×3 | 236 ×3 | 0/0/1 | 8/10/4 | 0.180/0.189/0.170 |
| `PEG_DV23_LAM2_045` | 256 | 1/1.000 ×3 | 236 ×3 | 236 ×3 | 0 ×3 | 10/10/12 | 0.123/0.118/0.125 |

All 18 admitted A1–A6. Replacement seeds used: 0. Decoder calls/binds: 0
(subprocess check: `v35_algorithm_development` absent from `sys.modules`
after `profile_only()`; `--batch` refuses rc 2 with no root write).
Future root
`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` absent.
Note for the batch-end review: connectivity-first PEG yields girth 4–12
and ≤1 four-cycle per graph (diagnostics only, unrepaired).

### Claim boundary (unchanged)

- Readiness evidence only: 18 connected full-rank graphs under the frozen
  contract. No decoder/threshold outcome, no FER/leakage/SKR/qualification/
  promotion/real-data claim. Next: R211 independent readiness review
  (`EVIDENCE_ACCESS: VERIFIED`); no execution authorized by this entry.

## 2026-09-14 — D10 R2 connectivity-first readiness (R201-R212)

### Authorization boundary

- This call was documentation-only (R212): code/docs file edits to the two
  allowed files plus focused fake tests and `PROFILE_ONLY` evidence recording
  only. No `--batch`, no decoder/DE/CAL/VAL/real-data call, no scientific
  root, no commit, no push. `--execution-authorized` remains default false;
  the future root
  `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` is
  absent. D7-H is not revived; no conclusion beyond readiness is drawn.
- Execution remains unauthorized: the terminal below grants no execution and
  a separate explicit user/main-thread authorization is still required before
  any scientific L1 batch.

### R201 OpenSpec amendment (4 files)

- Amended `openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/`
  `proposal.md`, `design.md`, `tasks.md`,
  `specs/mixed-degree-l1-finite-discriminator/spec.md`: frozen R1 scientific
  contract preserved exactly (two arms, widths, degree tables, graph/block
  seeds, Model-F root, priors, GF32/poly37, coefficient rule, decoder
  settings, paired blocks, thresholds, progression, budgets, claim ceiling)
  plus the R202–R207 delta. R1 replacement seeds `2026092210..15` retired
  (record only; zero replacement seeds in R2).

### R202–R207 mechanics delta (5-line idea)

- One constructor + tie policy shared by both arms; only the forced degree
  sequence differs. Phase A seeded-permutation backbone spans all `n+m`
  Tanner nodes within exact target degrees; Phase B fills remaining sockets
  with the unchanged R1 PEG/ACE rule. Deterministic Kuhn matching requires
  structural `m`; frozen-rule GF32 elimination requires `gf32_rank == m`.
  Admission A1–A6 precedes decoder binding; `--execution-authorized`
  (default false) refuses `--batch` with no write; `--verify` is fail-closed.

### 18-cell admission summary (all admitted, A1–A6)

- 18/18 `ok`+admitted; 0 seed replacements; 0 frozen-seed failures; 0 decoder
  calls/binds. Components 1 and largest fraction 1.000 in every cell;
  structural rank `== m` (59/118/236) and GF32 rank `== m` in every cell.
- Per-width extremes: n64 — 4-cycles 0/1 pattern, girth 4–10; n128 —
  4-cycles 0, girth 6–10; n256 — 4-cycles 0/1 pattern, girth 4–12.
  Four-cycle/girth values are diagnostics only (unrepaired). Full per-cell
  table retained in the preceding R202–R210 entry.

### Commands/tests raw results

```text
.venv/bin/python -m py_compile <module> <runner> <both test files>
# COMPILE_OK
.venv/bin/python -m pytest \
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py \
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1_r2.py \
  -p no:cacheprovider -o addopts= \
  --basetemp=workspace/d10_r2_tests_7f3a9c2e-1b44-4d88-9e0a-2c5f6d8e9a01 -q
# 44 passed (T0/T1 only; own basetemp)
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --profile-only
# rc 0; PROFILE_ONLY 18/18 admitted, 0 replacements, total wall ~1.2 s
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch [...]
# refused rc 2, no root written
# --verify on tampered/engineering-blocked root: rc 1 (fail-closed)
# decoder_calls=0 scientific_calls=0
```

### R211 independent readiness review (VERIFIED, trusted, not rerun)

- `REVIEW_ID D10-MIXED_DEGREE_L1-R211`, `EVIDENCE_ACCESS VERIFIED`,
  `VERDICT PASS`, terminal recommendation
  `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION`
  (grants no execution).
- Reviewer recomputation: 18/18 A1–A6 PASS (components 1, largest 1.000,
  structural `m`, GF32 `m`, all cells; 4-cycles 0/1 pattern, girth 4–12);
  matches the operator table; no seed change.
- Frozen equality PASS (tables/seeds/coefficient rule/Model-F/priors/
  decoder/thresholds/budgets/claim ceiling; zero replacement seeds; R1
  `2026092210..15` retired-doc only).
- Mechanics R202–R207 PASS (one constructor+tie both arms; deterministic
  Kuhn + GF32; admission before bind; `--execution-authorized` default
  false, `--batch` rc2 refusal no-write; `--verify` fail-closed; 0/0
  decoder/scientific calls; future root absent).
- Findings: BLOCKING none; N1 girth 8→12 ACCEPT (diagnostic-only); N2
  unrelated dirty files out-of-scope preserved; N3 retired-seed mentions
  are required retirement record.
- R202–R210 operator evidence: py_compile OK; 44 passed; PROFILE_ONLY
  18/18 admitted total ~1.2 s wall, 0 replacements/failures; `--batch`
  refusal rc2 no root; decoder_calls=0 scientific_calls=0.

### Terminal

- `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION`
  (R201–R212 complete; grants NO execution).

## 2026-09-14 — main-thread R2 readiness acceptance

Accepted as
`D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The R211 independent evidence is trusted: 18/18 original cells pass A1--A6,
zero replacement seeds, zero decoder/scientific calls, and no blocking finding.
No scientific execution is authorized by this acceptance.

## 2026-09-14 — D10 Batch A1 explicit main-thread authorization

`D10_MIXED_DEGREE_L1_BATCH_A1_AUTHORIZED_ONCE`.

The main thread explicitly authorizes exactly one invocation of the frozen A1
command on branch `formal-ir-v72p1-addendum-clean`, writing only to fresh root
`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`.
Authorization covers the frozen conditional sequence n64, then n128 iff n64 is
POSITIVE, then n256 iff n128 is POSITIVE; ceilings are 144 scientific L1 calls,
44 setup units, 1800 s wall, 120 s per call, RSS strictly below 2147483648 B,
single process. It also covers the required read-only independent batch-end
review and append-only result record. It does not cover repair, rerun, seed
replacement/search, tuning, changed inputs, L2/APP, D7-H, real data, commit or
push. The authorization is consumed when the exact `--batch
--execution-authorized` command starts.

### Claim boundary (unchanged)

- Readiness evidence only: no decoder/threshold outcome, no
  FER/leakage/SKR/qualification/promotion/real-data claim, no
  DE-to-decoder equivalence; the D9 terminal is not reinterpreted and D7-H
  is not revived. Project-memory triage for this R2 batch is left to the
  memory agent.

## 2026-09-14 — D10 Batch A1 pre-dispatch (AUTHORIZED_ONCE)

Track `EXPLORE`. Branch `formal-ir-v72p1-addendum-clean`. No
`--execution-authorized` used in this section. Grant
`D10_MIXED_DEGREE_L1_BATCH_A1_AUTHORIZED_ONCE` unconsumed (consumed only at
Phase-2 command start). Interpreter `.venv/bin/python` throughout. Append-only;
prior sections untouched.

### Pre-dispatch 1/7 — accepted R2 marker + R211 VERIFIED PASS/no blocker: PASS

- Raw grep `EXPLORATION_LOG.md`:
  - `365: - REVIEW_ID D10-MIXED_DEGREE_L1-R211, EVIDENCE_ACCESS VERIFIED,`
  - `366:   VERDICT PASS, terminal recommendation`
  - `379: - Findings: BLOCKING none; N1 girth 8->12 ACCEPT (diagnostic-only); N2`
  - `394: D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION.`
  - `401: D10_MIXED_DEGREE_L1_BATCH_A1_AUTHORIZED_ONCE.`
- `## 2026-09-14 — D10 R2 connectivity-first readiness (R201-R212)` records
  R211 `EVIDENCE_ACCESS VERIFIED`, `VERDICT PASS`, terminal
  `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION`, BLOCKING none.
- `## 2026-09-14 — main-thread R2 readiness acceptance` records accepted
  `D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.

### Pre-dispatch 2/7 — branch + scoped cleanliness: PASS

- Raw: `git branch --show-current` -> `formal-ir-v72p1-addendum-clean`;
  `git rev-parse --abbrev-ref HEAD` -> `formal-ir-v72p1-addendum-clean`;
  `git log --oneline -3` -> `278fdf07 feat(d7-h): implement minimal two-transfer
  alternating discriminator / cab63159 docs(d7-h): freeze alternating
  discriminator packet (R1A1 corrected) / 46141fcc docs(d7-g): accept extrinsic
  contract readiness`.
- Raw scoped diff: `git diff --name-only -- <7 D10 scoped paths>` -> empty
  (exit 0); `git ls-files -- <scoped paths>` -> empty (all 7 D10 scoped paths
  untracked-but-present, not tracked-modified).
- Raw full-tree `git diff --stat` -> 20 tracked files modified (unrelated,
  preserved untouched): AGENTS.md, AGENT_HANDOFF.md, AGENT_PROJECT_MEMORY.md,
  README.md, RUN_COMMANDS.md,
  comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py,
  comparison_bench/tests/test_v72p2d6_bp_provenance_compat.py,
  comparison_bench/tests/test_v72p2d6_gf32_graph_mother_r1d.py,
  docs/CURRENT_MAINLINE.md, docs/decision-log.md,
  docs/prompts/chatgpt-research-review.md,
  docs/prompts/opencode-research-execution.md, docs/research-cycle-sop.md,
  docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/cycle_state.yaml,
  docs/troubleshooting.md, docs/v35-algorithm-development-report.md,
  openspec/changes/v72p2d6-gf32-graph-mother-r1d-option-c/specs/r1d-option-c/spec.md,
  openspec/changes/v72p2d6-gf32-graph-mother-r1d-option-c/tasks.md,
  scripts/v72p2d6_graph_mother_development.py,
  workspace/pytest-evidence-test/output/expanded_evidence_manifest.json.
- No switch, no commit, no push. Did not modify unrelated dirty files.

### Pre-dispatch 3/7 — result root ABSENT + Model-F present/unchanged: PASS

- Raw: `ls -la workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
  -> `ls: cannot access ...: No such file or directory`.
- Raw: `ls -la workspace/v72p2d5_model_f_input/20260907_r1/` -> `model_f_input.npz
  (208467 B)`, `model_f_input_summary.json (752 B)`.
- Raw: `sha256sum workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz`
  -> `38e4bfba74d06234af22e931d43d00e51e4a3c61825c59f02c1ed00b6280d345`
  (matches prior `38e4bfba…`).
- Raw `model_f_input_summary.json`: `status=MODEL_F_INPUT_CANDIDATE`,
  `formal=false`, `cal_only=true`, `decoder_calls=0`, `cal_start=702`,
  `cal_end=1725`, `q=32 poly=37`.

### Pre-dispatch 4/7 — plan/seeds/arms/thresholds/command/budgets match OpenSpec: PASS

- Raw module constants (`PYTHONPATH=comparison_bench/src`):
  - `FROZEN_COMMAND=.venv/bin/python
    scripts/v72p2d10_mixed_degree_l1_development.py --batch --model-f-root
    workspace/v72p2d5_model_f_input/20260907_r1 --out-root
    workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
    (design section 8 base shape; packet adds `--execution-authorized` flag).
  - `ARMS=('PEG_DV3_MATCHED', 'PEG_DV23_LAM2_045')`, `WIDTHS=(64, 128, 256)`.
  - `GRAPH_SEEDS={64: (2026092201, 2026092202, 2026092203), 128: (2026092204,
    2026092205, 2026092206), 256: (2026092207, 2026092208, 2026092209)}`.
  - `BLOCK_SEEDS={64: (2026092301..2026092308), 128: (2026092311..2026092318),
    256: (2026092321..2026092328)}`.
  - `SCIENTIFIC=144 SETUP=44 WALL=1800.0 PERCALL=120.0 RSS=2147483648
    MAXITER=90 DAMPING=1.0 Q=32 POLY=37 PLAN_LEN=144
    MODEL_F_ROOT=workspace/v72p2d5_model_f_input/20260907_r1
    AUTHORIZATION=separate explicit user/main-thread authorization required
    before --batch`.
- Packet Frozen run command
  (`.workbuddy/tasks/D10_MIXED_DEGREE_L1_BATCH_A1_TASK_PACKET.md:20`):
  `.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch
  --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
  — exact authorized form of the frozen base. Thresholds/progression/budgets per
  design section 6/spec SHALL (POSITIVE/NEGATIVE/AMBIGUOUS/ENGINEERING_BLOCKED,
  n64->n128->n256 iff POSITIVE) unchanged.

### Pre-dispatch 5/7 — --profile-only 18/18 A1-A6, 0 replacements: PASS

- Raw: `.venv/bin/python
  scripts/v72p2d10_mixed_degree_l1_development.py --profile-only` -> `RC:0`,
  `/tmp/d10_profile.json 14246 B`.
- Raw counts: `total 18`, `admitted 18`, `A1-A6 all true` (every graph all six
  predicates true), `seed_replacements []`, `replacement_seeds_used 0`,
  `frozen_seed_failures []`, `wall_s 1.0963959200016689`.
- No decoder, no root (stdout only).

### Pre-dispatch 6/7 — py_compile + both D10 tests fresh basetemp: PASS

- Raw: `.venv/bin/python -m py_compile
  comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py
  scripts/v72p2d10_mixed_degree_l1_development.py
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1_r2.py` -> `COMPILE_OK`.
- Raw: `.venv/bin/python -m pytest
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py
  comparison_bench/tests/test_v72p2d10_mixed_degree_l1_r2.py -p no:cacheprovider
  -o addopts= --basetemp=workspace/d10_a1_predispatch_c9f1a2b4-1111-4222-8333-444455556666
  -q` -> `44 passed, 1 warning in 10.14s` (warning: Unknown config option
  `cache_dir`; benign). Fresh task-owned gitignored basetemp.

### Pre-dispatch 7/7 — unrelated output + authorization untouched: PASS

- Raw `BATCH_A1_AUTHORIZATION.md` (mtime `Sep 14 14:17`, sha256
  `49e6e86a9b4a25f44e13aebe245b7ef5653f55dc6e55af1adc56bf47729f0186`):
  `Status: D10_MIXED_DEGREE_L1_BATCH_A1_AUTHORIZED_ONCE`, branch
  `formal-ir-v72p1-addendum-clean`, root
  `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`, sequence
  `n64; n128 only iff n64 POSITIVE; n256 only iff n128 POSITIVE`, ceilings
  `144 / 44 / 1800 s / 120 s-per-call / RSS <2147483648 / one process`, command
  `exactly the packet Frozen run command, once`, afterward `one independent
  EVIDENCE_ACCESS: VERIFIED batch-end review`. No retry/repair/seed
  replacement-search/tuning/input change/L2-APP/D7-H/real-data/commit/push.
- Raw packet sha256 `f835649c8274caee77deec748f59b9d9247589c6478ddcb39f12b170823c9ddf`.
- This call wrote no result root, ran no `--batch`, touched no authorization file;
  only reads + `--profile-only` + tests in fresh gitignored basetemp.

### Pre-dispatch verdict

- `PRE_DISPATCH 7/7 PASS`. Proceeding to Phase-2 single authorized `--batch
  --execution-authorized` invocation. Grant consumed at command start.

## 2026-09-14 — D10 Batch A1 run evidence (AUTHORIZED_ONCE, GRANT_CONSUMED)

Single authorized invocation. One process. No retry/resume/repair/seed
replacement-search/tuning/input change/L2-APP/D7-H/DE/CAL-VAL/real-data/commit/push.
Exact and syndrome-valid counts kept SEPARATE (never merged).

### Command / exit / timestamps

- Command (exact, once):
  `.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch
  --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
- `EXIT_CODE:0`.
- Start `2026-09-14T06:25:55Z` (UTC; local `2026-09-14T14:25:57` in command_log).
- End `2026-09-14T06:26:45Z` (UTC; local `2026-09-14T14:26:45` in command_log).
- Stdout raw:
  `prior chain loaded ... / sampled matched blocks width=64 count=8 /
  width=128 count=8 / width=256 count=8 / built 18 graphs admitted=18 /
  dispatched width_results=['POSITIVE', 'AMBIGUOUS'] terminal=D10_L1_AMBIGUOUS /
  D10_L1 terminal=D10_L1_AMBIGUOUS calls=96 setup=44`.
- `GRANT_CONSUMED yes` (consumed at command start per authorization).

### Calls / setup / wall / per-call / RSS vs ceilings

- `scientific_l1_calls 96 <= 144 PASS`; `planned_l1_calls 144`.
- `setup_calls 44 <= 44 PASS` (= 18 graph constructions + 24 block samplings + 2 fixed).
- `wall_s 47.87750489698374 <= 1800 PASS` (outer 06:25:55Z->06:26:45Z ~50 s consistent).
- `max per-call wall_s 0.9959062389971223 <= 120 PASS`
  (`min 0.01664673798950389`; `l1_rows 96`, `call_idx 0..95`, `crash 0`).
- `peak_rss_bytes 124772352 < 2147483648 PASS`; `budget_violations []`;
  `budget_stop ""`. Single process.
- All resource predicates match frozen budgets (design section 6.1/spec SHALL).

### Admission per width (must be 18/18 or STOP-mismatch)

- `graphs 18 admitted 18 PASS` (`graph_records.csv`: every row `status ok`,
  `admitted True`).
- Per width: n64 6/6, n128 6/6, n256 6/6 (all `ok`+admitted, A1-A6 true;
  n256 graphs built for setup but 0 dispatched blocks by conditional stop).
- No construction/admission failure; no `ENGINEERING_BLOCKED` from admission.

### Per-graph + pooled EXACT counts (separate)

- n64 `PEG_DV3_MATCHED`: graph `2026092201 0/8`, `2026092202 0/8`,
  `2026092203 1/8`; pooled `1/24`.
- n64 `PEG_DV23_LAM2_045`: graph `2026092201 7/8`, `2026092202 7/8`,
  `2026092203 6/8`; pooled `20/24`.
- n128 `PEG_DV3_MATCHED`: graph `2026092204 0/8`, `2026092205 0/8`,
  `2026092206 0/8`; pooled `0/24`.
- n128 `PEG_DV23_LAM2_045`: graph `2026092204 5/8`, `2026092205 2/8`,
  `2026092206 3/8`; pooled `10/24`.
- n256 both arms: `0 blocks` (not dispatched; arm_summary rows `0/0`).
- Total `exact_count 31` (`summary.json`).

### Per-graph + pooled SYNDROME-VALID counts (separate, never merged)

- n64 `PEG_DV3_MATCHED`: graph `0/8, 0/8, 1/8`; pooled `1/24`.
- n64 `PEG_DV23_LAM2_045`: graph `7/8, 7/8, 6/8`; pooled `20/24`.
- n128 `PEG_DV3_MATCHED`: graph `0/8, 0/8, 0/8`; pooled `0/24`.
- n128 `PEG_DV23_LAM2_045`: graph `5/8, 2/8, 3/8`; pooled `10/24`.
- n256 both arms: `0/0` (not dispatched).
- Total `syndrome_valid_count 31` (`summary.json`). Exact-without-syndrome 0
  (verify invariant `exact -> syndrome_ok` holds: 31/31 identical).

### Width gates (frozen thresholds, conditional progression)

- n64: MIX `S_g 7,7,6 (all >=3 PASS)`, `E_g 7,7,6 (>=2 in 3/3 graphs PASS)`,
  `S_pool 20 >= 12 PASS`, `E_pool 20 >= 6 PASS`, DV3 `S_pool 1 <= 3 PASS`,
  `E_pool 1 <= 1 PASS` => `POSITIVE(n64) PASS` => n128 dispatched.
- n128: MIX `S_g 5,2,3 (2 < 3 FAILs POSITIVE-1)`, `E_pool 10`, `S_pool 10`,
  NEGATIVE requires `E_pool <= 2 and S_pool <= 4` (10/10 FAILs) => `AMBIGUOUS(n128)`
  => n256 NOT dispatched. No width skipped, no mid-width partial dispatch.
- `widths_dispatched [64, 128]`, `width_classifications {64: POSITIVE, 128: AMBIGUOUS}`.
- Thresholds match design section 6.2/spec SHALL exactly; no post-hoc change.

### Stored terminal

- `terminal D10_L1_AMBIGUOUS`, `terminal_reason progression complete`
  (`summary.json`). Valid frozen OpenSpec term (design section 6.4); evidence only,
  not route acceptance; D7-H not revived; claim ceiling unchanged
  (`synthetic finite-length L1-only diagnostic ...`).

### Root files + hashes (six-file evidence root)

- `arm_summary.csv 26bd36d2d981b8ff2ebb612f857b23e69ffa4a196979c1749f11dc1ee9ad09a0`
- `command_log.txt dbe271b803b7518459a92c20644ed37e35d4ed7bb1eacddd0b08fc43b6b6efb2`
- `graph_records.csv c678d00ea680fce01e45f5339e9555fedd5594594abd51f2666566d83714c7be`
- `l1_records.csv 87c4837a32d66682f22c0cf46e6d5dd3ecdbdb142ee3a16fd85f3f941c77c5cd`
- `manifest.json bc2ac507118a5eeb77b77f8b1e2fab0833172d497254908360f88a1472260d5f`
- `summary.json 98f0f75aa706a5020b122a229942e20e2cbb9f8834874b0e6624ef20fd1cdd6d`
- `manifest.json command` =
  `.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
  (base shape; authorized invocation added `--execution-authorized`).
- Failed partial root: none (exit 0, complete root); no repair/rerun performed.

### Authorization / commit / push state

- `AUTHORIZATION D10_MIXED_DEGREE_L1_BATCH_A1_AUTHORIZED_ONCE consumed`;
  no second invocation; no L2/APP/D7-H/DE/CAL-VAL/real-data.
- No commit, no push (branch `formal-ir-v72p1-addendum-clean` unchanged by this call
  except the log append + the single authorized result root + the gitignored
  pre-dispatch basetemp `workspace/d10_a1_predispatch_c9f1a2b4-1111-4222-8333-444455556666`).
- Next required: one independent `EVIDENCE_ACCESS: VERIFIED` batch-end review
  (not performed by this operator); review failure blocks use of evidence and
  grants no rerun.

## 2026-09-14 — D10 Batch A1 batch-end review (VERIFIED PASS)

- REVIEW_ID `D10-MIXED-DEGREE-L1-A1-REVIEW`, EVIDENCE_ACCESS VERIFIED, branch
  confirmed no switch (`formal-ir-v72p1-addendum-clean`).
- COMPLETENESS PASS: six root files sha256 all match (arm_summary
  `26bd36d2…`, command_log `dbe271b8…`, graph_records `c678d00e…`, l1_records
  `87c4837a…`, manifest `bc2ac507…`, summary `98f0f75a…`); single command_log
  pass; timestamps 14:25:57→14:26:45 local, EXIT 0.
- IDENTITIES PASS: 96 rows idx 0..95, crash 0, 96 unique keys, 2×2×3×8 plan
  exact, n256 zero rows, frozen block/graph seeds only, no `2026092210..15`.
- ADMISSION PASS: 18/18 A1-A6 independently recomputed all-true.
- COUNTS PASS (own recount): exact total 31 = syndrome-valid total 31,
  exact-without-syndrome 0; splits n64 DV3 [0,0,1]/1, n64 MIX [7,7,6]/20,
  n128 DV3 [0,0,0]/0, n128 MIX [5,2,3]/10, n256 0/0.
- GATES PASS: n64 POSITIVE(TRUE) → n128 dispatched; n128 AMBIGUOUS(TRUE: S
  5,2,3 fails P1, pools 10/10 fail P3 and NEGATIVE) → n256 undispatched;
  widths [64,128]; control never independent.
- TERMINAL PASS: `D10_L1_AMBIGUOUS` valid frozen term, follows from gates;
  evidence-only.
- BUDGETS PASS: 96/144, 44/44, wall 47.8775/1800, per-call max 0.9959/120,
  RSS 124772352<2147483648, violations [].
- NO-RETRY attestation + claim ceiling (synthetic L1-only; no
  FER/leakage/SKR/real-data/L2/D7-H).
- FINDINGS: BLOCKING none; NON-BLOCKING none (2s start-skew informational benign).
- VERDICT PASS; terminal recommendation
  `D10_MIXED_DEGREE_L1_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`;
  authorization consumed; no rerun; route decision main-thread only.
- Grant consumed, no second run authorized, no commit/push, memory triage pending.

## 2026-09-14 — main-thread A1 acceptance and route decision

Accepted as `D10_L1_AMBIGUOUS_RESULT_ACCEPTED_ROUTE_TO_R3_REPLICATION` under
the frozen synthetic L1-only ceiling. This is not a negative result: MIX beats
DV3 at n64 (20/24 vs 1/24) and n128 (10/24 vs 0/24), but n128 misses the
pre-frozen cross-graph/pool gate (5/2/3 across only three graphs). The evidence
cannot distinguish finite-width decay from graph-to-graph variability.

Next gate is implementation/readiness for a fresh-seed n128 replication and
conditional n256 scaling batch. A1 is not rerun and its seeds are not reused as
primary evidence. D7-H remains closed: until L1 recovery is shown stable across
fresh graphs at wider width, alternation would add layer-interface, schedule and
feedback/double-counting variables before the base-code effect is established.
No R3 execution is authorized by this decision.

## 2026-09-14 — R3 readiness complete pointer (no execution)

- D10 R3 fresh-graph scaling readiness (R301–R310) is complete with terminal
  `D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no
  execution; R310 `D10-R3-R310` VERIFIED pass-with-comments, no blocking).
- Records: `docs/research_cycles/V72P2D10-R3-FRESH-SCALING/READINESS_R1.md`,
  `docs/research_cycles/V72P2D10-R3-FRESH-SCALING/EXPLORATION_LOG.md`.
- Decoder calls 0; scientific calls 0; future R3 root absent; no commit/push.
  A1 evidence unmodified; no R3 execution authorized.
