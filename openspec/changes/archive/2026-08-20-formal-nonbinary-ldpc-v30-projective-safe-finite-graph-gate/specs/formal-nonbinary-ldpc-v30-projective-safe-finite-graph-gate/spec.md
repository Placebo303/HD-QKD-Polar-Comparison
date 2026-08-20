# Spec — v30r_projective_safe_finite_graph_gate

Status: ARCHIVED — terminal `finite_graph_fail`. P102 was accepted by the main thread on
2026-08-20 for the superseded V30 packet. The independent P103 freeze review
was ACCEPTED on 2026-08-20, releasing this V30R revision for implementation and
pre-registered execution. Canonical `run_01` completed with independent
read-only verifier `ok=true` and scientific terminal `finite_graph_fail`; fresh
qualification and promotion remain outside the release boundary.

## Requirement: frozen architecture and allocation

The implementation MUST use `q=32`, `n=1024`, F03 natural MSB→LSB
GF32+GF32, the V26 train-only source/delay posterior, `lambda={2:1}`, and
the frozen 64-bit tag/leakage contract. It MUST use only shared `m1` in
`{9,12,16,24,32,40}` with source `m_total={200,206,208}` and `m2=m_total-m1`.
V28R `m1=6` is a control and MUST NOT be promoted as a candidate. No degree,
matrix, seed, split, threshold, or iteration search is allowed.

M1 MUST execute exactly 72 screen calls: 12 per allocation (2 seeds × 3
sources × 2 layers). Eligibility requires all 12 final entropies `<=0.01` and
convergence. Eligible allocations MUST be ranked by
`(worst_final_entropy, mean_final_entropy, m1)`; at most the first two are
selected before confirmation. Each selected allocation MUST complete exactly
30 confirmation calls (5 seeds × 3 sources × 2 layers), even after a failure;
failure removes only that allocation. Thus confirmation is at most 60 calls,
and at least one selected allocation must pass 30/30. If all selected
allocations fail, the terminal is `de_allocation_fail`. A failed screen
allocation MUST still finish and persist all 12 registered screen calls; only a
global terminal may interrupt that registration sequence.

## Requirement: exact predecessor and field binding

The implementation MUST bind the V25 inventory
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
and split manifest
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`.
The exact source mapping is:

| source_id | pairs path | delay_used_ps | label | V28R m2 |
|---|---|---:|---|---:|
| `type2_1M_20260121_184040` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet` | -50 | `1M` | 194 |
| `type2_1p5M_20260121_183806` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet` | +50 | `1p5M` | 200 |
| `type2_2M_20260121_183657` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet` | +50 | `2M` | 202 |

V26 MUST bind the canonical
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
`RUN_MANIFEST.json`, `m0_report.json`, and `readonly_verify.json`. V28R MUST
bind
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
`v28_config.json`, `v28_evidence.json`, `RUN_MANIFEST.json`, and
`readonly_verify.json`. V29 holdout and raw `.ttbin` are forbidden.

Arithmetic MUST construct `GF2mField.create(32)` with primitive polynomial
`0b100101` and field_id
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`.
`ratio_index` MUST be zero-based into the deterministic `nonzero_cycle` tuple
and MUST be persisted for every selected coefficient.

The V26 channel-count input MUST be exactly
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`.
The V26 canonical `run_02/RUN_MANIFEST.json` `counts_basename` value is
`channel_counts.npz`, and that basename MUST resolve only to the V25 path
above. For F03, each source/layer entropy MUST come from
`run_02/m0_report.json` at
`detail["A02:<source_id>"].adapter_H.L1/L2`; rounded `v25_H` fields are not
authoritative. For source `s` and layer `i`, with `n=1024`, the DE equations
MUST be `R_i,s=1-m_i,s/n`, `leak_i,s=5*m_i,s` bits, and
`f_i,s=leak_i,s/(n*H_i,s)`. The 64-bit tag MUST NOT enter either single-layer
DE input. The total finite equations MUST be
`leak_total,s=5*m_total,s+64` bits and
`f_total,s=leak_total,s/(n*(H_L1,s+H_L2,s))`. Implementations MUST compute
these equations directly in float64 with no extra rounding; display values
MUST NOT determine a gate.

