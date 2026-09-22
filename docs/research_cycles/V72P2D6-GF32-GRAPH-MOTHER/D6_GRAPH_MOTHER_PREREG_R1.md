# D6 graph/mother — preregistration R1 (freezes packet §§4–9)

Status: `FROZEN_PREREG_R1`. No production implementation or decoder call may
use anything outside this freeze. Allowed before the prereg commit: source
reading, tiny hand calculations, fixture prototyping that does not invoke the
decoder. No candidate score table was generated before this commit.

## §4 Frozen scientific controls

- Decomposition `A = 32*U1 + U2` (D5 `symbols_to_layers` / `layers_to_symbols`).
- Prior: accepted E2 total-concentration/backoff candidate —
  `d5.prepare_model_f_prior_candidate(counts_ab, p_b)` with frozen
  `LAMBDA_STAR = 137.3823795883264`, CAL-only Model-F artifact
  (`counts_ab` (1024,1024), `p_b` (1024,)), audit floor `1e-300`, decoder
  floor `1e-15`, probability-domain transfer.
- GF32 poly 37; historical row-layered FFT-QSPA via `d5.bind_historical_decoder`
  (cold start, `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None`).
- Schedule L1 then APP-propagated L2 (`d5._run_layered_block`); oracle-L2 is
  diagnostic only and never feeds production decoding.
- Exact = full reconstructed Alice equality (`u1` and `u2` both exact).
  Syndrome is recorded separately and never upgrades exact. Any APP
  `syndrome_ok != exact` is an exact/syndrome disagreement (undetected errors
  isolated, never merged into exact).
- One sample per `(n, block_seed)` (`d5.sample_matched_block`), reused
  byte-identically across arms.
- Row budgets (= disclosure prefixes, construction order = disclosure order):

| n   | layer | k_min | m_max | f1.0 | f1.2 | square |
|-----|-------|-------|-------|------|------|--------|
| 64  | L1    | 49    | 64    | 49   | 59   | 64     |
| 64  | L2    | 43    | 64    | 43   | 52   | 64     |
| 128 | L1    | 98    | 128   | 98   | 118  | 128    |
| 128 | L2    | 86    | 128   | 86   | 104  | 128    |
| 256 | L1    | 196   | 256   | 196  | 236  | 256    |
| 256 | L2    | 172   | 256   | 172  | 208  | 256    |

- Graph/mother is the only scientific axis. Degree-3 coefficient triples are
  identical by `(n, layer, column)` across B1/T1–T4/M-degree-3. Labels are not
  optimized.

## §5 Frozen architecture family

Support storage is canonical: per-column row lists ascending. Matrix
`H[r,v] = coeff (1..31)` on support, else 0, shape `(m_max, n)`.
`B = [0, k_min)` base zone, `C = [0, m_max)` full zone, `deg[]` live
check-degrees, `used_pairs` unordered base pairs, `used_triples` sorted
triples. All loops run variables `v = 0..n-1` in order. No RNG in support
construction; every tie-break is lexicographic.

### B0_D5_DV3_NATIVE

`support = d5.build_dv3_nested_support(n, n, k_min, seed)`,
`H = d5.assign_gf32_coefficients(support, seed, None, n)` with D5 seeds L1
`2026090501` / L2 `2026090502`. Historical control; never a new winner.

### B1_D5_DV3_COMMON_LABELS

B0 support rebuilt with the §5.4 common stream attached in ascending-row
order. Label-stream control; not a new recovery claim.

### T1_PEG_DV3

Per variable: place 2 base edges then 1 expansion edge. For each edge, BFS the
current Tanner graph from variable node `v`; candidate checks are
`B − chosen` (base) or `C − chosen` (expansion). Preference key:
`(distance desc with unreachable = +inf, deg asc, index asc)`. Walk candidates
in preference order; skip any creating a duplicate base pair (2nd base edge)
or duplicate sorted triple (expansion); place the first legal candidate. If a
zone is exhausted, raise `D6_STRUCTURE_BLOCKED` (arm ineligible, recorded, no
substitute).

### T2_CYCLE_GREEDY_DV3

