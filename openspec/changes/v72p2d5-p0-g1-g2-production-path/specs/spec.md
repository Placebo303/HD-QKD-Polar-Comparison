# Spec delta: V72P2D5 P0/G1/G2 production path (candidate only)

No execution, no authorization, no CAL/VAL/raw read. This delta constrains the
rate-scan fix, stage builders, prep function, CLI reachability, and writers.
It does not merge or replace the accepted R2_DV3 plan; frozen R2_DV3
thresholds/seeds/budgets/gradings stay authoritative on conflict.

## S-RATE-PREFIX (prefix correctness)

- S-RP-01: For every reported `f`, the decoder input SHALL be
  `H1_f=H1_mother[:m1(f)]` and `H2_f=H2_mother[:m2(f)]` sliced from the same
  mother matrices passed into the scan. Reporting per-`f` rows while decoding
  with unsliced mothers SHALL be invalid.
- S-RP-02: `m1(f)/m2(f)` SHALL be `ceil(n*CE*f/5)` with `CE_L1=3.814742` /
  `CE_L2_oracle=3.347605`: P0/G1 `n=64`: `f=1.0` 49/43, `f=1.2` 59/52; G2
  `n=256`: `f=1.0` 196/172, `f=1.1` 215/189, `f=1.2` 235/206. SHALL NOT retune.
- S-RP-03: Prefixes SHALL be reused from one max mother per layer/width
  (`H[:k]` construction-order views). Per-`f` mother reconstruction, seed
  search, row reordering, and decoder-guided graph change SHALL NOT exist.
- S-RP-04: Layer order SHALL be L1-then-L2 per block (`q=softmax(L1 beliefs)`,
  `prior_l2=q@P`); L2 SHALL always be attempted. Oracle L2
  (`true-U1` prior) SHALL be diagnostic only and SHALL NOT gate PASS.

## S-STAGE (builders)

- S-ST-01: Stage builders SHALL reuse `build_dv3_nested_mother` with fixed
  graph seeds L1 `2026090501` / L2 `2026090502`: P0/G1 `(n=64, k_min 59/52)`,
  G2 `(n=256, k_min 235/206)`. `N=1024` mothers SHALL NOT be built here.
- S-ST-02: Blocks/seeds/calls SHALL be frozen: P0 2 blocks
  (`2026090510, 2026090511`), 12 calls; G1 100 paired `f={1.0,1.2}`, 440
  calls, oracle first-20 same-seed; G2 200 paired `f={1.0,1.1,1.2}`, 1320
  calls, oracle first-40 same-seed. Running order SHALL be seed order.
- S-ST-03: Decoder on the authorized path SHALL be the historical GF32
  `decode_row_layered_fftqspa` adapter with `max_iter=90`,
  `damping_alpha=1.0`, `warm_beliefs=None`. `decode_fn=None` SHALL refuse.
  Fake decoders SHALL exist only as test-injected callables.
- S-ST-04: Metric SHALL be named `exact_failure_fraction`
  (`1-exact_count/attempted_blocks`, synthetic block error fraction). It
  SHALL NOT be called FER and SHALL NOT be extrapolated to real frames.
- S-ST-05: Budgets SHALL be unchanged (single call 120 s; G1 ≤900 s; G2
  ≤3600 s; RSS <2 GiB; G2 `projected>3600s` is `RESOURCE_PROJECTION_BLOCKED`).
  Tag SHALL NOT be generated or counted.

## S-PRIOR-PREP (model-F input)

- S-PP-01: One explicit prep function SHALL be the sole P0/G1/G2 `(p_b, p_f)`
  source. It SHALL reuse `build_f_model` with `lambda*=137.3823795883264` and
  the accepted axis contract (`counts/P_F (Alice,Bob)`, `axis0=Alice`,
  `P_F.sum(axis=0)==1`, `P1 (32,B)`, `P2 (U1,B,U2)` over-U2 normalized,
  probability-domain transfer, floors `1e-300`/`1e-15` renormalized,
  zero-mass `(U1,B)` -> uniform `1/32`).
- S-PP-02: The prep function SHALL take injected inputs only. It SHALL NOT
  read CAL/VAL/parquet/raw/registry, SHALL NOT use `build_g0_fixture` output
  for P0/G1/G2, and SHALL NOT invent a replacement distribution.
- S-PP-03: With the accepted CAL-TRAIN counts input absent (current state),
  it SHALL stop as `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` before
  any construction/decode/write, naming exactly the D4R2 F-model CAL-TRAIN
  canonical counts `(1024,1024)` + `P(B)` marginal on `CAL702..1725` TRAIN.
  No other missing-input decision SHALL be emitted for this cause.

## S-CLI (reachability, still gated)

- S-CLI-01: Existing commands `python
  scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost|g1|g2` SHALL reach the
  stage builders. `--phase` SHALL stay required; no frozen-param override flag
  SHALL be added.
