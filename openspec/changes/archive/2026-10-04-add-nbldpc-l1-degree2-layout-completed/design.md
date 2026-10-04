# Design — NB-LDPC L1 degree-2 layout Stage-1

Change `add-nbldpc-l1-degree2-layout`. Implementation-only; zero scientific
decoder calls. Claim ceiling: no FER/leakage/SKR/qualification/promotion/
publication/real-data claim; the candidate is a frozen construction bundle,
not an accepted route.

## §1 Module/driver/test names (S101: exactly one name frozen)

Candidate names were `nbldpc_l1_degree2_layout.py` vs
`v72p2d14_l055_degree2_layout.py`. FROZEN: the descriptive name, because the
`v72p2d14*` namespace is already occupied (`v72p2d14-scientific-validity-reset`,
`v72p2d14n-calibrated-discriminator`, `v72p2d14_rate_calibration_audit.py`,
`v72p2d14n_calibrated_discriminator.py`) and a second `v72p2d14*` L1 module
would collide in review indexing:

- `comparison_bench/src/comparison_bench/formal_ir/nbldpc_l1_degree2_layout.py`
- `comparison_bench/src/comparison_bench/cli/nbldpc_l1_degree2_driver.py`
- `comparison_bench/tests/test_nbldpc_l1_degree2_layout.py`
  (S-T01–S-T05) + `comparison_bench/tests/test_nbldpc_l1_degree2_driver.py`
  (S-T06–S-T08)

## §2 L055 degree cells (frozen, transcribed from D12 `degree_cell`)

| width | n2 | n3 | E | check distribution | m |
|---|---|---|---|---|---|
| 128 | 83 | 45 | 301 | 2^53 + 3^65 | 118 |
| 256 | 166 | 90 | 602 | 2^106 + 3^130 | 236 |

Arithmetic: 128: 2·83+3·45 = 166+135 = 301; 53+65 = 118; 2·53+3·65 =
106+195 = 301. 256: 2·166+3·90 = 332+270 = 602; 106+130 = 236;
2·106+3·130 = 212+390 = 602. Syndrome payload per layer (GF32, one full
symbol per row): `l1_syn_bits = 5·m1`, `l2_syn_bits = 5·m2`.

## §3 Sole scientific delta: d2-directed Phase-B layout (F-1)

Control C reuses the accepted connectivity-first degree-sequence PEG
(`r2.build_degree_sequence_peg`) on the L055 cell. Candidate S reuses the
IDENTICAL Phase-A spanning backbone (same `_backbone_seed`, same seeded
variable/check permutations, same attach rule) at the same graph seed, so
same-seed backbones are identical and the only divergence is Phase-B fill:

- B1: degree-3 variables first, in index order, with the shared R1 PEG/ACE
  rule verbatim (free non-adjacent checks; unreachable cycle-free merges
  first; else max BFS depth → max ACE → seeded tie-break).
- B2: degree-2 variables LAST, in seeded-permutation order
  (`v10_seed("nbldpc-l1-d2order:{seed}")` → `default_rng.permutation` over
  sorted d2 indices). Each d2 socket uses the directed candidate rule.

Directed candidate priority (frozen, evaluated in this order; NO post-hoc
selection of the most favorable structural metric):

1. Unreachable (cycle-free merge) candidates beat reachable ones (feasibility
   first; within unreachable: max free capacity → seeded tie-break, i.e. the
   shared rule unchanged).
2. Among reachable: max BFS depth first (desc).
3. Then min d2 short-cycle participation (asc): `four` = number of 4-cycles
   the edge would close whose opposite variable is degree-2 (d2–d2 loop
   proxy); `six` = number of 6-cycles through the edge touching another
   degree-2 variable (secondary key). Definitions in module docstring.
4. Then max ACE score (desc, shared `_ace_score`).
5. Then seeded tie-break (`v10peg._tie_pick(seed, variable, socket, group)`
   over the sorted tied list).

One deterministic attempt per seed; parallel edge / degree overshoot / socket
mismatch / dead end → `status="construction_failed"`, no partial graph, no
seed change. Same seed → same edge table → same coefficient stream
(deterministic replay = A6).

## §4 Admission (no new predicates)

A1–A6 are exactly `r2.structural_record` (A1–A5) plus deterministic replay
equality of sorted edge list AND coefficient stream (A6, mirroring
`r2.build_graph`/`d12.build_graph`). Four-cycle/girth/ACE stay diagnostics.
The module aliases — never reimplements — `structural_rank`,
`coefficient_seed`, `coefficients_for_edges`, `dense_from_edges`.

## §5 Coefficients and matrix conversion (F-2)

Frozen rule `d10:coeff:{width}:{graph_seed}` (`v10_seed`), one
`integers(1,32)` per edge in sorted `(v,c)` order. Pairing limitation
(frozen): control and candidate edge sets differ, so the shared stream rule
gives same-distribution, sorted-position-paired draws — NOT socket-identity
pairing. The Stage-2 conclusion ceiling is therefore "this construction
bundle paired at the graph seed", and no causal attribution beyond the layout
delta beyond that ceiling is permitted.

## §6 Thin driver (F-3)

`run_pair(decode_fn, h1c, h1m, h2, p1, p2, block)` assembles control vs
candidate on one FIXED H2, one shared data-frame object interface, one shared
prior/decoder binding, via `d5._run_layered_block(..., oracle, ...)` with
`oracle=False` HARDCODED on both arms (`ORACLE_HARDCODED = False` + assert;
the CLI exposes NO oracle switch). `oracle_exact` keys are asserted absent.
CHECK_UPDATED forward semantics inherited (`on_blocked_transfer="record"`).
The D11 outer MIX runner (`oracle=True` upper-bound arm) is never called.
`decode_fn` must be explicitly injected; `None`/non-callable refuses before
any binding. No production decoder import at module import time.

## §7 Output record schema reservation (F-4, no data produced in Stage-1)

`RESULT_SCHEMA_COLUMNS` (frozen order): `u1_exact`, `u2_exact`,
`pair_exact`, `syn_l1`, `syn_l2`, `syn_joint`, `verify_accept`,
`accepted_wrong`, `status` ∈ {`ok`,`nonconverged`,`resource_abort`},
`l1_syn_bits`, `l2_syn_bits`, `extra_parity_bits`, `verify_tag_bits`,
`other_public_bits`, `rounds`, `wall_s`, `rss_b`.
`accepted_wrong` (undetected) is a single isolated column and NEVER merges
into success: `is_success = pair_exact and verify_accept and not
accepted_wrong`; `resource_abort` never counts as success or zero-failure.
Failed frames keep full disclosure accounting (attempted, no refund).

## §8 Reuse map (import, never copy)

`r2.build_degree_sequence_peg` (control path), `r2.structural_record`,
`r2.structural_rank`, `r2.gf32_row_rank`, `r2.coefficient_seed`,
`r2.coefficients_for_edges`, `r2.dense_from_edges`, `r2.refuse_out_root`,
`v10peg._tie_pick/_bfs_distance/_ace_score`, `common.v10_seed`,
`GF2mField.create(32)`, `d5.symbols_to_layers/layers_to_symbols`,
`d5._run_layered_block`, `d5._require_check_updated_provenance`
(fail-closed reference). No other production binding.
