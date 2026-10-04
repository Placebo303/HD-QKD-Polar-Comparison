# Design — D19 L2 Finite-Ensemble Validation (F01/F02 freeze)

Authority: `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`
§§1–11. All numbers below are frozen preregistration; nothing here
authorizes execution. Packet §§2/4/5 take precedence on any conflict; STOP
rules are fail-closed.

## 1. Route (packet §1)

- Repository `HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean`, change
  `v72p2d19-l2-finite-ensemble-validation`.
- Future batch track: `EXPLORE_HEAVY`; this readiness packet (F01–F10) is
  implementation/readiness only and authorizes zero scientific
  decoder/DE calls.
- Accepted predecessor:
  `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`
  (PRESENT — exact-string evidence in the proposal Return section).
- Route acceptance (main-thread decision): accept the D18 winner
  `lam_d2_0.20_d3_0.80` for one finite L2 validation against DV3. Not an
  optimality claim.
- Near-tie ceiling (explicit non-reopening): D18's 0.15/0.20/0.25 had
  identical reviewed DE thresholds; 0.20 won only via the frozen
  max-check-degree then ID tie-break (rank-4..6 0.30/0.35/0.40
  screen-indistinguishable). D19 adds no near-tie arm and reopens no
  family decision.
- Out of scope: scientific decoder calls, D7-H, APP, L1, real data,
  FER/leakage/SKR/qualification, route closure, push.

## 2. Frozen finite cells (packet §2) + F02 hand rederivation

Single rate point: D18 discriminator m/n = 94/128, corresponding to
`delta_L2=0.44915511536562214`, below DV3's DE threshold and above the
selected candidate's threshold. Both arms use the same constructor,
coefficient rule, decoder, prior, blocks, admission gates, and stopping
rule; only the frozen degree profile and implied sockets/checks differ.
L2 channel is true-U1-conditioned ORACLE, diagnostic-only and ungraded;
no APP/transfer.

### 2.1 Frozen table

| width | m | arm | variable counts | E | check counts |
|---:|---:|---|---|---:|---|
| 128 | 94 | DV3 | `3^128` | 384 | `4^86 + 5^8` |
| 128 | 94 | L020 | `2^35 + 3^93` | 349 | `3^27 + 4^67` |
| 256 | 188 | DV3 | `3^256` | 768 | `4^172 + 5^16` |
| 256 | 188 | L020 | `2^70 + 3^186` | 698 | `3^54 + 4^134` |

### 2.2 F02 rederivation (by hand, no code execution — VERIFIED, no mismatch)

Rule (accepted D9): edge-perspective nominal `lambda={2:0.20,3:0.80}`
converts to node fractions `L_d = (lambda_d/d) / sum_i(lambda_i/i)`;
node counts via largest remainder; `E = sum n_d*d`; check allocation is
concentrated: `q = floor(E/m)`, `b = E - q*m` checks of degree `q+1`,
`m-b` of degree `q`.

- Nominal: `lambda_2/2 = 0.10 = 3/30`; `lambda_3/3 = 0.80/3 = 8/30`;
  sum `11/30`. Hence `L2 = 3/11 = 0.272727…`, `L3 = 8/11 = 0.727272…`.
- n128 L020: `128*3/11 = 384/11 = 34 + 10/11 = 34.909090…`;
  `128*8/11 = 1024/11 = 93 + 1/11 = 93.090909…`. Remainders `10/11 >
  1/11` → round the degree-2 count up: `35 + 93 = 128` ✓ → `2^35 +
  3^93`. `E = 35*2 + 93*3 = 70 + 279 = 349` ✓. Checks:
  `floor(349/94) = 3`, `b = 349 − 282 = 67` → `27×3 + 67×4` ✓;
  sockets `81 + 268 = 349 = E` ✓.
- n128 DV3: `E = 128*3 = 384` ✓. `floor(384/94) = 4`,
  `b = 384 − 376 = 8` → `86×4 + 8×5` ✓; sockets `344 + 40 = 384` ✓.
