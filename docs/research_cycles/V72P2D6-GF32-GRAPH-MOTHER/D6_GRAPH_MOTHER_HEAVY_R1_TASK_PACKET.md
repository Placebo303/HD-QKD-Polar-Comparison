# V72P2D6 GF32 graph/mother successor — heavy R1 task packet

Status: `FROZEN_HEAVY_DEVELOPMENT_PACKET / EXECUTION_BOUNDARY_DEVELOPMENT_ONLY`

Repository: `D:\Code\HD-QKD_Polar_Comparison`

Branch: `formal-ir-v72p1-addendum-clean`

Expected starting HEAD: `821388d6`

Predecessor gate: `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`

Operator: strong autonomous research/implementation operator. Complete planning, OpenSpec, implementation, independent code review, Pre-EXECUTE review, bounded development execution, independent Pre-RESULT review, evidence delivery, and local commits without routine main-thread check-ins. Return only on complete or a concrete blocker that changes the frozen scientific contract.

Activation: the user forwarding the companion prompt authorizes only the bounded development decoder calls in this packet after an independent Pre-EXECUTE PASS. It does not authorize any formal CLI phase, formal G1 rerun, G2, VAL, real data, qualification, or promotion.

## 0. Mainline objective

D5 closed two successive hypotheses:

- the current fixed high-five/low-five two-layer rate-mother/BP path produced an accepted completed-no-signal G1 result;
- all 252 reversible 5+5 bit partitions left the current mapping decoder-blind optimal and produced APP exact `0/8` at n=64.

D6 changes one principal algorithm component: the finite GF32 parity-check graph/mother. Keep the accepted current decomposition, E2 total-concentration/backoff prior, row budgets, GF32 decoder, schedule, damping, seeds-by-role, and exact/syndrome semantics fixed.

The goal is to determine whether a structurally different nested short-block mother can recover useful APP decoding signal before any decoder-dynamics work. This is vertical mainline progress, not a generic graph library or a broad hyperparameter sweep.

## 1. Absolute prohibitions

- No CLI `--phase` invocation of any kind.
- No formal G1 rerun/resume/recovery; no read of VOID-G1 contents.
- No G2 invocation or `workspace/v72p2d5_g2*` creation.
- No VAL, raw/real IR, parquet outside CAL-TRAIN 702..1725, or real-data claim.
- No modification/overwrite/hash of accepted formal roots or accepted Model-F artifacts.
- No change to D5 formal production wiring, frozen constants, accepted results, authorization keys, or promotion state.
- No edits under frozen `src/`, `experiments/`, or `tools/`.
- No graph-seed search, block-seed search, coefficient search, decoder tuning, damping/schedule/iteration search, row-count tuning, estimator tuning, or decomposition tuning.
- No arbitrary random ensembles, general protograph optimizer, MET optimizer, density-evolution project, or reusable graph framework.
- No retries of a frozen decoder cell. Timeout/error consumes that cell.
- No push, force, reset, checkout, stash, clean, amend, rebase, EOL normalization, or unrelated-file cleanup.
- No scientific acceptance by the operator or reviewer. They may produce a reviewed candidate terminal only.

Tests must use explicit fakes/injection and task-owned basetemps. Development decoding must use explicit decoder and Model-F injection and one UUID development root. Formal roots are never default outputs.

## 2. Baseline gate (D6-B01)

Before writing:

1. Confirm branch and HEAD `821388d6`.
2. Confirm the appendix commit is one file and D5 state says:
   - `d5_current_path_stopped: true`;
   - `d5_decomposition_successor_terminal: DECOMPOSITION_NO_N64_RECOVERY`;
   - `next_gate: D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`.
3. Confirm all nine execution authorization keys false and `scientific_promotion: false`.
4. Confirm G2 absent.
5. Snapshot metadata only (name/size/mtime_ns and direct child dirs) for accepted G1 R2, Model-F, P0, G0, G0-recovery, and structure roots. Do not open/hash contents.
6. Confirm scoped content cleanliness with `git diff --numstat` and `git diff --cached --numstat`; known porcelain EOL churn is informational.
7. Record an exact allowlist. Preserve the existing untracked task/prompt files and every unrelated dirty path.

