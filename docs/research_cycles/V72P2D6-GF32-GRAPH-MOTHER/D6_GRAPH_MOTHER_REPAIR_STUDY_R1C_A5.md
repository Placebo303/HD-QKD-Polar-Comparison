# D6 graph/mother repair study R1c-A5 (sandbox-only, zero decoder)

Status: `REPAIR_STUDY_R1C_A5` =
`STRUCTURALLY_INFEASIBLE_AS_FROZEN` + redefinition menu
(`REQUIRES_MAIN_THREAD_RULING`, nothing landed).
Prereg: `D6_GRAPH_MOTHER_PREREG_R1C_A5.md` §A5-04 (rules frozen before
evaluation; order frozen: fewest changed support entries, then lower maximum
row degree, then rule ID; no decoder criterion exists or may be introduced).
Machine matrix: `D6_GRAPH_MOTHER_REPAIR_MATRIX_R1C_A5.csv` (60 rows:
10 rules x 3 widths x 2 layers; byte copy of the validated workspace product).
Decoder calls: exactly zero (sandbox construction + frozen coefficient
assignment only; real-decoder records: none anywhere in A5 work (the only
`decoder_records.csv` files are explicit-fake unit-test fixtures under
task-owned basetemps, permitted).

## Preregistered rules (uniform per family, frozen coefficient stream)

Sandbox builders:
`workspace/d6_r1c_a5_repair_9a2b4c1d8e6f4a3b8c5d7e0f1a2b3c4d/sandbox_sc_m.py`
(evaluator `sandbox_eval.py`); production `build_support` never imported for
construction (only for diffing). No randomness, no seed search.

- T3 (w=4) / T4 (w=8) mirrors: `-01` frozen order/windows, expansion rescues
  the `(deg,index)`-least doomed row (rows with degree+future-opportunities<2)
  with a free triple (overflow counted iff outside the window); `-02` frozen
  logic verbatim in reverse variable order; `-03` frozen windows, first base
  pair admitting a windowed triple-free expansion wins (triple veto on the
  base commitment), frozen global fallback only if none admits one.
- M1 (MAX) / M2 (HALF) mirrors, chain frozen: `-01` degree-3 base pairs in
  global least-degree-sum order; `-02` base-pair row order descending
  (largest-degree first). Expansion frozen (least-degree in C minus base,
  triple-skip) in both.
- T2 rank: no admissible rule (key/order frozen); recorded as bound.
- B0/B1: no repair (controls).

## Outcome: 0/10 rules admissible (R1-R5 per rule, all 6 cells)

| rule | I1-all cells /6 | gates-all /6 | changed entries (total) | max row deg | worst square nbelow | failing R |
|---|---|---|---|---|---|---|
| R-T3-01 | 0 | 5 | 228 | 4 | 81 | R3 (I1) |
| R-T3-02 | 0 | 0 | 2537 | 5 | 82 | R3 (I1+gates: rank/dups) |
| R-T3-03 | 0 | 6 | 0 (identity) | 4 | 81 | R3 (I1) |
| R-T4-01 | 0 | 6 | 965 | 6 | 78 | R3 (I1) |
| R-T4-02 | 0 | 0 | 2610 | 5 | 80 | R3 (I1+gates: rank/dups) |
| R-T4-03 | 0 | 6 | 0 (identity) | 6 | 77 | R3 (I1) |
| R-M1-01 | 0 | 6 | 0 (identity) | 3 | 83 | R3 (I1) |
| R-M1-02 | 0 | 0 | 504 | 87 | 85 | R3 (I1+gates) |
| R-M2-01 | 3 (L1 only) | 0 | 14 | 4 | 25 | R3 (gates where I1 passes) |
| R-M2-02 | 0 | 3 (L2 only) | 1728 | 171 | 94 | R3 (I1 where gates pass) |

R1 determinism holds for all 10 (replay True everywhere, re-verified on a
10-cell sample with full agreement on replay/I1/changed/admissible).
R2 holds (variable degrees preserved, no parallel edges; frozen replay True).
R4-structure holds except via R3 gate failures (no new parallel edges; the
`-02` rules introduce rank deficiency and base-pair duplicates, i.e. new
gate defects). The frozen evaluation order is moot: no rule passes R3, so no
rule reaches ordering.

## Why each rule fails (mechanism, verified by re-run)

- `-03` rules (T3/T4) and R-M1-01 are byte-identical to frozen production
  (changed entries 0 at all 6 cells, re-verified): the triple-availability
  veto never triggers because the frozen expansion pick is already the first
  triple-free candidate, and global least-degree-sum base ordering coincides
  with the frozen `(deg,index)` path. They are non-repairs: same I1
  violations as frozen (worst square nbelow 81/77/83).
- `-01` (SC): doomed-row rescue fires too late. A row becomes doomed
  (degree + future opportunities < 2) only when almost no covering variable
  remains, so rescue redirects a handful of late expansions (T3: 228
  entries total; T4: 965) while the interior zone rows keep exactly one hit
  each. Worst cells unchanged (81/78 below).
- `-02` (SC/M reverse/descending order): destroys the frozen pair/triple
  discipline — T3-02 rank falls to 254/126/62-pattern with base-pair
  duplicates, T4-02 rank to 251-124 with max row degree 5, M1-02 max row
  degree 87 with 504 changed entries. Gate defects replace degree defects.
-   M2-01 fixes I1 at L1 widths (2/1/4 changed entries) but L1 was never the
  problem: frozen gates (rank, base-pair duplicates) still fail there, and
  L2 still violates I1 (up to 25 below at n256). M2-02 mirrors it (gates pass
  at L2, I1 fails at L1 with up to 94 below, max row degree 171).
  No single uniform rule satisfies I1 and the frozen gates jointly (R1+R3).
## Infeasibility proofs (as-frozen)

- M1/M2-zone counting (exact): zone rows take edges only from the
  degree-3 expansions (base+chain confined to B). M1-MAX has Z+1 expansions
  for Z zone rows needing 2Z ends => >= Z-1 rows below degree 2 under any
  R2-compliant rule (observed == bound at all 6 cells: 14/20/29/41/59/83).
  M1 is unrepairable without lifting R2.
- SC window discipline: the frozen `(deg,index)` order provably singles each
  interior zone row (validity doc §A5-02: expansions-in-zone == zone rows,
  one hit each); the three preregistered disciplines exhaust the
  window-preserving space (forward rescue too late, reverse gate-breaking,
  veto vacuous) with worst cells unchanged at 77-82 below.
- T2 rank and B0/B1 bounds are recorded, not repaired (prereg).

## Redefinition menu (<=3, REQUIRES_MAIN_THREAD_RULING, NOT landed)

- Option A (SC lift): permit one extra expansion edge per variable whose
  window covers an interior zone row (those variables degree 3->4; windows,
  widths, seeds, coefficient stream otherwise frozen). Changes the
  variable-degree profile (R2 lift) and shifts §6 selection-key inputs
  (sumsq/rmax) => selection re-freeze required; decoder structure still
  dc>=2. Minimal single-edge addition.
- Option B (M lift): allow M degree-3 base pairs to cover zone rows (lift
  the two-zone base confinement for M only; chain/forest/N2/coeffs frozen).
  Weakens the M-over-B identity; selection keys shift. Minimal
  placement-domain lift, no new edges or degrees.
- Option C (no knob change): declare SC+M families structurally inadmissible
  as frozen; R1d proceeds eligible-only {B0,B1,T1} with T2 rank-bound
  recorded. The D6 question becomes unaskable for SC/accumulator families;
  zero science change, zero re-freeze. Minimal (status ruling, not repair).

## Sandbox/production separation (A5-A08)

Production `build_support` output byte-identical: double-build replay True
for T1/B0/B1 at all widths/layers plus T3/M1 n64 spot cells (validation
part4); the `-03`/`M1-01` identity finding independently confirms the
sandbox never leaked into production (identical outputs, separate module,
no production import for construction). T1/B0/B1 matrices satisfy I1 and
all frozen gates at every dispatched prefix (validity matrix: 18/18, 11-12
cells frozen-eligible with zero I1 delta).
