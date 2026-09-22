# Design — V72P2D6 GF32 graph/mother successor

## 1. Reuse map (import, never copy)

`v72p2d6_gf32_graph_mother.py` imports the accepted D5 module
`comparison_bench.formal_ir.v72p2d5_gf32_rate_mother` (aliased `d5`) and uses:

- arithmetic: `_gf32_mul_raw`, `_gf32_mul_vec_vec`, `_gf32_inv`, `_gf32_rank`,
  `_gf32_syndrome`, `Q=32`, `GF_POLY=37`;
- prior: `build_f_model_concentration`, `prepare_model_f_prior_candidate`,
  `marginalize_f_to_p1`, `conditionalize_f_to_p2`, `app_fed_l2_prior`,
  `oracle_l2_prior`, `symbols_to_layers`, `layers_to_symbols`;
- sampler: `sample_matched_block`;
- decoder adapter: `bind_historical_decoder` (cold start, `max_iter=90`,
  `damping=1.0` — frozen inside the D5 binder);
- layered-block semantics: `d5._run_layered_block` (L1 prior floor, APP-fed L2,
  oracle diagnostic, exact = full Alice equality, syndrome separate);
- audit: `audit_prefix`, `audit_frozen_prefixes`;
- constants: `LAMBDA_STAR`, `DECODER_FLOOR`, `L1_GRAPH_SEED`, `L2_GRAPH_SEED`,
  `MAX_ITER`, `DAMPING_ALPHA`.

No D5 production symbol is redefined. Any unavoidable reuse blocker stops the
task for a scope decision instead of patching D5.

## 2. Geometry (frozen)

Per `(n, layer)`: full mother is `(m_max, n)` with `m_max = n`.
Disclosure prefixes are the frozen row budgets:

| n   | L1 k_min | L1 prefixes    | L2 k_min | L2 prefixes    |
|-----|----------|----------------|----------|----------------|
| 64  | 49       | (49, 59, 64)   | 43       | (43, 52, 64)   |
| 128 | 98       | (98, 118, 128) | 86       | (86, 104, 128) |
| 256 | 196      | (196, 236, 256)| 172      | (172, 208, 256)|

M-arm degree-2 counts `N2`: MAX `k_min - 1`, HALF `floor((k_min - 1) / 2)`:

| n   | L1 MAX/HALF | L2 MAX/HALF |
|-----|-------------|-------------|
| 64  | 48 / 24     | 42 / 21     |
| 128 | 97 / 48     | 85 / 42     |
| 256 | 195 / 97    | 171 / 85    |

Support storage: per-column row lists in ascending order (canonical). Matrix
`H[r, v] = coeff` on support, else 0, values in `1..31`.

## 3. Arms (exact algorithms; full freeze in prereg §5)

- `B0_D5_DV3_NATIVE`: `d5.build_dv3_nested_support(n, n, k_min, seed)` +
  `d5.assign_gf32_coefficients(support, seed)` with D5 seeds
  L1 `2026090501` / L2 `2026090502`. Historical control, never a new winner.
- `B1_D5_DV3_COMMON_LABELS`: B0 support with the D6 common coefficient stream
  (label-stream control).
- `T1_PEG_DV3`: variables in order; 2 base edges in `[0, k_min)`, 1 expansion
  in `[0, m_max)`; sequential PEG choice maximizing BFS separation
  `(distance desc, check-degree asc, index asc)`; preference-ordered skip on
  base-pair/triple collision.
- `T2_CYCLE_GREEDY_DV3`: variables in order; exhaustive triple choice (2 base
  + 1 expansion) minimizing incremental `(four_cycles, max_pair_occupancy,
  variable_cycle_incidence_max, row_degree_max, row_degree_sumsq,
  support_tuple)` lexicographically (pair-count indexed, O(1) per candidate).
- `T3_SC_DV3_W4` / `T4_SC_DV3_W8`: base anchor `a_v = (v*k_min)//n`, window
  `{a_v..a_v+w-1}` clipped to `[0, k_min)`; expansion anchor
  `b_v = (v*m_max)//n`, window clipped to `[0, m_max)`; degree-balanced +
  lexicographic pick with collision skip and frozen full-zone overflow rule.
- `M1_ACCUMULATOR_FOREST_MAX` / `M2_ACCUMULATOR_FOREST_HALF`: first `N2`
  variables degree 2 as chain `i — i+1` (path forest, cycle rank 0 at every
  prefix); remaining variables degree 3 (2 base + 1 expansion) via
  check-degree-balanced + lexicographic placement with collision skip.
