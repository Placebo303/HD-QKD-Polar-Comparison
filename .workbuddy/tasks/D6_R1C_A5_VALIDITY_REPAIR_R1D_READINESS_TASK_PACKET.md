# D6 R1c-A5 — structural-validity closure, admissible arm repair, and R1d readiness

> **SUPERSEDED (2026-09-09):** absorbed in full by
> `D6_R1C_A5A6_VALIDITY_REPAIR_AND_PERF_TASK_PACKET.md` (merged A5+A6 run).
> Retained for traceability only — do not execute from this file.

Status: `FROZEN_TASK_PACKET_R1C_A5` (main-thread route decision; zero decoder)
Branch: `formal-ir-v72p1-addendum-clean`
Expected starting HEAD: `1a09220a`
Predecessor gate: `D6_GRAPH_MOTHER_R1C_A3_BLOCKED_AWAITING_MAIN_THREAD_ROUTE`

## 0. Authority, adjudication, and this packet's scope

Main-thread adjudication (recorded, not delegated):

- R1c-A3 is accepted as a **solidified implementation/structure-blocked
  development attempt** (`D6_R1C_A3_PRE_RESULT_REVIEW_PASS_BLOCKED_RUN`). The
  stored `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` label stays preserved and stays
  **unsupported**; recomputed `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` governs.
  No recovery/no-recovery, FER, leakage, or key-rate claim is accepted from the
  R1c-A2 root, and none of its 184 calls may be reused for a successor claim.
- R1c-A4 is accepted as `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` on the
  structure path only (scaling structure 10897.7 s -> 2.5 s, n64 bit-equal).
  It authorizes no run.
- Main-thread route decision (this packet): **route (a), validity closure plus
  admissible repair plus R1d readiness**, not route (b) "stop the T3/M1 line",
  and not a pure minimum-degree gate. Section 1.3 gives the decisive reason.

This packet authorizes **zero decoder calls**. It authorizes OpenSpec,
structure-only analysis, production gate/execution-integrity code, tests,
independent review, and a candidate R1d contract. It never authorizes an R1d
execution, a rerun, a resume, a `--phase`, G1/G2, VAL, or real/raw data.

Return only when every frozen item is complete, or on one concrete blocker that
would change the frozen scientific contract.

## 1. Decisive facts established before this packet

### 1.1 The frozen eligibility gate never checks check-node degree

`d5.audit_prefix` gates **variable** degree (`deg_min >= 2`) and records
`row_degree_histogram`, but its `passed` flag never constrains **check** row
degree. The D6 runner's `eligible` (in `build_structures*`) is
`rep["passed"] and duplicate_projective_columns == 0 and
base_pair_duplicates == 0 and support_triple_duplicates == 0`
(`+ m_cycle_rank == 0` for M arms). Check degree is recorded only as
`row_degree_max` / `row_degree_sumsq`; there is no `row_degree_min`. The frozen
heavy packet §6 hard-gate list also omits it.

The historical decoder hard-fails on such rows at
`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:465`
(`if dc < 2: raise ValueError("Check node requires degree >= 2")`).

### 1.2 Main-thread read-only audit (structure-only, zero decoder)

An independent main-thread audit (`build_support` + `assign_mother_from_support`
+ `d5.audit_prefix` over every arm x width x layer x frozen prefix; task-external
artifact `workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/`)
finds the defect is far wider than the A2 run could expose, because the A2 run
dispatched only the five arms the incomplete gate selected
(`B0, B1, T1, T3, M1` — reproduced exactly by this audit).