Mismatch in branch, lifecycle, authorization, accepted root inventory, or G2 absence is STOP.

## 3. Phase A — OpenSpec and preregistration before implementation

Create OpenSpec change:

`openspec/changes/v72p2d6-gf32-graph-mother-successor/`

Required files:

- `proposal.md`
- `design.md`
- `tasks.md`
- `specs/spec.md`

Create cycle files:

- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/cycle_state.yaml`
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_PREREG_R1.md`

The preregistration must freeze §§4–9 before production implementation or decoder calls. Source reading, tiny hand calculations, and test-fixture prototyping that does not invoke the decoder are allowed before the commit; no candidate score table may be generated before the prereg commit.

Commit only the OpenSpec/prereg/cycle-state files:

```text
docs(v72p2d6): preregister bounded GF32 graph-mother successor

Co-Authored-By: OpenAI Codex <noreply@openai.com>
```

## 4. Frozen scientific controls

Keep fixed:

- symbol decomposition: current `A = 32*U1 + U2`;
- prior: accepted E2 total-concentration/backoff candidate, CAL-only;
- GF32 field/polynomial and historical row-layered FFT-QSPA decoder;
- cold start, `max_iter=90`, `damping=1.0`;
- L1 then APP-propagated L2; oracle-L2 diagnostic only;
- n=64 row points: f1.0 `(49,43)`, f1.2 `(59,52)`, square `(64,64)`;
- scaled indications: n=128 `(98,86)/(118,104)/(128,128)` and n=256 `(196,172)/(236,208)/(256,256)`;
- exact means full reconstructed Alice equality; syndrome remains separate and never upgrades exact;
- samples are generated once per `(n, block_seed)` in memory and reused byte-identically across arms.

The graph/mother is the only scientific axis. For all degree-3 arms, coefficient triples are identical by `(n, layer, column)` across arms. Labels are not optimized.

## 5. Frozen architecture family

Implement the smallest standalone D6 module; reuse accepted D5 GF32 arithmetic, prior, sampler, decoder adapter, and audit helpers rather than copying them.

### 5.1 Controls

- `B0_D5_DV3_NATIVE`: exact current D5 support and native coefficient assignment. Historical control; never eligible as a new winner.
- `B1_D5_DV3_COMMON_LABELS`: exact D5 support with the D6 common coefficient stream. This isolates label-stream effects from support-topology effects.

### 5.2 Degree-3 topology arms

- `T1_PEG_DV3`: two base edges inside `k_min`, one expansion edge inside `m_max`; deterministic PEG/BFS choice maximizes separation before balancing degree, with lexicographic tie-break.
- `T2_CYCLE_GREEDY_DV3`: deterministic triple placement minimizing incremental `(four_cycles, max_pair_occupancy, variable_cycle_incidence_max, row_degree_max, row_degree_sumsq, support_tuple)` lexicographically.
- `T3_SC_DV3_W4`: spatially coupled/local-window degree-3 construction with coupling width 4.
- `T4_SC_DV3_W8`: identical rule with coupling width 8.

For T3/T4, define the check/variable positions, boundary termination, candidate window, and deterministic tie-break exactly in the prereg. Do not tune windows after seeing data; 4 and 8 are the complete frozen window set.

### 5.3 Accumulator/MET finite-feasible arms

- `M1_ACCUMULATOR_FOREST_MAX`: degree-2 variable count `N2=k_min-1`; all remaining variables degree 3.
- `M2_ACCUMULATOR_FOREST_HALF`: `N2=floor((k_min-1)/2)`; all remaining variables degree 3.

Here `k_min` is layer/width specific: n=64 L1/L2 `49/43`, scaled linearly to `98/86` and `196/172`. Degree-2 supports must form a simple forest over the first `k_min` checks at every relevant prefix. Degree-3 variables receive two base edges plus one expansion edge. The construction must be deterministic and check-degree balanced with lexicographic tie-break.

