# Design — D15 Paired Finite-Length Margin Curve (readiness, D1501/D1502)

Authority: `.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md`
§1–§3/§5. Track: `EXPLORE` readiness planning (docs only; no code, no execution,
decoder calls 0, no commit/push). Predecessor
`D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED` verified PRESENT
(decision-log:4257, memory:3907, D14 log:292).

## 1. Scientific question and scope

At n=128, when L1 and L2 are compared at approximately the same effective
disclosure factors, does failure remain L1-specific, move to L2, or chiefly
follow finite-length margin? This change estimates a small three-point margin
curve before any new degree search. n=128 only. No APP arm: cross-layer
transfer would reintroduce the L1 success confound. L2 arm is the accepted
true-conditioned single-layer oracle diagnostic (`oracle_l2_prior`), ungraded
except through the preregistered route vocabulary (§5).

## 2. Rate equations and effective factors (D1502a–b, exact-rational recompute)

Frozen inputs (trusted, stated): `H_L1 = 4.286720430201375`,
`H_L2 = 3.222719884634378`; `n = 128`; bits per disclosed row = 5.

Loads:

- `Load_L1 = 128 × 4.286720430201375 = 548.700215065776` bits.
  Check: 4.286720430201375×100=428.6720430201375; ×20=85.7344086040275;
  ×8=34.293763441611; sum=548.700215065776. CONFIRMED exact.
- `Load_L2 = 128 × 3.222719884634378 = 412.508145233200` bits (to 12dp;
  full product 412.50814523320038). CONFIRMED.
- Base rows are entropy-derived ceils: `ceil(548.700215065776/5)=ceil(109.74004…)=110`;
  `ceil(412.508145233200/5)=ceil(82.50163…)=83`. Upper points step +4 rows (L1)
  / +3 rows (L2) by frozen integer choice, NOT by copying rounded factors.

Effective factor definition: `f_eff = disclosed / load`, `disclosed = 5m`.

| layer | m | disclosed | f_eff recomputed | packet approx | verdict |
|---|---|---|---|---|---|
| L1 | 110 | 550 | 550/548.700215065776 = 1+1.299784934224/548.700215065776 ≈ **1.00237** | 1.002 | MATCH |
| L1 | 114 | 570 | 570/548.700215065776 = 1+21.299784934224/548.700215065776 ≈ **1.03882** | 1.039 | MATCH (3dp rounding) |
| L1 | 118 | 590 | 590/548.700215065776 = 1+41.299784934224/548.700215065776 ≈ **1.07527** | 1.075 | MATCH |
| L2 | 83 | 415 | 415/412.508145233200 = 1+2.4918547668/412.508145233200 ≈ **1.00604** | 1.006 | MATCH |
| L2 | 86 | 430 | 430/412.508145233200 = 1+17.4918547668/412.508145233200 ≈ **1.04240** | 1.042 | MATCH |
| L2 | 89 | 445 | 445/412.508145233200 = 1+32.4918547668/412.508145233200 ≈ **1.07877** | 1.079 | MATCH (3dp rounding) |

Derivation notes (hand): L1 0.0388×load=21.28956834455211, remainder
0.01021658967189 → +0.00001862 → 1.03881862. L1 0.075×load=41.1525161299332,
remainder 0.1472688042908 → +0.0002684 → 1.0752684. L2 0.006×load=
2.4750488713992, remainder 0.0168058954008 → +0.00004074 → 1.00604074.
Pairing gaps (L2−L1): +0.00367 / +0.00358 / +0.00350 — matched-margin within
~0.004 at every row point by integer-row construction. No contradiction; no amend.

## 3. Degree cells, sockets, allocations (D1502c, every histogram sums to n/m/E)

Variable side is m-independent (D9 largest-remainder rule, retained):

- L045: n2=71, n3=57 → n=128; E=71·2+57·3=142+171=**313**.
- L055: n2=83, n3=45 → n=128; E=83·2+45·3=166+135=**301**.
- L2 DV3: 128 degree-3 → n=128; E=128·3=**384** (n2=0).

Check side is concentrated floor/ceil: `floor=E/m` flo, `b=E−flo·m` ceils,
`a=m−b` floors, `a+b=m`, `a·flo+b·(flo+1)=E`.

