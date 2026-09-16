# D6 R1c-A5+A6 (merged) — validity closure, admissible repair, R1d readiness, and T2 structure acceleration

Status: `FROZEN_TASK_PACKET_R1C_A5A6` (main-thread route decision; **zero decoder**)
Branch: `formal-ir-v72p1-addendum-clean`
Expected starting HEAD: `1a09220a`
Predecessor gate: `D6_GRAPH_MOTHER_R1C_A3_BLOCKED_AWAITING_MAIN_THREAD_ROUTE`
Supersedes (absorbs in full): `D6_R1C_A5_VALIDITY_REPAIR_R1D_READINESS_TASK_PACKET.md`
and `D6_R1C_A6_STRUCTURE_PERF_T2_ACCELERATION_TASK_PACKET.md`.

## 0. Authority, adjudication, and scope

Main-thread adjudication (recorded, not delegated):

- R1c-A3 is accepted as a **solidified implementation/structure-blocked
  development attempt** (`PASS_BLOCKED_RUN`). The stored
  `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` label stays preserved and stays
  **unsupported**; recomputed `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` governs.
  None of the 184 R1c-A2 calls may be reused for a successor claim.
- R1c-A4 is accepted as `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` on the
  structure path only (scaling structure 10897.7 s -> 2.5 s, n64 bit-equal).
- Main-thread route decision: **validity closure + admissible repair + R1d
  readiness (Track A), plus exact-equivalent T2 structure acceleration and a
  repo-wide slow-task inventory (Track B)**, executed as one operator run with
  two separately committed and separately reviewed tracks.

This packet authorizes **zero decoder calls**. It authorizes OpenSpec,
structure-only analysis, production gate/execution-integrity code, an
exact-output-preserving T2 optimization, tests, benchmarks, independent
reviews, and a candidate R1d contract. It never authorizes an R1d execution,
rerun, resume, `--phase`, G1/G2, VAL, or real/raw data.

Return only when every frozen item in both tracks is complete, or on one
concrete blocker that would change the frozen scientific contract.

## 1. Decisive facts established before this packet

### 1.1 The frozen eligibility gate never checks check-node degree

`d5.audit_prefix` gates **variable** degree (`deg_min >= 2`) and records
`row_degree_histogram`, but its `passed` flag never constrains **check** row
degree. The D6 runner's `eligible` is `rep["passed"] and
duplicate_projective_columns == 0 and base_pair_duplicates == 0 and
support_triple_duplicates == 0` (`+ m_cycle_rank == 0` for M arms); check degree
is recorded only as `row_degree_max` / `row_degree_sumsq`. The frozen heavy
packet §6 hard-gate list also omits it. The historical decoder hard-fails on such
rows at `v35_algorithm_development.py:465`
(`if dc < 2: raise ValueError("Check node requires degree >= 2")`).

### 1.2 Main-thread read-only validity audit (structure-only, zero decoder)

Independent main-thread audit over every arm x width x layer x frozen prefix
(task-external artifact
`workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/`):

| arm | f1.0 | f1.2 | square | frozen-gate verdict |
|---|---|---|---|---|
| B0/B1 | 3 | 3 | 3 | n64 pass; n128 L2 base-pair dup; n256 L1/L2 disconnected |
| T1_PEG | >=2 | >=2 | >=2 | eligible everywhere |
| T2_CYCLE_GREEDY | >=2 | >=2 | >=2 | n64 rank 63/62 != 64 |
| T3_SC_W4 | 3 | **1** (10–81 rows) | **1** (12–81 rows) | ineligible once I1 applies |
| T4_SC_W8 | >=2 | **1** (8–40 rows) | **1** (8–77 rows) | ineligible once I1 applies |
| M1_FOREST_MAX | 2 | **1** (8–40 rows) | **1** (14–83 rows) | ineligible once I1 applies |
| M2_FOREST_HALF | 2 | 2 | **1** (L2, 6–25 rows) | n64 rank 48/61; n256 L2 rank 200 |

Mechanism: rows in `[k_min, m_max)` can only receive expansion edges, so a row
covered by exactly one variable window ends at degree 1. Cross-check: replaying
the frozen eligibility reproduces the A2 selection `{B0,B1,T1,T3,M1}` exactly.

### 1.3 Why a pure gate is not viable, and why T2 must also be accelerated

- Pure gate: at n64 only `{B0,B1,T1}` remain eligible; there is **no eligible M
  arm**, so the frozen §8.4 fallback pair loses its M leg and the D6 question
  cannot be asked of the SC or accumulator families at all.
- T2 cost: candidates per variable `|B|(|B|-1)/2*(|C|-2)` = 72,912 / 598,878 /
  4,853,940 at n64/n128/n256 (totals 4.67M / 76.7M / 1.24B); measured
  ~8.3–8.9 us per candidate -> ~41 s / ~650 s / ~2.85 h per layer. A4's pruning
  removed T2 from scaling only because T2 was not a frozen fallback. T2
  minimizes four-cycles first, so a repaired T2 is a plausible `best_T`; if it
  becomes the fallback, the 2.85 h/layer cost returns and the run cannot finish
  inside the frozen chunk budget (`chunk >= 5400 s` blocks further dispatch).
  Acceleration is therefore a **readiness precondition**, not cosmetics.

## 2. Hard boundaries (both tracks)

Allowed paths:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
- `scripts/v72p2d6_graph_mother_development.py`
- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`
- the existing `v72p2d6-gf32-graph-mother-successor` OpenSpec change
- new A5/A6 documents under `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/`
- `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md` (append-only, after final
  independent PASS)