## Requirement: projective safety and bounded deterministic cycle cancellation

Every degree-two column MUST have two nonzero entries. Its normalized key MUST
be `(sorted_check_pair, coefficient_ratio)` in GF(32). A matrix MUST have no
duplicate key, no proportional-column pair, no zero row/column, and full row
rank. L1 is shared; L2 is independently source-specific. Balanced-projective
and PEG-projective-cycle-cancelled are the only allowed families in this change.
For rows `a<b`, the first coefficient MUST be `1` and the second MUST follow
the frozen GF(32) nonzero-cycle without repeating a ratio for that support.
PEG MAY choose supports only, using the exact support tuple frozen in design §4;
no alternate or informal support ordering is allowed. Standard variable-side
ACE is not a discriminator because `d_v=2`. No extra RNG is allowed. A rank
failure rejects the matrix and cannot be repaired by changing a seed.

The 4-cycle FRC hard gate MUST be implemented as the projective-key gate:
duplicate normalized keys and proportional-column pairs MUST both be zero.
This is equivalent to rejecting the alternating-product-degenerate 4-cycle
(`Pi(C)=1`) and implies no weight-2 word from such a pair. Ordinary
nondegenerate 4-cycles are allowed and are only counted for topology/ranking.

During sequential label assignment, a candidate ratio MUST first be rejected
if it creates a duplicate projective key. For every remaining candidate, the
implementation MUST exactly count newly closed simple Tanner-6 cycles in the
currently assigned graph. “Newly closed” MUST mean that the cycle contains the
current column `j`; prior-only cycles are excluded. For current support `(a,b)`,
use `c notin {a,b}`, distinct prior columns `k1 != k2`, and prior supports
exactly `{a,c}` and `{c,b}` respectively. The canonical tuple
MUST be `min((j,a,k1,c,k2,b),(j,b,k2,c,k1,a))`, counted once. In GF(32),
`Pi(C)=(h[a,j]/h[a,k1])*(h[c,k1]/h[c,k2])*(h[b,k2]/h[b,j])`; reversal gives
`Pi(C)^(-1)`, so the degenerate test is invariant and is `Pi(C)=1` (the FRC
inequality is `Pi(C) != 1`). The candidate MUST be scored by exactly
`(degenerate_6_new, ratio_index)` and the lexicographically minimal score MUST
be chosen. A nonzero score is allowed and MUST be aggregated; it is not a
failure. Tanner-8 cycles MUST be used only for aggregate topology/girth
diagnostics and MUST impose no label-FRC constraint. No RNG, seed library,
random permutation, post-failure label search, per-cycle catalog, or
per-candidate rejection list is allowed. If no candidate survives projective
uniqueness, the family packet MUST be rejected as `finite_graph_fail`.

Balanced support construction MUST process columns `j=0..n-1`, enumerate all
`0<=a<b<m` lexicographically, and minimize
`(occupancy_after,max_check_degree_after,sumsq_after,a,b)`. PEG support
construction MUST form a check multigraph with one undirected edge for each
prior degree-two column support (parallel edges retained). Let `d_check(a,b)`
be its shortest-path edge distance, or infinity when disconnected, and define
`d(a,b)=2*d_check(a,b)` as the corresponding Tanner path length. Its exact
support tuple MUST be
`(component_flag,distance_cost,max_check_degree_after,sumsq_after,a,b)`;
use `component_flag=0,distance_cost=0` for infinity and otherwise
`component_flag=1,distance_cost=-(d(a,b)+2)`. Thus local Tanner girth is
directly `d(a,b)+2` (equivalently `2*d_check(a,b)+2`), projective uniqueness is
label-stage-only, and standard
variable-side ACE is omitted because `d_v=2` makes it zero. Shared L1 and each
source-specific L2 MUST use independent empty support/multigraph/ratio state.

