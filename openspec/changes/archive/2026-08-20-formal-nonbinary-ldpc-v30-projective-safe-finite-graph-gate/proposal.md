# V30R — projective-safe finite-graph gate for GF32×GF32

Status: ARCHIVED — terminal `finite_graph_fail`
V30 P102 was accepted on 2026-08-20, but is superseded by this V30R revision.
The independent P103 freeze review was ACCEPTED on 2026-08-20. The frozen
packet was implemented and executed once in canonical `run_01`; the read-only
verifier returned `ok=true`, and the scientific terminal is
`finite_graph_fail`. Fresh qualification, promotion, and push remain outside
this change.

P103 must review the literature-aligned bounded cycle-cancellation rule:
projective/4-cycle FRC is a zero hard gate, Tanner-6 degeneracy is minimized
greedily and reported in aggregate, and Tanner-8 is topology-only. This bounded
rule replaces the superseded all-4/6/8-cycle FRC catalog requirement.

## What

Revise the finite-graph development gate so that it preserves the successful V25
channel model and V27/V29 leakage accounting, but replaces the V28R degree-two
matrix construction with deterministic projective-safe graph families and a
bounded, literature-aligned nonbinary short-cycle full-rank/cycle-cancellation
label rule.

The gate has four phases:

- M0: reproduce and persist the finite-column projective audit;
- M1: use channel-informed multilevel DE to screen a small, explicitly frozen
  allocation set;
- M2: construct and audit deterministic projective-safe finite matrices using
  the exact support/label tuples frozen in design §4; no alternate or informal
  ranking is permitted. Standard variable-side ACE is not used for `d_v=2`;
  coefficient labels use the frozen bounded 4-cycle hard gate plus Tanner-6
  cancellation score;
- M3: evaluate only the V25 validation split as a development finite-code gate.

## Why

V29 stopped after 9 of 300 blocks because the 1M source could reach at most
92/100 exact blocks, below the 95/100 gate. Independent V28R structural audit
found 303 duplicate projective classes and 1107 guaranteed proportional-column
weight-2 pairs in the shared L1 matrix, hence `d_min<=2` for that finite
construction. This is a graph-construction defect, not a conclusion that the

## Frozen input binding (V25/V26/V28R)

V30R MUST resolve all source and evidence inputs through the following existing
repository-relative paths. These are bindings, not new data inputs:

| source_id | V25 pairs path | delay_used_ps | V26/V28R label | V28R m2 |
|---|---|---:|---|---:|
| `type2_1M_20260121_184040` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet` | -50 | `1M` | 194 |
| `type2_1p5M_20260121_183806` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet` | +50 | `1p5M` | 200 |
| `type2_2M_20260121_183657` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet` | +50 | `2M` | 202 |

The V25 inventory and split authority are
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
and `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`.
The V26 canonical authority is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
(`RUN_MANIFEST.json`, `m0_report.json`, and `readonly_verify.json`). The V28R
canonical finite predecessor is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
(`v28_config.json`, `v28_evidence.json`, `RUN_MANIFEST.json`, and
`readonly_verify.json`). V29 holdout and raw `.ttbin` remain excluded.

The finite-field binding is explicit: construct `GF2mField.create(32)` using
primitive polynomial `0b100101` and the V28R field identity
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`.
For every support, `ratio_index` is the zero-based index into that field's
`nonzero_cycle` tuple; the index itself, not a regenerated/random label, is
persisted for replay.

