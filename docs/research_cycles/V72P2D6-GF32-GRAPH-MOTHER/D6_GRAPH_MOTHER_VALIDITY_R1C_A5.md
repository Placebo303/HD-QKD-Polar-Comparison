# D6 graph/mother validity matrix R1c-A5 (structure-only, zero decoder)

Status: `VALIDITY_R1C_A5` (Track A evidence; not an authorization).
Branch `formal-ir-v72p1-addendum-clean`, HEAD `1f1622a7` (I1 gate landed).
Prereg: `D6_GRAPH_MOTHER_PREREG_R1C_A5.md` (`FROZEN_PREREG_R1C_A5`).
Machine matrix: `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv` (144 rows:
8 arms x {64,128,256} x {L1,L2} x 3 frozen prefixes; byte copy of the
validated workspace product).
Decoder calls in A5-01/A5-02: exactly zero (frozen builders + `d5.audit_prefix`
+ `audit_extra` only; scan evidence `part5_decoder_scan.json`: 8 files, 0 hits).

## A5-01 method (own implementation, no main-thread import)

`workspace/d6_r1c_a5_matrix_3f1c9a2e7b4a4f8e9c1d5a6b7e8f0a1b/a5_validity_matrix.py`
rebuilds every `(arm,n,layer)` from the frozen production builders
(`build_support` + `assign_mother_from_support`), double-builds for
determinism replay, and audits every frozen prefix with `d5.audit_prefix`
plus `audit_extra` (I1 diagnostics). T2 n128/n256 built structure-only
(4 groups x 2 replay halves; supports persisted as `ref_supports/*.npz`,
documented reuse as the A6 exact-equivalence reference). The main-thread
artifact `workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/`
was used only as a later cross-check (never imported).

Validation (`workspace/d6_r1c_a5a6_validcheck_6bac31b6d872/`, zero decoder):
- part1: 132/132 shared cells agree exactly on `row_degree_min`,
  `rows_below_degree_2`, `variable_degree_min` and violation verdict; the 12
  T2 n128/n256 cells are matrix-only extension (main-thread audit marks them
  `NOT_DISPATCHED_AT_WIDTH` by design). Zero value disagreements.
- part2: 51/51 recomputed cells match every matrix field
  (`row_degree_min`, `rows_below_degree_2`, rank, zeros, components,
  duplicates, `row_degree_max/sumsq`, frozen/new eligible); all rebuilds
  replay True (incl. T2 n64 L1 18.2 s / L2 14.1 s double-build walls,
  matching the matrix `build_wall_s` 18.12/13.94).

## Verdict grid (per arm x width x layer: frozen eligible / I1-new eligible)

`E` = all 3 prefixes eligible, `f` = fails one frozen gate at >=1 prefix,
`1` = fails I1 only (frozen-eligible), `F` = fails frozen gates and I1.
n64 row first (dispatched width), then n128, n256; each pair is L1 L2.

| arm | n64 | n128 | n256 |
|---|---|---|---|
| B0 | E E | E f(dup) | f(disc)/f(rank) f(disc) |
| B1 | E E | E f(dup) | f(disc) E / f(disc) E |
| T1 | E E | E E | E E |
| T2 | f(rank@sq) f(rank@sq) | f(rank@sq) f(rank@sq) | f(rank@f1.2,sq) f(rank@sq) |
| T3 | 1 1 | 1 1 | 1 1 |
| T4 | 1 1 | 1 1 | 1 1 |
| M1 | 1 1 | 1 1 | 1 1 |
| M2 | f f | f f | f f |

Per-cell census (18 cells/arm): B0 frozen 11/new 11; B1 12/12; T1 18/18;
T2 11/11; T3 18/6; T4 18/6; M1 18/6; M2 3/3. I1 binds exactly on the
SC/M families (T3/T4/M1 lose f1.2+square everywhere; M2 already frozen-out).
Controls (B0/B1/T1/T2) are I1-neutral: no control cell changes eligibility.

Degree-1 inventory (rows with check degree < 2 at dispatched prefixes):

