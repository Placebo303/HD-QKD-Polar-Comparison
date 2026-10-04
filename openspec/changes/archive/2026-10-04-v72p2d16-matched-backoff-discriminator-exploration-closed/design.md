# Design — D16 One-Point Matched-Backoff Discriminator (readiness, D1601/D1602)

Authority: `.workbuddy/tasks/D16_MATCHED_BACKOFF_DISCRIMINATOR_READINESS_R1_TASK_PACKET.md`
§1–§6. Track: `EXPLORE` readiness planning (docs only; no code, no execution,
decoder calls 0, no commit/push). Predecessor
`D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR` verified PRESENT
(decision-log:4290, D15 EXPLORATION_LOG:192, packet:10).

## 1. Scientific question and scope

At one matched effective disclosure factor near 1.139, does L055 become
adequate while true-conditioned L2 DV3 remains weak? This single point closes
the gap between the D15 high point (L1 19/22 of 32 at m118; L2 0/32 at m89)
and the D14N over-disclosed L2 result, without a new degree search. n=128 only.
No APP arm: cross-layer transfer would reintroduce the L1 success confound. L2
arm is the accepted true-conditioned single-layer oracle diagnostic
(`oracle_l2_prior`), ungraded except through the preregistered route vocabulary
(§5). L045 is descriptive only (relative L055-vs-L045 evidence, no gate).

## 2. Rate equations and effective factors (D1602a, exact-rational recompute by hand)

Frozen inputs (trusted, stated): `Load_L1 = 548.700215065776` bits,
`Load_L2 = 412.508145233200` bits; `n = 128`; bits per disclosed row = 5.

Disclosed: L1 `5×125 = 625` bits; L2 `5×94 = 470` bits.

Definition: `f_eff = disclosed / load`.

### L1 factor: 625 / 548.700215065776 = 1.1390555039696448 — CONFIRMED

Hand check: residual `625 − 548.700215065776 = 76.299784934224`.
`0.139 × load = 76.26932989414286` (0.1→54.8700215065776;
0.03→16.46100645197328; 0.009→4.938301935591984; sum).
Remainder `76.299784934224 − 76.26932989414286 = 0.03045504008114`.
`0.03045504008114 / 548.700215065776 ≈ 0.0000555039696448`
(0.0000555×load=0.03045286…, remainder ≈2.18e-06 → +0.00000000397…).
Total `1 + 0.1390555039696448 = 1.1390555039696448`. MATCHES packet to 16dp.

### L2 factor: 470 / 412.508145233200 = 1.1393714413428093 — CONFIRMED

Hand check: residual `470 − 412.508145233200 = 57.491854766800`.
`0.139 × load = 57.3386321874148` (0.1→41.25081452332;
0.03→12.375244356996; 0.009→3.7125733070988; sum).
Remainder `57.4918547668 − 57.3386321874148 = 0.1532225793852`.
`0.1532225793852 / 412.508145233200 ≈ 0.0003714413428093`
(0.0003714×load≈0.1532055…, remainder ≈1.7e-05 → +0.00000004134…).
Total `1 + 0.1393714413428093 = 1.1393714413428093`. MATCHES packet to 16dp.

### Absolute gap: |L2 − L1| = 0.00031593737316448767 — CONFIRMED

Digit-wise subtraction `1.1393714413428093 − 1.1390555039696448`:
`0.0003159373731645` (full 17dp `0.00031593737316448767` per packet).
Both factors sit near 1.139 with L2 higher by ≈3.16e-04. No contradiction; no amend.

## 3. Degree cells, sockets, allocations (D1602b, every histogram sums to n/m/E)

Variable side is m-independent (D9 largest-remainder rule, retained from D15):

- L045: n2=71, n3=57 → n=128; E=71·2+57·3=142+171=**313**.
- L055: n2=83, n3=45 → n=128; E=83·2+45·3=166+135=**301**.
- L2 DV3: 128 degree-3 → n=128; E=128·3=**384** (n2=0).

Check side is concentrated floor/ceil: `flo=floor(E/m)`, `b=E−flo·m` ceils,
`a=m−b` floors, `a+b=m`, `a·flo+b·(flo+1)=E`.

| cell | allocation | count sum | socket sum | verdict |
|---|---|---|---|---|
| L045 m125 (new) | `2^62+3^63` | 62+63=125 | 124+189=313=E | PASS (b=313−250=63, a=62) |
| L055 m125 (new) | `2^74+3^51` | 74+51=125 | 148+153=301=E | PASS (b=301−250=51, a=74) |
| L2 m94 (new) | `4^86+5^8` | 86+8=94 | 344+40=384=E | PASS (b=384−376=8, a=86) |