- fresh task-owned roots `workspace/<name>_<uuid>/`

Forbidden:

- any decoder call, real or fake, outside unit tests with an explicit fake
  decoder; any `--phase`; G1/G2/VAL/real/raw; any new scientific sample
- editing `v72p2d5_gf32_rate_mother.py`, `v35_algorithm_development.py`, `src/`,
  `experiments/`, `tools/`, or any D5/D4 production module
- modifying, deleting, regenerating or restaging anything in
  `workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b` or the
  committed A2/A3 evidence paths
- changing frozen knobs: arms inventory, seeds by role, row budgets, prior,
  decoder, coefficient seeds/stream, SC widths 4/8, M `N2` rules, terminal
  thresholds, selection/advancement/ordering, budgets
- changing the T2 choice key, its field order, tie-breaks, candidate set, or
  greedy order; any float approximation of an integer key; any unproven
  shortlist; any repair or speedup chosen by decoder outcome (no decoder may run)
- persisting a new six-file schema in this packet (schema changes are proposed in
  the R1d readiness package, not landed)
- push, force, reset, checkout, stash, clean, amend, rebase, EOL normalization,
  broad staging, unrelated-file cleanup, or `git add -A`
- marking anything accepted, or requesting/assuming execution authorization

## 3. Track A — validity closure, admissible repair, R1d readiness

### 3.1 A5-01 independent frozen validity matrix

Reproduce the full matrix with your own implementation (do not import or inherit
the main-thread artifact; use it only as a later cross-check and report any
disagreement). Cover every arm x {64,128,256} x {L1,L2} x every frozen prefix,
plus T2 at n128/n256 (structure-only, not dispatched there). Per cell record:
`row_degree_min`, rows with degree < 2, row-degree histogram, `variable_degree_min`,
rank, zero rows/cols, components, largest-component fraction, duplicate
projective columns, base-pair/triple duplicates, M degree-2 cycle rank,
girth/`NOT_COMPUTED`, determinism replay, and the current frozen `eligible` flag.
Deliver a machine-readable CSV plus a human table in
`D6_GRAPH_MOTHER_VALIDITY_R1C_A5.md`.

Acceptance: A5-A01 matrix complete/reproducible; A5-A02 the frozen `eligible`
flag and the A2 five-arm selection reproduced exactly.