No other topology, degree distribution, window, or parameter is in scope.

### 5.4 Common coefficients

For B1/T1–T4 and degree-3 columns of M1/M2, generate the same ordered nonzero GF32 coefficient stream by `(n,layer,column,edge_index)`. Degree-2 columns use the first two entries. Freeze seeds:

```text
L1 coefficient seed = 202609120100 + n
L2 coefficient seed = 202609120200 + n
```

No coefficient candidate selection is allowed. Record projective duplicate and degenerate-cycle diagnostics but do not optimize against decoder outcomes.

## 6. Structural gates and decoder-blind finalist selection

For each arm, n, layer, and every applicable prefix, record at least:

- GF32 rank/full-row-rank;
- zero rows/columns;
- connected components and largest variable component;
- variable/check degree histograms and maxima;
- duplicate supports and proportional/projective columns;
- exact 4-cycle count and maximum variable 4-cycle incidence;
- girth or explicit `NOT_COMPUTED` with reason;
- degree-2 subgraph cycle rank for M1/M2;
- determinism replay equality.

Hard structural eligibility:

- expected shape and nonzero GF32 coefficients;
- rank equals prefix row count;
- zero rows/columns = 0;
- one connected component and all variables included;
- duplicate/proportional columns = 0;
- no parallel edge within a column;
- M1/M2 degree-2 cycle rank = 0.

Before decoder calls, freeze:

- baseline B0;
- B1 label control;
- best two eligible T arms by `(four_cycles, incidence_max, -girth, row_degree_max, row_degree_sumsq, arm_id)`;
- both eligible M arms.

If a category has fewer eligible arms, record it; do not substitute a new design. Maximum decoder arms = 6.

## 7. Implementation and independent pre-execution gates