- Common coefficients: `rng = default_rng(202609120100 + n)` (L1) or
  `202609120200 + n` (L2); `vals = rng.integers(1, 32, (n, 3))`; column `v`
  edge `e` takes `vals[v, e]`; degree-2 columns use the first two entries.
  No candidate selection; projective-duplicate diagnostics recorded only.

## 4. Structural gates and blind selection

Per `(arm, n, layer, prefix)`: D5 `audit_prefix` items (rank, zero rows/cols,
components + largest fraction, degree histograms/maxima, 4-cycle count +
variable incidence max, duplicate/projective columns, base-pair/triple
duplicates) plus exact girth by Tanner-BFS (`NOT_COMPUTED` with reason only if
acyclic), row-degree max/sumsq, M degree-2 cycle rank by DSU, determinism
replay equality, no-parallel-edge check.
Eligible ⟺ every prefix passes: shape + nonzero GF32; `rank == rows`;
zero rows/cols 0; one component with all variables; duplicate/proportional 0;
base-pair/triple duplicates 0; no parallel edge; M cycle rank 0
(equivalent to D5 `audit_prefix.passed` plus the D6 extras).
Decoder set: B0 + B1 + best two eligible T by
`(four_cycles_sum, incidence_max, -girth_min, row_degree_max,
row_degree_sumsq_sum, arm_id)` at f1.2 prefixes (`NOT_COMPUTED` girth = -1,
worst) + both eligible M (no substitution; max 6 arms).
Fallbacks (pre-registered before any decoder call): best eligible T + best
eligible M.

## 5. Execution protocol

Prior: accepted Model-F artifact (`counts_ab`, `p_b`) loaded only through an
explicit `--model-f-root` (no default); E2 candidate via
`d5.prepare_model_f_prior_candidate`; `p1`/`p2` derived once per width.
Samples: generated once per `(n, block_seed)` via `d5.sample_matched_block`
in memory, reused byte-identically across arms.
Cell = `(arm, n, block_seed, width-point)` → `d5._run_layered_block`
(APP L1 + APP L2 + oracle-L2 diagnostic) = 3 decoder invocations counted
against the 2500-call budget; per-invocation 120 s watchdog in a dedicated
respawnable worker process (pids recorded); no retry — timeout/error consumes
the cell. Main-process + worker RSS recorded per cell (unknown RSS blocks
strong classification).
Canary: every frozen arm × 4 canary seeds × {f1.2, square}.
Advancement (new T/M arms only; B0 never, B1 control): f1.2 APP exact ≥ 1/4,
max 2, ordered by (f1.2 exact desc, f1.2 APP iter-total asc, square exact
desc, structural rank, arm_id). Confirmation: advancing arms × 16 seeds ×
{f1.0, f1.2, square}; strong ≥ 12/16, partial 1..11/16, both requiring
f1.0 ≤ f1.2 ≤ square, zero crash/nonfinite, zero APP exact/syndrome
disagreement (any `syndrome_ok != exact` on APP L1/L2, undetected errors
counted separately and never merged into exact), known RSS < 2 GiB.
Scaling (only if no new arm reaches 1/4 at n=64 f1.2): preregistered fallbacks
× 4 scaling seeds × {f1.2, square} at n=128, then n=256 if silent; first
signaling width advances ≤ 2 arms to 16-seed confirmation with the same rules
(labeled SCALING + width).

## 6. Evidence and gates

Development root `workspace/d6_graph_mother_r1_<uuid>/` holds scalar/metadata
only: `manifest.json`, `structure_records.csv`, `selected_arms.json`,
`decoder_records.csv`, `summary.json`, `command_log.txt`, plus scalar-ID
provenance of implementation/review. Independent scalar recomputation covers
coverage/counts/separation/extrema/advancement/classification.
Gates: implementation review PASS → Pre-EXECUTE review PASS → §8 calls (code
freeze; post-call fixes limited to evidence/report arithmetic; any code/graph/
seed/row/decoder change needs a new revision) → Pre-RESULT review PASS →
result solidification. Commits (local, exact-path staged, no push): (1)
OpenSpec+prereg+state; (2) implementation+tests+script; (3) reviews;
(4) evidence+result+state+memory/log appends.