### 3.2 A5-02 root cause per family, with proofs

Code-independent structural proof plus structure-only rebuild per family (A3
style): T3/T4 uncovered rows in `[k_min, m_max)`; M1/M2 forced by the frozen `N2`
rule plus the two-zone split and forest requirement; T2 n64 rank deficiency;
B0/B1 n128 L2 base-pair duplicate and n256 disconnection (controls, **must not
be modified**, recorded as dispatchable-set bounds). Add a **decoder
precondition inventory** mapping every structural precondition of the historical
decoder/adapter to an existing frozen gate or to the new invariant, so the whole
gate-gap class is closed, not just this instance.

### 3.3 A5-03 land the invariant gate (production, fail-closed)

Invariant **I1 (frozen)**: for every dispatched `(arm, n, layer, prefix)`, every
check row has degree >= 2, in addition to every existing frozen hard gate.

1. D6 module: compute `row_degree_min` / `rows_below_degree_2` in `audit_extra`
   and expose them. No D5 edits.
2. Runner `eligible`: existing condition AND `row_degree_min >= 2`.
3. Build-time fail-closed: an arm whose dispatched prefix violates I1 is
   recorded structurally ineligible (matching the frozen gate semantics) and can
   never produce a dispatchable matrix.
4. Dispatch-time guard: no decoder cell may be constructed from a violating
   matrix; the guard fails closed with a clear error.
5. `--verify`: independent I1 recomputation over `structure_records.csv`,
   reported as INFO for the historical root (which predates the gate) and as
   PASS/FAIL for roots written after this packet. Never rewrite the historical
   root or its stored fields.

Tests (fake-only, task-owned basetemp): degree-1 detected; degree-2 boundary
accepted; degree-0 still blocked by the zero-row gate; ineligibility propagates
to selection; the guard refuses dispatch; the historical six-file root verifies
unchanged; the new diagnostic is not persisted into the frozen schema.

Acceptance: A5-A03 gate landed/tested; A5-A04 zero decoder calls; A5-A05
historical root fields/mtimes/verify output unchanged.

### 3.4 A5-04 admissible repair study (structure-only, no decoder)

Admissibility of a repair rule `R` for family `F`:

- **R1 determinism**: one uniform documented rule per family, frozen in the
  prereg before evaluation; no randomness beyond the frozen coefficient stream;
  no seed/parameter search; at most three documented candidate rules per family,
  all preregistered before any is evaluated.
- **R2 frozen knobs preserved**: `n`; the three prefix row counts per
  (layer,width); SC widths 4/8; M `N2` rules; degree-3 variables stay degree 3
  and M chain variables stay degree 2; the two-zone split (base `k_min`,
  expansion `m_max`); the common coefficient stream keyed by
  `(n,layer,column,edge_index)`; family identity (SC local-window coupling; M
  degree-2 support a simple forest over the first `k_min` checks).
- **R3 validity**: I1 plus every existing frozen hard gate at every dispatched
  prefix of every width/layer, proven by the full matrix.
- **R4 no new defects**: no parallel edges, no new duplicate/proportional
  columns, no new base-pair/triple duplicates, determinism replay equal.
- **R5 disclosure**: exact structural diff versus the frozen builder per
  `(arm,n,layer)` — changed support entries, degree histograms, rank,
  components, girth, 4-cycles, incidence max, M cycle rank, selection-key
  components.

Evaluation order frozen before evaluating: fewest changed support entries, then
lower maximum row degree, then preregistered rule ID. No decoder-based criterion
exists or may be introduced. If no rule satisfies R1–R5, record
`STRUCTURALLY_INFEASIBLE_AS_FROZEN` with the proof plus a **redefinition menu**
(<=3 options) stating which frozen knob changes, the structural consequences, and
why it is minimal — marked `REQUIRES_MAIN_THREAD_RULING` and **not landed**.

Repair candidates live in a clearly separated sandbox section/module; production
`build_support` output for every `(arm,n,layer)` stays byte-identical in this
packet. Deliverable: `D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md` + matrix/CSV.

