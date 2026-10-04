# Design — V72P2D10 mixed-degree L1 finite discriminator (R1 + R2)

Change: `v72p2d10-mixed-degree-l1-finite-discriminator`
Cycle: `V72P2D10-MIXED-DEGREE-L1`
Track: implementation/readiness (no EXPLORE/DECIDE execution; no
  decoder/DE/CAL/VAL/real-data). R1 F01–F12 complete and retained; R2 R201–R212
  governed by
  `.workbuddy/tasks/D10_MIXED_DEGREE_L1_CONNECTIVITY_R2_TASK_PACKET.md`.
Predecessor: `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`.
Authority: R1 packet §2–§6 (F01–F12) + R2 packet §2–§7 (R201–R212).
State: `D10_MIXED_DEGREE_L1_R1_RETAINED_R2_AMENDMENT` (R1
  `D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION` evidence retained
  but batch not authorized; main-thread decision
  `REVISE_REQUIRED_CONNECTIVITY_AND_RANK`; R201 amends OpenSpec, R202–R212
  pending). Intended R2 terminal (requires separate explicit authorization for
  any batch):
  `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION`, else
  `BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION`.

## 1. Two-arm scientific isolation contract (frozen R1; R2 keeps one constructor)

Exactly two arms:

| arm id | variable degree profile | role |
|---|---|---|
| `PEG_DV3_MATCHED` | regular degree 3 | matched control |
| `PEG_DV23_LAM2_045` | D9-selected `lambda2 = 0.45` mixed `{2,3}` | candidate |

Both arms SHALL use the same: graph-construction algorithm (R2
connectivity-first degree-sequence PEG, §2), tie-breaking policy (v10
BFS-depth → ACE → seeded pick), graph-seed rule, coefficient-distribution/
stream rule, Model-F L1 prior chain, row count (`m` per width), block seed set
and paired block objects, decoder (`v35.decode_row_layered_fftqspa`),
schedule (cold row-layered), iteration cap (`max_iter=90`), damping
(`damping_alpha=1.0`), field (`q=32, poly=37`), syndrome/exact/stop semantics
and record schema.

The candidate differs only where mathematically forced by its D9 degree/socket
profile (§3): variable degree histogram, total sockets `E`, and the
floor/ceil check-degree allocation. No other difference is permitted. R2
restates the R1 rule strictly: one constructor and one tie policy shared by
both arms; only the forced degree sequence input may differ (R202).

Primary scope only: L1 marginal decoding; f1.2 `(n,m) = (64,59), (128,118),
(256,236)`; q=32 polynomial 37; cold row-layered v35 decoder `max_iter=90`,
`damping_alpha=1.0`; exact and syndrome-valid reported separately with
provenance and residual syndrome weight.

Not in scope (packet §2): no L2, APP transfer, oracle-L2, f1.0, square point,
alternation or D7-H. No decoder/DE/CAL/VAL/real-data execution in R201.

## 2. Builder inventory, selection (F02, frozen) and R2 connectivity-first delta (R202–R204)

### 2.0 R1 inventory and selection (retained)

Requirement: a builder that honors an arbitrary exact variable-degree sequence
and exact check-degree counts, is deterministic given the frozen graph seed,
produces a simple graph (no duplicate edges, no empty checks) and supports the
prescribed tie-breaking.

Inventory (read-only; real pointers):