Per variable: enumerate all triples `{b1 < b2} ⊂ B`, `e ∈ C − {b1, b2}` with
`(b1, b2) ∉ used_pairs` and `sorted triple ∉ used_triples`. Maintain
check-pair occupancy counts (indexed 2-D array) and pair→columns map.
Incremental metrics per candidate: `four = total + occ(ab) + occ(bc) +
occ(ac)`; `mpair = max(old max, occ + 1 over the 3 pairs)`; `ninc = occ(ab) +
occ(bc) + occ(ac)` for the new column and affected-column scan for the global
incidence max; `rmax/rsumsq` by O(1) degree update; `stup = sorted triple`.
Pick the lexicographic minimum
`(four, mpair, incidence_max, rmax, rsumsq, stup)`. Exhaustion →
`D6_STRUCTURE_BLOCKED`.

### T3_SC_DV3_W4 / T4_SC_DV3_W8 (frozen widths 4 / 8, never tuned)

Base anchor `a_v = (v*k_min)//n`, base window
`Wb(v) = [a_v, a_v+w) ∩ B`. Expansion anchor `b_v = (v*m_max)//n`, window
`We(v) = [b_v, b_v+w) ∩ C` (clipped termination, no wrap). Base pair: order
`Wb(v)` by `(deg, index)`; try pairs in lexicographic order of that ranking;
first with `(b1,b2) ∉ used_pairs` wins. Expansion: order `We(v) − {b1,b2}` by
`(deg, index)`; first with sorted triple unused wins. If a window is
exhausted, extend deterministically to the full zone (`B` resp. `C − base`) in
`(deg, index)` order and increment the `window_overflow` diagnostic. Total
exhaustion → `D6_STRUCTURE_BLOCKED`.

### M1_ACCUMULATOR_FOREST_MAX / M2_ACCUMULATOR_FOREST_HALF

`N2 = k_min − 1` (MAX) resp. `floor((k_min − 1)/2)` (HALF); values:
n64 L1 `48/24`, L2 `42/21`; n128 L1 `97/48`, L2 `85/42`; n256 L1 `195/97`,
L2 `171/85`. Variables `0..N2−1` are degree 2 with chain edges
`(i, i+1)` — a path forest over the first `k_min` checks (cycle rank 0 at
every prefix). Variables `N2..n−1` are degree 3: base pair = first unused
pair from `B` ordered by `(deg, index)` lexicographic combination order;
expansion = first row of `C − base` in `(deg, index)` order with sorted triple
unused. Exhaustion → `D6_STRUCTURE_BLOCKED`.

### §5.4 Common coefficients

`rng = np.random.default_rng(202609120100 + n)` (L1),
`np.random.default_rng(202609120200 + n)` (L2);
`vals = rng.integers(1, 32, size=(n, 3))`. Column `v`, stored edge `e` takes
`vals[v, e]`; degree-2 columns use entries 0–1. Applies to B1, T1–T4, and
degree-3 columns of M1/M2. No candidate selection. Projective-duplicate and
degenerate-cycle diagnostics are recorded, never optimized.

## §6 Structural gates and decoder-blind finalist selection

Per `(arm, n, layer, prefix)` record: D5 `audit_prefix` full item set, plus
(a) exact girth by Tanner-graph BFS from every variable node (shortest
returned-to-source cycle; `NOT_COMPUTED` with reason `acyclic` only when no
cycle exists); (b) row-degree max and sumsq; (c) M degree-2 subgraph cycle
rank by DSU (`edges − vertices + components` over touched checks);
(d) determinism replay equality (build twice, exact array equality);
(e) no-parallel-edge check (distinct rows per column);
(f) `window_overflow` (T3/T4) and projective diagnostics.
Hard eligibility (every prefix of both layers): expected shape; all
coefficients in `1..31`; `rank == prefix rows`; zero rows/cols 0; exactly one
component containing all variables; duplicate/projective columns 0;
base-pair and triple duplicates 0; no parallel edge; M cycle rank 0.
Decoder freeze (before any decoder call): B0; B1; best two eligible T by
`(Σfour_cycles, max incidence, −min girth with NOT_COMPUTED = −1,
max row_degree_max, Σrow_degree_sumsq, arm_id)` evaluated at the f1.2 prefixes
of both layers; both eligible M. Fewer eligible arms are recorded, never
substituted. Maximum decoder arms 6.
Preregistered fallbacks (before any n64 decoder call): structurally best
eligible T + structurally best eligible M (absent categories recorded empty).

## §7 Implementation / review gates (frozen paths)