Acceptance: A5-A06 every violating family repaired admissibly (with proof) or
declared infeasible with a menu; A5-A07 sandbox matrices satisfy I1 and all
frozen gates everywhere; A5-A08 T1/B0/B1 production outputs byte-identical.

### 3.5 A5-06 execution-integrity terminal (land, tests only)

Any attempted (non-placeholder) crash or nonfinite cell anywhere in a run forces
`D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (degree invariant) or
`D6_GRAPH_ATTEMPTED_CELL_INVALID` (other), overriding recovery/no-recovery
classification; `call_idx=-1` placeholders never count; the historical root is
never re-run or rewritten and its verify output still reports stored versus
recomputed with the agreement flag.

Acceptance: A5-A11 fake-only tests for canary/scaling/confirmation branches;
A5-A12 no historical artifact changed.

### 3.6 A5-10 R1d structure-cost guard

For the candidate R1d arm set, profile structure builds at every dispatched width
(fresh roots, zero decoder) and project wall against the chunk budget
(`>= 5400 s` blocks dispatch) and the 12 h run wall. Any projected breach must
route to the Track B acceleration numbers, or declare that arm inadmissible at
that width with the structural reason.

Acceptance: A5-A18 structure-cost projection recorded with the breach decision.

### 3.7 A5-08 R1d readiness package (no execution, no authorization)

Create `D6_GRAPH_MOTHER_R1D_READINESS_R1C_A5.md`, marked
`NOT_AUTHORIZED / REQUIRES_MAIN_THREAD_RULING_AND_AUTHORIZATION`: candidate arm
set (controls + repaired families + eligible-only fallback branch); the frozen
validity matrix required before any dispatch; unchanged frozen science
(decomposition, E2 prior, decoder/schedule/damping, row points, seeds by role,
budgets 2500 calls / 12 h / 120 s / RSS < 2 GiB / no retry, selection,
advancement, scaling, terminals); the evidence schema change listed explicitly
as requiring approval; the crash-precedence terminal semantics; the no-reuse rule
for the R1c-A2 root; a Pre-EXECUTE checklist (output-root absence, authorization
keys, G2 absence, protected-root metadata, test set, exact command); and an
explicit claim ceiling. Update `cycle_state.yaml` (`next_gate` only; every
authorization key stays false; `evidence_root`/`terminal` stay null). No R1d root
may be created.

## 4. Track B — T2 exact-equivalent acceleration and slow-task inventory

Track B code work starts **after** the Track A gate commit lands (same files).

### 4.1 A6-01 profile first, freeze the baseline

Fresh roots, structure-only, workers 18 and 1. Per `(n, layer)` for T2: candidate
counts, per-variable wall distribution, `affected`-update share, allocation/GC
share, peak RSS. Per arm at n64 and per fallback at n128/n256: A4-shape baseline
for regression comparison. Freeze the baseline table in the prereg commit before
touching code.

Acceptance: A6-A01 baseline table frozen and reproducible.

### 4.2 A6-02/A6-03 implement and prove

Equivalence principle (the licence): the candidate set is fixed by
`used_pairs`/`used_triples`; the key's last field is the sorted triple, which
uniquely identifies a candidate; therefore the lexicographic argmin is unique and
order-independent. Vectorization and staged filtering are allowed; changing the
key, tie-break, candidate set or greedy order is not.

Allowed techniques: staged lexicographic filtering (compute the cheap `four`
prefix for all candidates first — measured 0.27 us vs 1.45 us full key — then
evaluate later fields only for candidates tied on the minimal prefix);
vectorized candidate enumeration; integer-encoded pair/triple membership;
incremental maintenance of `pair_counts`, `pair_to_cols`, `inc_per_col`,
`total_four`, `max_pair`, `incid_max`, degrees; skipping the `affected` rebuild
for candidates eliminated earlier.

Equivalence gates (all must pass):

1. support-array equality for all 8 arms x 2 layers x {64,128,256} against the
   reference builder (one n256 T2 reference run may be performed inside a 4 h
   total structure-only budget; document it);
2. per-variable chosen-triple trace equality for T2 at every width;
3. committed R1c-A2 n64 `structure_records.csv` rows byte-identical (existing
   `r1c_a4_equivalence_committed_n64` plus a T2-specific test);
4. structural ordering, eligibility flags, `selected_arms.json` unchanged;
5. determinism replay equal; sequential and parallel paths equal;
6. the exactly-two-constructions property and A4 pruning unchanged;
7. if the Track A study produced a sandbox repaired T2, re-run gates 1–3 against
   that sandbox builder (its own unoptimized reference) so the acceleration is
   proven for whichever T2 lands in R1d.

Performance acceptance (fresh roots, cold and warm, A4 protocol): T2 per-layer
n64 <= 5 s, n128 <= 90 s, n256 <= 600 s (target >= 10x, report the measured
factor); n64 all-8 build <= 8 s; non-T2 arms no regression > 10 %; scaling
fb-only within 2x of the A4 after-side (2.5 s / 2.7 s); peak aggregate RSS
< 2 GiB; zero decoder calls; no retry framework. If the target is not met,
return `PERF_TARGET_NOT_MET` with the profile and the remaining hot loop, and
keep the reference path intact.

Tests must fail if the key or tie-break changes, a candidate the reference would
evaluate is skipped, the greedy order changes, sequential/parallel differ, T2
outputs differ from committed evidence, or the A4 guards regress.

### 4.3 A6-04 repo-wide slow-task inventory (read-only, no implementation)

Measure and tabulate: v38 T0/T1 cold+warm and the residual hot spot (lane-A
construction ~20 s = ~3.78M tiny `compute_gf32_rank` calls; perf-v38 already
delivered 1513 s -> 807 s on the full file); the two orchestration tests (~340 s
each); D5/D6 structure helpers (`audit_prefix` GF32 rank, `compute_girth`,
`_build_M_support` pair enumeration, `build_dv3_nested_support`); V30R-style
DE/decoder phases (74.8 s / 719.9 s); any other concretely measured heavy
command. Deliver a prioritized menu: measured wall, hot symbol, suspected cause,
expected gain, semantic risk, whether OpenSpec is needed. **Do not implement any
of it here.**

Acceptance: A6-A04 menu with measured numbers for every listed item.

## 5. Reviews (independent, read-only; reviewer edits only its own file)

1. `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1C_A5.md` — the I1 gate, the
   execution-integrity fix, tests, and the claim that production builder outputs
   are unchanged.
2. `D6_GRAPH_MOTHER_VALIDITY_REVIEW_R1C_A5.md` — validity matrix, per-family
   proofs, repair admissibility, sandbox matrices, readiness package. Must
   independently recompute sampled cells and re-check admissibility against the
   prereg.
3. `D6_GRAPH_MOTHER_PERFORMANCE_REVIEW_R1C_A6.md` — T2 prereg vs implementation,
   equivalence evidence (including the sandbox-T2 gate), benchmark arithmetic,
   and the claim that A4 gains did not regress.

State the independence mechanism if a dedicated reviewer tool is unavailable; do
not inherit the main-thread conclusion. Allowed verdicts:

- A5: `D6_R1C_A5_REVIEW_PASS_R1D_READY` / `PASS_ELIGIBLE_ONLY_BRANCH` / `FAIL`
- A6: `D6_R1C_A6_REVIEW_PASS` / `PERF_TARGET_NOT_MET` / `FAIL`

At most one rework round per review; a second blocking finding returns as a
blocker. Reviews never authorize execution.

## 6. Commits and closeout

Exact-path staged, in this order (no `git add -A`, no push):

1. `docs(v72p2d6): freeze R1c-A5/A6 validity, repair and performance contracts`
   — A5 prereg/OpenSpec delta + A6 prereg (both frozen before any code);
2. `feat(v72p2d6): R1c-A5 check-degree invariant gate` — gate + execution
   integrity + tests;
3. `docs(v72p2d6): R1c-A5 validity matrix, repair study and R1d readiness` —
   matrix, root causes, repair study, readiness package, `cycle_state.yaml`
   `next_gate`;
4. `perf(v72p2d6): R1c-A6 exact-equivalent T2 acceleration` — implementation +
   tests;
5. `docs(v72p2d6): R1c-A6 performance report and slow-task inventory` —
   benchmark tables + inventory menu;
6. `docs(v72p2d6): accept R1c-A5/A6 reviews` — the three review files;
7. `docs(v72p2d6): record R1c-A5/A6 closeout` — append-only decision-log +
   `AGENT_PROJECT_MEMORY.md` + `cycle_state.yaml`.

Run `py_compile` on touched modules, focused D6 tests, and the established
seven-file non-perf regression suite with a fresh UUID basetemp; run perf-v38
only if a scoped dependency makes it materially necessary and record the choice.

## 7. Acceptance IDs and return contract

- A5-A01 validity matrix complete and reproducible
- A5-A02 frozen `eligible` flag and A2 five-arm selection reproduced exactly
- A5-A03 I1 gate landed with build-time and dispatch-time fail-closed behaviour
- A5-A04 zero decoder calls in the entire packet
- A5-A05 historical root fields, mtimes and verify output unchanged
- A5-A06 every violating family repaired admissibly or declared infeasible with
  a redefinition menu
- A5-A07 sandbox matrices satisfy I1 and all frozen gates everywhere
- A5-A08 T1/B0/B1 production outputs byte-identical to HEAD
- A5-A09 performance/RSS/replay reported against the A4 baseline
- A5-A10 no decoder records in any A5/A6 root
- A5-A11 crash-precedence execution terminal landed with fake-only tests
- A5-A12 no historical artifact changed
- A5-A13 independent reviews recorded with allowed verdicts
- A5-A14 R1d readiness package complete, marked not authorized
- A5-A15 cycle_state/decision-log/memory updated append-only, all auth keys false
- A5-A16 focused + seven-file non-perf suites green (or scoped failures named)
- A5-A17 no push; no acceptance; G2 absent
- A5-A18 R1d structure-cost projection recorded, with any chunk-budget breach
  routed to the Track B numbers or an explicit width-inadmissibility declaration
- A6-A01 T2 baseline table frozen and reproducible
- A6-A02 T2 key/candidate-set/greedy-order semantics unchanged
- A6-A03 all seven equivalence gates pass (including the sandbox-T2 gate)
- A6-A04 repo-wide slow-task inventory with measured numbers
- A6-A05 performance targets met, or `PERF_TARGET_NOT_MET` with profile evidence
- A6-A06 A4 gains not regressed (n64, scaling fb-only, RSS, pruning, two-builds)
- A6-A07 zero decoder calls in every A6 root; no retry framework
- A6-A08 independent performance review PASS (or NOT_MET recorded)

Return only deltas: commits and file manifests; the validity matrix summary and
per-family proofs; the gate/execution-integrity changes with test results; the
repair rules chosen, their structural diffs, resulting eligible sets, and any
`STRUCTURALLY_INFEASIBLE_AS_FROZEN` menu; T2 baseline/after tables, equivalence
matrix, measured speedups, RSS and zero-decoder accounting; the slow-task menu;
the three review verdicts; the R1d readiness statement; protected-root and
authorization state; and the A5-A01..A6-A08 table.

End exactly:

`D6 R1c-A5/A6 合并任务已完成并独立复核：I1（检查行度≥2）缺陷已证明并被闸门封堵、修复候选与 R1d 就绪包待主线程裁决；T2 精确等价加速达成（或 PERF_TARGET_NOT_MET 并附热点证据），A4 收益未回退；全程零 decoder 调用，R1c-A2 根保持 immutable，授权全 false，G2 未授权、未执行。`