| family | n64 f1.2 / square | n128 f1.2 / square | n256 f1.2 / square |
|---|---|---|---|
| T3 | 10 / 12 | 20 / 27-39 | 40 / 57-81 |
| T4 | 8 / 8-14 | 20 / 23-35 | 40 / 53-77 |
| M1 | 9 / 14-20 | 19 / 29-41 | 39 / 59-83 |
| M2 | 0 / 0-6 | 0 / 0-12 | 0 / 0-25 |
| T1/B0/B1 | 0 / 0 | 0 / 0 | 0 / 0 |

(T2 passes I1 everywhere: min row degree 2 at every prefix; its bound is rank.)

## A5-A02: frozen `eligible` and the A2 five-arm selection reproduced exactly

Recomputed from the matrix under the frozen rule (arm eligible iff every
prefix of both layers at n64 is frozen-eligible; selection = B0 + B1-if +
best-2 eligible T by the frozen f1.2 §6 key + eligible M, cap 6):

- frozen eligible: B0 T, B1 T, T1 T, T2 F (square rank 63/62), T3 T, T4 T,
  M1 T, M2 F — identical to committed `selected_arms.json` `eligible` map.
- T-rank keys (four_sum, incid_max, -girth, rmax, sumsq, arm):
  T1 `(0,0,-8,4,1102)`, T3 `(13,2,-4,4,1309)`, T4 `(21,2,-4,6,1299)` —
  best two = T1, T3.
- selected = {B0,B1,T1,T3,M1} — identical to committed `selected_arms.json`
  `selected` and to fallbacks (`fallback_T`=T1, `fallback_M`=M1).
- Under I1 the eligible set collapses to {B0,B1,T1} (no eligible M arm;
  the §8.4 fallback pair loses its M leg) — the eligible-only branch.

## A5-02 root cause per family (mechanism + counts, proofs)

Notation: `B=[0,k_min)` base zone, `Z=[k_min,m)` expansion-only zone
(base pairs and the M chain never leave B by construction: SC builder
window/global stages draw base pairs from `Wb`/`range(k_min)` only;
M chain `(v,v+1)` and base pairs from `range(k_min)` only).

- T3/T4 (SC, w=4/8): zone rows receive only expansion edges. Frozen
  `(deg,index)` least-degree ordering with sliding windows gives each
  interior zone row exactly one expansion: T3 n64 L1 places 10 expansions
  over the 10 f1.2 zone rows (one each, rows exactly [49,59)) and 18 over
  the 15 square zone rows (12 x1 + rows 61-63 x2; degree-1 rows exactly
  [49,60]). Same shape at every width/layer (zone rows = degree-1 rows;
  only the trailing ~3 rows mop up second hits). Late zone rows always lose
  index ties to earlier candidates and, once at degree 1, lose to degree-0
  rows — the frozen discipline cannot give any interior zone row its second
  hit. T4 identical with w=8 (degree-1 rows exactly the zone rows).
- M1 (MAX, N2=k_min-1): counting impossibility under R2. Zone Z=n-k_min
  rows need 2Z edge-ends, all from the n-N2=Z+1 expansion edges (base+chain
  confined to B). Hence >= Z-1 zone rows sit below degree 2 for every
  (n,layer), under any R2-compliant placement. Observed equals bound
  exactly: n64 L1 14 (rows [50,63], row 49 takes the single spare of the 16
  in-zone expansions), n64 L2 20, n256 L2 83. No window-preserving repair
  can beat this; only a knob lift (menu in the repair study) can.
- M2 (HALF, N2=(k_min-1)/2): expansions are plentiful (e.g. 36 in-zone vs
  ~12 needed at n64 L2) but frozen least-degree-in-C ordering fills early
  zone rows first and starves the tail (degree-1 rows exactly the last zone
  rows: [58,63] at n64 L2). L1 widths pass I1 (min 2) yet fail frozen gates
  (n64 rank 63/48-63 pattern, n128+ base-pair duplicates); L2 fails I1 at
  f1.2/square. Ordering, not counting, is the force — and the two
  preregistered reorderings each fix one side while breaking the other
  (repair study).