The two families MUST produce at most one packet per family per selected
allocation, hence at most two packets per allocation. Because M1 retains at
most two allocations, the complete M2/M3 packet set MUST contain at most four
packets globally.

## Requirement: validation boundary

M3 MUST use only validation frames 1M `1200..1599`, 1p5M `1660..2059`, and 2M
`2187..2586`, inclusive. It MUST use 256 pairs/frame and four-frame 1024-
symbol blocks. V29 holdout, raw `.ttbin`, and validation fitting/calibration
are forbidden.

## Requirement: finite development gate

Screen MUST evaluate the global set of at most four matrix packets, with fixed
blocks `0..19` per source at `max_iter=100`, and require 15/20
exact/tag-verified per source with false_accept=0 for each of at most four
matrices. Ordinary 4/6/8-cycles are allowed and only enter audit/ranking;
duplicate-projective/4-cycle FRC failures MUST be zero. Tanner-6 degeneracy
may be nonzero and is aggregated; Tanner-8 is topology-only. Eligible matrices
MUST be ranked by the exact design §5 tuple
`(-min_source_exact,-total_exact,four_cycle_count,m1,family_order)`, where
`four_cycle_count=four_cycle_count_L1+sum_s four_cycle_count_L2[s]` includes
the shared L1 once and all three source-specific L2 counts. The four components
and total MUST be persisted;
standard variable-side ACE MUST NOT appear because `d_v=2` makes it zero;
`family_order` is balanced-projective before PEG-projective-cycle-cancelled.
After the complete screen, only the single top-ranked eligible matrix MUST be
run on fixed blocks `20..69` per source at `max_iter=200` and require 45/50
exact/tag-verified per source with false_accept=0. A screen-stage matrix failure
removes only that matrix and does not interrupt other registered screen packets.
If no matrix is screen-eligible, or the single top-ranked confirmation fails,
the global gate is `finite_graph_fail`; no fallback matrix may be run.
L1→L2 is Bob-only and L2 receives only the returned L1 estimate. Every block
record MUST be persisted before the next block; L1 failure makes L2 `not_run`.

M1 DE calls and M3 decoder calls MUST have independent cumulative 24-hour
meters. After a current call/block is persisted, stage completion or a global
irreversible failure is evaluated before the resource gate. A screen-stage
matrix-local failure MUST remove only that matrix; other registered screen
packets may continue. A top-ranked confirmation failure is global and MUST NOT
start a fallback. M1 MUST finish all 12 calls for a failed allocation unless a
global terminal occurs. No unregistered call/block may start after a global
terminal. M2 construction is outside both meters, but an M2 implementation
timeout is `implementation_blocked`.

## Requirement: terminal and verification

PASS MUST be `pass_projective_finite_graph_ready_for_fresh` and requires all
structural, projective/4-cycle-FRC, bounded-6-cycle, binding, leakage, and
confirmation gates. Other terminals MUST be
`finite_graph_fail`, `de_allocation_fail`, `resource_blocked`, or
`implementation_blocked`. M1 with no confirmed allocation is
`de_allocation_fail`; M2 with no valid matrix is `finite_graph_fail`; M3 with
no eligible screen matrix or the single top-ranked confirmation failed is
`finite_graph_fail`. The
verifier MUST rebuild projective audits, the 4-cycle duplicate/proportional hard
gate, deterministic per-column candidate order and newly closed Tanner-6 scores,
aggregate Tanner-8 topology/girth, packet caps, and replay evidence, including
rank tuples, eligible sets, selected allocation/family/matrix IDs, and terminal
selection, without rerunning DE/decoder. It MUST NOT require a complete cycle
catalog or per-candidate rejection list. If the single top-ranked matrix
confirmation fails, the verifier MUST recompute the global `finite_graph_fail`
terminal and confirm that no fallback matrix was run. PASS only permits
proposing V31 fresh qualification; it does not itself qualify or promote.
