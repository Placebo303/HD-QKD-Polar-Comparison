# Design — V72P2D10 R3 fresh-graph scaling replication (readiness)

Change: `v72p2d10-r3-fresh-graph-scaling`
Cycle: `V72P2D10-MIXED-DEGREE-L1` (successor replication of accepted R2/A1)
Track: implementation/readiness (no EXPLORE/DECIDE execution; zero scientific
  decoder calls; no `--r3-batch`, no L2/APP, no D7-H, no real data, no
  commit/push).
Authority: `.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md`
  §1–§4 (frozen). Reuse baseline (read-only):
  `openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/design.md` +
  spec, `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`,
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/EXPLORATION_LOG.md`.
A1: root `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`,
  stored terminal `D10_L1_AMBIGUOUS`, reviewed `VERIFIED PASS` — immutable,
  contextual-only, never pooled into R3.

## 1. Two-arm isolation contract (preserved from R2/A1)

Exactly two arms: `PEG_DV3_MATCHED` (regular degree 3, matched control) vs
`PEG_DV23_LAM2_045` (D9-selected `lambda2 = 0.45` mixed `{2,3}` candidate).
Both arms SHALL share: the connectivity-first shared constructor
`build_degree_sequence_peg`, the v10 tie-breaking policy (BFS-depth → ACE →
seeded pick), the graph-seed rule, the coefficient-distribution/stream rule,
the Model-F L1 prior chain, the row count `m` per width, the block seed set
and paired block objects, the decoder (`v35.decode_row_layered_fftqspa`),
schedule (cold row-layered), iteration cap (`max_iter=90`), damping
(`damping_alpha=1.0`), field (`q=32, poly=37`), syndrome/exact/stop semantics
and record schema. The candidate differs only where mathematically forced by
its degree/socket profile: variable degree histogram, total sockets `E`, and
the floor/ceil check-degree allocation. No other difference is permitted.

Primary scope only: L1 marginal decoding; f1.2 rows `(n,m) = (128,118),
(256,236)`; q=32 polynomial 37; cold row-layered v35 decoder `max_iter=90`,
`damping_alpha=1.0`; exact and syndrome-valid reported separately with
provenance and residual syndrome weight. Not in scope: no L2, APP transfer,
oracle-L2, f1.0, square point, alternation or D7-H; no FER/leakage/SKR/
qualification/promotion/real-data claim.

## 2. Constructor and admission (R2 mechanics reused unchanged)

R3 implements NO new construction mathematics. It reuses the R2
connectivity-first shared constructor `build_degree_sequence_peg` and the
A1–A6 admission unchanged:

- A1: exact variable/check degree histograms == §3 + socket balance
  `sum_v d(v) = sum_c d(c) = E`;
- A2: simple bipartite graph (no duplicate edge, no empty check, min check
  degree == §3 min);
- A3: exactly ONE connected component over all `n+m` Tanner nodes;
- A4: deterministic structural rank `structural_rank == m`;
- A5: exact GF32 (poly 37) row rank `gf32_rank == m` under the frozen
  coefficient rule;
- A6: deterministic replay equality (identical sorted edge list +
  coefficient stream on rebuild).

Any A1–A6 failure blocks without seed replacement (no retry/resume/repair/
seed search/adaptation). Four-cycle/girth/ACE remain reported diagnostics
only. R302 SHALL reuse the R2 construction and decoder path rather than
copying them.

## 3. Frozen degree tables (n128/n256; transcribed from R1 READINESS)

| arm | n | m | n2 | n3 | E | check allocation |
|---|---|---|---|---|---|---|
| `PEG_DV3_MATCHED` | 128 | 118 | 0 | 128 | 384 | `3^88 + 4^30` |
| `PEG_DV3_MATCHED` | 256 | 236 | 0 | 256 | 768 | `3^176 + 4^60` |
| `PEG_DV23_LAM2_045` | 128 | 118 | 71 | 57 | 313 | `2^41 + 3^77` |
| `PEG_DV23_LAM2_045` | 256 | 236 | 141 | 115 | 627 | `2^81 + 3^155` |

Socket balance `E = 2*n2 + 3*n3 = sum(d*count)` holds in every cell
(384/768/313/627); realized rate is exactly `1 - m/n`. R3 SHALL NOT
re-derive, re-round, re-select or repair these integers. STOP on any
table drift.

## 4. Seeds, coefficients, blocks, prior, call order (frozen)

- Graph seeds (fresh, never searched or replaced): n128
  `2026092401, 2026092402, 2026092403, 2026092404, 2026092405, 2026092406`;
  n256 `2026092501, 2026092502, 2026092503, 2026092504, 2026092505, 2026092506`.
  Verified absent from the repo (proposal §"Frozen successor design" scan;
  matches only in the authority packet). STOP with BLOCKED + raw evidence if
  any seed collides.
- Block seeds (fresh, separate from graph seeds, never searched or replaced):
  n128 `2026092601..2026092612` (12); n256 `2026092701..2026092712` (12).
  Verified absent (same scan).
- Coefficient rule (frozen): `COEFF_SEED =
  v10_seed(f"d10:coeff:{width}:{graph_seed}")`, one `integers(1,32)` per edge
  in sorted `(variable,check)` order; same rule both arms.
- Blocks: one matched block sampled once per `(width, block_seed)` from the
  accepted CAL-only Model-F artifact; the same block object is used by both
  arms and all six graphs at that width (paired decoding on identical L1
  blocks).
- Prior chain (frozen; same both arms): load `counts_ab`, `p_b` from
  `workspace/v72p2d5_model_f_input/20260907_r1` (CAL-only) →
  `prepare_model_f_prior_candidate` → `marginalize_f_to_p1` →
  `_floor_renorm(DECODER_FLOOR=1e-15)`; no VAL/real-data contact.
- Call order (deterministic): widths n128 first, n256 only iff
  `R3_REPRODUCED(n128)`; within a width arm `PEG_DV3_MATCHED` before
  `PEG_DV23_LAM2_045`; graph seeds ascending; block seeds ascending. Per call:
  select admitted graph → `syndrome_of_gf32(H, u1)` →
  `decode_row_layered_fftqspa(H, priors, syn, max_iter=90,
  damping_alpha=1.0, warm_beliefs=None, field=GF32/poly37)` → record `exact`
  (`syndrome_ok and x_hat == u1`), `syndrome_ok`, residual syndrome weight,
  iterations, status, provenance. `exact` and `syndrome_ok` never merged.
- Each width: 2 arms × 6 graphs × 12 paired blocks = 144 calls; max 288.

## 5. Gates, terminals, root, budgets (frozen, packet §2 verbatim logic)

For each graph let `M_g` and `C_g` be MIX and DV3 exact counts from the same
12 blocks. Let `M`, `C` be fresh-width pools (72 each). Exact is primary;
syndrome-valid is reported separately and never substitutes for exact.

`R3_REPRODUCED(w)` iff all hold:

1. `M >= 18`;
2. `M - C >= 12`;
3. MIX wins (`M_g > C_g`) on at least 5 of 6 graph pairs;
4. at least 4 of 6 MIX graphs have `M_g >= 2`;
5. `C <= 6`;
6. no engineering/resource violation.

`R3_NEGATIVE(w)` iff `M <= 6` OR `M - C <= 3`, with no engineering block.
Otherwise `R3_AMBIGUOUS(w)`. Paired discordances, exact one-sided McNemar and
intervals are reported descriptively; p-values do not override the frozen
gate.

Terminals:

- n128 NEGATIVE → `D10_R3_N128_NOT_REPRODUCED`;
- n128 AMBIGUOUS → `D10_R3_N128_AMBIGUOUS`;
- n128 REPRODUCED then n256 NEGATIVE → `D10_R3_FINITE_WIDTH_DECAY`;
- n128 REPRODUCED then n256 AMBIGUOUS → `D10_R3_N256_AMBIGUOUS`;
- both REPRODUCED → `D10_R3_WIDE_L1_SIGNAL_REPRODUCED`;
- otherwise explicit engineering/resource blocked terminal.

Future root (absent, unauthorized; verified absent — STOP if present):
`workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`.
Budgets: ≤288 scientific calls; ≤50 setup units (=24 graph builds + 24
width-block samples + Model-F load + plan build); wall ≤1800 s; ≤120 s/call;
RSS <2147483648 B; one process; no retry/resume/repair/seed search/adaptation.
No-overwrite; A1 contextual-only non-pooling rule (A1 evidence MUST be
impossible to pool into R3 gate arithmetic).

## 6. Claim ceiling

The future batch establishes at most a synthetic finite-length L1-only
diagnostic under the accepted CAL-only Model-F prior and the frozen decoder
contract. It establishes no L2/APP result, no FER, no leakage, no SKR, no
qualification, promotion or real-data claim, and no DE-to-decoder equivalence.
D7-H is not revived by any R3 outcome. Readiness (R301–R310) establishes at
most that the R3 plan is frozen, specified, admission-bounded, and
mechanically routable with zero decoder calls.
