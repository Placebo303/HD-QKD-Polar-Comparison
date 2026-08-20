# V30R Design — projective-safe finite-graph gate

Status: ARCHIVED — terminal `finite_graph_fail`.
V30 P102 (main-thread freeze review, 2026-08-20) is superseded by this V30R
revision. The independent P103 freeze review was ACCEPTED on 2026-08-20.
Implementation and the pre-registered V30R execution are complete in the
canonical `run_01`; independent read-only verification returned `ok=true` and
the scientific terminal is `finite_graph_fail`. Fresh qualification,
promotion, and push remain outside this change.

## 1. Immutable boundary

V29 is closed with `v29_finite_gate_fail` on an authorized 9-block prefix.
Its holdout is not a V30 validation or qualification source. V28R is the
engineering predecessor. V30R keeps `q=32`, `n=1024`, F03 natural
MSB→LSB GF32+GF32, the V26 train-only source/delay posterior, `lambda={2:1}`,
the 64-bit SHA-256 tag, and source leakage budgets. It does not alter the
decoder or fit a new channel from validation data.

P102 is historical evidence for the superseded V30 packet. It does not
authorize V30R implementation or execution. Only P103 ACCEPT can release the
V30R packet.

V30R deliberately uses a literature-aligned bounded cycle-cancellation rule:
the projective/4-cycle hard gate is exact, Tanner-6 label cancellation is
greedy and aggregate, and Tanner-8 is topology-only. It does not attempt an
infeasible all-cycle FRC enumeration at `n=1024`.

The M0 baseline audit is frozen as: 15 L1 support groups; maximum group
multiplicity 69; 303 duplicate projective classes; 922 columns in duplicate
classes; and 1107 guaranteed proportional-column/weight-2 pairs.

### 1.1 Exact predecessor input bindings

The following repository-relative paths and identifiers are frozen for V30R;
the change must not infer a new source from a path basename or read raw data:

| source_id | V25 pairs path | delay_used_ps | label | V28R m2 |
|---|---|---:|---|---:|
| `type2_1M_20260121_184040` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet` | -50 | `1M` | 194 |
| `type2_1p5M_20260121_183806` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet` | +50 | `1p5M` | 200 |
| `type2_2M_20260121_183657` | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet` | +50 | `2M` | 202 |

The V25 authority files are
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
and `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`.
The V26 canonical evidence is under
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
and is bound by `RUN_MANIFEST.json`, `m0_report.json`, and
`readonly_verify.json`. The V28R canonical configuration/evidence is under
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
and is bound by `v28_config.json`, `v28_evidence.json`,
`RUN_MANIFEST.json`, and `readonly_verify.json`.

The field contract is `GF2mField.create(32)`, primitive polynomial
`0b100101`, field_id
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`.
`ratio_index` is zero-based into the resulting field's deterministic
`nonzero_cycle` tuple and is persisted with every selected label.

### 1.2 Channel-count, entropy, and leakage authority