Every histogram sums to its (n, m, E). No contradiction; no amend.

## 4. Constructor-feasibility screen (D1602c — PASS, no STOP)

R2 admission gates (frozen, `v72p2d10-mixed-degree-l1` spec/design): A1 exact
variable/check histograms + socket balance `sum_v=sum_c=E`; A2 simple graph (no
duplicate edge, no empty check, min check degree == design §3 min); A3 exactly
ONE connected component over all n+m Tanner nodes; A4 deterministic structural
rank == m; A5 exact GF32 (poly 37) row rank == m; A6 deterministic replay
equality. Four-cycles/girth/ACE are diagnostics only, never gating.

- Min-dc-4 / max-dc-5 on L2 m94 (`4^86+5^8`): NO gate forbids dc 4/5. A2 compares
  min against the design-declared min (§3: L2 min 4), not a hardcoded 2; no gate
  requires degree-2 checks. Precedent: D15 admitted all nine cells 36/36
  including three L2 min-4 cells (m83 `4^31+5^52`, m86 `4^46+5^40`, m89
  `4^61+5^28`) under the same gates (decision-log:4275/4286). Max dc 5 is within
  the D9 normative max-check-degree ≤8 ceiling (frozen D15 matrix max was 5;
  D16 max is also 5 — no increase). PASS.
- Variable side L2 all-degree-3 (n2=0): NO gate requires n2>0. A1 checks exact
  match to the declared `(0,128,384)` profile; the frozen D10 DV3 control is
  exactly `(n2,n3,E)=(0,n,3n)` and passed admission mechanics. PASS.
- Shared connectivity-first constructor (`build_degree_sequence_peg`: spanning
  backbone + PEG/ACE fill, one deterministic attempt, fail-closed
  `construction_failed`) takes only the forced degree-sequence input per arm
  family; the three sequences above are all valid inputs. L2 density E/m=4.09
  vs D15 4.63/4.47/4.31 — sparser than admitted D15 L2 cells; L1 density
  313/125=2.50 and 301/125=2.41 vs D15 2.65–2.85 — sparser, still valid. PASS.
- Novel row counts m125/m94 impose NO gate constraint: A1 reads m from the
  record (`a+b=m`, socket sum=E); A3 counts n+m nodes; A4/A5 require rank==m.
  Gates are parametric in m, not an allowlist. PASS.
- ANY contradiction would have forced STOP before code with the exact
  calculation. NONE FOUND → proceed to D1601 freeze.

## 5. Reuse map (import unchanged, duplication rejected)

Base: `comparison_bench/src/comparison_bench/formal_ir/`.
D1603 SHALL import (later call; frozen here): D15 graph construction
(`build_degree_sequence_peg`), A1–A6 admission (`structural_record`,
`build_graph` + A6 replay, `structural_rank`, `gf32_row_rank`), coefficient rule
(`coefficient_seed`/`coefficients_for_edges`, `v10_seed(f"d10:coeff:128:{graph_seed}")`),
block sampling (`sample_matched_block`), Model-F CAL-only L1 prior chain
(`prepare_model_f_prior_candidate` → `marginalize_f_to_p1` →
`_floor_renorm(DECODER_FLOOR=1e-15)`), L1 dispatch pattern, and the D15
true-conditioned L2 oracle path (`oracle_l2_prior` → `get_conditional_posterior_l2`,
diagnostic-only, shared per graph/block, EXCLUDED from grading except via §7).
NO APP transfer (no `transfer_prior_l1_to_l2`/`canonical_transfer_l2_prior`/
`app_fed_l2_prior` consumption in this change). No copied decoder
(`decode_row_layered_fftqspa` bound only) or GF32 kernels. One construction path
per frozen arm family. R2/D12/D5 remain donors through D15; D15 is the direct
predecessor. Frozen decoder contract (for D1605+): max_iter=90,
damping 1.0, cold start, q=32/poly37; exact/syndrome/undetected/iterations
isolated, `undetected` never merged into success/FER; non-oracle provenance
must be `CHECK_UPDATED` (L2 oracle cells carry `ORACLE`).

## 6. Seeds, root, command freeze + absence proof (D1609 groundwork)

- Graph seeds (12, fresh, disjoint per cell, 4 per cell):
  L045-m125 `2026094001..04`; L055-m125 `2026094005..08`;
  L2-m94 `2026094009..12`.