| cell | allocation | count sum | socket sum | verdict |
|---|---|---|---|---|
| L045 m110 (retained D14N) | `2^17+3^93` | 17+93=110 | 34+279=313=E | PASS (b=313−220=93, a=17) |
| L045 m114 (new) | `2^29+3^85` | 29+85=114 | 58+255=313=E | PASS (b=313−228=85, a=29) |
| L045 m118 (retained D12) | `2^41+3^77` | 41+77=118 | 82+231=313=E | PASS (b=313−236=77, a=41) |
| L055 m110 (retained D14N) | `2^29+3^81` | 29+81=110 | 58+243=301=E | PASS (b=301−220=81, a=29) |
| L055 m114 (new) | `2^41+3^73` | 41+73=114 | 82+219=301=E | PASS (b=301−228=73, a=41) |
| L055 m118 (retained D12) | `2^53+3^65` | 53+65=118 | 106+195=301=E | PASS (b=301−236=65, a=53) |
| L2 m83 (new) | `4^31+5^52` | 31+52=83 | 124+260=384=E | PASS (b=384−332=52, a=31) |
| L2 m86 (new) | `4^46+5^40` | 46+40=86 | 184+200=384=E | PASS (b=384−344=40, a=46) |
| L2 m89 (new) | `4^61+5^28` | 61+28=89 | 244+140=384=E | PASS (b=384−356=28, a=61) |

Reference (not in the nine, retained context): D11 L2 DV3 m104 `3^32+4^72`:
32+72=104; 96+288=384=E. PASS.
Every histogram sums to its (n, m, E). No contradiction; no amend.

## 4. Constructor-feasibility screen (D1502d — PASS, no STOP)

R2 admission gates (frozen, `v72p2d10-mixed-degree-l1` spec): A1 exact
variable/check histograms + socket balance `sum_v=sum_c=E`; A2 simple graph (no
duplicate edge, no empty check, min check degree == design §3 min); A3 exactly
ONE connected component over all n+m Tanner nodes; A4 deterministic structural
rank == m; A5 exact GF32 (poly 37) row rank == m; A6 deterministic replay
equality. Four-cycles/girth/ACE are diagnostics only, never gating.

- Min check degree 4–5 on L2 cells: NO gate forbids dc 4/5. A2 compares min
  against the design-declared min (§3: L2 min 4), not a hardcoded 2; no gate
  requires degree-2 checks. Precedent: D11 L2 DV3 m104 (`3^32+4^72`, min 3, zero
  degree-2 checks) was constructed and admitted under the same gates. Max dc 5
  is within the D9 normative max-check-degree ≤8 ceiling (frozen matrix ≤4
  previously; 5 is one above but far below 8). PASS.
- Variable side L2 all-degree-3 (n2=0): NO gate requires n2>0. A1 checks exact
  match to the declared `(0,128,384)` profile; the frozen D10 DV3 control is
  exactly `(n2,n3,E)=(0,n,3n)` and passed admission mechanics. PASS.
- Shared connectivity-first constructor (`build_degree_sequence_peg`: spanning
  backbone + PEG/ACE fill, one deterministic attempt, fail-closed
  `construction_failed`) takes only the forced degree-sequence input per arm
  family; the nine sequences above are all valid inputs. L2 density E/m =
  4.63/4.47/4.31 vs D11 3.69 — denser but still sparse; no gate penalizes it. PASS.
- ANY contradiction would have forced STOP before code with the exact
  calculation. NONE FOUND → proceed to D1501 freeze.

## 5. Reuse map (import unchanged, duplication rejected)

Base: `comparison_bench/src/comparison_bench/formal_ir/`.
D1503 SHALL import (later call; frozen here): D14N/D12 graph construction
(`build_degree_sequence_peg`), A1–A6 admission (`structural_record`,
`build_graph` + A6 replay, `structural_rank`, `gf32_row_rank`), coefficient rule
(`coefficient_seed`/`coefficients_for_edges`, `v10_seed(f"d10:coeff:128:{graph_seed}")`),
block sampling (`sample_matched_block`), Model-F CAL-only L1 prior chain
(`prepare_model_f_prior_candidate` → `marginalize_f_to_p1` →
`_floor_renorm(DECODER_FLOOR=1e-15)`), L1 dispatch pattern, and the D11
true-conditioned L2 oracle path (`oracle_l2_prior` → `get_conditional_posterior_l2`,
diagnostic-only, shared per graph/block, EXCLUDED from grading except via §7).
NO APP transfer (no `transfer_prior_l1_to_l2`/`canonical_transfer_l2_prior`/
`app_fed_l2_prior` consumption in this change). No copied decoder
(`decode_row_layered_fftqspa` bound only) or GF32 kernels. One construction path
per frozen arm family. Frozen decoder contract (for D1505+): max_iter=90,
damping 1.0, cold start, q=32/poly37; exact/syndrome/undetected/iterations
isolated, `undetected` never merged into success/FER; non-oracle provenance
must be `CHECK_UPDATED` (L2 oracle cells carry `ORACLE`).

## 6. Seeds, root, command freeze + absence proof

- Graph seeds (36, fresh, disjoint per cell, 4 per cell):
  L045-m110 `2026093801..3804`; L045-m114 `2026093805..3808`;
  L045-m118 `2026093809..3812`; L055-m110 `2026093813..3816`;
  L055-m114 `2026093817..3820`; L055-m118 `2026093821..3824`;
  L2-m83 `2026093825..3828`; L2-m86 `2026093829..3832`; L2-m89 `2026093833..3836`.