The V26 channel input is the exact V25 file
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`.
V26 canonical `run_02/RUN_MANIFEST.json` records
`counts_basename="channel_counts.npz"`; V30R resolves that basename only to
the exact V25 path above. The V26 adapter and its canonical M0 evidence are
therefore linked as: `run_02/m0_report.json` →
`detail["A02:<source_id>"].adapter_H.{L1,L2}`, where A02 is the frozen F03
GF32+GF32 factorization. The `adapter_H` float64 values, not the rounded
`v25_H` display fields, are the H authority:

| source_id | H_L1 bits/symbol | H_L2 bits/symbol | H_total = H_L1+H_L2 |
|---|---:|---:|---:|
| `type2_1M_20260121_184040` | 0.0242805468186788 | 0.7767572780789986 | 0.8010378248976774 |
| `type2_1p5M_20260121_183806` | 0.02519949687785432 | 0.8003665547438693 | 0.8255660516217236 |
| `type2_2M_20260121_183657` | 0.02566204879687012 | 0.8069006731253252 | 0.8325627219221954 |

For each source `s`, `m_L1=m1`, `m_L2=m2_s=m_total_s-m1`, and `n=1024`.
The per-layer DE contract is exactly
`R_i,s = 1 - m_i,s/n`, `leak_i,s = 5*m_i,s` bits, and
`f_i,s = leak_i,s/(n*H_i,s)` for `i in {L1,L2}`. The 64-bit tag is not part
of either single-layer DE input. The finite total contract is exactly
`leak_total,s = 5*m_total_s + 64` bits and
`f_total,s = leak_total,s/(n*(H_L1,s+H_L2,s))`. All quantities are computed
directly in float64 with no extra rounding; displayed decimals are for
inspection only and MUST NOT be used as gate inputs.

## 2. M0 projective-column audit

For a degree-two GF(32) column with nonzero entries at rows `a<b`, compute the
canonical key `(a,b,h_b/h_a)` in the frozen field. Equal keys are proportional
columns; their difference is a weight-2 kernel word. A valid matrix therefore
has no zero column, no zero coefficient, no duplicate key, and at most 31
ratios per support pair.

M0 rebuilds the V28R baseline and persists each column's support,
coefficients, normalized key, duplicate groups, proportional pairs, and the
derived weight-2 lower bound. M0 is read-only and cannot alter the baseline.

## 3. M1 channel-informed allocation screen

The frozen budgets and candidates are:

| source | m_total | shared m1 candidates | m2=m_total-m1 |
|---|---:|---|---|
| 1M | 200 | 9,12,16,24,32,40 | 191,188,184,176,168,160 |
| 1p5M | 206 | 9,12,16,24,32,40 | 197,194,190,182,174,166 |
| 2M | 208 | 9,12,16,24,32,40 | 199,196,192,184,176,168 |

The old V28R `m1=6` is a control only, not a V30 candidate. No candidate is
added after observing results. Existing V26 channel-informed DE is run
separately for L1/L2 with `lambda={2:1}` and frozen sequential conditioning.
Any layer/source/seed failure marks that allocation ineligible, but all 12
pre-registered calls for the allocation still execute and persist. Only a
global terminal (resource, verifier, implementation, or equivalent stage-wide
failure) may interrupt the registered call sequence; no tuning or rerun is
allowed.

Proposed reviewable parameters: screen `n_samples=400`, `max_iter=100`,
`tol=0.01`, `streak=20`, seeds `[30001,30002]`; confirmation
`n_samples=2000`, `max_iter=200`, `tol=0.01`, `streak=20`, seeds
`[30101,30102,30103,30104,30105]`. Every call binds source and delay.

One allocation's screen is exactly 12 calls: 2 seeds × 3 sources × 2 layers.
It is eligible only if all 12 converge with final entropy `<=0.01` bits.
Eligible allocations are ranked by the exact tuple
`(worst_final_entropy, mean_final_entropy, m1)`; the first
`min(2,Neligible)` are selected before any confirmation call. Each selected
allocation runs its complete 30-call confirmation (5 seeds × 3 sources × 2
layers), even when an earlier call has already failed; a failed allocation is
then removed and does not cancel the other selected allocation's 30 calls. At
least one selected allocation must pass 30/30 to enter M2. Thus M1 has exactly
72 screen calls and at most 60 confirmation calls (132 calls total maximum).
If all selected allocations fail confirmation, the terminal is
`de_allocation_fail` and no M2 construction runs. If two pass, the same tuple
orders them before M2.

M1 has one cumulative 24-hour DE meter. After each call result is persisted,
stage completion or an irreversible failure is evaluated first; only then may
the incomplete stage become `resource_blocked`, and no next call starts.

## 4. M2 deterministic projective-safe families and labels

For at most two DE-passing allocations, construct at most one packet from each
fixed family. Thus each allocation has at most two packets and the complete
M2/M3 packet set has at most four packets. A family construction failure is
retained as a rejected packet and does not authorize a replacement seed or a
third packet from that family. The families are not random searches and do not
use a seed library.

### balanced-projective

For each independent matrix state, process columns `j=0..n-1`. The candidate
support set is every `(a,b)` with `0<=a<b<m`, enumerated lexicographically.
For a candidate, add both edges hypothetically and define
`occupancy_after = 1 + count(previous_columns_with_support_(a,b))`,
`max_check_degree_after` as the maximum check degree after the addition, and
`sumsq_after = sum_r degree_after[r]^2`. Choose the unique minimum of the exact
tuple `(occupancy_after, max_check_degree_after, sumsq_after, a, b)`. Only
after this support is selected is its coefficient label assigned.

For the selected support, set the first coefficient to `1`. Enumerate unused
ratios as `(ratio_index, ratio)` in increasing zero-based `ratio_index` into
the frozen GF(32) `nonzero_cycle`; at most 31 ratios may be used by one
support. Reject a ratio only for the projective-duplicate hard gate, then
score it by the bounded newly-closed Tanner-6 rule in §4.1 and choose the
minimum `(degenerate_6_new, ratio_index)`. Support and label states are
deterministic and contain no RNG.

### PEG-projective-cycle-cancelled

Use deterministic progressive edge growth, again processing columns
`j=0..n-1` and enumerating `(a,b)` lexicographically. Before adding a candidate,
the check multigraph has one undirected edge `(u,v)` for every previously
assigned degree-two column support `(u,v)`; parallel edges are retained. Let
Let `d_check(a,b)` be the shortest-path edge distance between checks `a,b` in
this multigraph, or `infinity` if disconnected. Define `d(a,b)=2*d_check(a,b)`
as the corresponding prior Tanner check-to-check path length. The directly
implementable local Tanner-girth score is `d(a,b)+2` (equivalently
`2*d_check(a,b)+2`; a prior direct edge gives a 4-cycle). Minimize the exact tuple
`(component_flag, distance_cost, max_check_degree_after, sumsq_after, a, b)`,
where `component_flag=0,distance_cost=0` for `d_check=infinity`, and otherwise
`component_flag=1,distance_cost=-(d+2)`. This prefers disconnected candidates,
then larger local Tanner girth, then degree balance, then lexicographic ties.
Projective uniqueness is intentionally not checked during support selection.

After support selection, PEG uses exactly the balanced label procedure above:
first coefficient `1`, increasing `ratio_index`, projective duplicate rejection,
then the Tanner-6 score. Standard variable-side ACE is removed entirely: with
`d_v=2` its variable-side extrinsic ACE is identically zero and cannot rank
candidates. No random tie break, permutation, or extra RNG is permitted.

### 4.1 Frozen bounded short-cycle cancellation rule

The 4-cycle FRC hard gate is the projective-key gate: a duplicate normalized
key `(a,b,h_b/h_a)` is an alternating-product-degenerate 4-cycle and implies a
proportional-column weight-2 word. Every matrix MUST therefore have zero
duplicate keys and zero proportional-column pairs. Ordinary nondegenerate
4-cycles are allowed and are counted only for topology/ranking.

Assign each degree-two column in the frozen support order. Its first
coefficient is `1`; its second coefficient is considered in the fixed
`nonzero_cycle` order. First reject candidates that create a duplicate
projective key. For every remaining candidate, inspect only the newly closed
simple Tanner-6 cycles in the currently assigned graph. “Newly closed” means
the cycle contains the current column `j`; cycles wholly among prior columns
are not counted. A simple cycle candidate is formed only when `c notin {a,b}`,
`k1 != k2`, and the two distinct prior columns have supports exactly
`{a,c}` and `{c,b}` respectively, with current support `(a,b)`. Its canonical tuple is the
lexicographically smaller of `(j,a,k1,c,k2,b)` and
`(j,b,k2,c,k1,a)`; this counts each undirected cycle once. For each candidate
ratio, enumerate these canonical tuples as a set and count only those with
`Pi(C)=1`. Explicitly,
`Pi(C)=(h[a,j]/h[a,k1])*(h[c,k1]/h[c,k2])*(h[b,k2]/h[b,j])` in GF(32);
the FRC alternating-product inequality is `Pi(C) != 1`; reversing orientation
gives `Pi(C)^(-1)` and therefore the same degeneracy test (`Pi(C)=1`). The
candidate score is exactly
`(degenerate_6_new, ratio_index)`. Choose its lexicographic minimum; a nonzero
count is allowed and recorded in aggregate. This is bounded greedy cycle
cancellation, not all-cycle elimination.

The shared L1 matrix and each source-specific L2 matrix have independent
support/multigraph/ratio state initialized from empty state; no state or used
ratio set crosses from L1 to L2 or between sources.

Tanner-8 cycles are counted only as topology/girth diagnostics. They impose no
label-FRC constraint, are not individually persisted, and do not reject a
packet. No RNG, seed library, random permutation, or post-failure label search
is permitted. If no candidate survives projective uniqueness, the family
packet is rejected as `finite_graph_fail`.

For each selected allocation, the two families collectively produce at most
two matrix packets (one per family; shared L1 plus source-specific L2 bindings
are one matrix packet). Across at most two selected allocations, the complete
packet set is at most four. This is not two or four packets per family. If any
required matrix is not full rank, has a projective duplicate, or fails the
4-cycle FRC hard gate, that matrix/allocation-family packet is rejected; it
cannot be regenerated with another seed. Both families build shared L1 and
source-specific L2 matrices. Each matrix must report degree distributions,
GF(32) full row rank, no zero row/column, unique projective keys, support
occupancy, aggregate ordinary 4-cycle count, aggregate newly closed
degenerate-6 score totals/maxima, aggregate Tanner-8 topology count, girth
lower bound, `standard_ace_status=not_applicable_dv2`, support-score summary,
per-column selected ratio_index/score for deterministic replay, syndrome
consistency, and deterministic replay. No cycle catalog or per-candidate
rejection list is persisted. Any structural or projective failure rejects the
matrix before finite decoding.

## 5. M3 validation-only development gate

Only V25 validation frames are allowed: 1M `1200..1599`, 1p5M `1660..2059`,
and 2M `2187..2586`, inclusive; 400 frames/source, 256 pairs/frame, four
frames/block, 100 blocks/source. V29 holdout and raw `.ttbin` are forbidden.
Validation data cannot fit the channel or tune matrices, thresholds, split, or
iterations.

For the global set of at most four valid matrix packets total, screen fixed
blocks `0..19` per source with `max_iter=100`; a matrix is eligible only if every source
has at least 15/20 exact and tag-verified blocks and false accepts are zero.
For each packet, the ranking metric `four_cycle_count` is the total ordinary
4-cycle count across its shared L1 and its three source-specific L2 matrices:
`four_cycle_count = four_cycle_count_L1 +
sum_s four_cycle_count_L2[s]`. The evidence MUST persist the shared L1 count,
each of the three L2 components, and this total; the shared L1 count is included
once, not once per source.
Rank eligible matrices by
`(-min_source_exact, -total_exact, four_cycle_count, m1, family_order)`;
ordinary 4-cycle count is an ordering metric only, and `family_order` is
balanced-projective before PEG-projective-cycle-cancelled. After the complete
screen, only the single top-ranked eligible matrix uses fixed blocks `20..69`
per source. A screen-stage matrix failure removes only that matrix and does not
interrupt other registered screen packets. If no matrix is screen-eligible,
the gate is `finite_graph_fail`; if the single top-ranked confirmation fails
45/50, the gate is also `finite_graph_fail` and no fallback matrix is run.
Confirmation requires at least 45/50 exact and tag-verified per source, false
accepts zero.

L1→conditional-L2 is Bob-only and uses the actual returned `x1_hat`; L1
failure makes L2 `not_run`. Persist block status, iterations, syndromes, tags,
exact/errors, source/delay identity, and runtime. M3 has one cumulative
24-hour decoder meter. After each block is persisted, the screen matrix-local
threshold or the global top-ranked confirmation threshold is evaluated before
the resource gate. A screen failure does not interrupt other registered screen
packets; a confirmation failure is global and no fallback starts. All FER is
development-stage scoped.

## 6. Evidence, verifier, and terminal

The additive evidence root contains `RUN_MANIFEST.json`,
`projective_column_audit.json`, `de_allocation_screen.json`,
`de_allocation_confirmation.json`, `matrix_audits.json`,
`validation_frame_selection.json`, `validation_block_results.jsonl`,
`validation_summary.json`, `gate.json`, and `readonly_verify.json`.

The verifier rebuilds the field/config, projective keys, rank/topology,
4-cycle duplicate/proportional hard gate, deterministic per-column candidate
order and newly closed Tanner-6 degenerate counts, aggregate Tanner-8 topology
count/girth, packet caps, validation frame identity, source/delay binding,
syndromes/tags/leakage/f, exact M1 rank tuples and eligible/selected allocation
IDs, exact M2 family/matrix IDs, M3 matrix rank tuples, the four-cycle
components/total used for ranking, and attempted/selected
matrix IDs,
and terminal without rerunning DE or decoder. It
rejects V29 holdout paths, raw `.ttbin`, extra scientific inputs, duplicate
projective keys, and tampered aggregate/replay evidence.

`pass_projective_finite_graph_ready_for_fresh` requires every source to meet
45/50 exact and tag-verified, false_accept=0, `f<1.3`, and all structural and
manifest checks, including the 4-cycle FRC hard gate and bounded 6-cycle
cancellation audit. Other terminals are `finite_graph_fail`,
`de_allocation_fail`, `resource_blocked`, and `implementation_blocked`. If M1
has no confirmed allocation, terminal is `de_allocation_fail`; if M2 has no
valid matrix, terminal is `finite_graph_fail`; if M3 screen has no eligible
matrix or the single top-ranked matrix confirmation fails, terminal is
`finite_graph_fail`.
Only PASS may propose V31 fresh time-separated qualification; V32 integration
is downstream of V31 PASS.
