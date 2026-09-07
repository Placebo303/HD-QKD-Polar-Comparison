# Design: V72P2D5 P0/G1/G2 production path

Status: `IMPLEMENTATION_CANDIDATE_ONLY`. No execution, no authorization, no
CAL/VAL/raw read, no formal output. All constants below are frozen from the
accepted R2_DV3 plan and current core/tests; this change invents none.

## 1. Dataflow (the defect fix)

```text
f -> (m1(f), m2(f)) -> H1_f = H1_mother[:m1(f)], H2_f = H2_mother[:m2(f)]
  -> L1 decode(H1_f, P1 prior) -> q = softmax(L1 beliefs)
  -> L2 prior = q @ P -> L2 decode(H2_f, L2 prior) -> APP exact
  -> (diagnostic only) oracle L2 decode(H2_f, true-U1 prior)
```

- `_run_rate_scan` MUST slice per `f` inside the `f` loop before any
  `_run_layered_block` / `_decode_block` call. Slicing after decoding, or
  reporting `frozen_rows` without slicing, is the filed defect and stays
  forbidden.
- `run_p0_cost_phase` MUST apply the same per-`f` slicing (it currently ignores
  `f` for matrix shape). Cost records remain wall/iterations/RSS only.
- Prefixes are views `H[:k]` in construction order (natural order = build
  order). No row reordering, no `order_rows_for_prefix_coverage`, no decoder-
  driven reordering (already absent; stays absent).
- L1-then-L2 order is frozen (`_run_layered_block` semantics): L1 APP `q`
  always feeds L2; L2 is always attempted even if L1 fails.

## 2. Mother-prefix reuse

- Reuse `build_dv3_nested_mother(n, m_max, k_min, seed, field=None)` unchanged.
- One max mother per layer per stage width:
  - P0/G1 width 64: `H1_max` built with `(n=64, k_min=m1(f=1.2)=59)`,
    `H2_max` with `(n=64, k_min=m2(f=1.2)=52)`, seeds L1 `2026090501` /
    L2 `2026090502`. Prefixes `m1 in {49, 59}`, `m2 in {43, 52}` reused
    across `f`. (Builder `k_min` takes the stage max so the earliest prefix
    still satisfies the degree>=2 construction contract; disclosure `k` values
    are exactly the frozen tables in §3.)
  - G2 width 256: `H1_max` with `(n=256, k_min=235)`, `H2_max` with
    `(n=256, k_min=206)`, same two graph seeds. Prefixes per §3 reused
    across `f`.
  - N=1024 mothers (`M_MAX=1000`, `k_min` 782/686) are NOT built here; no
    full-mother construction in this change.
- Fixed graph seeds only (`2026090501` / `2026090502`). No seed search, no
  per-`f` reconstruction, no support追 rank, no decoder-guided graph change.
- `n=64/256` use the same dv3 construction contract (2 base + 1 expansion,
  column-degree 3, GF32 `1..31`, deterministic greedy) scaled to stage width;
  row counts follow §3 via the frozen formula `rows=ceil(n*CE*f/5)`.

## 3. Stage builder params (frozen)

| Stage | Width | f set | m1 table | m2 table | Block seeds | Calls (frozen) |
|---|---|---|---|---|---|---|
| P0 cost | 64 | {1.0, 1.2} | {49, 59} | {43, 52} | 2 blocks: `G0_SEEDS[:2]` = 2026090510, 2026090511 | 12 (APP 2/block + oracle 1/block) |
| G1 trend | 64 | {1.0, 1.2} | {49, 59} | {43, 52} | 100 paired: `G1_SEEDS` 2026090600..0699 | 440 (APP 100x2x2 + oracle 20x2x1) |
| G2 grade | 256 | {1.0, 1.1, 1.2} | {196, 215, 235} | {172, 189, 206} | 200 paired: `G2_SEEDS` 2026091000..1199 | 1320 (APP 200x3x2 + oracle 40x3x1) |

- Row tables verified: `ceil(n*CE_L1*f/5)` with `CE_L1=3.814742`,
  `ceil(n*CE_L2*f/5)` with `CE_L2_oracle=3.347605`
  (matches `PLAN_FREEZE.md` §2 scaled + `test_T1_11` / `TR7` asserts).
- P0 seeds freeze the current implementation (`G0_SEEDS[:2]`); G1/G2 seeds are
  the frozen 100/200 ranges. Running order is seed order; no retry, no
  substitution, no search. Oracle subsets are the first 20 (G1) / 40 (G2)
  same-seed paired blocks, diagnostic only.
- Budgets unchanged: single call 120 s, G1 total ≤900 s, G2 total ≤3600 s,
  peak RSS <2 GiB; G2 `projected>3600s` from P0 is
  `RESOURCE_PROJECTION_BLOCKED`. Tag never generated/counted.
- Metric naming: `exact_failure_fraction=1-exact_count/attempted_blocks`
  (synthetic block error fraction). Never call it real FER; never extrapolate
  to real frames.