- S-CLI-02: Every phase SHALL check `is_phase_authorized` before any
  builder/decoder/writer work and refuse (exit 3) while its key
  (`p0_cost/g1/g2_execution_authorized`) is false. Unauthorized entry SHALL
  create no files/dirs and import no decoder.

## S-WRITE (four-file, no-overwrite)

- S-WR-01: Roots SHALL be `workspace/v72p2d5_p0_cost/20260906_r1/`,
  `workspace/v72p2d5_g1/20260906_r1/`,
  `workspace/v72p2d5_g2/20260906_r1/`, each with exactly `results.json`,
  `table.csv`, `report.md`, `execution_summary.json`.
- S-WR-02: An existing root SHALL raise `FileExistsError` before any write.
  Payloads SHALL be scalar-only (design §7 surface); mothers, supports,
  coefficients, priors, syndromes, raw symbols, beliefs, absolute paths,
  hashes/checksums/tags/signatures SHALL NOT be written.

## S-GRADE (G2)

- S-GR-01: G2 SHALL grade APP-fed end-to-end exact only:
  `>=90%@1.2`+monotonic `G2_SYNTHETIC_QUALIFIED`; `50-90%`
  `G2_INCONCLUSIVE`; `<50%` `G2_CURRENT_CONFIGURATION_FAILED`;
  crash/nonfinite/math-inconsistent `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`.
- S-GR-02: Monotonicity SHALL be raw inequality
  `exact_rate(1.2)>=exact_rate(1.1)>=exact_rate(1.0)` (G1 two-point form).
  `oracle<APP` SHALL be `ORACLE_APP_NONMONOTONIC_DIAGNOSTIC`, not failure.

## S-STOP (boundaries)

- S-SP-01: This change SHALL NOT execute P0/G1/G2, grant authorization,
  read CAL/VAL/raw/real data in code or tests, create formal output, or modify
  `cycle_state.yaml` authorizations.
- S-SP-02: It SHALL NOT add a generic sweep framework, `IRRunResult` adapter,
  concurrency/resume/retry, hashes/manifests/versioning, YAML grids, alternate
  families, or `max_iter`/damping/seed tuning.
- S-SP-03: STRUCTURE/G0/G0-recovery behavior SHALL be regression-preserved;
  frozen experiments, seeds, tables, budgets, calls, and naming SHALL NOT
  change.

## S-TEST-ISOLATION (test-only isolation, lifecycle-independent)

- TS01 lifecycle-independent: tests SHALL NOT depend on real formal-root existence/absence; missing-isolation SHALL use monkeypatched absent tmp; existing-preservation SHALL use local `(size,mtime_ns)` snapshot, no hash/copy.
- TS02 no implicit prod decoder: every authorized test-only synthetic call SHALL pass explicit `decode_fn` (fake); authorized `True` reaching default `bind_historical_decoder` SHALL fail.
- TS03 tmp-only: every authorized test-only synthetic call SHALL pass explicit `out_dir` under `tmp_path`; reaching a formal out_dir SHALL fail.
- TS04 injected Model-F: every authorized test-only synthetic call SHALL pass explicit `counts_ab`/`p_b` (fake Model-F); loading the real formal root in tests SHALL fail except documented missing-isolation with booms.
- TS05 missing-isolation via monkeypatch tmp: BLOCKED-path tests SHALL monkeypatch the formal root/loader to absent tmp (or exact BLOCKED error), with binder+writer booms, expecting `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` with decoder/writer 0 and tmp empty.
- TS06 existing-preservation snapshot: tests SHALL snapshot Model-F/G0/G1 `(size,mtime_ns)` before/after and assert unchanged; SHALL NOT write/delete/move/rename/copy/normalize/hash formal artifacts; P0/G2 SHALL remain absent; no new formal root SHALL be created.
- TS07 future-neutrality: tests SHALL NOT assert real Model-F/G1 absence (and SHALL NOT invert to assert exists); SHALL observe G1 existence only to prove unchanged, with no validity/acceptance/qualification/promotion/perf/G2-auth claim.
- TS08 fake counts test-only: fake Model-F counts SHALL be test-only injected tables, never written to formal roots, never claimed as CAL-TRAIN.
- TS09 incident label: the 20260907 unauthorized G1 test execution SHALL be labeled `INVALID_UNAUTHORIZED_TEST_TRIGGERED`; SHALL NOT be accepted/qualified/promoted, SHALL NOT support G1-perf or G2-auth, SHALL be preserved pending disposition with no delete/hash/copy.
- TS10 collection safety static check: a stdlib AST test SHALL fail if any authorized `True` synthetic call can reach the default decoder/formal out_dir without explicit `decode_fn`/`out_dir`/counts; documented fail-before-decoder exceptions (missing-isolation with booms) SHALL be listed; no CLI authorized phase SHALL appear in tests; no `cycle_state` mutation SHALL appear in tests.
