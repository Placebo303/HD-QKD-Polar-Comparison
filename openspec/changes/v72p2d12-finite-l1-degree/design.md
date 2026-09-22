# Design — D12 finite L1 degree refinement (readiness, D1201–D1202)

Change: `v72p2d12-finite-l1-degree`
Cycle: `V72P2D12-FINITE-L1-DEGREE`
Track: implementation/readiness (no EXPLORE/DECIDE execution; zero scientific
decoder calls; no D12 batch, no L2, no D7-H, no real data, no commit/push).
Future batch (if ever authorized separately) is `EXPLORE_HEAVY`.
Authority: `.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md`
§1–§4 (frozen). Branch `formal-ir-v72p1-addendum-clean` (do not switch).
Predecessor (immutable, read-only context, never pooled):
`D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`
(root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`,
stored terminal `D11_FORWARD_APP_WIDE_RECOVERY`, VERIFIED PASS_WITH_FINDINGS).
A1/R3/D11 evidence SHALL never enter D12 gate arithmetic.

## Goal

Freeze the smallest finite L1 comparison of the three D9-justified degree mixes
(λ2 = 0.45 frozen reference, 0.50 and 0.55 challengers) at f1.2, n128+n256,
before any behavior edit.

## Non-Goals

No D12 execution; no broad grid; no decoder-schedule change; no L2/APP work;
no D7-H; no FER/leakage/SKR/qualification/promotion/publication/real-data
claim; no predecessor modification, rerun, re-thresholding, or pooling; no
seed search/replacement/repair/resume/retry/adaptation/tuning; no commit/push;
no future-root creation in readiness.

## 1. Three-arm scientific isolation contract (frozen)

Exactly three arms, all L1-only, f1.2, widths n128 and n256, both always
measured:

| arm id | edge λ2 | role |
|---|---|---|
| `L045` | 0.45 | frozen reference (D9-selected) |
| `L050` | 0.50 | challenger |
| `L055` | 0.55 | challenger |

All three arms SHALL share: the accepted connectivity-first shared constructor
`build_degree_sequence_peg`, the v10 tie-breaking policy (BFS-depth → ACE →
seeded pick), the graph-seed rule, the coefficient-distribution/stream rule,
the Model-F CAL-only L1 prior chain, the row count `m` per width, the block
seed set and paired block objects, the decoder
(`v35.decode_row_layered_fftqspa`), schedule (cold row-layered), iteration cap
(`max_iter=90`), damping (`damping_alpha=1.0`), field (`q=32, poly=37`),
syndrome/exact/stop semantics and record schema. A challenger differs only
where mathematically forced by its D9 degree/socket profile: variable degree
histogram, total sockets `E`, and the floor/ceil check-degree allocation. No
other difference is permitted. No replacement/search/adaptation.

Primary scope only: L1 marginal decoding; f1.2 rows `(n,m) = (128,118),
(256,236)`; q=32 polynomial 37; cold row-layered v35 decoder `max_iter=90`,
`damping_alpha=1.0`; exact primary with syndrome-valid and undetected reported
separately (never merged, never counted as success).

## 2. Frozen degree cells (packet §2 table; D1202-verified EXACT)

| width | arm | n2 | n3 | E | checks |
|---|---|---:|---:|---:|---|
| 128 | L045 | 71 | 57 | 313 | `2^41+3^77` |
| 128 | L050 | 77 | 51 | 307 | `2^47+3^71` |
| 128 | L055 | 83 | 45 | 301 | `2^53+3^65` |
| 256 | L045 | 141 | 115 | 627 | `2^81+3^155` |
| 256 | L050 | 154 | 102 | 614 | `2^94+3^142` |
| 256 | L055 | 166 | 90 | 602 | `2^106+3^130` |

D12 SHALL NOT re-derive, re-round, re-select, or repair these integers. STOP on
any table drift (packet STOP: D9 table mismatch).

### D1202(a) recomputation — raw evidence (rule + arithmetic per cell)

Accepted rule source: D9 `design.md` §5
(`openspec/changes/v72p2d9-gf32-de-decoder-calibration/design.md:220-284`):
`edge_to_node_distribution` (`v37_degree_feasibility.py:118-139`,
`L_i = (λ_i/i) / Σ_j(λ_j/j)`) → `largest_remainder_counts`
(`:142-165`, descending fractional part, tie by ascending degree) →
`calculate_node_degree_counts` (`:168-187`, integer `n2+n3 = n`) → sockets
`E = 2n2+3n3 = 3n-n2` (`:190-192`) → check allocation
`calculate_check_degree_allocation` (`:205-261`: `dc_floor = floor(E/m)`,
`c_ceil = E mod m`, `c_floor = m-c_ceil`) → degree-2 context
`analyze_degree2_subgraph` (`:264-297`). Nominal-socket non-integrality flagged
at D9 `:238-242` (0.45 → `E = 15360/49, 30720/49`; 0.50 → `1536/5, 3072/5`;
0.55 → `5120/17, 10240/17`); apportioned `λ̂2 = 2n2/E` is the realization of
record. f1.2 reference table at D9 `:244-259`; D9 root
`workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/summary.json`
`graph.cells` carries matching `n2/n3/E` for every f1.2 cell; D10 R1
transcription at `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/READINESS_R1.md:87-104`
(table `:92-99`, read-only cross-check `:101-104`).

Recomputation (m: f1.2 `m/n = 59/64`, so m=118 at n128, m=236 at n256):

- λ2=0.45: harmonic `0.45/2+0.55/3 = 49/120`; `L2 = 27/49`, `L3 = 22/49`.
  n128: `n2* = 128·27/49 = 3456/49 ≈ 70.53` → floors 70+57=127, rem 1,
  fractions 26/49 vs 23/49 → extra to deg-2 → **71/57**; `E = 142+171 = 313`;
  `λ̂2 = 142/313`; `floor(313/118) = 2`, `313−236 = 77` → **2^41+3^77** ✓.
  n256: `n2* = 6912/49 ≈ 141.06`, `n3* = 5632/49 ≈ 114.94` → floors 141+114,
  rem 1, largest fraction n3 (46/49) → **141/115**; `E = 282+345 = 627`;
  `λ̂2 = 282/627 = 94/209`; `627−472 = 155` → **2^81+3^155** ✓.
  Matches D9 root cells (`E/n2/n3` = 313/71/57, 627/141/115), D9 table
  (`:252-253`), D10 R1 (`:98-99`), packet L045 rows.
- λ2=0.50: harmonic `0.5/2+0.5/3 = 5/12`; `L2 = 3/5`, `L3 = 2/5`.
  n128: `n2* = 76.8`, `n3* = 51.2` → floors 76+51=127, rem 1, 0.8 vs 0.2 →
  **77/51**; `E = 154+153 = 307`; `λ̂2 = 154/307`; `307−236 = 71` →
  **2^47+3^71** ✓.
  n256: `n2* = 153.6`, `n3* = 102.4` → floors 153+102=255, rem 1, 0.6 vs 0.4 →
  **154/102**; `E = 308+306 = 614`; `λ̂2 = 154/307`; `614−472 = 142` →
  **2^94+3^142** ✓.
  Matches D9 root cells (307/77/51, 614/154/102), D9 table (`:254-256`),
  packet L050 rows.
- λ2=0.55: harmonic `0.55/2+0.45/3 = 17/40`; `L2 = 11/17`, `L3 = 6/17`.
  n128: `n2* = 1408/17 ≈ 82.82`, `n3* = 768/17 ≈ 45.18` → floors 82+45=127,
  rem 1, 14/17 vs 3/17 → **83/45**; `E = 166+135 = 301`; `λ̂2 = 166/301`;
  `301−236 = 65` → **2^53+3^65** ✓.
  n256: `n2* = 2816/17 ≈ 165.65`, `n3* = 1536/17 ≈ 90.35` → floors 165+90=255,
  rem 1, 11/17 vs 6/17 → **166/90**; `E = 332+270 = 602`; `λ̂2 = 166/301`;
  `602−472 = 130` → **2^106+3^130** ✓.
  Matches D9 root cells (301/83/45, 602/166/90), D9 table (`:257-259`),
  packet L055 rows.

Socket balance `E = 2n2+3n3 = Σ d·count` holds in all six cells; realized rate
exactly `1−m/n`; min check degree 2, max 3 (≤8 bound satisfied). All six cells
verified EXACT against packet §2, D9 design §5, D9 root `graph.cells`, and
(D10 R1-transcribed) L045 cells. No mismatch → D9-table STOP not triggered.

## 3. Seeds, coefficients, blocks, prior, call order (frozen)

- Graph seeds (fresh, never searched or replaced): n128
  `2026093001..2026093006`; n256 `2026093101..2026093106`. Verified absent
  (scan in §7; STOP with BLOCKED + raw evidence on collision).
- Block seeds (fresh, separate from graph seeds, never searched or replaced):
  n128 `2026093201..2026093212` (12); n256 `2026093301..2026093312` (12).
  Verified absent (same scan).
- Coefficient rule (frozen): `COEFF_SEED =
  v10_seed(f"d10:coeff:{width}:{graph_seed}")`, one `integers(1,32)` per edge
  in sorted `(variable,check)` order; same rule all arms (R2
  `v72p2d10_mixed_degree_l1.py:584-599`).
- Blocks: one matched block sampled once per `(width, block_seed)` from the
  accepted CAL-only Model-F artifact
  (`v72p2d5_gf32_rate_mother.sample_matched_block`, `:873-911`); the same block
  object is used by all arms and all six graphs at that width (paired decoding
  on identical L1 blocks).
- Prior chain (frozen; same all arms): load `counts_ab`, `p_b` from
  `workspace/v72p2d5_model_f_input/20260907_r1` (CAL-only) →
  `prepare_model_f_prior_candidate` (`:2480-2507`, frozen `LAMBDA_STAR`, no new
  search, no VAL) → `marginalize_f_to_p1` (`:309-321`) →
  `_floor_renorm(DECODER_FLOOR=1e-15)` (`:346-351`, `DECODER_FLOOR` at `:48`);
  no VAL/real-data contact.
- Call order (deterministic): widths n128 + n256 both always measured (no
  conditional progression in D12); within a width arm order L045, L050, L055;
  graph seeds ascending; block seeds ascending. Per call: select admitted graph
  → `syndrome_of_gf32(H, u1)` (`v35_algorithm_development.py:139-157`) →
  `decode_row_layered_fftqspa(H, priors, syn, max_iter=90, damping_alpha=1.0,
  warm_beliefs=None, field=GF32/poly37)` (`:781-789`; module
  `DEFAULT_MAX_ITER=30` at `:60` is NOT used — the frozen 90 is passed
  explicitly, cf. R2 `dispatch_l1` binding at
  `v72p2d10_mixed_degree_l1.py:882-884`) → record `exact` (`syndrome_ok and
  x_hat == u1`), `syndrome_ok`, residual syndrome weight, iterations, status,
  provenance. `exact`, `syndrome_ok`, and `undetected` remain separate fields
  and are never merged.
- Each width: 3 arms × 6 graphs × 12 paired blocks = 216 calls; total plan
  3×6×12×2 = **432** L1 call identities.

## 4. Gates, selection, terminals (packet §2 verbatim logic)

Per width `w`, per graph exact counts from the same 12 blocks; pools are 72
each. Exact is primary; syndrome-valid and undetected remain separate. Report
per-graph, per-width and pooled paired discordances.

An arm is `STABLE(w)` when exact ≥18/72, at least 5/6 graphs have ≥2 exact,
and no engineering/resource violation. L045 is the frozen reference.

A challenger is `MATERIAL_BETTER` only if, at both widths: it is STABLE; exact
is at least L045+6; pooled challenger-only discordance exceeds L045-only; and
it has higher per-graph exact on at least 4/6 graph pairs.

Selection:

- if exactly one challenger is MATERIAL_BETTER, select it;
- if both are, rank by total exact, then worst-width exact, then smaller λ2;
- if neither is and there is no split-width conflict, retain L045;
- `SPLIT_WIDTH_CONFLICT` when a challenger beats L045 by ≥6 at one width but
  trails by >2 at the other, or widths favor opposing challengers.

Terminals: `D12_SELECT_L050`, `D12_SELECT_L055`,
`D12_RETAIN_L045_NO_MATERIAL_GAIN`, `D12_FINITE_DEGREE_SPLIT_AMBIGUOUS`, or
an explicit engineering/resource blocked terminal. Descriptive p-values do not
override the frozen selection.

## 5. Future root, budgets, claim ceiling (frozen)

Future root (absent, unauthorized; verified absent — STOP if present):
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Budgets: ≤432 scientific calls; ≤62 setup (=36 graph builds + 24 block samples
+ Model-F load + plan build); wall ≤1800 s; ≤120 s/call; RSS <2147483648 B;
one process; no retry/resume/repair/seed search/tuning. No-overwrite; A1/R3/D11
contextual-only non-pooling rule (D12 gate arithmetic SHALL make predecessor
pooling structurally impossible). Claim ceiling: synthetic finite L1 degree
comparison only; no forward/L2, FER/leakage/SKR, real-data, qualification,
optimality or D7-H claim.

## 6. D1202(b) import map (exact path:line) + duplication rejection

- D9 realization rule: `openspec/changes/v72p2d9-gf32-de-decoder-calibration/design.md:220-284`
  (rules `:222-236`, nominal non-integrality `:238-242`, f1.2 table `:244-259`);
  `comparison_bench/src/comparison_bench/formal_ir/v37_degree_feasibility.py:118-139,142-165,168-187,190-192,205-261,264-297`;
  D9 root `workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/summary.json`
  `graph.cells` (f1.2 `n2/n3/E` per candidate/width).
- D10 R1 L045 transcription: `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/READINESS_R1.md:87-114`
  (table `:92-99`, cross-check `:101-104`, seeds/coeff `:106-114`);
  `openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/design.md:168-193`
  (§3 table), `:196-285` (§4 seeds/coeff/blocks/prior/call order), `:286-319` (§5 A1–A6).
- D10 R2 shared constructor/admission/coeff/decoder path:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`
  `:109-125` (arms/widths/graph+block seeds), `:132-151` (DEGREE_TABLE),
  `:153-155` (`DECODER_MAX_ITER=90`, `DAMPING_ALPHA=1.0`), `:241`
  (`build_degree_sequence_peg`, one connectivity-first constructor),
  `:457` (`structural_rank`), `:545` (`gf32_row_rank`), `:584`
  (`coefficient_seed`), `:589` (`coefficients_for_edges`), `:602`
  (`dense_from_edges`), `:628` (`structural_record`), `:726` (`build_graph`,
  A1–A6 admission + A6 replay `:755-764`), `:779` (`build_call_plan`),
  `:855` (`dispatch_l1`: admission gate before binding `:867-871`, injected
  decoder/syndrome only `:872-875`, frozen call `:882-884`), `:933`
  (`execute_plan`), `:1059` (`profile_graphs`), `:1100` (`refuse_out_root`).
- R3 plan/seed/block pattern:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_r3_fresh_scaling.py`
  `:39` (R2 reuse import), `:74-87` (`ARMS` reuse, `GRAPH_SEEDS`/`BLOCK_SEEDS`
  fresh-pattern precedent), `:90-103` (`DEGREE_TABLE`), `:106-113` (drift
  guard), `:115-118` (decoder constants reuse), `:185` (`degree_cell`),
  `:201` (`build_graph` delegates to R2), `:219` (`build_call_plan`
  144/width), `:239` (`build_full_plan`), `:291/:339/:369/:396/:439/:516`
  (tallies/classify/route/describe/execute/profile), `:178-179` (refuse reuse).
- Model-F L1 prior chain:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py:48,309-321,346-351,873-911,2480-2507`
  (floor constant, marginalize, floor/renorm, matched-block sampler, candidate
  prior preparation); artifact root
  `workspace/v72p2d5_model_f_input/20260907_r1` (CAL-only).
- v35 row-layered decoder contract:
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:139-157,781-789`
  (syndrome + row-layered FFT-QSPA signature; frozen `max_iter=90`,
  `damping_alpha=1.0`, cold `warm_beliefs=None`, GF32/poly37 passed at call).

Duplication rejection: D12 SHALL reuse the R2 construction/admission/decoder
path (`build_graph`, `dispatch_l1`, `coefficient_seed`, `refuse_out_root`) and
the R3 plan/seed/block structural pattern rather than copying them. No new
PEG/rank/coefficient/prior/decoder/message/provenance framework and no
duplicate message semantics SHALL be introduced; any D1203+ implementation
that re-implements (rather than imports) the shared constructor, A1–A6, coeff
rule, prior chain, or decoder binding is a scope violation → STOP.

## 7. Seed/root absence scan (raw output, no collision)

- Exact-boundary scan, pattern
  `2026093001|2026093006|2026093101|2026093106|2026093201|2026093212|2026093301|2026093312`
  over the repo: matches ONLY in the authority packet
  (`.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md:22-23`).
  Zero matches in code/scripts/tests/docs/openspec/analysis/results/workspace.
- Future-root UUID scan, pattern `94fb9d22-cadc-47f4-a96e-b2170bdba450`: matches
  ONLY in the authority packet (`:65`). The directory
  `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450` is
  absent (no such entry under `workspace/`); the OpenSpec target directory did
  not exist before this change.
- Prefix-scan note: a broad `20260930|20260931|20260932|20260933` scan returned
  one additional non-packet hit
  (`comparison_bench/outputs_comparison/formal_ir_methods/20260731_v5d_nbldpc_post_synthetic/pre_run_plan.json:2248`);
  the reported line was inspected read-only and contains no D12 seed literal,
  and exact-range scans (`202609300[1-6]`, `202609310[1-6]`, `20260932[0-9]+`,
  `20260933[0-9]+`) over that file return zero → tool-artifact false positive,
  NOT a seed collision. STOP condition (collision) not triggered.

## 8. Preserved-items checklist

- [x] D11 wide-forward result accepted as immutable predecessor (terminal +
  VERIFIED PASS_WITH_FINDINGS + accepted route); root read-only, never pooled.
- [x] A1/R3/D11 evidence contextual-only; D12 gates structurally unpoolable.
- [x] D9 table reproduced EXACTLY (§2 above); no re-derivation in D12.
- [x] Only `openspec/changes/v72p2d12-finite-l1-degree/**` written in D1201–D1202.
- [x] L2/D7-H untouched; no real data; no FER/leakage/SKR/optimality claim.
- [x] Execution false; decoder calls 0; no root created; no commit/push.

## Impact Scope

ADDED: this change only. READ-ONLY: §6 map. FORBIDDEN: code/scripts/tests/
roots/results/predecessor artifacts/`AGENTS.md`/decision-log.

## Acceptance Criteria

D1201+D1202 DONE when: the four files exist with packet §2 verbatim; §2
recomputation above matches EXACTLY; §6 import map + duplication rejection
recorded; §7 absence scan shows no collision; §8 checklist all checked; zero
decoder calls; no commit/push. Otherwise STOP with BLOCKED + raw evidence.