- G2 grading (APP-fed end-to-end exact only): `>=90%@1.2` + monotonic
  `G2_SYNTHETIC_QUALIFIED`; `50-90%` `G2_INCONCLUSIVE`; `<50%`
  `G2_CURRENT_CONFIGURATION_FAILED`; crash/nonfinite/math-inconsistent
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`. Monotonicity is raw
  `exact_rate(1.2)>=exact_rate(1.1)>=exact_rate(1.0)` (G1: two-point form).
  Oracle never gates PASS; `oracle<APP` is `ORACLE_APP_NONMONOTONIC_DIAGNOSTIC`,
  not failure.

## 4. Decoder connection (frozen)

- Historical entrypoint `decode_row_layered_fftqspa` via the existing thin
  adapters (`historical_g0_decoder` / G0-recovery bind-once pattern):
  `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None` (cold start).
- Authorized production path binds the historical decoder once and reuses the
  bound adapter for all seeds/blocks of the phase (recovery pattern); ordinary
  G0 per-seed loader behavior is unchanged and not copied.
- `decode_fn=None` refuses; unauthorized phases refuse before any
  construction, loader import, decode, or write. Fake decoders exist only as
  test-injected callables; the authorized path never uses a fake.
- No `max_iter`/damping/seed tuning in this change.

## 5. Model-F preparation function (single, frozen, BLOCKED path)

- One explicit function, e.g. `prepare_model_f_prior(...)`, is the sole place
  that turns accepted model-F input into `(p_b, p_f)` for P0/G1/G2:
  - Reuses `build_f_model(counts_ab, lam=LAMBDA_STAR)` with
    `LAMBDA_STAR=137.3823795883264` (column-wise smoothing, then
    `axis0=Alice` normalization).
  - Preserves accepted axis semantics: `counts.shape=(Alice,Bob)`,
    `P_F.shape=(Alice,Bob)`, `axis0=Alice`, `axis1=Bob`,
    `assert_allclose(P_F.sum(axis=0),1.0)`; `P1=P_F.reshape(32,32,B).sum(axis=1)`
    shape `(32,B)`, `P1.sum(axis=0)==1`; `P2` shape `(U1,B,U2)` normalized over
    U2; probability-domain transfer; `log2` for CE only; audit floor `1e-300`
    vs decoder floor `1e-15` (both renormalized); zero-mass `(U1,B)` slice
    falls back to uniform `1/32` without dropping samples.
  - Takes injected tables only (same injection pattern as `run_g*_phase`).
    It MUST NOT read CAL/VAL/parquet/raw/registry, MUST NOT import a data
    loader, MUST NOT use the G0 toy fixture (`build_g0_fixture` 2x8 table) for
    P0/G1/G2, and MUST NOT invent a replacement distribution (no uniform /
    random / synthetic-contrast fallback).
  - Verdict for this change: **BLOCKED**. The accepted model-F input (D4R2 F
    outer-mean table with `CE_L1=3.814742 / CE_L2_oracle=3.347605`,
    `lambda*` above) has no committed in-repo artifact reconstructible without
    CAL access. The single missing input is the **D4R2 F-model CAL-TRAIN
    canonical counts `(1024,1024)` + `P(B)` marginal on frozen `CAL702..1725`
    TRAIN** (the TRAIN counts that `build_f_model` smooths). Without reading
    CAL, the prep function MUST return/raise
    `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` (naming may adjust to
    existing `*_BLOCKED` style) before any construction/decode/write, naming
    exactly that missing input and no other. Tests assert the BLOCKED path
    with injected `None`/absent input and assert no VAL read and no G0-toy
    reuse.
- No CAL/VAL/raw read is added anywhere to satisfy the prep function in this
  round. A future change that commits or authorizes the CAL-TRAIN counts would
  revisit this verdict through a new OpenSpec revision; this change does not.

## 6. CLI phases (existing commands, production-reachable)

- Keep `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost|g1|g2`
  with `--phase` required and no frozen-param overrides (no `--seed`,
  `--degree`, `--family`, `--k_min`, `--m_max`, `--retry`, `--real`,
  `--run_01`, `--VAL`, `--all`).
- Each phase checks `is_phase_authorized(state, phase)` first (single choke,
  keys `p0_cost_execution_authorized` / `g1_execution_authorized` /
  `g2_execution_authorized`, all false today) and refuses with exit 3 before
  any builder/decoder/writer work.
- Authorized path calls the stage builder with frozen seeds/root and the
  historical decoder adapter, then the stage four-file writer. Unauthorized
  path creates no directories/files and imports no decoder.

## 7. Four-file writers (explicit, no-overwrite)

- One writer per stage root (names mirror `write_g0_evidence` /
  `write_structure_evidence` scalar-only pattern):
  - `workspace/v72p2d5_p0_cost/20260906_r1/`
  - `workspace/v72p2d5_g1/20260906_r1/`
  - `workspace/v72p2d5_g2/20260906_r1/`
- Each writes exactly `results.json`, `table.csv`, `report.md`,
  `execution_summary.json`, then returns. If the root exists, raise
  `FileExistsError` before writing anything (refuse overwrite/merge).
- Scalar-only payloads: seeds, per-`f` exact counts/rates/failure fractions,
  frozen row tables, monotonic flag, G2 grade, decoder call counts, wall/RSS,
  oracle-diagnostic counters, decisions. Never write mothers, supports,
  coefficients, priors, syndromes, raw symbols, beliefs/messages, absolute
  paths, hashes/checksums/tags/signatures.
- `table.csv` columns and JSON keys for the new writers are new surface (no
  schema-stability conflict with G0/structure writers, which stay unchanged).

## 8. Authorization gate

- `is_phase_authorized` remains the single choke; unknown phases deny.
- This change grants no authorization (`*_execution_authorized` stay false;
  `decoder_executed`, `cal_rows_read`, `val_rows_read` unchanged by
  implementation/tests). Pre-EXECUTE / Pre-RESULT gates still apply to any
  future execution/solidification and are out of scope here.

## 9. Explicitly not in design

Generic sweep loops, YAML grids, `IRRunResult` mapping, concurrency, resume,
retry, watchdogs beyond the documented outer-process note, versioning,
hash/manifest/tag fields, alternate families (V31/V35/V36/V38/Lane-C), and any
tuning of `max_iter`/damping/seeds/graph degree.