- Block seeds (8, same 8 blocks feed all nine cells): `2026093901..3908`.
- Prior ranges (must not collide): D10 2201–2215; R3/D11-L1 2401–2406/2501–2506,
  blocks 2601–2612/2701–2712; D11-L2 2801–2806/2901–2906; D12 graphs
  3001–3006/3101–3106, blocks 3201–3212/3301–3312; D14N graphs 3401–3406/3501–3506,
  blocks 3601–3612. Selected 3801–3836/3901–3908 sit strictly outside all of them.
- Absence proof (this call, `rg` over repo): `20260938|20260939` → zero content
  hits (only the packet change-name line matches the broader `v72p2d15` pattern);
  exact strings `8c1e4f2a`, `d15_finite_margin_curve`, `2026093801`,
  `2026093901` → zero hits (`No files found`). Direct-read of the future root
  path: not created (no filesystem probe beyond absence-by-search; D1510 SHALL
  re-prove before any execution).
- Frozen future root (absent through readiness, never overwritten):
  `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`
  (six-file D11/D12 convention; exact filenames frozen at D1506).
- Frozen exact future command (unauthorized; NO execution authorized here):
  `.venv/bin/python scripts/v72p2d15_margin_curve_development.py --d15-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`
  (runner belongs to D1505; `--profile-only`/`--verify` and default-false
  `--execution-authorized` refusal-before-root/binding/Model-F-load frozen in spec).
- STOP rule: on any seed/root collision D1501 FAILS and returns BLOCKED; none found.

## 7. Matrix, plan, gates (conservative route vocabulary)

Nine cells (3 points × 3 arms); 4 graphs/cell (36 objects); 8 paired blocks/cell
(8 samples); 288 scientific calls (9×4×8); 46 setup (36+8+2). Deterministic call
order (point ascending, arm L045→L055→L2-ORACLE, graph ascending, block
ascending) frozen in spec. Paired blocks: the same 8 block objects feed all nine
cells; L045/L055 discordances paired per D12; no predecessor pooling.

Route terminals (first-match priority; thresholds preregistered, frozen before
any result, never tuned post-hoc):

1. Engineering/resource violation → `MARGIN_CURVE_ENGINEERING_BLOCKED`.
2. L1-specific: highest matched-margin point shows L1 weak while L2-ORACLE
   adequate with multi-graph support + cross-point monotonic L1 weakness →
   `MARGIN_CURVE_L1_SPECIFIC`.
3. L2-specific: mirror image → `MARGIN_CURVE_L2_SPECIFIC`.
4. Finite-backoff: both layers fall together toward the near-entropy point and
   recover together with margin (monotonic across points, multi-graph) →
   `MARGIN_CURVE_FINITE_BACKOFF`.
5. Both-weak at all points (no margin recovery anywhere) → `MARGIN_CURVE_BOTH_WEAK`.
6. Else → `MARGIN_CURVE_AMBIGUOUS` (no investment claim; escalate to planner).

Conservative rules (normative): the highest matched-margin point
(L1-m118/L2-m89) anchors every layer-specific claim; cross-point monotonic
evidence is REQUIRED (a single point never closes the route); multi-graph
support REQUIRED (≥2 graphs show the pattern; no single pooled count, no single
graph, no rescued block closes the route); Wilson intervals + paired
discordances are descriptive only (§D1507); fit NO asymptotic threshold from
three points.

## 8. Budgets

Scientific calls exactly/at most 288; setup exactly/at most 46; wall ≤1800 s
total; per call ≤120 s (checked between/after calls, never interrupted);
RSS strictly <2147483648 B; one CPU process; CPU-only; no
retry/resume/repair/seed search/tuning/adaptive stop. Ceiling breach → STOP as
out-of-scope, re-scope, never tune.

## 9. Rejected alternatives (recorded, not implemented)

- Entropy-rounded factor copying (rejected: rows chosen by exact integer m, factors
  computed from the load; rounded factors never copied).
- APP/forward-transfer arm (rejected: reintroduces the L1 success confound; D11
  already covers forward transfer).
- New L2 degree family (rejected: L2 stays frozen DV3; degree search belongs after
  the curve, not before).
- m118-to-fit-old-strings or m104-L2 retention (rejected: destroys the
  matched-margin design; D14N 1.002-vs-1.261 confound is the reason for D15).
- Single-graph / single-point / pooled-count route closure (rejected: §7
  conservative rules).
- Threshold fitting from three points, investment selection, D7-H revival
  (rejected: claim ceiling §10).

## 10. Claim ceiling

Synthetic single-layer diagnostic only. No threshold fit, no L1/L2 investment
selection, no D7-H/FER/leakage/SKR/real-data/qualification/optimality/
publication claims. Terminal is `READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants
no execution. Invalid inferences from packet §2 restated verbatim in proposal
and SHALL be rejected by the future audit.
