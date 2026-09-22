# D19 L2 Finite-Ensemble Validation — Readiness R1 Task Packet

## 1. Identity and route decision

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d19-l2-finite-ensemble-validation`
- Future batch: `EXPLORE_HEAVY`; this packet is implementation/readiness only.
- Accepted predecessor:
  `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.
- Accept the D18 winner `lam_d2_0.20_d3_0.80` for one finite L2 validation
  against DV3. This is not an optimality claim.
- D18's 0.15/0.20/0.25 candidates had identical reviewed DE thresholds;
  0.20 won only through the frozen max-check-degree then ID tie-break. Do not
  reopen the family or include extra near-tie arms in D19.
- No scientific decoder calls, D7-H, APP, L1, real data, FER/leakage/SKR/
  qualification, route closure, or push are authorized by readiness.

## 2. Frozen finite cells

Single rate point: D18 discriminator m/n = 94/128, corresponding to
`delta_L2=0.44915511536562214`, below DV3's DE threshold and above the selected
candidate's threshold.

| width | m | arm | variable counts | E | check counts |
|---:|---:|---|---|---:|---|
| 128 | 94 | DV3 | `3^128` | 384 | `4^86 + 5^8` |
| 128 | 94 | L020 | `2^35 + 3^93` | 349 | `3^27 + 4^67` |
| 256 | 188 | DV3 | `3^256` | 768 | `4^172 + 5^16` |
| 256 | 188 | L020 | `2^70 + 3^186` | 698 | `3^54 + 4^134` |

- Independently derive every table from the accepted D9 largest-remainder
  realization and exact socket balance before coding. Any mismatch is STOP.
- Both arms use the same connectivity-first degree-sequence PEG constructor,
  coefficient rule, decoder, prior, blocks, admission gates, and stopping rule.
  Only the frozen degree profile and its implied sockets/check allocation differ.
- L2 channel is true-U1-conditioned ORACLE, diagnostic-only and ungraded; no
  APP/transfer.

## 3. Frozen seeds and paired plan

- n128 graph seeds `2026094401..4406`; n256 `2026094407..4412`.
- n128 block seeds `2026094501..4508`; n256 `2026094511..4518`.
- Prove disjointness from every D10–D18 graph/block/DE seed and protected D16
  identities. No replacement or seed search.
- Within each width, both arms share graph-seed labels and the same eight
  generated source blocks; graphs remain arm-specific because degree sequences
  differ.
- Deterministic order width→graph→block→arm; n128 plan 2×6×8=96 calls.
- n256 is dispatched only after a frozen n128 POSITIVE gate; another 96 calls.
  Maximum scientific calls 192. Controls never advance independently.

## 4. Graph construction and admission

- Reuse the accepted D10-R2 connectivity-first `build_degree_sequence_peg`
  and coefficient/admission helpers; do not add a graph constructor.
- Use one deterministic coefficient seed namespace
  `v10_seed("d19:l2:coeff:{width}:{arm}:{graph_seed}")`, with uniform nonzero
  GF32 coefficients in sorted-edge order.
- Before decoder binding, require the accepted A1–A6 gates for every graph:
  exact variable degrees; exact check degrees; one connected component; full
  structural rank m; full GF32 rank m; deterministic replay identity.
- Record four-cycle count/girth and other structure diagnostics, but never
  repair, replace, or gate on them beyond A1–A6.
- Any invalid graph makes the batch engineering-blocked before scientific
  dispatch; zero replacement seeds.

## 5. Decoder and measurements

- Reuse D16's accepted true-conditioned L2 oracle block sampler/prior and
  canonical cold row-layered decoder: GF32/poly37, max_iter90, damping1.0.
- Exact recovery is the sole success gate. Record syndrome-valid, undetected,
  iterations, residual syndrome weight, provenance, wall, and failures
  separately. Never merge exact with syndrome-valid or undetected.
- Require `ORACLE` provenance for every row; oracle rows remain ungraded.
- One decoder call per `(width,graph,block,arm)`; no retry/resume/warm start.

## 6. Frozen width gates

For each width, let `M_g` and `C_g` be L020 and DV3 exact successes out of 8;
`M`, `C` are pooled out of 48; `b` candidate-only and `c` control-only paired
block outcomes.

