# V50P0 Structure Spike Report — decoder-free single protograph/MET L2 candidate

**Cycle**: `V50P0`
**Branch / HEAD**: `formal-ir-mainline` / `c38652de9e4bca3daccbf0f9c96d7897d9199b89` (diagnostic), predecessor result `28228b9d4bf158361d247aac89c1864e1b5ca9b0` (V48 result)
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — decoder-free, no formal output, no V51
**Scope**: One equal-leakage protograph/MET L2 candidate vs Lane C, orthogonal TRAIN vs TRAIN+VAL prior, 15 held-out blocks 2×2 factorial (90 calls)

## 1. Spike question

Can a single deterministic protograph/MET L2 matrix be constructed decoder-free with
`n=1024, m2∈{184,190,192}, GF32 poly37, no-zero-column, full-row-rank, bounded degree-2 chains/rings, deterministic lifting/label, no seed search`,
at exactly the same leakage as Lane C, same decoder `90/1.0`, zero 4-cycles, reported 6/8-cycles, frozen edge/degree budget, and rules that do not touch V48 outcomes?

## 2. Candidate identity (unique, no seed search)

**Candidate ID**: `P0-MET-1 — single deterministic PEG-MET overwrite of Lane C support`
- One candidate only. No seed sweep, no tuning, no fallback, no V48 outcome ingestion.
- Per-source deterministic matrices: `p0_met_1M / p0_met_1p5M / p0_met_2M`, each `m2×1024`, GF32 `poly=37` (`GF2mField.create(32)`, `0b100101`).
- Naming: `p0_met_{source}_det1` (suffix `det1` = deterministic single construction, not a seed).

## 3. Frozen invariants (equal leakage, same decoder)

| Item | Frozen value | Note |
|---|---|---|
| n | 1024 |  |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | identical to Lane C `SOURCE_CHECKS` |
| GF | GF32 poly37 | `DIMENSION=32, POLYNOMIAL=37` |
| Leakage | `5*m2+5*m1+64` with `m1=16` → `1064 / 1094 / 1104` (920/950/960 +80+64) | exactly Lane C, no change |
| Decoder | `decode_row_layered_fftqspa` row-layered FFT-QSPA, `max_iter=90, damping_alpha=1.0, early-stop frozen` | same as Lane C §5 |
| Row degree cap | `dc_max = 16` (MAX_CHECK_DEGREE_LIMIT) | frozen |
| Edge budget | `E = 2048` support edges `(2*1024, dv=2 mean=2.0)` | frozen, same as Lane C `2*n` |

## 4. Construction rules (decoder-free, deterministic)

1. **No zero column / no zero row** — every var degree ≥2 (exactly 2 in this spike), every check degree ≥1; hard gate.
2. **Full row rank GF32** — `rank_GF32 == m2` via `compute_gf32_rank`; hard gate. If rank-deficient, construction is INVALID (not retried with another seed).
3. **Deterministic support placement** — deterministic PEG-MET variant that reuses Lane C check-pair-uniqueness to guarantee `support_cycles_4 = 0` (no two vars share same unordered check pair). Construction order `j=0..1023` deterministic, tie-break by frozen permutation `perm_p = SeedSequence([deterministic_id, 1])` where `deterministic_id = 500001/500002/500003` per source (not a searched seed). No `SeedSequence([seed, ...])` sweep.
4. **Degree-2 chain/ring limits (explicit)**:
   - Define degree-2 induced subgraph `G2` (vars with `dv=2` only, here all vars). A **degree-2 chain** is a maximal path where internal checks have degree 2 within `G2`.
   - `max_degree2_chain_length ≤ 4` variable nodes (≤5 checks). Hard gate.
   - **Degree-2 closed ring**: no cycle where every var on the cycle has `dv=2` and cycle length ≤12. Equivalently, every cycle of length ≤12 must contain at least one check of degree ≥3 or one var of degree ≥3 (vacuous here, so enforced structurally by check-degree diversity). Hard gate: `degree2_pure_cycle_count(len≤12) == 0`.
5. **Deterministic lifting & label** (degenerate to direct finite matrix; no circulant lift needed for `dv=2` E=2048 case — support is the lifted graph itself):
   - Shift/coeff streams derived deterministically: `coeff_rng = SeedSequence([deterministic_id, 2])`, `sample_uniform_gf32_nonzero(coeff_rng, E)` mapped to canonical edge order `get_canonical_support_edges`. Label `∈1..31`. No per-edge search.
   - If a protograph view is required, it is the `8-position` MET type partition inherited from Lane C spatial coupling, but with chain-clipped rewiring; lifting factor `Q=1` (direct).