Allowed implementation paths:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`
- `scripts/v72p2d6_graph_mother_development.py`
- the D6 OpenSpec/cycle documents;
- one UUID root `workspace/d6_graph_mother_r1_<uuid>/`;
- append-only `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md` at final delivery;
- D5 `cycle_state.yaml` only for final `next_gate` handoff and D6 pointer fields.

Do not edit D5 production modules/tests unless an unavoidable reuse blocker is independently demonstrated. If that occurs, STOP and request one scope decision.

Tests before decoder calls must cover:

- deterministic replay and exact arm inventory;
- all structural hard gates on small and n=64 fixtures;
- coefficient identity across degree-3 arms;
- M-arm forest-cycle detection including a failing injected cycle;
- prefix nesting and rank;
- explicit decoder/prior/out-dir injection;
- exact/syndrome/oracle separation;
- formal-root no-write guards;
- budget/call accounting and terminal truth tables.

Commit implementation+tests+script locally. Then obtain an independent code review. The reviewer must not edit files. It must verify the one-axis contract, arm formulas, structural gates, isolation, accounting, and tests.

After code-review PASS, obtain an independent Pre-EXECUTE review. It must freshly verify scoped code, fixed arms/seeds/rows, output-root absence, protected-root metadata, relevant tests, development authorization in the forwarded prompt, and watchdog availability. A PASS permits autonomous progression to §8. A FAIL permits at most two implementation/review cycles before returning BLOCKER; no decoder call may occur before PASS.

## 8. Heavy bounded development execution

Use one fresh root `workspace/d6_graph_mother_r1_<uuid>/`. Persist scalar/metadata only; no raw symbols, priors, beliefs, matrices, or per-iteration messages.

### 8.1 Seeds

- n=64 canary: `2026091000..2026091003`.
- confirmation: `2026091010..2026091025` (16 fresh seeds).
- scaling canary: `2026091100..2026091103`.

No other block seeds.

### 8.2 n=64 canary

For every frozen decoder arm and all four canary seeds, run:

- f1.2 `(59,52)` APP L1 + APP L2 + oracle-L2 diagnostic;
- square `(64,64)` APP L1 + APP L2 + oracle-L2 diagnostic.

Each cell is invoked once. Record flags, iterations, wall, RSS, arm, matrix identity, seed, rows, layer/mode, and failure text.

An eligible new arm advances to n=64 confirmation if f1.2 end-to-end APP exact is at least `1/4`. Advance at most two, ranked by:

1. f1.2 APP exact count descending;
2. f1.2 APP total iterations ascending;
3. square APP exact descending;
4. frozen structural rank;
5. arm ID.

This decoder screen may select confirmation arms because confirmation seeds are disjoint. It may not alter graph, labels, rows, decoder, or seeds.

### 8.3 n=64 confirmation

For each advancing arm and all 16 confirmation seeds, run f1.0, f1.2, and square, each with APP L1 + APP L2 + oracle-L2 diagnostic.

Classify:

- `D6_GRAPH_STRONG_N64_RECOVERY`: f1.2 APP exact `>=12/16`, f1.0 exact `<=` f1.2 exact `<=` square exact, zero crash/nonfinite, zero exact/syndrome disagreement, known RSS `<2GiB`.
- `D6_GRAPH_PARTIAL_N64_SIGNAL`: f1.2 APP exact `1..11/16` with the same safety conditions.
- `D6_GRAPH_N64_SIGNAL_INVALID`: a required safety/ordering condition fails.

### 8.4 Scaling branch

Run only if no new arm reaches `1/4` at n=64 f1.2.

Before any n=64 decoder calls, preregister two fallback arms: the structurally best eligible T arm and structurally best eligible M arm. For each fallback arm, use the four scaling seeds at n=128 f1.2+square. If neither reaches `1/4` f1.2, repeat at n=256. Stop at the first width where any arm reaches `1/4`.

At the first signaling width, advance at most two arms by the same ordering and run 16-seed confirmation at f1.0/f1.2/square.

Classify strong/partial using the same `12/16` and `1..11/16` rules, labeled `D6_GRAPH_STRONG_SCALING_RECOVERY` or `D6_GRAPH_PARTIAL_SCALING_SIGNAL` with the width attached.

n=128/n=256 here are development widths, not formal G2.

### 8.5 No-signal and square-only outcomes

- `D6_GRAPH_SQUARE_ONLY_DIAGNOSTIC`: one or more square points show APP exact but every non-square point is zero.
- `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`: all tested non-square APP exact counts are zero and no stronger square-only label applies.
- `D6_GRAPH_IMPLEMENTATION_OR_RESOURCE_BLOCKED`: structural invariants, process ownership, wall, RSS, or execution integrity fails.

### 8.6 Resource limits

- maximum scientific decoder calls: 2500;
- aggregate wall: 12 hours;
- per-call watchdog: 120 seconds;
- RSS: `<2GiB`; unknown RSS prevents strong classification;
- no retry of any cell;
- stop before a call that would exceed the call/wall budget;
- own and record every launched process; terminate only task-owned processes.

## 9. Evidence and independent Pre-RESULT review

Minimum development-root files:

- `manifest.json`
- `structure_records.csv`
- `selected_arms.json`
- `decoder_records.csv`
- `summary.json`
- `command_log.txt`
- implementation/review provenance copied as scalar IDs only

After execution, independently recompute from saved scalars:

- arm/seed/row/mode coverage;
- decoder call count;
- exact/syndrome/oracle separation;
- iterations and resource maxima;
- advancement decisions;
- terminal classification.

Then obtain an independent Pre-RESULT review before committing the result report. Reviewer is read-only except for creating:

`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1.md`

FAIL blocks result solidification. Fixes after scientific calls are limited to evidence/report arithmetic; any code, graph, seed, row, or decoder change requires a new revision and no reuse of prior calls.

## 10. Tests

Run focused tests during implementation. At implementation-review and final milestones run:

```powershell
python -m pytest comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py comparison_bench/tests/test_v72p2d4r2_cal_gf32_model_rate_audit.py comparison_bench/tests/test_nonbinary_v31.py comparison_bench/tests/test_v37_degree_feasibility.py comparison_bench/tests/test_v38_architecture_triage.py -p no:cacheprovider --basetemp workspace/d6_graph_mother_tests_<uuid> -q --tb=line
```

Use a fresh UUID each milestone. Delete only task-owned basetemps after resolved-prefix verification. A test failure may be repaired before decoder calls. After decoder calls begin, any production-code failure is a STOP; do not patch and continue using mixed-version evidence.

## 11. Delivery and routing

Create:

- `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1.md`
- `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1.md`
- `D6_GRAPH_MOTHER_RESULT_R1.md`
- `D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1.md`

Update D6 state and append durable final deltas to decision log/memory. Update D5 state only with D6 linkage and `next_gate`.

Final next gate:

- strong n64/scaling: `D6_GRAPH_MOTHER_CANDIDATE_ACCEPTANCE_REVIEW`;
- partial: `D6_GRAPH_MOTHER_PARTIAL_SIGNAL_ROUTE_REVIEW`;
- square-only/no useful recovery: `D6_DECODER_DYNAMICS_SUCCESSOR_PROPOSAL`;
- blocked: `D6_GRAPH_MOTHER_REWORK_REQUIRED`.

Do not start decoder-dynamics work in this packet.

Commit sequence, all local and exact-path staged:

1. OpenSpec + prereg + initial D6 state.
2. implementation + tests + development script.
3. accepted code-review + Pre-EXECUTE review records.
4. after Pre-RESULT PASS: evidence + result/reviews + state + append-only memory/log.

No broad staging and no push.

## 12. Acceptance matrix

- D6-A01 baseline/lifecycle/protected-root gate.
- D6-A02 OpenSpec and prereg precede implementation scores/calls.
- D6-A03 only the frozen controls/T/M families exist.
- D6-A04 graph algorithms deterministic; no seed/parameter search.
- D6-A05 common coefficient stream isolates degree-3 support topology.
- D6-A06 all prefix structural hard gates and negative tamper tests pass.
- D6-A07 decoder-blind finalist/fallback freeze precedes calls.
- D6-A08 implementation review PASS before Pre-EXECUTE.
- D6-A09 Pre-EXECUTE PASS before first decoder call.
- D6-A10 samples paired across arms; canary/confirmation seeds disjoint.
- D6-A11 advancement and scaling follow frozen rules exactly.
- D6-A12 calls/wall/watchdog/RSS and no-retry accounting hold.
- D6-A13 exact/syndrome/oracle remain isolated.
- D6-A14 independent scalar recomputation agrees.
- D6-A15 Pre-RESULT PASS before result commit.
- D6-A16 relevant eight-file suite has zero new failures.
- D6-A17 formal roots unchanged and G2 absent.
- D6-A18 authorization/promotion/formal-result fields unchanged.
- D6-A19 commits contain only allowlisted files and are unpushed.
- D6-A20 conclusion stays within tested graph family/width/model/decoder scope.

Any deviation is STOP unless a named reviewer classifies it as a non-scientific documentation correction before decoder calls.

## 13. Return contract

Return only when D6-A01–A20 are complete or on a concrete blocker.

Complete return, deltas only:

1. A01–A20 table.
2. commit SHAs and exact manifests.
3. implemented arm formulas and structural finalist table.
4. decoder coverage/results and terminal.
5. calls/wall/RSS/watchdog/no-retry accounting.
6. literal focused and eight-file test summaries.
7. implementation, Pre-EXECUTE, and Pre-RESULT review verdicts.
8. protected-root equality, G2 absence, authorization/gate status, no push.
9. strongest supported statement and explicit non-claims.

Blocker return: failing ID, raw output, in-scope remedies attempted, and exactly one main-thread decision. Do not return routine partial progress.

Final sentence:

```text
D6 graph/mother 主线开发已按冻结边界完成；所有结果仅为 CAL-only/开发级有限图证据，不构成正式 G1 重跑、G2 授权或科研资格。
```