- n256 L020: `256*3/11 = 768/11 = 69 + 9/11 = 69.818181…`;
  `256*8/11 = 2048/11 = 186 + 2/11 = 186.181818…`. Remainders `9/11 >
  2/11` → `70 + 186 = 256` ✓ → `2^70 + 3^186`. `E = 140 + 558 =
  698` ✓. Checks: `floor(698/188) = 3`, `b = 698 − 564 = 134` →
  `54×3 + 134×4` ✓; sockets `162 + 536 = 698 = E` ✓.
- n256 DV3: `E = 256*3 = 768` ✓. `floor(768/188) = 4`,
  `b = 768 − 752 = 16` → `172×4 + 16×5` ✓; sockets `688 + 80 =
  768` ✓.
- Result: all four packet cells VERIFIED exactly. No STOP.

### 2.3 Exact rational realized lambda/rho deviations from nominal (F02 record)

Nominal edge `lambda = {2:1/5, 3:4/5}`; nominal node `L2 = 3/11`,
`L3 = 8/11`. Realized values are identical at both widths (exact
doubling: `70/140/186` reduce to the n128 fractions):

- L020 realized edge: `lambda2 = 70/349 ≈ 0.2005730659` (deviation
  `+1/1745 ≈ +0.0005730659`); `lambda3 = 279/349 ≈ 0.7994269341`
  (deviation `−1/1745`).
- L020 realized node: `L2 = 35/128 = 0.2734375` (deviation `+1/1408 ≈
  +0.0007102273` over `3/11`); `L3 = 93/128 = 0.7265625` (deviation
  `−1/1408`).
- L020 realized check edge: `rho3 = 81/349 ≈ 0.2320916905`,
  `rho4 = 268/349 ≈ 0.7679083095`; node `R3 = 27/94 ≈ 0.2872340426`,
  `R4 = 67/94 ≈ 0.7127659574`; mean check degree `349/94 ≈ 3.7127660`.
- DV3 realized check edge (both widths): `rho4 = 43/48 ≈ 0.8958333333`,
  `rho5 = 5/48 ≈ 0.1041666667`; node `R4 = 43/47 ≈ 0.9148936170`,
  `R5 = 4/47 ≈ 0.0851063830`; mean `384/94 = 192/47 ≈ 4.0851064`
  (n256 identical: `688/768 = 43/48`, `80/768 = 5/48`).

### 2.4 delta_L2 recompute (by hand — VERIFIED)

`5·94/128 = 470/128 = 235/64 = 3.671875` exactly.
`3.671875 − H_L2(3.222719884634378, trusted D18 stage-C value) =
0.449155115365622`, matching packet `0.44915511536562214` to 15dp
(trailing digit is full-double display). No mismatch; no STOP.

## 3. Frozen seeds and paired plan (packet §3)

- Graph seeds: n128 `2026094401..4406` (6); n256 `2026094407..4412` (6).
- Block seeds: n128 `2026094501..4508` (8); n256 `2026094511..4518` (8).
- Disjointness PROVEN this call: rg for the full `20260944xx`/`20260945xx`
  ranges hits only the D19 packet lines 42–43; no D10–D18 graph/block/DE
  seed and no protected D16 identity collides. No replacement or seed
  search. Any collision found later → STOP.
- Within each width, both arms share graph-seed labels and the same eight
  generated source blocks; graphs remain arm-specific because degree
  sequences differ.
- Deterministic order width→graph→block→arm; n128 plan 2×6×8 = 96 calls.
- n256 is dispatched only after a frozen n128 POSITIVE gate; another 96
  calls. Maximum scientific calls 192. Controls never advance
  independently.

## 4. Graph construction and admission (packet §4)

- Reuse the accepted D10-R2 connectivity-first `build_degree_sequence_peg`
  and coefficient/admission helpers; do NOT add a graph constructor.
