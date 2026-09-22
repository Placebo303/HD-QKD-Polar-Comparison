# Spec — L2 finite-ensemble validation (delta requirement set)

Scope: D19 readiness freeze (planner, no code). Normative language
(`SHALL`/`SHALL NOT`) binds F03–F10 implementation and F09 review. Packet
§§2/4/5 take precedence on any conflict; STOP rules are fail-closed.

## Route and ceiling (packet §1)

- REQ-D19-ROUTE-01: The implementation SHALL validate ONLY the single D18
  winner `lam_d2_0.20_d3_0.80` (arm `L020`) against DV3 at the single rate
  point m/n = 94/128. It SHALL NOT add a near-tie arm (0.15/0.25 or any
  other family member) and SHALL NOT reopen the D18 family decision.
- REQ-D19-ROUTE-02: The batch SHALL make no optimality, FER, leakage,
  SKR, qualification, promotion, publication, route-closure, APP, L1,
  D7-H, or real-data claim. All terminals SHALL be labeled synthetic
  finite-L2 diagnostics only.

## Frozen cells (packet §2)

- REQ-D19-CELL-01: The four cells SHALL be exactly: n128/DV3 `3^128`,
  E=384, `4^86+5^8`; n128/L020 `2^35+3^93`, E=349, `3^27+4^67`;
  n256/DV3 `3^256`, E=768, `4^172+5^16`; n256/L020 `2^70+3^186`,
  E=698, `3^54+4^134`. F02 has verified every cell by hand from the D9
  largest-remainder rule + socket balance (`design.md` §2.2); any
  implementation mismatch SHALL STOP the batch.
- REQ-D19-CELL-02: The discriminating point SHALL be m/n = 94/128 with
  `delta_L2 = 0.44915511536562214` (recomputed by hand as `5·94/128 −
  H_L2 = 3.671875 − 3.222719884634378`; `design.md` §2.4), below DV3's DE
  threshold and above the candidate's. The L2 channel SHALL be
  true-U1-conditioned ORACLE, diagnostic-only, ungraded; APP/transfer
  SHALL NOT enter.
- REQ-D19-CELL-03: Only the frozen degree profile and its implied
  sockets/check allocation SHALL differ between arms. Constructor,
  coefficient rule, decoder, prior, blocks, admission gates, and stopping
  rule SHALL be identical across arms.

## Seeds and paired plan (packet §3)

- REQ-D19-SEED-01: Graph seeds SHALL be exactly n128 `2026094401..4406`
  and n256 `2026094407..4412`; block seeds SHALL be exactly n128
  `2026094501..4508` and n256 `2026094511..4518`. They SHALL be disjoint
  from every D10–D18 graph/block/DE seed and protected D16 identity
  (absence proven at F01; see proposal Return). Any collision SHALL STOP
  the batch. No replacement or seed search SHALL occur.
- REQ-D19-PLAN-01: Within each width both arms SHALL share graph-seed
  labels and the same eight generated source blocks; graphs SHALL remain
  arm-specific. Order SHALL be deterministic width→graph→block→arm.
- REQ-D19-PLAN-02: The n128 plan SHALL be exactly 2×6×8 = 96 decoder
  calls. The n256 plan SHALL be another 96 calls dispatched ONLY after a
  frozen n128 POSITIVE gate. Maximum scientific calls SHALL be 192.
  Controls SHALL NEVER advance independently.

## Construction and admission (packet §4)

- REQ-D19-BUILD-01: The implementation SHALL reuse the accepted D10-R2
  connectivity-first `build_degree_sequence_peg` and
  coefficient/admission helpers; it SHALL NOT add a graph constructor.
- REQ-D19-BUILD-02: Coefficients SHALL use the single deterministic
  namespace `v10_seed("d19:l2:coeff:{width}:{arm}:{graph_seed}")` with
  uniform nonzero GF32 coefficients in sorted-edge order.
- REQ-D19-BUILD-03: Before decoder binding, EVERY graph SHALL pass the
  accepted A1–A6 gates: exact variable degrees; exact check degrees; one
  connected component; full structural rank m; full GF32 rank m;
  deterministic replay identity.
- REQ-D19-BUILD-04: Four-cycle count/girth and other structure
  diagnostics SHALL be recorded but SHALL NEVER repair, replace, or gate
  beyond A1–A6. Any invalid graph SHALL make the batch
  engineering-blocked before scientific dispatch with zero replacement
  seeds.

## Decoder and measurements (packet §5)