- T2 (rank): square-prefix rank deficiency at every width —
  n64 63/62, n128 123/122, n256 246/240 (L2 square 16 short). Greedy
  four-cycle minimization accumulates linear dependencies. Key/order frozen
  => no admissible rank rule preregistered; recorded as a bound.
- B0/B1 (controls, unmodified): n128 L2 one base-pair duplicate (all three
  prefixes); n256 f1.0-prefix disconnection (B0 L1 11 / L2 41 components;
  B1 same) reconnecting at f1.2/square; B0 n256 L1 square rank 255 (B1 256).
  These bound the dispatchable set and are not repaired.

## Decoder-precondition inventory (gate-gap class closure)

Every structural precondition of the historical decoder/adapter
(`comparison_bench/.../v35_algorithm_development.py`, FWHT check update)
maps to a frozen gate — except one, now closed by I1:

| precondition (code) | frozen gate before A5 | status |
|---|---|---|
| check degree >= 2 (`_check_update_log_batch`, v35:464-465; extrinsic FWHT undefined for dc<2) | NONE (`zero_rows` blocks only degree 0) | CLOSED by I1 (eligible-AND + dispatch guard + verify) |
| no zero rows / cols | `audit_prefix.passed` (zero_rows/zero_cols==0) | gated |
| variable degree >= 2 | `passed` (deg_min>=2, column degrees) | gated |
| full row rank (rank==k) | `passed` (rank==k; catches T2) | gated |
| connected Tanner graph | `passed` (comp==1, largest_frac==1; catches B0/B1 f1.0) | gated |
| no duplicate/proportional columns | `passed` (dup==0) | gated |
| no base-pair / triple duplicates | `passed` (base_dup==0, triple_dup==0) + runner AND | gated |
| GF(32) coefficient validity | `passed` (vals_ok) | gated |
| M forest acyclicity | runner `m_cycle_rank==0` | gated |
| coefficient-stream determinism | double-build replay recorded per record | checked |

The class is closed: I1 was the single structural precondition the frozen
gate set never constrained (A3 forensics: 64 attempted degree crashes).

## A5-10 structure-cost projection (fresh-root measured + calibrated model)

Measured single support+mother build walls (matrix, both layers <= shown):

| set | n64 | n128 | n256 |
|---|---|---|---|
| eligible-only {B0,B1,T1} | <=0.02 s | <=0.08 s | <=0.34 s |
| T2 per-layer (support-only / task-equiv) | 9.1 s / ~41 s | proj ~150 s / 650 s (A4) | proj ~0.67 h / 2.85 h (A4) |

Cost model: wall ~= total_candidates x 1.95 us (calibrated T2 n64 L1:
4.67M candidates -> 9.1 s); predicts n128/n256 within ~15% of the A4
measured task times (candidate ratios 16.4x/16.2x vs wall ratios
15.9x/15.8x). Replay (x2) and audits add only seconds for non-T2 arms.

Breach decision (A5-A18): the eligible-only set builds in seconds at every
width — no chunk/12h breach. T2 at n256 (~2.85 h/layer) exceeds the
`>=5400 s` chunk dispatch block on a single layer — breach routed to the
Track B acceleration numbers (target <=600 s/layer); if Track B misses,
T2 is width-inadmissible at n256. T2 at n128 (~650 s/layer) fits the chunk
but dominates the 12 h wall if redispatched — same routing.

## Evidence and acceptance

- `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv` (this dir) + validation JSONs
  (`workspace/d6_r1c_a5a6_validcheck_6bac31b6d872/part{1,2,3}_*.json`).
- Historical root `--verify` after the gate: exit 0, 15/15 PASS, VERIFY PASS,
  stored `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` vs recomputed
  `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (agreement False, recomputed
  governs), INFO I1-historical checked=132 violations=36 (T3/T4/M1
  frozen-eligible cells) skippedNOT_RECOMPUTED=T2-scaling x4; six files
  lengths/mtimes byte-identical before/after, worktree path git-clean;
  header has no `row_degree_min` column (diagnostic not persisted: schema
  stable, A5-A05/A5-A12).
- A5-A01 matrix complete/reproducible (132/132 + 51/51, replay all True).
  A5-A02 eligible + selection exact (triple-confirmed vs committed JSON).