Allowed: `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`,
`comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`,
`scripts/v72p2d6_graph_mother_development.py`, D6 OpenSpec/cycle documents,
one UUID root `workspace/d6_graph_mother_r1_<uuid>/`, final append-only
`docs/decision-log.md` + `AGENT_PROJECT_MEMORY.md`, D5 `cycle_state.yaml`
linkage + `next_gate` only. D5 production modules/tests change only on an
independently demonstrated reuse blocker (otherwise STOP + scope decision).
Tests cover the ten packet items. Code-review PASS, then Pre-EXECUTE PASS
(scope, frozen arms/seeds/rows, output-root absence, protected-root metadata,
tests, forwarded-prompt authorization, watchdog), at most two cycles, then
BLOCKER. No decoder call before Pre-EXECUTE PASS; code freeze once calls start.

## §8 Bounded execution (frozen)

One fresh root; scalar/metadata only (no symbols, priors, beliefs, matrices,
per-iteration messages). Seeds: canary `2026091000..03`, confirmation
`2026091010..25`, scaling `2026091100..03`; nothing else.
Canary: every frozen arm × 4 canary seeds × {f1.2 APP L1 + APP L2 +
oracle-L2 diagnostic, square ditto}. One invocation per cell; 3 decoder
invocations per cell counted in the budget.
Advancement pool = new T/M finalists only (B0 never wins; B1 is a control).
Advance on f1.2 end-to-end APP exact ≥ 1/4, at most two, ordered by
(f1.2 exact desc, f1.2 APP iter-total asc with iter-total = Σ(L1 + APP-L2)
over canary seeds, square exact desc, structural rank, arm_id). Screening
never alters graph/labels/rows/decoder/seeds.
Confirmation per advancing arm: 16 seeds × {f1.0, f1.2, square} full layered
cells. `D6_GRAPH_STRONG_N64_RECOVERY`: f1.2 ≥ 12/16 AND f1.0 ≤ f1.2 ≤ square
AND zero crash/nonfinite AND zero APP exact/syndrome disagreement AND known
RSS < 2 GiB. `D6_GRAPH_PARTIAL_N64_SIGNAL`: f1.2 in 1..11/16 with identical
safety. Else `D6_GRAPH_N64_SIGNAL_INVALID`.
Scaling iff no new arm reaches 1/4 at n=64 f1.2: fallbacks × 4 scaling seeds
× {f1.2, square} at n=128; if silent, repeat n=256; stop at first signaling
width; confirm ≤ 2 arms by the same ordering/rules (16 seeds, f1.0/f1.2/
square), labeled `D6_GRAPH_STRONG_SCALING_RECOVERY` /
`D6_GRAPH_PARTIAL_SCALING_SIGNAL` + width. n=128/n=256 are development widths,
not formal G2.
`D6_GRAPH_SQUARE_ONLY_DIAGNOSTIC`: square APP exact exists but every
non-square point is zero. `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`: all tested
non-square APP exact zero with no stronger label. `D6_GRAPH_IMPLEMENTATION_OR_
RESOURCE_BLOCKED`: invariant/process/wall/RSS/integrity failure.
Limits: 2500 decoder invocations, 12 h wall, 120 s per-invocation watchdog
(dedicated respawnable worker, pids logged), RSS < 2 GiB, no retry, stop
before exceeding call/wall budgets; only task-owned processes terminated.

## §9 Evidence and Pre-RESULT (frozen)

Root files: `manifest.json`, `structure_records.csv`, `selected_arms.json`,
`decoder_records.csv`, `summary.json`, `command_log.txt`, scalar-ID
implementation/review provenance. Independent recomputation of coverage,
counts, separation, extrema, advancement, classification from saved scalars.
Pre-RESULT review is read-only except its own file
`D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1.md`; FAIL blocks solidification.
Post-call fixes limited to evidence/report arithmetic; any code/graph/seed/
row/decoder change needs a new revision with no call reuse.

## Prereg witness

Baseline D6-B01: branch `formal-ir-v72p1-addendum-clean`, HEAD `821388d6`,
appendix commit single-file, D5 `d5_current_path_stopped: true` /
`DECOMPOSITION_NO_N64_RECOVERY` / `next_gate: D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`,
nine execution authorizations false + `scientific_promotion: false`, G2
absent, `git diff --numstat` 0 lines, `--cached` 0 lines (porcelain churn is
EOL-only, informational), untracked + dirty allowlist in
`D6_GRAPH_MOTHER_BASELINE_R1.md`. No candidate score table generated.