### POSITIVE

All must hold:

1. `M >= 30/48`;
2. at least five of six graphs have `M_g >= 4/8`;
3. L020 wins strictly on at least five of six graphs (`M_g>C_g`);
4. `b-c >= 12`;
5. `C <= 20/48`.

### NEGATIVE

Both hold:

1. `M <= 16/48`;
2. `b-c <= 4`.

Otherwise AMBIGUOUS. Gates use exact only; paired p-values/Wilson intervals and
structure correlations are descriptive. n256 dispatches iff n128 is POSITIVE.

## 7. Batch terminals

- n128 POSITIVE and n256 POSITIVE:
  `D19_L2_FINITE_SIGNAL_REPRODUCED`.
- n128 NEGATIVE, or n128 POSITIVE then n256 NEGATIVE:
  `D19_L2_FINITE_NO_USEFUL_RECOVERY`.
- Any entered width AMBIGUOUS:
  `D19_L2_FINITE_AMBIGUOUS`.
- Contract/admission/resource/incomplete-plan failure:
  `D19_L2_FINITE_ENGINEERING_BLOCKED`.

These are synthetic finite L2 diagnostic terminals, not qualification.

## 8. Implementation/readiness tasks

- **F01** OpenSpec first with §§1–7, claim ceiling, and execution boundary.
- **F02** Independently rederive the four degree/socket tables and record exact
  rational realized lambda/rho deviations from nominal.
- **F03** Add one thin D19 module importing D10-R2 graph construction and D16
  L2 oracle/decoder helpers; reject duplicate kernels/builders.
- **F04** Implement graph cells, seeds, paired plan, admissions, exact-only
  gates, conditional width dispatch, terminals, writer, and verifier.
- **F05** Add a runner with `--profile-only`, `--d19-batch`, default-false
  `--execution-authorized`, fresh-root refusal, and read-only `--verify`.
- **F06** Focused tests: arithmetic/socket tables; 24 graph admissions (2 arms
  ×2 widths×6); replay; seed disjointness; plan/order/pairing; every gate edge;
  n256 dispatch; exact/syndrome/undetected isolation; L2 ORACLE-only boundary;
  fake complete/negative/ambiguous/engineering runs; refusal/no-overwrite;
  verifier recomputation.
- **F07** PROFILE_ONLY builds all 24 graphs and 192-call maximum plan with zero
  decoder calls and no official root.
- **F08** Freeze one future root/command/budget; leave it absent/unauthorized.
- **F09** Independent review with actual access: D18 winner provenance,
  arithmetic, construction isolation, 24 admissions, seeds/plan/gates,
  decoder boundary, budgets, tests, zero production.
- **F10** Memory triage and one decision-log entry. Optional scoped local commit
  may include only additive D19 paths if safe; no push.

## 9. Future execution boundary

- Fresh root: `workspace/d19_l2_finite_ensemble_<uuid>` chosen and frozen during
  readiness; absent afterwards.
- Maximum 192 decoder calls; setup ≤42 (24 graphs + 16 width-specific blocks
  + 2 binding/plan).
- Wall ≤1800s; per-call ≤120s; RSS <2GiB; one CPU process; no retry/resume/
  replacement/tuning/adaptive thresholds.
- One later explicit grant may cover n128 and the mechanically conditional n256
  arm sequence. Readiness grants none.

## 10. STOP conditions

STOP without scientific execution if degree/socket arithmetic disagrees; the
D18 winner changes; a non-winner arm is added; corrected current-channel L2
oracle identity is not exact; any A1–A6 graph fails; seeds collide; APP/L1 or
graded oracle enters; exact/syndrome/undetected merge; thresholds adapt; future
root exists; or independent review has a blocker.

## 11. Return contract

Return only:

`D19_L2_FINITE_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`

with route acceptance and near-tie ceiling; exact degree/socket tables and
realized distributions; reuse map; seeds/plan/admission results; gates and
terminals; command/root/budgets; tests/profile/fake/refusal/verifier;
independent verdict; zero production calls; root absence; commit/no-push and
memory state.

Do not execute D19, add near-tie arms, run APP/D7-H/real data, or make FER/
leakage/SKR/qualification/optimality/publication claims.