- Block seeds (8, same 8 blocks feed all three cells): `2026094101..08`.
- Prior ranges (must not collide): D10 2201–2215; R3/D11-L1 2401–2406/2501–2506,
  blocks 2601–2612/2701–2712; D11-L2 2801–2806/2901–2906; D12 graphs
  3001–3006/3101–3106, blocks 3201–3212/3301–3312; D14N graphs 3401–3406/3501–3506,
  blocks 3601–3612 (+3701-prereg reserved); D15 graphs 3801–3836, blocks
  3901–3908. Selected 4001–4012/4101–4108 sit strictly above all of them
  (40xx/41xx hundred-blocks) — disjoint by construction.
- Absence proof (this call, `rg` over repo): `20260940|20260941` exact-seed
  integers → only the packet's own two lines
  (`.workbuddy/tasks/D16_…_PACKET.md:35–36`); `2026094001`, `2026094005`,
  `2026094009`, `2026094101` → zero hits outside the packet;
  `d16_matched_backoff` → zero hits (`No files found`);
  `b7c2d4e6-8f1a-4c3d` → zero hits (`No files found`). Direct-read of the future
  root path: not created (no filesystem probe beyond absence-by-search; D1609
  SHALL re-prove before any execution).
- Frozen future root (absent through readiness, never overwritten):
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  (six-file D11/D12/D15 convention; exact filenames frozen at D1605).
- Frozen exact future command (unauthorized; NO execution authorized here):
  `.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  (runner belongs to D1604; `--profile-only`/`--verify` and default-false
  `--execution-authorized` refusal-before-root/binding/Model-F-load frozen in spec).
- STOP rule: on any seed/root collision D1601 FAILS and returns BLOCKED; none found.

## 7. Matrix, plan, gates (six terminals, first-match priority)

Three cells (1 point × 3 arms); 4 graphs/cell (12 objects); 8 paired blocks/cell
(8 samples); 96 scientific calls (3×4×8); 22 setup (12+8+2). Deterministic call
order (arm L045→L055→L2-ORACLE, graph ascending, block ascending) frozen in
spec. Paired blocks: the same 8 block objects feed all three cells; L045/L055
discordances paired per D12/D15; no predecessor pooling. Batch tag prevents
predecessor pooling.

Cell predicates (reused D15, applied independently per 32-trial arm):

- ADEQUATE: pool ≥24/32 and at least two graphs ≥6/8.
- WEAK: pool ≤16/32 and at least two graphs ≤4/8.
- otherwise MIDDLE.

Route terminals (first-match priority; thresholds preregistered, frozen before
any result, never tuned post-hoc):

1. Engineering/resource violation → `D16_ENGINEERING_BLOCKED`.
2. L055 ADEQUATE and L2 WEAK → `D16_L2_DEGREE_SIGNAL`.
3. L055 WEAK and L2 ADEQUATE → `D16_L1_CONSTRUCTION_SIGNAL`.
4. L055 ADEQUATE and L2 ADEQUATE → `D16_MATCHED_BACKOFF_SUFFICIENT`.
5. L055 WEAK and L2 WEAK → `D16_BOTH_WEAK`.
6. otherwise → `D16_AMBIGUOUS`.

Conservative rules (normative): L045 is descriptive only (never gates);
Wilson intervals + paired discordances are descriptive only (spec §D1607);
multi-graph support REQUIRED (no single pooled count, no single graph closes
the route); stored terminals remain evidence awaiting main-thread adjudication.

## 8. Budgets

Scientific calls exactly/at most 96; setup exactly/at most 22; wall ≤900 s
total; per call ≤120 s (checked between/after calls, never interrupted);
RSS strictly <2147483648 B; one CPU process; CPU-only; no
retry/resume/repair/seed search/tuning/adaptive stop. Ceiling breach → STOP as
out-of-scope, re-scope, never tune.

## 9. Rejected alternatives (recorded, not implemented)

- Entropy-rounded factor copying (rejected: rows chosen by exact integer m, factors
  computed from the load; rounded factors never copied).
- APP/forward-transfer arm (rejected: reintroduces the L1 success confound; D11
  already covers forward transfer).
- New L2 degree family now (rejected: L2 stays frozen DV3 for the discriminator;
  degree design belongs after the signal, not before — `L2_DEGREE_SIGNAL` routes there).
- Broad multi-point scan (rejected: D15 already ran the 9-cell curve; D16 is the
  single matched point the D15 acceptance routes to).
- m125-to-fit-old-strings or m104-L2 retention (rejected: destroys the
  matched-factor design; D14N 1.002-vs-1.261 confound is the reason for matching).
- Single-graph / pooled-count route closure (rejected: §7 multi-graph rules).
- Investment selection, D7-H revival, threshold fitting from one point
  (rejected: claim ceiling §10).

## 10. Claim ceiling

Synthetic single-layer diagnostic only. No investment choice, no D7-H/FER/
leakage/SKR/real-data/qualification/optimality/publication claims. Terminal is
`READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution.
