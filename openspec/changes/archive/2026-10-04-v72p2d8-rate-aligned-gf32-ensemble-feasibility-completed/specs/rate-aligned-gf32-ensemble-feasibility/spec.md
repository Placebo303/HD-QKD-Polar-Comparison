# Spec delta — V72P2D8 rate-aligned GF32 ensemble feasibility (L1-first)

## SHALL (frozen)

- The D8 DE engine SHALL be the accepted V26 kernel
  `nonbinary_v26_mcde.run_mcde_posterior` (q=32, `GF2mField.create(32)` poly
  37) with the exact delta list of `design.md` §1: one L1 Model-F channel
  sampler, one `R = 1 - m/n` / `ρ = make_rho(R, λ)` mapping helper, one bounded
  candidate enumeration, one runner and one focused test file. V26/V27/V37/V14/
  V9/v35 SHALL NOT be edited.
- The DE channel SHALL be built only from the accepted CAL-only Model-F
  artifact `workspace/v72p2d5_model_f_input/20260907_r1` through the frozen
  chain artifact → `pb = p_b/p_b.sum()` → E2 backoff `P_F` →
  `P1 = marginalize_f_to_p1(P_F)` → `_floor_renorm(·, 1e-15)` → per-sample
  true-symbol XOR centering, exactly as recorded in `design.md` §2. The 32-ary
  posterior distribution SHALL be preserved exactly; no BSC, AWGN, q-SC or
  scalar surrogate substitution SHALL occur.
- DE messages SHALL be full length-32 row-normalized probability vectors; the
  check update SHALL be the coefficient-permuted WHT XOR convolution with
  kernel floor `1e-300` and the accepted nonzero GF32 coefficient stream.
- L1 SHALL be the only sweep target. L2 SHALL be a read-only comparator and
  SHALL NOT be swept, co-optimized or used in the advancement key.
- The rate mapping SHALL be `R = 1 - m/n` with `m` from the accepted D6 row
  budgets — n64 L1 (49,59,64) / L2 (43,52,64); n128 L1 (98,118,128) / L2
  (86,104,128); n256 L1 (196,236,256) / L2 (172,208,256) — and
  `ρ = make_rho(R, λ)` via the accepted harmonic-exact concentrated check
  distribution. Only f1.2 (primary) and f1.0 (secondary) SHALL be conditions;
  square SHALL be excluded.
- Candidate enumeration SHALL be deterministic and bounded: edge-perspective λ
  support `{2,3}`, `λ2 ∈ {0.00,0.05,…,1.00}`, `λ3 = 1-λ2`, exactly 21
  candidates per condition, hard cap 21, canonical IDs
  `lam_d2_<λ2>_d3_<λ3>`, ascending order. The regular-DV3 baseline
  `λ={3:1}` SHALL be included. Enumeration SHALL NOT adapt to observed sweep
  outcomes, and no replacements or extensions SHALL occur.
- Candidate compatibility SHALL require: variable degrees ∈ {2,3}; minimum
  check degree ≥ 2; simple Tanner graph; accepted nonzero GF32 coefficient
  stream with coefficients not optimized; realized check degree ≤ 8 (E08
  asserts ≤ 4 for the frozen grid). A candidate/condition pair whose
  `make_rho` raises SHALL be refused with a recorded reason, never silently
  dropped. The V37-P0 finite-forest diagnostic (`N2`,
  `gamma_2 = max(0, N2-(m-1))`) SHALL be recorded per candidate per registered
  (n,m) cell as finite-length context and SHALL NOT be a refusal gate.
- The future sweep SHALL use `n_samples=4000`, `max_iter=60`,
  `entropy_tol_bits=1e-4`, `streak=20`, `record_entropy=True`,
  `record_channel_entropy=True`, and the frozen seeds
  `2026091601..2026091603`; it SHALL NOT retry, resume, search seeds, extend
  the population, or stop adaptively.
- The advancement decision SHALL require all three seeds converged
  (`H60 < 1e-4`) in both conditions and a primary-condition worst-seed `AUT_30`
  at most 0.95× the regular-DV3 baseline; if the eligible set is nonempty
  exactly one winner SHALL be selected by the frozen key `(primary worst-seed
  AUT_30 asc, primary mean AUT_30 asc, primary worst-seed T_0.01 asc,
  candidate ID lexicographic)`.
- Terminal states SHALL be exactly: `D8_DE_ADVANCE_ONE_ENSEMBLE`,
  `D8_DE_NO_ADVANCE`, `D8_DE_BASELINE_NOT_CONVERGED`,
  `D8_DE_EVIDENCE_INVALID`, `D8_DE_RESOURCE_BLOCKED`, `D8_DE_NOT_RUN`. A
  `NO_ADVANCE` result SHALL close only the frozen support/grid and SHALL route
  to a broader degree/ensemble proposal or an explicit channel/decoder
  mismatch analysis; it SHALL NOT be recorded as nonbinary-LDPC or
  graph-family impossibility.
- Budgets SHALL be ≤126 DE calls + ≤20 setup calls, wall ≤1800 s, per-call
  ≤120 s, aggregate RSS <2 GiB strict, single process. The future run SHALL
  use a fresh root `workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`
  (verified absent at freeze) and SHALL refuse overwrite; the exact future
  command is frozen in `design.md` §6.
- The claim ceiling SHALL be DE-only synthetic asymptotic evidence under the
  frozen CAL-only Model-F channel and decoder contract. Advancement SHALL
  authorize only the next finite-length task packet; it SHALL NOT authorize
  execution, FER/leakage/SKR numbers, qualification, promotion, real-data
  work or D7-H.
- The future root and command SHALL remain absent and unauthorized until a
  separate explicit user/main-thread authorization names this batch, branch,
  root, candidate cap, seeds and budgets.

## SHALL NOT

- No production decoder call, no model-F content read outside the accepted
  artifact, no CAL/VAL/raw/real-data contact in readiness or tests.
- No L2 joint optimization, coefficient optimization, graph/topology search,
  protograph/MET/SC-LDPC construction, or decoder/schedule change in this
  change.
- No generalized optimizer, workflow engine, cache, checkpoint system,
  integrity manifest, retry framework or new dependency.
- No claim that any candidate is superior, that D6 is a graph-family
  impossibility, or that a DE advancement is a decoder result.