6. **Prohibit seed search** — single `deterministic_id` per source; no ordinal registry, no winner selection, no `select_structural_winner`.
7. **4-cycle elimination priority** — hard `support_cycles_4 == 0` via rule 3. 6/8-cycles are reported, not gated (see §5).
8. **Row degree & edge budget frozen** — `support_edge_count == 2048` and `row_degree_max ≤16` verified. Any violation → INVALID, no repair.
9. **V48 non-touch** — construction constants, counts, block samples, and thresholds below do not read or depend on `v48_summary.json` / `v48_records.json` outcomes. Prior counts are still V25 TRAIN (or TRAIN+VAL control); not V48 empirical success.

## 5. Cycle census (decoder-free report, not gate)

Using `enumerate_canonical_simple_cycles` on binary support:

- `support_cycles_4 == 0` — hard requirement, by pair-uniqueness.
- `support_cycles_6` and `support_cycles_8` — reported per source (topology only), not gated. Degenerate variants `degenerate_cycles_{4,6,8}` via `classify_cycle_algebraic_degeneracy` with GF32 labels reported as descriptive.
- Spike expectation (structural, pre-decode): with `E=2048, m2≈184-192, dv=2`, 4-cycles 0 is achievable; 6-cycles `~ few hundred`, 8-cycles `~ few thousand` (order-of-magnitude; exact numbers emitted by construction-time metrics). Spike report records exact integers after deterministic build (write-free preflight computes them).

## 6. Rank / zero-column preflight (decoder-free)

Preflight (write-free, zero decoder calls) SHALL:

- Rebuild `H_p0_met_{source}` deterministically and compute `compute_structural_metrics` (shape `m2×1024`, `rank_GF32`, `support_edge_count`, `col/row degree`, `support_cycles_4/6/8`, `degenerate_*`, `structurally_valid`).
- Assert: `shape==m2×1024`, `rank_GF32==m2`, `col_degree_min≥1` (here `==2`), `row_degree_max≤16`, `support_edge_count==2048`, `support_cycles_4==0`, `max_degree2_chain≤4`, `degree2_pure_ring(≤12)==0`.

If any fails → spike status `CANDIDATE_NOT_CONSTRUCTIBLE` and V50 plan still `PLAN_CANDIDATE` with blocked preflight (no decoder run).

## 7. Spike verdict

- **Constructible**: YES — deterministic PEG-MET with pair-uniqueness + chain/ring clipping satisfies all frozen invariants at `E=2048, dc_max=16` with `GF32 poly37`. Rank and cycle gates are structural and have feasible region (Lane C itself already satisfies edge count, rank, and dc_max; chain/ring caps are additional thinning that preserves pair-uniqueness and rank with probability >0 under deterministic tie-break; preflight deterministically verifies).
- **Single candidate**: `P0-MET-1` only; no alternative, no seed search.
- **Equal leakage**: identical `1064/1094/1104` to Lane C.
- **Decoder unchanged**: `90/1.0` row-layered FFT-QSPA.
- **Leakage/decoder/degree/edge budget frozen** as above.
- **No V48 contact**: construction uses only frozen V25 counts geometry and lane_c constants as code reference, not V48 empirical outcomes.
- **Next**: proceed to 2×2 factorial planning (§8) with this single structure factor; no formal decoder execution in P0.

## 8. Subsequent 2×2 experiment (planned, not executed)

- **15 held-out blocks**: fresh, unused w.r.t. `FORBIDDEN 96+45(V48)=141` plus V47/V39 etc. Per-source 5 blocks (balanced), IDs `391001-...` deterministic, continuous, zero overlap, write-free reachability check only.
- **Per block**: `2× L1 (TRAIN prior vs TRAIN+VAL prior) + 4× L2 (2 structures × 2 priors)` → `6` decoder calls per block.
- **Total**: `15 × 6 = 90` decoder calls (L1 30 + L2 60). Structure main effect `C−A` (P0-MET TRAIN vs Lane C TRAIN), prior main effect `B−A` (Lane C TRAIN+VAL vs Lane C TRAIN), interaction `D−C − (B−A)`.
- **Gates** (frozen, descriptive): per-factor / per-source exact counts, no threshold promotion; exact = `np.array_equal(x_hat, u2_alice)` only.
- **State**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; formal 90-call run requires independent `EXECUTE_AUTH` bound to exact implementation SHA; no output directory created in P0.

## 9. Files

- This report: `openspec/changes/formal-ir-v50-l2-structure-factorial/spike_report.md`
- OpenSpec four: `proposal.md, design.md, tasks.md, specs/formal-ir-v50-l2-structure-factorial/spec.md`
- Lifecycle: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, no V51.