| # | candidate | capability | verdict |
|---|---|---|---|
| B1 | `nonbinary_v10_peg.peg_construct` (`:276-458`) | deterministic PEG over edge-perspective `lambda`/`rho`; parallel edges forbidden (`:339-355`); field parameter (`:296-299`); caller-supplied `edge_label_seed`; BFS + ACE + seeded tie-break (`:356-391`); counts are *derived* by largest-remainder (`:80-116`) | closest reuse, but its API is `lambda`/`rho`, not exact sequences; rejects the literal capability |
| B2 | `nonbinary_v7_r3_codebook._construct` (`:191-230`) | takes an explicit per-column `degrees` list (`:191`); BFS-PEG frontier + min-degree + SHA256 tie-break (`:104-113`, `:169-188`) | rejected: `_N=1024` hardcoded (`:197`), no exact check-degree counts (emergent min-degree balance; `:200-218`), SHA256 coefficient/tie machinery |
| B3 | `v72p2d6_gf32_graph_mother._build_T1_support` (`:110-207`) / `build_support` (`:608-638`) | deterministic DV3 support with `m_max=n`, `k_min` prefixes | rejected: fixed degree 3 only; check allocation emergent from nested prefix semantics; no mixed degrees |
| B4 | `nonbinary_v36_empirical_graph.construct_source_native_peg_matrix` (`:553-619`) | source-bound builder; floor/ceil check counts encoded as `rho` (`:570-582`); calls `peg_construct` | rejected as a builder: fixed `m` from `M2_BY_SOURCE` and `n=N_SYMBOLS`, plus a rank-based backup-coefficient-seed retry (`:594-610`) = seed search. Its count-encoding pattern is reused as precedent |
| B5 | `nonbinary_v30.build_supports_peg` (`:442-481`) / `nonbinary_v31.build_supports_peg_capacity` (`:306`) / `build_supports_qc_cyclic` (`:394`) | degree-2 support pairs for MET/QC structures, fixed `n` | rejected: no arbitrary variable-degree sequence, no exact check counts |
| B6 | `v35_algorithm_development.build_hand_designed_mixed_degree_protograph` (`:1007`) | fixed hand-designed protograph | rejected: not parameterizable by counts |
| B7 | `v72p2d5_gf32_rate_mother.build_dv3_nested_support` (`:423`) | DV3 nested prefix support, frozen seed | rejected: DV3 only, prefix/nested semantics, no exact check allocation |

**R1 selection: B8** — one minimal deterministic degree-sequence PEG,
`build_degree_sequence_peg(n, m, var_counts, check_counts, seed, field)`. B8
reuses, read-only, the accepted B1 placement primitives so the tie-breaking
policy is not reinvented:

- tie pick: `nonbinary_v10_peg._tie_pick` (`:265-273`, seeded PCG64 via
  `nonbinary_v10_common.v10_seed(f"peg_tie:{seed}:v:{v}:s:{s}")`, `:340-349`);
- BFS distance: `nonbinary_v10_peg._bfs_distance` (`:461-475`, offset check-node
  id scheme `n+c`, `:327-332`);
- ACE score: `nonbinary_v10_peg._ace_score` (`:478-495`).

R1 B8 semantics (retained as the base; R2 §2.1–§2.3 amends the placement and
admission but preserves inputs, conventions, coefficient rule and determinism):

1. Inputs validated fail-closed: `var_counts` and `check_counts` integer
   mappings, all degrees >= 2, `sum(var_counts) = n`, `sum(check_counts) = m`,
   `sum(d*count) = E` equal on both sides, no negative/zero counts; mismatch
   raises before any placement.