- REQ-D19-DEC-01: The implementation SHALL reuse D16's accepted
  true-conditioned L2 oracle block sampler/prior and the canonical cold
  row-layered decoder (GF32/poly37, max_iter90, damping1.0).
- REQ-D19-DEC-02: Exact recovery SHALL be the sole success gate.
  Syndrome-valid, undetected, iterations, residual syndrome weight,
  provenance, wall, and failures SHALL be recorded separately and SHALL
  NEVER be merged with exact.
- REQ-D19-DEC-03: EVERY row SHALL carry `ORACLE` provenance; oracle rows
  SHALL remain ungraded. There SHALL be exactly one decoder call per
  `(width,graph,block,arm)` with no retry/resume/warm start.

## Width gates (packet §6)

- REQ-D19-GATE-01 (POSITIVE): a width SHALL be POSITIVE iff ALL five
  hold: `M >= 30/48`; at least five of six graphs have `M_g >= 4/8`;
  L020 wins strictly on at least five of six graphs (`M_g > C_g`);
  `b - c >= 12`; `C <= 20/48` (exact successes; `b`/`c` paired
  candidate-only/control-only block outcomes).
- REQ-D19-GATE-02 (NEGATIVE): a width SHALL be NEGATIVE iff BOTH hold:
  `M <= 16/48` AND `b - c <= 4`. Otherwise the width SHALL be
  AMBIGUOUS.
- REQ-D19-GATE-03: Gates SHALL use exact only. Paired p-values/Wilson
  intervals and structure correlations SHALL be descriptive only. n256
  SHALL dispatch iff n128 is POSITIVE.

## Terminals (packet §7)

- REQ-D19-TERM-01: Terminals SHALL be exactly the four frozen labels
  with `design.md` §7 conditions: `D19_L2_FINITE_SIGNAL_REPRODUCED`
  (n128 + n256 POSITIVE); `D19_L2_FINITE_NO_USEFUL_RECOVERY` (n128
  NEGATIVE, or n128 POSITIVE then n256 NEGATIVE);
  `D19_L2_FINITE_AMBIGUOUS` (any entered width AMBIGUOUS);
  `D19_L2_FINITE_ENGINEERING_BLOCKED`
  (contract/admission/resource/incomplete-plan failure). All SHALL be
  labeled synthetic finite-L2 diagnostics, not qualification.

## Boundary, runner, tests, review (packets §8–9)

- REQ-D19-BOUND-01: The future root SHALL match
  `workspace/d19_l2_finite_ensemble_<uuid>` (UUID picked at F08) with one
  exact repo-venv command frozen at F08; the root SHALL be absent
  throughout readiness. Ceilings SHALL be ≤192 decoder calls + ≤42 setup,
  wall ≤1800s, per-call ≤120s (between/after-call check only), RSS
  <2GiB, one CPU process, no retry/resume/replacement/tuning/adaptive
  thresholds. This packet SHALL grant zero calls; one later explicit user
  grant may cover n128 + the mechanically conditional n256 sequence.
- REQ-D19-BOUND-02: The runner SHALL expose `--profile-only`,
  `--d19-batch`, default-false `--execution-authorized` (refuse before
  output/input reads when unauthorized, never overwrite), fresh-root
  refusal, and read-only `--verify`.
- REQ-D19-BOUND-03: F06 tests SHALL cover arithmetic/socket tables; 24
  graph admissions (2 arms × 2 widths × 6); replay; seed disjointness;
  plan/order/pairing; every gate edge; n256 dispatch; exact/syndrome/
  undetected isolation; L2 ORACLE-only boundary; fake complete/negative/
  ambiguous/engineering runs; refusal/no-overwrite; verifier
  recomputation.
- REQ-D19-BOUND-04: F07 SHALL be plan/graph arithmetic only with zero
  decoder calls and proven root absence. F09 SHALL independently verify,
  with actual artifact access, D18 winner provenance, arithmetic,
  construction isolation, 24 admissions, seeds/plan/gates, decoder
  boundary, budgets, tests, and zero production; any blocker SHALL STOP
  promotion.

## STOP (packet §10)

- REQ-D19-STOP-01: Execution SHALL STOP with no scientific call if
  degree/socket arithmetic disagrees; the D18 winner changes; a
  non-winner arm is added; corrected current-channel L2 oracle identity
  is not exact; any A1–A6 graph fails; seeds collide; APP/L1 or graded
  oracle enters; exact/syndrome/undetected merge; thresholds adapt; the
  future root exists; or independent review has a blocker.

(End of file)
