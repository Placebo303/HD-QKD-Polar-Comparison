# Spec delta — V72P2D9 GF32 DE-decoder calibration and threshold (R1)

## SHALL (frozen)

- The D9 calibration contract SHALL reuse the accepted V26 kernel
  `nonbinary_v26_mcde.run_mcde_posterior` unchanged (q=32, poly 37), the D7-A
  certified v35 row-layered decoder semantics as read-only reference, the D8
  Model-F L1 channel chain and the accepted V37P0 `v37_degree_feasibility`
  helpers. V26, v35, D7-A and D8 result files SHALL NOT be edited.
- The semantic map SHALL record, with real path:line pointers and explicit
  MATCH/APPROX/MISMATCH boundaries: (a) channel centering and prior/floor
  chain; (b) coefficient permutation direction and syndrome/coset centering;
  (c) variable-node update; (d) check-node update; (e) posterior/belief metric
  versus decoder output; (f) flooding DE iteration versus row-layered finite
  sweep; (g) stopping metric (normalized entropy versus exact/syndrome stop),
  exactly as frozen in `design.md` §2.
- The equivalence ceiling SHALL be: primitive same-input check update and
  coefficient direction certified (D7-A; D8 cross-kernel unit-coefficient);
  flooding-DE ↔ row-layered trajectory equivalence, DE-terminal ↔ decoder
  terminal equivalence, and finite-length/FER inference NOT established. A DE
  terminal SHALL NOT substitute for a decoder exact/syndrome result.
- The prospective f1.0 role SHALL be `BOUNDARY_DIAGNOSTIC` under the frozen
  criterion `mu >= 0.05 bits/symbol` AND `R_ent - R >= 0.01` with
  `H_L1=3.814742`, `mu = 5m/n - H_L1`, `R_ent = 1 - H_L1/5`; f1.0 SHALL NOT
  block eligibility, ranking or any terminal. A boundary crossing
  (`S4000(f1.0) >= 7/8` for a non-baseline candidate) SHALL be reported to the
  main thread only, without promotion.
- The finite-graph realization SHALL use the deterministic
  largest-remainder node-count rule and the floor/ceil check allocation of
  `v37_degree_feasibility.py:118-261`, with socket balance
  `Σ i·c_i = E = 2n2+3n3`, `Σ c_i = m`; realized rate SHALL equal `1 - m/n`
  exactly; min check degree SHALL be >= 2 and realized max check degree <= 8;
  non-integer exact nominal socket counts SHALL be flagged with exact numbers
  as in `design.md` §5; `N2 > m-1` cells SHALL be flagged as forced degree-2
  cycle components (none for the frozen matrix).
- The future calibration matrix SHALL contain only regular-DV3 plus candidate
  0.45, 0.50 (mandatory) and the 0.55 upper-flank control with its stated
  control role; no broader search, no extra point without a stated control
  role, no adaptive rule.
- The matrix SHALL be: f1.2 primary at populations {4000, 16000}; f1.0
  boundary diagnostic at population {4000}; 8 frozen seeds
  (`2026091601..2026091603`, `2026091801..2026091805`); V26 parameters
  `max_iter=60`, `entropy_tol_bits=1e-4`, `streak=20`, entropy and
  channel-entropy recording on; <=96 DE calls + <=12 setup calls; all
  registered calls run (no early stop, no seed extension, no candidate
  addition).
- Stability SHALL be defined by `S4000`/`S16000` counts of seeds with
  `H60 < 1e-4`: `stable_converged` ⇔ both equal 8; `stable_unconverged` ⇔ both
  <= 6; otherwise `stability_ambiguous`.
- Selection SHALL require primitive semantic certification PASS, valid graph
  realization, DV3 `stable_unconverged`, and `stable_converged` candidates with
  16000-sample worst-seed `AUT_30 <= 0.95 x` the DV3 16000-sample worst-seed
  `AUT_30`; exactly one winner by `(worst-seed AUT_30 p16000 asc, mean AUT_30
  p16000 asc, worst T_0.01 p16000 asc, candidate ID lexicographic)`. A
  selection SHALL authorize only the next finite-length synthetic task packet.
- Terminal states SHALL be exactly: `D9_DE_CALIBRATION_SELECT_ONE`,
  `D9_DE_STABILITY_NOT_CONFIRMED`, `D9_DE_BASELINE_CONVERGED_REVIEW`,
  `D9_SEMANTICS_BLOCKED`, `D9_GRAPH_REALIZATION_INVALID`,
  `D9_DE_EVIDENCE_INVALID`, `D9_DE_RESOURCE_BLOCKED`, `D9_DE_NOT_RUN`.
  Routing SHALL follow `design.md` §7 (packet §8); no outcome SHALL revive
  D7-H, reinterpret the D8 terminal or retroactively relabel D8 candidates as
  winners.
- The future run SHALL use the fresh root
  `workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b/`
  (verified absent at freeze), the six-file D8 evidence convention, fresh-root
  refusal, wall <=1200 s, per-call <=300 s, RSS <2 GiB strict, single process,
  no retry/resume, and the exact command frozen in `design.md` §6. The root
  SHALL remain absent and unauthorized until a separate explicit
  user/main-thread authorization names this batch.
- The claim ceiling SHALL be: readiness/calibration-contract evidence under the
  frozen CAL-only Model-F channel and decoder contract; no
  finite-length/FER/leakage/SKR/qualification/promotion/real-data claim.

## SHALL NOT

- No production decoder call, no scientific DE sweep, no Model-F content read
  beyond the accepted artifact, no CAL/VAL/raw/real-data contact in readiness.
- No modification of v35, V26, the D7-A code, the D8 implementation or the
  channel model; no decoder tuning inside D9.
- No generalized DE framework, optimizer, graph library, checkpoint system,
  cache, integrity manifest, retry framework or new dependency.
- No claim that V26 DE and the v35 decoder are trajectory-equivalent, that a DE
  convergence is a decoder result, or that D8 established a winner.