2. Degree-to-index convention (same as B1 `:306-321`): variables `0..n3-1`
   receive the highest degree (3, i.e. the mixed arm's degree-3 block) first,
   then remaining variables receive degree 2; check degrees are assigned to
   indices `0..m-1` in decreasing degree order. Placement itself iterates
   variables `0..n-1` and sockets `0..d_v-1`.
3. R1 selection rule per socket (B1 policy, counts imposed): candidates are
   free checks (remaining capacity > 0) not already adjacent to the variable;
   no candidate -> `status="construction_failed"` with no partial graph; first
   socket of a variable picks max remaining capacity; later sockets run BFS
   from the variable over the partial bipartite graph, pick maximum BFS
   depth; ties maximize the ACE score; final ties use `_tie_pick` over the
   sorted candidate list; if no free check is reachable (exhausted component),
   pick max remaining capacity then `_tie_pick`.
4. One deterministic attempt per seed (no `max_trials` loop). Failure is
   retained as a record and excluded from decoder dispatch (§5).
5. Output edges are simple by construction; the audit re-verifies. Edge list
   is returned sorted ascending by `(variable, check)`.
6. Coefficients: one independent uniform nonzero GF32 draw per edge in sorted
   `(variable, check)` order, `rng = numpy.random.default_rng(COEFF_SEED)`,
   `COEFF_SEED = nonbinary_v10_common.v10_seed(f"d10:coeff:{width}:{graph_seed}")`
   and `int(rng.integers(1, 32))` (`1..31`). Same seed rule for both arms; the
   edge sets differ, so coefficients are not edgewise identical between arms.

No graph library, optimizer, framework, cache or new dependency is added.

### 2.1 R202 — connectivity-first degree-sequence PEG (R2 delta)

Rationale (F4 blocker): the R1 capacity-constrained PEG leaves 9–68 connected
components per graph; component decomposition confounds the degree-profile
test. R2 keeps B8's inputs, degree-to-index convention, shared PEG/ACE tie
policy, determinism and coefficient rule, and inserts a deterministic
connectivity-first phase:

1. Phase A — spanning backbone: before general fill, create a deterministic
   spanning structure that touches every variable node `0..n-1` and every
   check node `0..m-1` while consuming at most the exact target degree of
   each endpoint (no degree overshoot, no parallel edge). Backbone edge order
   and candidate order are seeded-deterministic under the frozen
   `graph_seed`; both arms use the identical backbone procedure with only
   their frozen degree sequences as differing input.
2. Phase B — shared PEG/ACE fill: fill all remaining sockets with the R1 B8
   placement policy (free checks not already adjacent; first-socket max
   remaining capacity; later sockets max BFS depth, then max ACE, then
   `_tie_pick` over the sorted candidate list; unreachable-component fallback
   identical for both arms).
3. Rejection (fail-closed, record-and-stop): parallel (duplicate) edge, any
   degree/socket mismatch against §3, any empty check, or any backbone/fill
   dead end with no admissible candidate yields `construction_failed` with no
   partial graph forwarded; the cell is retained and the width becomes
   engineering-blocked (§6.2). No seed change, no reseeding, no candidate
   selection across alternatives.
4. Determinism: the same `(arm, width, graph_seed)` SHALL always produce the
   identical sorted edge list; replay equality is an admission predicate
   (§5). Both arms SHALL share the one constructor and tie policy; only the
   forced §3 degree sequence may differ.

### 2.2 R203 — deterministic structural rank (R2 delta)

After edge construction and before coefficients, compute a deterministic
maximum bipartite matching over the `(n variables, m checks)` Tanner graph
(fixed deterministic vertex/edge visitation order under the frozen
`graph_seed`; no randomness beyond the frozen seed). `structural_rank` is the
matching cardinality over checks. Admission requires `structural_rank == m`
(all `m` checks covered). Failure records the cell and stops; no graph or
coefficient seed is altered.

### 2.3 R204 — frozen-rule coefficients and exact GF32 rank (R2 delta)

Coefficients are generated by the frozen R1 rule (§2.0 item 6) with NO change:
`COEFF_SEED = v10_seed(f"d10:coeff:{width}:{graph_seed}")`, one
`integers(1,32)` per edge in sorted `(variable,check)` order, same rule both
arms. Then compute the exact GF32 (poly 37) row rank of the resulting `m×n`
parity-check matrix with a deterministic exact algorithm. Admission requires
`gf32_rank == m`. On failure the cell is recorded and the width stops as
engineering-blocked; graph and coefficient seeds SHALL NOT be altered,
repaired, reseeded or searched.

## 3. Frozen degree tables (F03a; f1.2, L1 only; unchanged by R2)

Transcribed exactly from the accepted D9 `openspec/changes/v72p2d9-gf32-de-decoder-calibration/design.md`
§5 f1.2 table (`:244-259`) and cross-checked against the D9 root
`workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/summary.json`
`graph.cells` (`n2`, `n3`, `E` fields for `condition="f1.2"`). R2 SHALL NOT
re-derive, re-round, re-select or repair these integers.

| arm | n | m | n2 | n3 | E | realized lambda2 | check allocation | min dc | max dc |
|---|---|---|---|---|---|---|---|---|---|
| `PEG_DV3_MATCHED` | 64 | 59 | 0 | 64 | 192 | 0 | `3^44 + 4^15` | 3 | 4 |
| `PEG_DV3_MATCHED` | 128 | 118 | 0 | 128 | 384 | 0 | `3^88 + 4^30` | 3 | 4 |
| `PEG_DV3_MATCHED` | 256 | 236 | 0 | 256 | 768 | 0 | `3^176 + 4^60` | 3 | 4 |
| `PEG_DV23_LAM2_045` | 64 | 59 | 35 | 29 | 157 | 70/157 = 0.445860 | `2^20 + 3^39` | 2 | 3 |
| `PEG_DV23_LAM2_045` | 128 | 118 | 71 | 57 | 313 | 142/313 = 0.453674 | `2^41 + 3^77` | 2 | 3 |
| `PEG_DV23_LAM2_045` | 256 | 236 | 141 | 115 | 627 | 94/209 = 0.449761 | `2^81 + 3^155` | 2 | 3 |

Socket balance: `E = 2*n2 + 3*n3` and
`sum(d*count) = E` in every cell. Realized rate is exactly `1 - m/n`
(`0.078125` at n64). Degree-2 forest feasibility
`N2 <= m-1` (`35 <= 58`, `71 <= 117`, `141 <= 235`) is retained as a
sanity check but is NOT sufficient for R2 admission (connectivity + rank
required, §5). The nominal `lambda2=0.45` socket counts are
non-integers (`E = 7680/49, 15360/49, 30720/49`); the apportioned
`lambda_hat2` above is the realization of record per D9 `design.md` §5
(`:238-242`).

## 4. Seeds, coefficients, blocks and call order (F03b–F03e; R2 retires replacement)

### 4.1 Graph seeds (3 per width; separate from block seeds; R1 assignment frozen)

Frozen before execution; verified absent in `docs/`, `openspec/`, `scripts/`,
`.workbuddy/`, `comparison_bench/src`, `comparison_bench/tests`, `analysis/`
and top-level `*.md` at R1 freeze time (2026-09-14):

| width | graph seeds (R1 assignment, preserved) |
|---|---|
| n64 | 2026092201, 2026092202, 2026092203 |
| n128 | 2026092204, 2026092205, 2026092206 |
| n256 | 2026092207, 2026092208, 2026092209 |

18 graphs total (`2 arms × 3 widths × 3 seeds`). Seeds are never
result-adaptive: no seed may be added, replaced or re-rolled after any decoder
result.

R2 change (packet §2): ZERO replacement seeds. The R1 clause permitting at
most one pre-decoder profile replacement per `(width, arm)` from
`PROFILE_REPLACEMENT_SEEDS = tuple(range(2026092210, 2026092216))` is RETIRED
and SHALL NOT be implemented, referenced as available, or consumed in R2. Any
R2 construction/admission failure at a frozen seed is retained as a record,
the width becomes engineering-blocked (§5–§6.2), and the R2 terminal follows
packet §7 (`BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION` if any of the 18
original cells cannot pass without changing a frozen item). No seed search,
no topology selection across candidates, no decoder feedback into
construction.

### 4.2 Coefficient rule (frozen; R204 uses it unchanged)

Uniform nonzero GF32, independent draws, one per edge, in sorted
`(variable, check)` order, seeded as `§2.0 item 6`
(`v10_seed(f"d10:coeff:{width}:{graph_seed}")`). Same distribution and seed
rule in both arms; no edgewise identity claim (different edge counts/sets).
No coefficient repair, reseed or search under R2 (R204 record-and-stop only).

### 4.3 Block seeds (8 per width; separate from graph seeds; frozen)

Frozen before execution; verified absent (same scan as §4.1):

| width | block seeds |
|---|---|
| n64 | 2026092301..2026092308 |
| n128 | 2026092311..2026092318 |
| n256 | 2026092321..2026092328 |

One matched block is sampled once per `(width, block_seed)` from the accepted
CAL-only Model-F artifact via
`v72p2d5_gf32_rate_mother.sample_matched_block(p_b, p_f, n, seed)`
(`:873-911`; `B ~ P(B)`, `A ~ P_F(.|B)`, `A = 32*U1 + U2`), before any decoder
dispatch, and retained in memory. The same block object is used by both arms
and all three graphs at that width: paired decoding on identical L1 blocks.
The 8 blocks per width are shared across the 3 graphs by design; the paired
matrix is 8 blocks × 3 graphs × 2 arms = 48 calls per width.

### 4.4 Prior chain (frozen; same both arms)

- Load `counts_ab`, `p_b` from
  `workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz`
  (CAL-only, `status=MODEL_F_INPUT_CANDIDATE`, `formal=false`,
  `decoder_calls=0`);
- `p_b, p_f = v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate(counts_ab, p_b)`
  (`:2480-2507`, frozen `LAMBDA_STAR`, no new search, no VAL);
- `p1 = marginalize_f_to_p1(p_f)` (`:309-321`);
- per call `priors = _floor_renorm(p1[:, block["bob"]].T, DECODER_FLOOR)`
  (`:346-351`, `DECODER_FLOOR=1e-15` at `:48`), the same prior line as the
  accepted runner `scripts/v72p2d6_graph_mother_development.py:817` and
  `v72p2d5_gf32_rate_mother.py:1415`.

### 4.5 Call order (deterministic; frozen)

Widths dispatched in order n64 → n128 → n256, only under §7/§6.3 progression.
Within a dispatched width: arm `PEG_DV3_MATCHED` before `PEG_DV23_LAM2_045`;
within an arm, graph seeds ascending; within a graph, block seeds ascending.
Global `call_idx` is contiguous from 0 over executed calls only; planned call
count is 144 for the full ceiling (48 per width), and conditional stopping
reduces the executed count before a width is dispatched.

Per scientific call, in order:
1. select graph `(width, arm, graph_seed)` already admitted by §5 gates;
2. `syn = syndrome_of_gf32(H, block["u1"])` (`v35_algorithm_development.py:139-155`);
3. `res = decode_row_layered_fftqspa(H, priors, syn, max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=GF32/poly37)`
   (`v35_algorithm_development.py:781-789`; cold start);
4. record `exact = res.syndrome_ok and array_equal(res.x_hat, u1)`,
   `syndrome_ok = res.syndrome_ok`, `residual_syndrome_weight = hamming(syndrome_of_gf32(H, res.x_hat) XOR syn)`,
   `iterations`, `status`, `belief_provenance`, `prior_mass_on_truth`.

`exact` and `syndrome_ok` are reported as separate fields and are never merged;
`undetected`/failed calls are never counted as success.

## 5. Structural gates → R2 admission predicates (R205; binding before decoder)

R1 gates G1–G10 are retained as the measurement base; R2 elevates the binding
admission to six predicates A1–A6 that SHALL ALL pass on every one of the 18
graphs before any decoder binding. Formerly reported-only rank/components
(R1 G7–G8) are now binding; four-cycle/girth/ACE remain reported diagnostics
only.

| predicate | requirement (binding) | source/notes |
|---|---|---|
| A1 | exact variable degree histogram == §3 AND exact check degree histogram == §3 AND socket balance `sum_v d(v) = sum_c d(c) = E` (R1 G1–G3) | edges; mismatch → `construction_failed`, record-and-stop |
| A2 | simple bipartite graph: no duplicate edge (`len(set(edges)) == E`), no empty check, `min check degree` == §3 min (`>= 2`) (R1 G4–G5) | audit re-verifies backbone+fill output |
| A3 | exactly ONE connected component over all `n+m` Tanner nodes (union-find over variables + checks); report component count and largest-component fraction | R2 connectivity requirement; R1 G8 diagnostic becomes binding `components == 1` |
| A4 | deterministic structural rank `structural_rank == m` via maximum bipartite matching covering all `m` checks (R203) | R2 rank requirement (graph skeleton) |
| A5 | exact GF32 (poly 37) row rank `gf32_rank == m` under the frozen §4.2 coefficients (R204) | R2 rank requirement (labeled matrix); failure records cell, no seed change |
| A6 | deterministic replay equality: rebuilding `(arm,width,graph_seed)` reproduces the identical sorted edge list and identical coefficient stream | guards nondeterminism across processes/seeds |

Reported diagnostics (never gates, never repaired): four-cycle count (+
incidence max), girth (`compute_girth` pattern; report `None`+reason for
acyclic), ACE distribution summary, degree-2 subgraph `N2/cycle_rank_lower_bound`
(`analyze_degree2_subgraph` pattern), wall time per construction.

Construction-failure retention (R1 G10, hardened): any A1–A6 failure or
backbone/fill dead end is retained as a record and excluded before decoder
dispatch; no invalid graph may reach the decoder (assert-dispatchable
pattern). A predicate failure at any `(arm,w,g)` makes that width
`engineering_blocked` (§6.2) and no algorithm conclusion is drawn from it;
the R2 terminal follows packet §7.

The A1–A6 admission is checked immediately before the first decoder call of
each graph (admission-before-binding) and re-verified in `--verify` (R207).
R210 `PROFILE_ONLY` records A1–A6 plus diagnostics for exactly the original
18 cells with zero decoder calls/binds.

## 6. Matrix, thresholds, progression and terminals (F04 frozen; R2 terminal added)

### 6.1 Matrix and budgets (frozen)

Full ceiling: `2 arms × 3 widths × 3 graphs × 8 blocks = 144` scientific L1
calls (48 per width). Conditional stopping may reduce this; no width is
skipped and no mid-width partial dispatch is permitted. No L2 calls consume
unused budget.

Budgets (frozen): scientific L1 calls <=144; setup units <=44 (= 18 graph
constructions + 24 matched-block samplings + 2 fixed setup units for the
Model-F/prior-chain load and the plan build); wall <=1800 s; per-call <=120 s
(checked between/after calls, no in-flight watchdog claim); RSS <2 GiB strict
(2147483648 B); single process; `retry=false`, `resume=false`,
`seed_search=false`, `adaptive_stop=false`. A budget/resource stop is an
engineering block, not an algorithm result.

### 6.2 Per-width classification (thresholds frozen before execution; unchanged)

For width `w`, arm `a ∈ {DV3, MIX}`, graph `g` of 3, block `b` of 8:
`E_g(a,w) = number of blocks with exact=True` (0..8),
`S_g(a,w) = number with syndrome_ok=True` (0..8),
`E_pool = sum_g E_g` (0..24), `S_pool = sum_g S_g` (0..24).

`POSITIVE(w)` iff all four hold:

1. `S_g(MIX,w) >= 3` for every one of the 3 graph seeds (reproducible
   syndrome-valid signal across all graphs);
2. `E_g(MIX,w) >= 2` for at least 2 of 3 graphs (exact recovery is not a
   single-graph event);
3. `S_pool(MIX,w) >= 12` and `E_pool(MIX,w) >= 6` (pooled consistency; pooled
   counts are never sufficient alone);
4. `S_pool(DV3,w) <= 3` and `E_pool(DV3,w) <= 1` (the matched control does not
   reproduce the signal; degree distribution is the differentiator).

`NEGATIVE(w)` iff `E_pool(MIX,w) <= 2` and `S_pool(MIX,w) <= 4`.

`AMBIGUOUS(w)` iff neither POSITIVE nor NEGATIVE nor ENGINEERING_BLOCKED
(e.g. pooled-only signal, a signal failing per-graph reproducibility, or a
control-confounded signal).

`ENGINEERING_BLOCKED(w)` iff any construction/admission failure (A1–A6) at
any `(arm,w,g)`, any decoder crash at `w`, or any budget/resource stop. R2:
any A3/A4/A5 failure is an engineering block, never an algorithm result and
never a trigger for reseeding.

Justification retained from R1 (3 graphs × 8 paired blocks): per-graph floor
3/8 across all three graphs has low probability under weak per-block rates
and kills pooled-only artifacts; exact rule rejects single-rescued-block;
control caps prevent attributing general L1 improvement to the distribution.
Thresholds frozen before execution; not changed after observing results.

### 6.3 Conditional width progression (frozen)

1. Dispatch n64 first (48 calls).
2. If and only if `POSITIVE(n64)`, dispatch n128 (48 calls).
3. If and only if `POSITIVE(n128)`, dispatch n256 (48 calls).
4. No later width after a non-POSITIVE width; no width skipped; at most the
   mixed candidate advances (the control never advances and is never
   re-tuned).

### 6.4 Terminals and routing (R1 retained; R2 readiness terminal added)

| terminal | condition | routing (packet §7) |
|---|---|---|
| `D10_L1_CANDIDATE_REPRODUCIBLE` | POSITIVE at every dispatched width, n256 reached | propose a separate L2/APP integration experiment; D7-H does not auto-revive |
| `D10_L1_FINITE_SIZE_SIGNAL` | POSITIVE at n64 (or n64+n128), then NEGATIVE at the next dispatched width | retain as finite-size signal; diagnose scaling/degree realization before any L2 |
| `D10_L1_NO_MATERIAL_ADVANTAGE` | NEGATIVE at the first dispatched width | close this `{2,3}` finite realization; return to a broader ensemble/protograph proposal, not more alternation |
| `D10_L1_AMBIGUOUS` | AMBIGUOUS at the stopping width | main-thread review; no promotion; any larger matrix requires a new preregistration |
| `D10_L1_ENGINEERING_BLOCKED` | ENGINEERING_BLOCKED at any dispatched width | engineering block; no algorithm conclusion |
| `D10_L1_NOT_RUN` | root absent/unauthorized | none |
| `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION` (R2 readiness) | R201–R212 complete: all 18 original cells pass A1–A6, zero replacement seeds, zero decoder calls/binds in R210, independent review (EVIDENCE_ACCESS: VERIFIED) with no blocker | grants NO execution; future batch still needs separate explicit authorization naming batch/branch/root/seeds/budgets |
| `BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION` (R2 stop) | any of the 18 original cells cannot pass A1–A6 without changing a frozen item | report exact failing cells; STOP; no seed change/retry |

Precedence: ENGINEERING_BLOCKED overrides all algorithm classifications; a
POSITIVE prefix followed by a non-POSITIVE width is `FINITE_SIZE_SIGNAL`
(NEGATIVE stop) or `AMBIGUOUS` (AMBIGUOUS stop); `CANDIDATE_REPRODUCIBLE`
requires n256 dispatched and POSITIVE.

## 7. Claim ceiling (F04 freeze; unchanged, R2 scope noted)

The future batch establishes at most a synthetic finite-length **L1-only**
diagnostic under the accepted CAL-only Model-F prior and the frozen decoder
contract. It establishes no L2/APP result, no oracle-L2, no FER, no leakage,
no SKR, no qualification, promotion or real-data claim, and no DE-to-decoder
equivalence. D7-H is not revived by any D10 outcome. R2 readiness establishes
at most that the 18 admitted graphs are each connected and full-rank under
the frozen contract; it establishes no decoder/threshold outcome.

## 8. Future root, command, runner authorization and evidence convention (F05 + R206–R207)

Fresh root UUID `b2dd13e4-6600-4e27-90df-5c9038cf2c34`, verified absent at
`workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` and
absent as a literal string in `docs/`, `openspec/`, `scripts/`, `.workbuddy/`,
`comparison_bench/src`, `comparison_bench/tests`, `analysis/` at R1 freeze time.

Exact future command shape (do not run; left absent and unauthorized; R206
adds the explicit auth argument):

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
```

R206 (replaces the R1 `BATCH_AUTHORIZED` source-constant flip): the runner
SHALL expose an explicit CLI execution-authorization argument (e.g.
`--execution-authorized`, default false following the repo convention). While
it is false the runner SHALL refuse `--batch` before any root creation and
before any decoder binding (fail-closed, no-write/no-bind). Flipping a source
constant SHALL NOT be an authorization mechanism. R201–R211 keep the argument
false and unused; no R2 readiness step sets it.

Read-only verifier (future; requires a completed root; R207 fail-closed):

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --verify \
  --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
```

R207: `--verify` SHALL recompute A1–A6 for every stored graph with zero skip
and SHALL exit FAIL on any partial or engineering-blocked root (including a
mid-width engineering-blocked root by design). R207 creates no scientific
root.

Readiness-only profile (R210; no decoder, no root, stdout only; exactly the
original 18 cells):

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --profile-only
```

R210 records per cell: component count, largest-component fraction,
structural rank, GF32 rank, four-cycle count, girth, wall time. Requires zero
replacement seeds and zero decoder calls/binds.

Runner files (R1 created in F06; R2 R202–R207 modifies within the same allowed
code paths — NOT in this R201 OpenSpec-only task):

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`
  (connectivity-first builder, structural/GF32 rank, A1–A6 admission, frozen
  tables/plan/thresholds);
- `scripts/v72p2d10_mixed_degree_l1_development.py` (`--batch` + explicit auth
  arg, `--verify` fail-closed, `--profile-only`);
- `comparison_bench/tests/test_v72p2d10_mixed_degree_l1.py` (R208 coverage).

Six-file evidence root (`manifest.json`, `l1_records.csv`, `graph_records.csv`,
`arm_summary.csv`, `summary.json`, `command_log.txt`), fresh-root refusal,
single process, no retry/resume/seed search, `l1_only: true`,
`authorization: "separate explicit user/main-thread authorization required
before --batch"`. The root remains absent and every authorization flag false
until a separate explicit authorization names this batch, branch, root, seeds
and budgets. R201 creates no root.

## 9. Pointer summary (real path:line; R1 retained)

- D9 acceptance/realization: `openspec/changes/v72p2d9-gf32-de-decoder-calibration/design.md:220-284`;
  `v72p2d9_de_decoder_calibration.py:564-656`;
  `v37_degree_feasibility.py:118-261,264-297`;
  D9 root `summary.json` `graph.cells` (f1.2 subset).
- Builder primitives: `nonbinary_v10_peg.py:80-127,265-273,276-458,461-495`;
  `nonbinary_v10_common.py:222-236,340-349`.
- Prior chain: `v72p2d5_gf32_rate_mother.py:48,309-321,346-351,401-406,873-911,2480-2507`;
  `scripts/v72p2d6_graph_mother_development.py:794-798,817`.
- Decoder: `v35_algorithm_development.py:139-155,660-669,781-789,890-936`.
- Structural audit: `v72p2d5_gf32_rate_mother.py:704-845`;
  `v72p2d6_gf32_graph_mother.py:672-728,799-822`.
- Runner convention: `scripts/v72p2d9_de_decoder_calibration_development.py:37,747-775`.
- R1 evidence: `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/READINESS_R1.md`,
  `EXPLORATION_LOG.md`, `INDEPENDENT_REVIEW_R1.md` (§F04 table for the F4
  blocker numbers).
- R2 authority: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_CONNECTIVITY_R2_TASK_PACKET.md`.