| arm | f1.0 prefix | f1.2 prefix | square prefix | frozen-gate verdict |
|---|---|---|---|---|
| B0_D5_DV3_NATIVE | min check deg 3 | 3 | 3 | n64 pass; n128 L2 base-pair dup; n256 L1/L2 disconnected |
| B1_D5_DV3_COMMON_LABELS | 3 | 3 | 3 | same as B0 |
| T1_PEG_DV3 | >=2 | >=2 | >=2 | eligible at every width/layer/prefix |
| T2_CYCLE_GREEDY_DV3 | >=2 | >=2 | >=2 | n64 rank 63/62 != 64 (ineligible) |
| T3_SC_DV3_W4 | 3 | **1** (10–81 rows) | **1** (12–81 rows) | ineligible once I1 is enforced |
| T4_SC_DV3_W8 | >=2 | **1** (8–40 rows) | **1** (8–77 rows) | ineligible once I1 is enforced |
| M1_ACCUMULATOR_FOREST_MAX | 2 | **1** (8–40 rows) | **1** (14–83 rows) | ineligible once I1 is enforced |
| M2_ACCUMULATOR_FOREST_HALF | 2 | 2 | **1** (L2, 6–25 rows) | n64 rank 48/61; n256 L2 rank 200; plus L2 square deg-1 |

Per-cell exact numbers, histograms, and the failing frozen criterion for every
blocked cell are in that artifact. The gate defect is uniform: rows in
`[k_min, m_max)` receive only expansion edges, so any such row covered by
exactly one variable's window ends at check degree 1.

### 1.3 Why a pure gate is not a viable route

Enforcing `min check degree >= 2` on the frozen builders leaves exactly
`{B0, B1, T1}` eligible at n64. That has three consequences: the T finalist set
is `{T1}`; **no M arm is eligible**, so the frozen §8.4 fallback pair
(`best_T`, `best_M`) degenerates and the scaling branch loses its M leg; and the
n64 canary would re-test an arm whose R1c-A2 canary was already `f1.2 exact 0/4`.
A pure gate therefore cannot answer the D6 question for the SC and accumulator
families at all. The route must repair construction validity, and must prove
the repair is structural, deterministic, and non-tuned.

### 1.4 What is not in question

The frozen scientific controls (decomposition, E2 prior, GF32 decoder, cold
start, `max_iter=90`, `damping=1.0`, L1-then-APP-L2, exact/syndrome separation,
row points, seeds by role, budgets, terminals) stay unchanged. This packet does
not revisit any of them and does not touch the R1c-A2 root.

## 2. Hard boundaries

Allowed production paths:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
  (D6 module only: new diagnostics, build-time invariant enforcement, repair
  candidates in a clearly separated sandbox section)
- `scripts/v72p2d6_graph_mother_development.py` (gate wiring, dispatch-time
  guard, execution crash-precedence terminal)
- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`
- the existing `v72p2d6-gf32-graph-mother-successor` OpenSpec change
  (proposal/design/tasks/spec + `R1C_parallel_revision.md` A5/R1d delta)
- new A5 documents under `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/`
- `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md` (append-only, after final
  independent PASS)
- fresh task-owned roots under `workspace/<a5-name>_<uuid>/`

Forbidden:

- any decoder call, real or fake, outside unit tests that pass an explicit fake
  decoder; any `--phase`; G1/G2/VAL/real/raw; any new scientific sample
- editing `v72p2d5_gf32_rate_mother.py`, `v35_algorithm_development.py`, `src/`,
  `experiments/`, `tools/`, or any D5/D4 production module
- modifying, deleting, regenerating, or restaging any file in
  `workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`, or the
  committed A2/A3 evidence paths
- changing frozen knobs: arms inventory, seeds by role, row budgets, prior,
  decoder, coefficient seeds/stream, SC widths 4/8, M `N2` rules, terminal
  thresholds, selection/advancement/ordering rules, budgets
- random search, seed tuning, parameter sweep, or any repair chosen by decoder
  outcome (no decoder may run, so any such choice is a contract violation)
- changing the persisted six-file schema (`structure_records.csv` header,
  `summary.json`/`manifest.json` keys) in this packet; schema changes are
  proposed in the R1d readiness package, not landed
- push, force, reset, checkout, stash, clean, amend, rebase, EOL normalization,
  broad staging, or unrelated-file cleanup; never `git add -A`
- marking any result accepted, or requesting/assuming execution authorization

## 3. A5-01 — independent frozen validity matrix

Independently reproduce the full structural-validity matrix with your own
implementation (do not import or inherit the main-thread artifact; use it only
as a later cross-check, and report any disagreement as a finding):

- every arm in `ARMS` x n in {64,128,256} x layer in {L1,L2} x every frozen
  prefix of that layer/width, plus the full-matrix row for n=128/256 for T2
  (structure-only, it is cheap; T2 is not dispatched at scaling);
- per cell: `row_degree_min`, number of rows with degree < 2, full row-degree
  histogram, `variable_degree_min`, rank, zero rows/cols, components,
  largest-component fraction, duplicate projective columns, base-pair
  duplicates, triple duplicates, M degree-2 cycle rank, girth/`NOT_COMPUTED`,
  determinism replay equality, and the frozen `eligible` flag as currently
  computed;
- a machine-readable CSV plus a human table.

Deliverable: `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.md` (with the CSV path inside it)
under a fresh task-owned root, plus the matrix reproduced as a table in the A5
prereg/OpenSpec delta is not required — the report is authoritative.

Acceptance: A5-A01 matrix complete and reproducible; A5-A02 the current frozen
`eligible` flag and the five-arm A2 selection are reproduced exactly (this is
the cross-check that the audit path is faithful).

## 4. A5-02 — root cause per family, with proofs

For each violating family produce a code-independent structural proof plus a
structure-only rebuild, in the A3 style:

- T3/T4 (SC): identify exactly which rows in `[k_min, m_max)` end at degree 1
  and why the frozen window/tie-break rule leaves them uncovered; prove the
  condition recurs at every width and layer.
- M1/M2 (accumulator forest): prove the degree-1 set is forced by the frozen
  `N2` rule plus the two-zone split (base zone `k_min`, expansion zone
  `m_max`), including the interaction with the forest requirement and the
  degree-balanced lexicographic base-pair choice.
- T2: prove the n64 rank deficiency (rank 63/62 vs 64) and state whether it is
  intrinsic to the frozen cycle-greedy key or a tie-break artifact.
- B0/B1: prove the n128 L2 base-pair duplicate and the n256 disconnection are
  properties of the frozen D5 native support at widths never before dispatched.
  **These are controls and must not be modified**; record them as facts that
  bound the successor's dispatchable set.

Also deliver a **decoder precondition inventory** (A5-05): enumerate every
structural precondition the historical decoder and adapter impose (start from
`v35_algorithm_development.py` check/variable update paths and the D5 adapter),
and map each one to an existing frozen gate or to the new invariant. The point
is to close the whole class of gate gaps, not only this instance.

Deliverable: sections in `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.md`.

## 5. A5-03 — land the invariant gate (production, fail-closed)

Invariant **I1 (frozen)**: for every dispatched `(arm, n, layer, prefix)`, every
check row has degree >= 2, in addition to every existing frozen hard gate.

Implement the smallest correct change:

1. D6 module: compute `row_degree_min` (and `rows_below_degree_2`) in
   `audit_extra`; expose it to callers. No D5 edits.
2. Runner `eligible`: existing condition AND `row_degree_min >= 2`.
3. Build-time fail-closed: a builder that would emit a prefix violating I1 for a
   dispatched arm must not silently produce a dispatchable matrix — either the
   arm is recorded structurally ineligible, or the build raises
   `D6StructureBlocked`. Choose the behaviour that matches the frozen gate
   semantics (ineligible, recorded) and state it.
4. Dispatch-time guard: no decoder cell may be constructed from a matrix whose
   dispatched prefix violates I1; a guard that fails closed with a clear error.
5. `--verify`: add an independent I1 recomputation over `structure_records.csv`
   rows, reported as INFO for the historical root (which predates the gate) and
   as a PASS/FAIL check for roots written after this packet. Do not rewrite the
   historical root or its stored fields.

Tests (fake-only, task-owned basetemp) must cover: degree-1 row detected;
degree-2 boundary accepted; a matrix with a degree-0 row still blocked by the
existing zero-row gate; I1 ineligibility propagates to arm selection; the guard
refuses dispatch; the historical six-file root verifies unchanged; the new
diagnostic is not persisted into the frozen schema.

Acceptance: A5-A03 gate landed and tested; A5-A04 no decoder call anywhere;
A5-A05 the historical root's stored fields and mtimes are unchanged.

## 6. A5-04 — admissible repair study (structure-only, no decoder)

Main-thread ruling on admissibility. A repair rule `R` for family `F` is
admissible only if all of the following hold:

- **R1 determinism**: single uniform rule per family, documented in the prereg
  before evaluation; no randomness beyond the frozen coefficient stream; no
  seed/parameter search; at most three documented candidate rules per family,
  all preregistered before any is evaluated.
- **R2 frozen knobs preserved**: `n`; the three prefix row counts per
  (layer,width); SC widths 4/8; M `N2` rules (`MAX = k_min-1`,
  `HALF = floor((k_min-1)/2)`); degree-3 variables stay degree 3 and M chain
  variables stay degree 2; the two-zone split (base zone `k_min`, expansion zone
  `m_max`); the common coefficient stream keyed by `(n,layer,column,edge_index)`;
  family identity (SC = local-window coupling; M = degree-2 support is a simple
  forest over the first `k_min` checks).
- **R3 validity**: I1 plus every existing frozen hard gate holds at every
  dispatched prefix of every width and layer, proven by the full matrix.
- **R4 no new defects**: no parallel edges, no new duplicate/proportional
  columns, no new base-pair/triple duplicates, determinism replay equal.
- **R5 disclosure**: report the exact structural diff versus the frozen builder
  per `(arm,n,layer)` — changed support entries, row/column degree histograms,
  rank, components, girth, 4-cycles, incidence max, M cycle rank, and the frozen
  structural selection key components.

Evaluation order (frozen before evaluating): prefer the rule that satisfies
R1–R4 with the fewest changed support entries; break ties by lower maximum row
degree, then by preregistered rule ID. No decoder-based criterion exists or may
be introduced.

If no rule satisfying R1–R5 exists for a family, record
`STRUCTURALLY_INFEASIBLE_AS_FROZEN` with the proof and provide a **redefinition
menu** (<=3 options) that states, for each option, exactly which frozen knob
changes, the structural consequences (rate/rows/degrees/girth/selection key),
and why it is the minimal change. Redefinitions are `REQUIRES_MAIN_THREAD_RULING`
and must **not** be landed in production paths.

Repair candidates are explored in a clearly separated sandbox section/module.
Production `build_support` behaviour for any `(arm,n,layer)` stays byte-identical
in this packet; landing repaired builders is deferred to the R1d revision after
the main-thread ruling. Exception: nothing here prevents landing the A5-03 gate
and the A5-06 execution-integrity fix.

Deliverable: `D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md` + machine-readable
matrix/CSV, including for each family: rule(s), proofs, matrix under the chosen
rule, structural diff, and the resulting eligible set per width.

Acceptance: A5-A06 every violating family is either repaired admissibly (with
proof) or declared infeasible with a redefinition menu; A5-A07 the repaired
sandbox matrices satisfy I1 and all frozen gates at every prefix; A5-A08 T1,
B0, B1 production outputs are byte-identical to HEAD.

## 7. A5-05 — performance and equivalence guard

- Re-run the structure-only benchmark for the sandbox-repaired arm set at
  n64/n128/n256 in fresh roots (A4 protocol; cold and warm) and report wall,
  records, replay, peak RSS. The A4 acceptance must not regress: scaling
  structure wall stays within 2x of the A4 after-side (2.5 s / 2.7 s) and n64
  within 10% of 21.0 s.
- Confirm the A4 pruning still applies (only frozen fallbacks built at scaling;
  T2 not rebuilt at n128/n256 unless it is the frozen fallback) and that the
  exactly-two-constructions-per-`(n,arm,layer)` property survives.
- Zero decoder calls in every benchmark root; report the check explicitly.

Acceptance: A5-A09 timing/RSS/replay reported with the A4 comparison;
A5-A10 no decoder records anywhere in A5 roots.

## 7b. A5-10 — R1d structure-cost guard (readiness blocker)

The A4 pruning removed T2 from the scaling dispatch because T2 was not a frozen
fallback. A repair can change that: T2 minimizes four-cycles first, so a repaired
T2 is a plausible `best_T`. If T2 becomes the frozen fallback, the A2-era cost
returns in full and the run cannot finish inside the frozen budgets.

Frozen numbers to check against (structure-only, from the A4 profile and the
main-thread cost model `workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/t2_cost_model.py`):
T2 candidates per variable are `|B|(|B|-1)/2 * (|C|-2)` = 72,912 (n64),
598,878 (n128), 4,853,940 (n256); total 4.67M / 76.7M / 1.24B; measured
per-candidate cost ~8.3–8.9 us, giving ~41 s (n64 per layer), ~650 s (n128),
~2.85 h (n256) — the exact wall that stalled the A2 run.

Requirement: for the candidate R1d arm set, profile the structure build at every
dispatched width (fresh roots, zero decoder) and project the structure wall
against the frozen chunk budget (`chunk >= 5400 s` blocks further dispatch) and
the 12 h run wall. If any dispatched `(arm, n)` is projected to breach the chunk
budget, the readiness package must either (i) include a frozen,
equivalence-gated optimization plan for that arm (the A6 packet), or (ii) declare
that arm inadmissible for that width with the structural reason. A readiness
package that ignores this is incomplete.

Acceptance: A5-A18 structure-cost projection for every candidate R1d arm/width,
with the breach decision recorded explicitly.

## 8. A5-06 — execution-integrity terminal (land, tests only)

The R1c-A2 run stored a scientific terminal while 64 attempted cells had crashed.
A3 repaired the *verifier*; the *runner* must also fail closed for any future
run. Land, with tests:

- any attempted (non-placeholder) crash or nonfinite cell anywhere in the run
  forces the blocking terminal `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` when the
  error is the degree invariant, otherwise `D6_GRAPH_ATTEMPTED_CELL_INVALID`,
  overriding recovery/no-recovery classification;
- skipped placeholders (`call_idx=-1`) never count;
- the stored historical root is not re-run, not rewritten, and its verify output
  keeps reporting stored versus recomputed terminal with the agreement flag.

Acceptance: A5-A11 fake-only tests for canary, scaling and confirmation branches;
A5-A12 no change to any historical artifact.

## 9. A5-07 — independent reviews

Two independent, read-only reviews (reviewer edits only its own file; state the
independence mechanism if a dedicated reviewer tool is unavailable; do not
inherit the main-thread conclusion):

1. `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1C_A5.md` — the A5-03 gate, the A5-06
   execution-integrity fix, tests, and the claim that production builder outputs
   are unchanged.
2. `D6_GRAPH_MOTHER_VALIDITY_REVIEW_R1C_A5.md` — the validity matrix, per-family
   proofs, repair admissibility, the repaired matrices, and the R1d readiness
   package. It must independently recompute a sample of cells and re-check the
   admissibility criteria against the prereg.

Allowed verdicts:

- `D6_R1C_A5_REVIEW_PASS_R1D_READY` (repair candidates admissible; R1d package
  ready for a main-thread authorization decision)
- `D6_R1C_A5_REVIEW_PASS_ELIGIBLE_ONLY_BRANCH` (no family repair admissible; the
  R1d package must fall back to the eligible-only arm set, which must be stated
  explicitly in the readiness document)
- `D6_R1C_A5_REVIEW_FAIL` (blocks closeout)

At most one rework round per review; a second blocking finding returns as a
blocker. Reviews never authorize execution.

## 10. A5-08 — R1d readiness package (no execution, no authorization)

Create `D6_GRAPH_MOTHER_R1D_READINESS_R1C_A5.md` containing a **candidate**,
explicitly marked `NOT_AUTHORIZED / REQUIRES_MAIN_THREAD_RULING_AND_AUTHORIZATION`:

- the candidate arm set: controls plus repaired families that passed review, plus
  the eligible-only fallback branch if any family is infeasible as frozen;
- the frozen validity matrix that must hold before any dispatch, and the rule
  that no cell may be dispatched from a violating matrix;
- unchanged frozen science: decomposition, E2 prior, decoder/schedule/damping,
  row points, seeds by role, budgets (2500 calls / 12 h / 120 s / RSS < 2 GiB /
  no retry), selection, advancement, scaling, and terminal thresholds;
- the R1d evidence schema change (new check-degree diagnostic column/key),
  listed explicitly as a schema change requiring approval;
- the R1d crash-precedence terminal semantics and the no-reuse rule for the
  R1c-A2 root;
- a Pre-EXECUTE checklist for the future reviewer, including output-root
  absence, authorization-key state, G2 absence, protected-root metadata, test
  set, and the exact command;
- an explicit statement of what R1d could and could not claim, and that a
  negative result would close the SC/accumulator families only as tested.

Also update `cycle_state.yaml` (execution keys stay false, `evidence_root` and
`terminal` stay null) with `next_gate` =
`D6_GRAPH_MOTHER_R1D_READY_AWAITING_MAIN_THREAD_AUTHORIZATION` or
`D6_GRAPH_MOTHER_R1D_ELIGIBLE_ONLY_AWAITING_MAIN_THREAD_RULING` per the review
verdict. No R1d root may be created.

## 11. A5-09 — closeout

Commits, exact-path staged, in this order:

1. prereg/OpenSpec A5 delta + tasks (`docs(v72p2d6): freeze R1c-A5 validity and
   repair contract`);
2. implementation + tests (gate + execution integrity)
   (`feat(v72p2d6): R1c-A5 check-degree invariant gate`);
3. validity matrix + root causes + repair study + readiness package
   (`docs(v72p2d6): R1c-A5 validity matrix and repair study`);
4. both independent reviews
   (`docs(v72p2d6): accept R1c-A5 reviews`);
5. append-only `docs/decision-log.md` + `AGENT_PROJECT_MEMORY.md` +
   `cycle_state.yaml` (only after both reviews PASS).

Run: `py_compile` on the touched modules; focused D6 tests; the established
seven-file non-perf regression suite with a fresh UUID basetemp. Run perf-v38
only if a scoped dependency makes it materially necessary and record the choice.

Do not push. Do not mark any result accepted. Keep every authorization key
false, G2 absent, and the R1c-A2 root immutable.

## 12. Acceptance IDs and return contract

- A5-A01 validity matrix complete and reproducible
- A5-A02 current `eligible` flag and A2 five-arm selection reproduced exactly
- A5-A03 I1 gate landed with build-time and dispatch-time fail-closed behaviour
- A5-A04 zero decoder calls in the entire packet
- A5-A05 historical root fields, mtimes and verify output unchanged
- A5-A06 every violating family repaired admissibly or declared infeasible with
  a redefinition menu
- A5-A07 repaired sandbox matrices satisfy I1 and all frozen gates everywhere
- A5-A08 T1/B0/B1 production outputs byte-identical to HEAD
- A5-A09 performance/RSS/replay reported against the A4 baseline
- A5-A10 no decoder records in any A5 root
- A5-A11 crash-precedence execution terminal landed with fake-only tests
- A5-A12 no historical artifact changed
- A5-A13 both independent reviews recorded with allowed verdicts
- A5-A14 R1d readiness package complete, marked not authorized
- A5-A15 cycle_state/decision-log/memory updated append-only, all auth keys false
- A5-A16 focused + seven-file non-perf suites green (or scoped failures named)
- A5-A17 no push; no acceptance; G2 absent
- A5-A18 R1d structure-cost projection recorded, with any chunk-budget breach
  routed to the A6 optimization plan or an explicit width-inadmissibility
  declaration

Return only deltas: commits and file manifests; the validity matrix summary and
per-family proofs; the gate and execution-integrity changes with test results;
the repair rules chosen, their structural diffs, and the resulting eligible sets;
any `STRUCTURALLY_INFEASIBLE_AS_FROZEN` declaration with its redefinition menu;
the performance/equivalence numbers; both review verdicts; the R1d readiness
statement; protected-root and authorization state; and the A5-A01..A5-A17 table.

End exactly:

`D6 R1c-A5 有效性收口与修复研究已完成并独立复核：I1（检查行度≥2）缺陷已证明并被闸门封堵，修复候选与 R1d 就绪包待主线程裁决；全程零 decoder 调用，R1c-A2 根保持 immutable，授权全 false，G2 未授权、未执行。`