The V26 channel-count binding is
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`.
V26 canonical `run_02/RUN_MANIFEST.json` records only
`counts_basename="channel_counts.npz"`; V30R resolves it to the exact V25
path. The F03 layer entropies are the float64
`detail["A02:<source_id>"].adapter_H.L1/L2` values in the bound V26
`m0_report.json`. Per-layer DE uses
`R_i=1-m_i/n`, `leak_i=5*m_i` bits, `f_i=leak_i/(n*H_i)`; the 64-bit tag is
excluded from single-layer DE. The finite total uses
`leak_total=5*m_total+64` and
`f_total=leak_total/(n*(H_L1+H_L2))`, all direct float64 with no extra
rounding; displayed values never determine a gate. Full definitions and
source values are frozen in design §1.2.

## In scope

- GF(32), `n=1024`, F03 natural MSB→LSB GF32+GF32;
- V26 train-only source/delay-conditioned channel posterior;
- source leakage budgets `m_total={200,206,208}` for 1M/1p5M/2M and the
  existing 64-bit tag accounting; the per-layer and total float64 equations
  are frozen in design §1.2;
- shared L1 allocation candidates `{9,12,16,24,32,40}`, with
  `m2=m_total-m1` source by source;
- deterministic `balanced-projective` and
  `PEG-projective-cycle-cancelled` graph families;
- fixed GF(32) nonzero-cycle coefficient candidates and projective-key
  uniqueness;
- bounded short-cycle cancellation: duplicate projective keys are the 4-cycle
  FRC failure and must be zero; candidate labels minimize newly closed
  degenerate Tanner-6 cycles by `(degenerate_6_new, ratio_index)`; Tanner-8 is
  topology/girth diagnostics only; for every ordinary short-cycle FRC audit,
  the alternating-product inequality is `Pi(C) != 1` (with `Pi(C)=1` recorded
  as the degenerate case);
- balanced/PEG support selection and Tanner-6 labels use only the exact
  algorithms and tuples frozen in design §4. Projective uniqueness is
  label-stage-only; newly closed Tanner-6 cycles contain the current column
  only and are counted independently for shared L1 and each source-specific
  L2;
- aggregate projective, rank, 4/6/8 topology, bounded-cycle, syndrome, tag,
  runtime, and finite validation evidence plus deterministic replay. Standard
  variable-side ACE is not used because `d_v=2` makes it identically zero.

## Out of scope

- reusing the V29 holdout as fresh qualification data;
- raw `.ttbin`, fresh qualification, promotion, or public residual claims;
- random degree/matrix search, seed libraries, random tie breaks, or blind
  repository search;
- MET, joint protograph, cross-layer checks, or a new decoder;
- changing q, n, F03 labels, channel training split, leakage target, or the
  V29 95/100 semantics without a new change.

## Frozen lifecycle boundary

Before P103 ACCEPT, only document review and static checks are allowed. After
P103, one M0–M3 execution packet may run under the frozen parameters. P102 is
retained as superseded historical review evidence and cannot authorize a run.
A failed individual M1 allocation is retained after its 12 registered calls and
does not interrupt the other allocations. Only the global condition of no
confirmed allocation is terminal `de_allocation_fail`; it does not authorize
random search. V30R PASS may propose V31 fresh time-separated qualification.
V31 PASS is the only route to V32 integration/benchmark work.

The M1 screen is exactly 72 calls: each allocation has all 12 calls (2 seeds ×
3 sources × 2 layers), and a failed allocation still completes and persists
its 12 calls. Eligibility requires all 12 calls to converge with final entropy
`<=0.01`. Eligible allocations are ranked by
`(worst_final_entropy, mean_final_entropy, m1)`; `min(2,Neligible)` are selected
for confirmation before any confirmation result is used. Each selected
allocation then completes exactly 30 confirmation calls (5 seeds × 3 sources
× 2 layers), even if it fails early; a failure only removes that allocation.
Thus confirmation has at most 60 calls. At least one selected allocation must
pass 30/30 to enter M2; if all selected allocations fail, terminal is
`de_allocation_fail`. If two allocations pass, the same tuple orders the
survivors before M2. For each confirmed allocation, M2 constructs at most two matrix packets total: at most one
  `balanced-projective` packet and at most one
  `PEG-projective-cycle-cancelled` packet.
Across at most two confirmed allocations this is at most four packets globally.
M3 screens that global set of at most four packets using fixed blocks `0..19`;
a matrix that cannot meet 15/20 is removed while the other registered packets
continue. After the complete screen, rank the eligible set using the exact
design §5 tuple (where `four_cycle_count` is the persisted shared-L1 plus
three-source-L2 total) and send only the
single top-ranked matrix to fixed confirmation blocks `20..69`. A top-ranked
confirmation failure is global `finite_graph_fail`; no second matrix is used as
a fallback.

For a 4-cycle, duplicate projective keys are exactly the alternating-product
FRC-degenerate case (`Pi(C)=1`); the hard gate requires zero duplicate keys and
zero proportional-column pairs. After support selection, each degree-two column
fixes its first coefficient to `1`; its second coefficient is considered in
the frozen GF(32) `nonzero_cycle` order. Before scoring, candidates that create
a duplicate projective key are rejected. For each remaining candidate, count
the newly closed degenerate Tanner-6 cycles in the currently assigned graph,
where degeneracy means the alternating product `Pi(C)=1`. Choose the
lexicographically minimal `(degenerate_6_new, ratio_index)`; a nonzero count is
allowed and is recorded in aggregate. Tanner-8 cycles are counted only as
topology/girth diagnostics and impose no label-FRC elimination rule. Support
selection MUST use only the exact tuples frozen in design §4; no alternate
maximum-girth/degree/ACE ordering is permitted. No RNG, seed library, random permutation, or
post-failure label search is permitted. If no candidate survives projective
uniqueness, the packet is rejected as `finite_graph_fail`.

M1 DE calls and M3 decoder calls each have an independent cumulative 24-hour
gate. The current call/block is persisted first; stage completion or a global
irreversible failure is decided before the resource gate. A screen-stage
matrix-local failure only removes that matrix; the other registered screen
packets continue. The single top-ranked confirmation failure is global and
terminal; it does not authorize a fallback packet. M2 construction is outside
both resource meters; an M2 implementation timeout is `implementation_blocked`.

## Terminal states

- `pass_projective_finite_graph_ready_for_fresh`;
- `finite_graph_fail`;
- `de_allocation_fail`;
- `resource_blocked`;
- `implementation_blocked`.
