# V31 Design — deterministic finite-graph redesign gate

Status: FROZEN_BY_USER_OBJECTIVE (2026-08-20, new user-authorized change). The explicit V31 goal text is the authorization for implementation and one pre-registered execution.

## 1. Immutable boundary

V30R is archived with `finite_graph_fail`. Its balanced-projective and
PEG-projective-cycle-cancelled packets must NOT be rerun, expanded, or tuned.
V25/V26/V28R/V29 evidence is read-only authority. V31 keeps:

- `q=32` via `GF2mField.create(32)`, primitive polynomial `0b100101`, V28R
  field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`;
- F03 natural MSB→LSB GF(32)+GF(32) factorization of 10-bit symbols:
  `y1 = (symbol >> 5) & 31`, `y2 = symbol & 31`;
- V25 source/delay-conditioned channel posterior via the accepted V26 F03
  adapter;
- `lambda={2:1}`, 64-bit SHA-256 block tag, and the exact leakage equations;
- `m1=16` as the ONLY allocation; n ∈ {1024, 2048};
- the V28 decoder (`nonbinary_v28.decode_error_domain_posterior`) unchanged.

V31 is a development finite-gate only. It performs no qualification, promotion,
V29-holdout or raw-.ttbin usage, and no random matrix search or seed tuning.

## 1.1 Source, field, and H authority

Repository-relative paths and identifiers are frozen in proposal §"Frozen input
binding". The F03 H values are the float64 values in V26 canonical
`run_02/m0_report.json` at `detail["A02:<source_id>"].adapter_H.{L1,L2}`.

## 1.2 Allocation table

`m_total` for n=1024: 1M=200, 1p5M=206, 2M=208 (V30R authority).
`m_total` for n=2048: 1M=413, 1p5M=426, 2M=430 (V27 frozen budget table).

With `m1=16`:

| n | source | m_total | m1 | m2 | leak_total | f_total |
|---|---:|---:|---:|---:|---:|---:|
| 1024 | 1M | 200 | 16 | 184 | 1064 | 1.2971453628 |
| 1024 | 1p5M | 206 | 16 | 190 | 1094 | 1.2940931533 |
| 1024 | 2M | 208 | 16 | 192 | 1104 | 1.2949474816 |
| 2048 | 1M | 413 | 16 | 397 | 2129 | 1.29775 |
| 2048 | 1p5M | 426 | 16 | 410 | 2194 | 1.29764 |
| 2048 | 2M | 430 | 16 | 414 | 2214 | 1.29847 |

Total leakage is always `leak_total = 5*m_total + 64` bits, and
`f_total = leak_total / (n * (H_L1 + H_L2))`, computed directly in float64.

## 2. M0 read-only predecessor audit (no execution)

M0 rebuilds the V28R matrices in memory and re-extracts the V30R baseline
audit values (15 support groups / 69 max multiplicity / 303 duplicate classes /
922 affected columns / 1107 proportional pairs). It verifies the V25/V26/V28R
canonical files exist and their key fields match. M0 must not write to those
directories, must not read raw `.ttbin`, and must not invoke DE or a decoder.

## 3. M1 pre-registered 30-call DE confirmation (`m1=16`)

For each `n in {1024, 2048}`, run exactly these 30 MC-DE calls in this order:

- seeds: `(30101, 30102, 30103, 30104, 30105)`,
- sources in order 1M, 1p5M, 2M,
- layers in order L1, L2.

Each call uses:

- `n_samples = 2000`, `max_iter = 200`, `entropy_tol_bits = 0.01`,
  `streak = 20`;
- `rate = 1 - m_i/n` for the layer `i`;
- `rho = make_rho(rate, {2:1})` from `nonbinary_v26_mcde`;
- channel sampler from the V26 F03 adapter for that source/layer;
- the frozen seed.

A call PASSES iff `converged == True` and
`final_entropy_bits <= 0.01` (finite).

A block length's confirmation PASSES iff all 30 calls pass. Both block lengths
must pass before any matrix construction. If a block length has any failed call,
the terminal is `de_allocation_fail` and no M2/M3 runs for that length (and no
M2/M3 runs at all, because both lengths are required by the gate).

M1 has a single cumulative 24-hour DE meter across both block lengths. Each
call is persisted before the next call starts.

## 4. M2 deterministic matrix construction

For each block length that passed M1, construct one packet for each of the two
frozen families. A packet contains the shared L1 matrix (m1×n) and the three
source-specific L2 matrices (m2_s×n). Each packet's matrices are independent:
L1 and each L2 begin from empty graph/ratio state.

### 4.1 Coefficient label rule (both families, identical)

For every degree-two column with support `(a,b)`, `a<b`:

1. first coefficient is `1`;
2. second coefficient is chosen from the frozen GF(32) `nonzero_cycle` in
   increasing zero-based `ratio_index`;
3. a ratio already used for the same support (same projective key) is rejected
   before scoring;
4. for each remaining ratio, count newly closed simple Tanner-6 cycles
   containing the current column, exactly as in the V30R frozen rule, and score
   by `(degenerate_6_new, ratio_index)`;
5. choose the lexicographically minimal score.

The projective hard gate requires zero duplicate projective keys, zero
proportional-column pairs, no zero row/column, and full GF(32) row rank.
Topology diagnostics are bounded: the ordinary 4-cycle count is always exact
(from support multiplicities); the girth of the simple check graph is always
exact (BFS); exact 6/8-cycle enumeration over the check multigraph (C(m,3)/
C(m,4)) is computed only for small m (<=60) and for large V31 L2 sizes the
6/8-cycle counts are reported as `None` with `six_eight_exact=False`. These
diagnostics never enter the finite pass/fail gate (ranking uses only the exact
4-cycle count). Standard variable-side ACE is `not_applicable_dv2` because every
variable degree is 2.

The support pair occupancy constraint is a HARD structural constraint for both
families: for every support pair `(a,b)`, the number of columns using that
support must be `<= 31` (GF(32) has exactly 31 nonzero ratios). Construction
fails (packet rejected) if this is violated; no fallback construction is
allowed.

### 4.2 Family 1 — `PEG-capacity-aware`

Process columns `j=0..n-1`. The candidate set is all `(a,b)`,
`0 <= a < b < m`, in lexicographic order. The implementation may use vectorized
numpy scoring as long as the mathematical score and tie-break are EXACTLY the
frozen tuple below. State:

- `occupancy[(a,b)]` = number of already-assigned columns with that support;
- `degrees[r]` = check degree of row r;
- `dist[a][b]` = shortest-path edge distance `d_check(a,b)` in the current
  check multigraph (all-pairs matrix, `inf` when disconnected), updated
  incrementally after each edge insertion via the standard two-side relaxation
  `dist[x][y] = min(dist[x][y], dist[x][u]+1+dist[v][y],
  dist[x][v]+1+dist[u][y])` for the new edge `(u,v)`;
- `edges` = list of prior supports (a multigraph).

For each candidate `(a,b)`:

- skip if `occupancy[(a,b)] >= 31` (capacity-exhausted hard gate);
- `occupancy_after = occupancy[(a,b)] + 1`;
- `d_check = dist[a][b]`; `d = 2*d_check`;
- `component_flag = 0, distance_cost = 0` if disconnected, else
  `component_flag = 1, distance_cost = -(d+2)`;
- `max_degree_after` and `sumsq_after` from the hypothetical degree update
  (only the two endpoints change by one);
- score tuple (lexicographic min):
  `(occupancy_after, component_flag, distance_cost, max_degree_after,
  sumsq_after, a, b)`.

Select the minimum tuple among capacity-valid candidates; assign the support;
then apply §4.1 label rule.
This makes the construction explicitly projective-capacity-aware: it prefers
less-used supports first and hard-stops at 31 uses.

### 4.3 Family 2 — `QC-cyclic-projective` (deterministic control)

This is a deterministic quasi-cyclic control family with a completely different
structural prior from PEG. For a matrix with `m` rows and `n` columns:

- Enumerate candidate supports by increasing shift `s = 1, 2, 3, ...`, and for
  each `s`, increasing base row `a = 0..m-1`:
  `support = (min(a, (a+s) mod m), max(a, (a+s) mod m))`;
- skip candidates where `a == (a+s) mod m` (i.e., `s % m == 0`);
- stop as soon as `n` supports are selected.

This yields a cyclic-symmetric support set. Each support pair has multiplicity
at most `ceil(n/m)/...` bounded by the number of `s` values with the same
`(a,s) mod m` class; the implementation MUST compute and assert the hard
`occupancy <= 31` bound.

After support selection, apply §4.1 label rule column by column in the same
deterministic order. No RNG, seed, permutation, or library search is used.

Rationale for the control arm: it is a structurally regular QC-type graph, not
an entropy-balanced or locally-girth-maximized graph; it isolates whether
projective-capacity-aware PEG support ordering is what matters, versus any
deterministic finite GF(32) graph.

### 4.4 Packet rejection semantics

If any required matrix fails the structural gate (rank, projective hard gate,
occupancy>31, zero row/column), that family packet for that block length is
REJECTED with `finite_graph_fail`-per-packet status and is persisted. No
replacement construction, seed change, or rerun is allowed. If both families
are rejected for a block length, the overall terminal is `finite_graph_fail`.

## 5. M3 Bob-only validation gate

### 5.1 Validation frames and blocks

Only V25 validation frames are used (same as V30R):

- 1M: frames 1200..1599 (400 frames)
- 1p5M: frames 1660..2059 (400 frames)
- 2M: frames 2187..2586 (400 frames)

Block grouping by n:

- n=1024: 4 frames/block, 256 symbols/frame → 1024-symbol blocks,
  100 blocks/source;
- n=2048: 8 frames/block, 256 symbols/frame → 2048-symbol blocks,
  50 blocks/source.

V29 holdout (1M 1600..1999, 1p5M 2213..2612, 2M 2916..3315) and raw `.ttbin`
are forbidden.

### 5.2 Decoding

Bob-only sequential decoding: for each block, factor Bob symbols into
L1/L2 GF(32) layers, decode L1 from Bob posterior rows with the public L1
syndrome using the V28 decoder (`max_iter=200`, `streak=20`); if L1 succeeds,
decode L2 conditioned on the returned `x1_hat`; otherwise L2 is `not_run`.
Alice symbols are used only offline to compute truth syndromes, exact
comparison, tag, and FER; they are never passed to the adapter/decoder.

Per block record fields:

- `source`, `source_id`, `delay_used_ps`, `block_index`, `frame_ids`;
- `l1_ok`, `l2_ok`, `l1_status`, `l2_status`, `l2_not_run_due_l1`;
- `l1_syndrome_ok`, `l2_syndrome_ok` (syndrome convergence per layer);
- `offline_exact`, `tag_verified`, `false_accept`;
- `l1_symbol_errors`, `l2_symbol_errors` (counts, not full arrays);
- `l1_iterations`, `l2_iterations`, `decoder_calls`, `runtime_s`.

All blocks are evaluated for every (n, family) packet that was constructed
(no screen/confirmation split): the full window is the waterfall itself.

### 5.3 Aggregate summaries and waterfall

For each (n, family) packet and each source, persist:

- `block_count`, `exact_count`, `tag_verified_count`, `false_accept_count`;
- `syndrome_convergence = (l1_ok AND l2_ok) / block_count` per source;
- `exact_fer = 1 - exact_count/block_count`;
- `tag_fer = 1 - tag_verified_count/block_count`;
- `failure_positions` = list of `{block_index, exact_failed, tag_failed,
  l1_failed, l2_failed}` for blocks that are not exact/tag-verified;
- `waterfall` = per block index: cumulative exact count and cumulative tag
  count (from block 0 through that index), per source and overall.

### 5.4 Pass/fail thresholds (pre-registered)

For a given (n, family), PASS means for EVERY source:

- `exact_count >= ceil(0.95 * block_count)` (n=1024: ≥95/100; n=2048: ≥48/50);
- `tag_verified_count >= ceil(0.95 * block_count)` (same counts);
- `false_accept_count == 0`.

V31 finite result:

- `finite_graph_pass` iff, for EACH n in {1024, 2048}, at least one family
  packet passes;
- otherwise `finite_graph_fail`.

The comparison report must state, for each n: which family wins on exact FER,
tag FER, syndrome convergence, and where failures are concentrated (block
indices/sources).

### 5.5 Resource gate

M3 has INDEPENDENT cumulative 24-hour decoder meters per block length
(n=1024 and n=2048), because the two lengths are separate validation gates with
different block counts. Each block record is persisted before the next block
starts. If a block length's meter hits its limit, that length is
`resource_blocked`; if any required length is resource-blocked, the overall
terminal is `resource_blocked`. A complete window that fails thresholds is
`finite_graph_fail`, not resource.

## 6. Evidence layout

Additive root:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`