- One deterministic coefficient seed namespace
  `v10_seed("d19:l2:coeff:{width}:{arm}:{graph_seed}")`, with uniform
  nonzero GF32 coefficients in sorted-edge order.
- Before decoder binding, require the accepted A1–A6 gates for every
  graph: exact variable degrees; exact check degrees; one connected
  component; full structural rank m; full GF32 rank m; deterministic
  replay identity.
- Record four-cycle count/girth and other structure diagnostics, but never
  repair, replace, or gate on them beyond A1–A6.
- Any invalid graph makes the batch engineering-blocked before scientific
  dispatch; zero replacement seeds.

## 5. Decoder and measurements (packet §5)

- Reuse D16's accepted true-conditioned L2 oracle block sampler/prior and
  canonical cold row-layered decoder: GF32/poly37, max_iter90,
  damping1.0.
- Exact recovery is the sole success gate. Record syndrome-valid,
  undetected, iterations, residual syndrome weight, provenance, wall, and
  failures separately. Never merge exact with syndrome-valid or
  undetected.
- Require `ORACLE` provenance for every row; oracle rows remain ungraded.
- One decoder call per `(width,graph,block,arm)`; no retry/resume/warm
  start.

## 6. Frozen width gates (packet §6)

For each width, let `M_g` and `C_g` be L020 and DV3 exact successes out
of 8; `M`, `C` pooled out of 48; `b` candidate-only and `c`
control-only paired block outcomes.

### POSITIVE — all must hold

1. `M >= 30/48`;
2. at least five of six graphs have `M_g >= 4/8`;
3. L020 wins strictly on at least five of six graphs (`M_g > C_g`);
4. `b - c >= 12`;
5. `C <= 20/48`.

### NEGATIVE — both hold

1. `M <= 16/48`;
2. `b - c <= 4`.

Otherwise AMBIGUOUS. Gates use exact only; paired p-values/Wilson
intervals and structure correlations are descriptive. n256 dispatches
iff n128 is POSITIVE.

## 7. Batch terminals (packet §7)

- n128 POSITIVE and n256 POSITIVE: `D19_L2_FINITE_SIGNAL_REPRODUCED`.
- n128 NEGATIVE, or n128 POSITIVE then n256 NEGATIVE:
  `D19_L2_FINITE_NO_USEFUL_RECOVERY`.
- Any entered width AMBIGUOUS: `D19_L2_FINITE_AMBIGUOUS`.
- Contract/admission/resource/incomplete-plan failure:
  `D19_L2_FINITE_ENGINEERING_BLOCKED`.

These are synthetic finite L2 diagnostic terminals, not qualification.

## 8. Rejected alternatives (recorded)

Near-tie arms (0.15/0.25) or any family reopening; optimality/route
reading of the winner; hand-set check distributions; graph-constructor or
decoder-kernel copies; graded/APP/L1 evidence in the L2 decision;
merging exact/syndrome/undetected; retry/resume/warm-start or replacement
seeds; adaptive thresholds; FER/leakage/SKR/qualification use of the
outcome.

## 9. Future execution boundary (packet §9)

- Fresh root: `workspace/d19_l2_finite_ensemble_<uuid>` chosen and frozen
  during readiness (F08 picks the UUID); absent afterwards.
- Maximum 192 decoder calls; setup ≤42 (24 graphs + 16 width-specific
  blocks + 2 binding/plan).
- Wall ≤1800s; per-call ≤120s; RSS <2GiB; one CPU process; no
  retry/resume/replacement/tuning/adaptive thresholds.
- One later explicit grant may cover n128 and the mechanically
  conditional n256 arm sequence. Readiness grants none.

## 10. STOP conditions (packet §10)

STOP without scientific execution if degree/socket arithmetic disagrees;
the D18 winner changes; a non-winner arm is added; corrected
current-channel L2 oracle identity is not exact; any A1–A6 graph fails;
seeds collide; APP/L1 or graded oracle enters; exact/syndrome/undetected
merge; thresholds adapt; future root exists; or independent review has a
blocker.

(End of file)
