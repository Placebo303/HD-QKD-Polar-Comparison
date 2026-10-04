# Tasks: V72P2D5 P0/G1/G2 production path (coder-fast, candidate only)

Frozen packet: P0 -> G1 -> G2 order; no execution/authorization; no
CAL/VAL/raw read; focused tests only. Implement exactly what is specified;
if any task is ambiguous, stop and return to planner (do not guess).
Allowlist: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
`scripts/v72p2d5_gf32_rate_mother.py`,
`comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (additive cases
only). No other code/test file. No `cycle_state.yaml` auth change. No formal
output creation.

- [x] T1 — Prefix-slice fix in rate path
  - In `_run_rate_scan` (and the `f` loop of `run_p0_cost_phase`), slice per
    `f`: `H1_f=H1_mother[:m1(f)]`, `H2_f=H2_mother[:m2(f)]` from the SAME
    passed-in mothers before any decode call for that `f`.
  - `m1(f)/m2(f)` from the frozen formula `ceil(n*CE*f/5)` with
    `CE_L1=3.814742`, `CE_L2_oracle=3.347605` (tables in design §3).
  - Preserve L1-then-L2 order, oracle-subset pairing, `exact_failure_fraction`
    naming, G2 four-state grading. No generic sweep, no tuning.
  - Verify: focused test shows different `f` decode with different row counts.

- [x] T2 — Stage builders reusing `build_dv3_nested_mother`
  - One max mother per layer per width (P0/G1 `n=64` with `k_min` 59/52; G2
    `n=256` with `k_min` 235/206), graph seeds `2026090501`/`2026090502`,
    prefixes reused across `f` per design §2-§3.
  - Builders take injected `(p_b, p_f)` + `decode_fn` (same pattern as
    `run_g*_phase`); no data-file read; no seed search; no per-`f` rebuild.
  - Preserve frozen blocks/seeds/calls: P0 2 blocks (`G0_SEEDS[:2]`), 12
    calls; G1 100 paired `f={1.0,1.2}`, 440 calls; G2 200 paired
    `f={1.0,1.1,1.2}`, 1320 calls; APP L1-then-L2; oracle first-20/40
    diagnostic only.
  - Verify: prefixes come from the same mother object (identity/prefix test).

- [x] T3 — Historical decoder connection (frozen config)
  - Authorized path uses historical `decode_row_layered_fftqspa` adapter with
    `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None` (bind-once reuse
    pattern where applicable); `decode_fn=None` refuses; fake only via test
    injection.
  - Verify: adapter kwargs asserted; unauthorized path loads no decoder.

- [x] T4 — Single model-F prep function with BLOCKED path
  - Add one explicit `prepare_model_f_prior(...)` reusing `build_f_model` and
    accepted axis semantics (design §5). Injected inputs only. No VAL read.
    No `build_g0_fixture` reuse for P0/G1/G2. No invented distribution.
  - Missing accepted CAL-TRAIN counts input MUST yield single-decision
    `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` (style may match existing
    `*_BLOCKED`) before construction/decode/write, naming exactly the D4R2
    F-model CAL-TRAIN canonical counts `(1024,1024)` + `P(B)` marginal.
  - Verify: BLOCKED on absent input; no VAL/G0-toy path exists (source assert).

- [x] T5 — CLI `p0-cost` / `g1` / `g2` production-reachable (still gated)
  - Wire the three existing `--phase` values to the stage builders + writers
    with frozen seeds/roots; keep `--phase` required, no new flags, keep
    `is_phase_authorized` pre-check (exit 3, no side effects while false).
  - Verify: authorized-spy reaches builder with frozen args; unauthorized
    creates nothing and loads no decoder.

- [x] T6 — Four-file writers (no-overwrite)
  - One writer per root: `workspace/v72p2d5_p0_cost/20260906_r1/`,
    `workspace/v72p2d5_g1/20260906_r1/`,
    `workspace/v72p2d5_g2/20260906_r1/`; files exactly `results.json`,
    `table.csv`, `report.md`, `execution_summary.json`; existing root raises
    `FileExistsError`; scalar-only payloads (design §7); no hash/tag/path.
  - Verify: four files on tmp root; second write refuses; formal roots absent
    after tests.

- [x] T7 — Frozen-experiment preservation
  - Keep P0 cost-projection shape (APP+oracle, wall/iterations/RSS,
    `projected_g1/g2_s`, `projection_blocked`), G1 trend gate (monotonic +
    zero crash/nonfinite), G2 sole grading experiment (four states, PASS only
    APP-fed), `exact_failure_fraction` naming (never FER), oracle diagnostic
    9-field reporting pattern where already present.
  - Verify: existing frozen-row asserts (`49/43`, `235/206`) and grade asserts
    still hold.

- [x] T8 — Focused tests (single test file, additive only)
  - Extend `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` only:
    (a) different-`f`-different-prefix-rows; (b) prefixes-from-same-mother;
    (c) APP L1-then-L2 call order/shape; (d) frozen call counts (12/440/1320)
    and seeds; (e) authorization refusal before builder/decoder/write;
    (f) no VAL/real-data access (source + no-file-creation asserts mirroring
    `T0_38`/`T1_12`/`T1_14`); (g) four-file no-overwrite per new root;
    (h) G2 four-state grading incl. `STRUCTURE`-style monotonic + nonfinite
    BLOCKED; (i) G0/recovery/structure regression unchanged.
  - Constraints: injected fakes/tiny tables only; no CAL/VAL/raw read; no
    formal-root creation; no production decoder import on fake paths.

- [x] T-ISOL — Lifecycle-independent test containment (additive, no T1-T9 rewrite)
  - T-ISOL-01 — Unauthorized choke (SAFE A): `authorized=False` synthetic calls raise before builder/loader/decoder/writer/files. Mapped: `test_M19_d5_unauthorized_artifact_zero`, `test_P0G1G2_e_authorization_refuses_before_work`.
  - T-ISOL-02 — Authorized fake tmp (SAFE B): `authorized=True` non-BLOCKED calls pass explicit injected `counts_ab`+`p_b` + fake `decode_fn` + tmp `out_dir`. Mapped: `test_M20_d5_authorized_fake_load_reaches_runner` (440 calls, tmp only).
  - T-ISOL-03 — Missing isolation fail-before (SAFE C): `authorized=True` without injected tables only under monkeypatched absent `MODEL_F_INPUT_FORMAL_ROOT` + `bind_historical_decoder` boom + writer boom(s), expecting `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`, zero binder/writer entries, tmp empty, real Model-F/G1 snapshots unchanged. Mapped: `test_M21_d5_missing_artifact_blocked_no_toy` (P0/G1/G2 loop, 1 physical / 3 logical).
  - T-ISOL-04 — Ex-unsafe G1 documented: `test_P0G1G2_i_g0_recovery_structure_regression` keeps G0/recovery/structure asserts + one documented isolated G1 missing-isolation call (same SAFE C markers); no other bare `authorized=True`.
  - T-ISOL-05 — Static guard: `test_TIS_static_authorized_synthetic_isolation` (stdlib AST only) enforces SAFE A/B/C over direct `mod.run_*`, `runner=getattr(mod,name)`, loop-var `fn`, parametrized `runner_name`; fail-before exceptions allowlisted only with boom+BLOCKED+absent-tmp markers.
  - T-ISOL-06 — Lifecycle snapshots: `test_M24_formal_roots_absent` + `test_P12_formal_roots_absent` + G1/P0/G2 snapshot asserts in M19/M20/M21/P0G1G2_f/g/i prove tmp-only, P0/G2 absent, Model-F/G0/G1 unchanged; no global formal-root absence assert.
  - T-ISOL-07 — No CLI auth exec / no cycle write: no `--execution-authorized` literal, no `*_execution_authorized": True`, no `STATE_PATH` write / `yaml.dump`, CLI unauthorized exit 3 only.
  - T-ISOL-08 — New parametrized missing isolation: `test_M21_param_missing_isolation` parametrized over `(runner_name,writer_name)` P0/G1/G2 pairs (1 physical definition / 3 logical variants), same SAFE C markers per pair, real roots unchanged.
  - T-ISOL-09 — No prod/formal reachability: binder boom zero, writer boom zero, no `bind_historical_decoder` entry, no formal `out_dir` default, no new formal output, no prod decoder import on fake paths.
  - T-ISOL-10 — Gates+evidence: G01-G09 pre-pytest gate, focused+combined pytest literals, `TEST_ISOLATION_REWORK_EVIDENCE_R1.md` durable record, incident stays `INVALID_UNAUTHORIZED_TEST_TRIGGERED` unaccepted/unmoved.

- [x] T9 — Compile + focused suite
  - `py_compile` on both touched `.py` files clean; run only the focused test
    file (`pytest -p no:cacheprovider` on Windows if ACL issues arise, fresh
    additive `workspace/<task>/<uuid>` tmp root where needed); confirm no
    formal output created and `*_execution_authorized` paths still refuse.
  - Do NOT run P0/G1/G2 production, long runs, or any real-data benchmark.