Files:

- `RUN_MANIFEST.json` — global frozen config, source/field/input bindings,
  allocation registry, stage results summary, terminal;
- `de_confirmation.json` — all 60 M1 calls for both n (30 per n), with
  per-n pass/fail;
- `m1_registry.json` — registered order/sets/params for the 60 calls;
- `matrix_audits.json` — per-n per-family matrix audits (audits are aggregate +
  deterministic per-column label-replay; no cycle/candidate rejection lists);
- `matrix_payloads.json` — per-n per-family matrices (deterministic replay);
- `validation_frames_n1024.json`, `validation_blocks_n1024.json`,
  `validation_frames_n2048.json`, `validation_blocks_n2048.json`;
- `per_block_n1024.jsonl`, `per_block_n2048.jsonl` — block records for all
  (n, family) windows, with `stage`-independent `packet_id`/`n`/`family`
  columns;
- `summary_n1024.json`, `summary_n2048.json` — per-source per-family
  syndrome/FER/failure-position/waterfall summaries;
- `gate.json` — terminal and the evidence needed to recompute it;
- `readonly_verify.json` — verifier output.

## 7. Read-only verifier

`verify_v31(run_root)` recomputes, from persisted evidence only (no DE, no
decoder):

- field/config/source/input binding equality;
- allocation table for both n;
- M1 registry and call-order replay, per-n 30-call counts, per-n pass;
- per-n per-family matrix audit consistency: occupancy<=31, duplicate
  projective keys == 0, proportional pairs == 0, full rank, deterministic
  label-replay equality;
- validation frame/block identity for both n;
- block-record registration (no duplicates, correct source/block order,
  per-packet full-window completeness when a packet was run);
- per-source exact/tag/syndrome/false-accept/FER/waterfall recomputation;
- terminal recomputation and equality with persisted terminal;
- `no_de_rerun=true`, `no_decoder_rerun=true`.

The verifier must return `ok=true` and `problems=[]` for the terminal to be
final.

## 8. Prohibited operations

- no V30R packet re-execution, expansion, or tuning;
- no random matrix-library search, seed libraries, random permutations, or
  post-failure label search;
- no qualification/promotion/public-residual claims;
- no V29 holdout, raw `.ttbin`, or new channel fitting;
- no modification of V25/V26/V28R/V29/V30R evidence directories;
- no push.
