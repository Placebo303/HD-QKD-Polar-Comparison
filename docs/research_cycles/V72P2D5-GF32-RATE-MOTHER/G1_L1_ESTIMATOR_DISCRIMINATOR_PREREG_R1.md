# G1 L1 estimator discriminator preregistration R1

- repo: `HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`
- basis: R2 acceptance `G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`
  (terminal `LAMBDA_APPLICATION_CONTRACT_DEFECT`; C1 L1 truth mass `0.096`
  fails everywhere including square — binding constraint).
- status: `PREREGISTERED / EXPERIMENTS_NOT_STARTED`. This file was written
  from source code and already-persisted R2 evidence only. No new CAL score
  was read and no new decoder call was run before this commit.

## 1. Question

Whether any honest CAL-only estimator lifts L1 truth mass past this
decoder's n=64 threshold at ≤64 rows, or L1-at-64 is below the BP threshold
regardless of estimator — and if the latter, whether block-length scaling
(not post-hoc smoothing) restores a nonzero-rate signal.

## 2. Frozen data contract (CAL-TRAIN only, no VAL)

- Parquet:
  `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet`,
  columns `frame_id/alice_symbol/bob_symbol`, filter `702 <= frame_id <= 1725`.
- Assert `262144` rows; set `val_touched=false`. VAL frames are never read
  and never used for selection or confirmation.
- Frozen outer folds (frame-blocked, TRAIN768/TEST256):
  F0 TEST `702..957`, F1 TEST `958..1213`, F2 TEST `1214..1469`,
  F3 TEST `1470..1725` (each TEST `256*256` symbols, TRAIN `768*256`).
- Mapping: `symbol = low + 32*high`, `U1 = high = (a>>5)&31`,
  `U2 = low = a&31`; `Q=1024`, `QS=32`.
- Floors: audit `AUDIT_FLOOR=1e-300`, decoder `DECODER_FLOOR=1e-15`.

## 3. Estimator candidates (at most three, §5 contracts)

- E1 baseline: accepted joint-F concentration backoff at frozen
  `lam*=137.3823795883264`, marginalized to L1 via `marginalize_f_to_p1`.
  No selection.
- E2 direct: aggregated `counts_L1[B,U1]` (sum over U2 first),
  `P(u1|b) = (counts_L1 + kap * p1_global) / (n_b + kap)`, with `kap`
  selected on held-out L1 NLL over grid30 `logspace(-2,3)` on the same 4
  outer folds. Same unit as `lam*` (total concentration per Bob column;
  column count unchanged by Alice aggregation), hence the same grid.
- E3 hierarchical anchor: same aggregated statistic as E2 but frozen
  `kap=lam*` (no selection) — the W4a-C3 `P1[B,U1]` component, justified by
  the chain factorization `P(A|B)=P(U1|B)·P(U2|U1,B)` and existing R2 math.
  E2-vs-E3 isolates the selection axis; E1-vs-E3 isolates the
  sufficient-statistic axis.
- Known statistic difference (recorded, not subtracted): E1 smooths full
  `1024×1024` joint counts then marginalizes (L1 borrows strength through
  joint backoff); E2/E3 aggregate to `1024×32` first (L1-local smoothing).
  Same population, different sufficient statistics.

## 4. Primary endpoint and selection (CAL-only, 0 calls)

- Primary: mean held-out CAL L1 NLL over the 4 frozen outer folds
  (TEST256 each, `AUDIT_FLOOR`).
- Select by lowest mean only. Tie-break: if `|Δmean| < 0.01` bits, prefer
  the frozen-strength estimator (E1, then E3) over selected E2.
- Report per estimator: effective concentration + prior fraction, support
  (column min/max/mean), in-sample channel CE (L1/L2/joint), model-sampled
  truth mass (4 paired seeds, labeled resub diagnostic), L1 MI.
- Decoder success is evaluation, never the selection objective. Estimator
  choice is frozen before any new decoder call; interim decoder results
  never reselect the estimator.

## 5. Paired decoder harness (fixed within comparisons)

- Core: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`.
- Decoder: `bind_historical_decoder()` (historical GF32, cold,
  `max_iter=90`, damping `1.0`).
- Mothers: L1 family `build_dv3_nested_mother(64,59,59,2026090501,None)`;
  square `build_dv3_nested_mother(64,64,64,2026090801,None)` (rank 64).
- L1 APP call per (estimator, disclosure, seed): prior
  `_floor_renorm(p1_est[:,bob].T, 1e-15)`, syndrome of true `u1`,
  blocks `sample_matched_block(pb, pf_est_law, 64, seed)` under the
  estimator's own law with identical seeds across estimators (paired).
- Block seeds: `2026090600..0603` (4 per point). One axis changes per
  control (estimator, disclosure, or block length — never two).
- Endpoints per call: exact (recomputed `array_equal` vs truth), syndrome
  (recomputed via `_gf32_syndrome(x_hat)` vs given syndrome, plus the
  decoder flag; disagreement flagged), iterations, nonfinite
  (`final_beliefs`), wall_s, rss_bytes. Recovery requires recomputed exact
  AND recomputed syndrome agreement; the decoder flag is recorded, not
  decisive.

## 6. Disclosure frontier (sparse bracket, not a scan)

- n=64 L1 points: `H1[:49]` (frozen f=1.0 anchor), `H1[:59]` (frozen f=1.2
  anchor), `Hsq[:64]` (square). 3 points × 4 seeds × ≤2 estimators.
- Decoder estimator set: `{winner, E1}`; if the winner is E1, `{E1, E2}`
  (runner-up contrast).
- Useful-n64 rule: recovery must occur at `m<64` (nonzero rate). `m=64`
  is zero-rate and never counts as recovery.
- Recovery bar per point: `≥3/4` exact AND `≥3/4` recomputed-syndrome at
  the same `m<64` point with flag agreement. `0–1/4` = fail. `2/4` =
  ambiguous → the single named MIXED test (§9).

## 7. Block-scaling arm (conditional, development-only)

- Trigger: only if n=64 fails (every tested honest estimator `≤1/4` at
  every `m<64` point, after resolving any `2/4` via §9).
- Order `n=128` then `n=256`; stop at the first width with nonzero-rate
  recovery (never run 256 if 128 recovers). These are development-only
  diagnostics: never called G2; no formal G2 seeds, thresholds, roots, or
  authorization role.
- Mothers per width `n`: square `build_dv3_nested_mother(n,n,n,2026090801,None)`;
  L1 family `build_dv3_nested_mother(n,m_hi,m_hi,2026090501,None)` with
  `m_hi` = top disclosure rows below. Same decoder/max_iter/floors.
- Disclosure (rate-matched to §6 anchors): `{⌈n·49/64⌉, ⌈n·59/64⌉, n}`,
  i.e. n128 `{98,118,128}`, n256 `{196,236,256}`. Same 4 block seeds;
  same ≤2-estimator set; S0 delta-prior sanity (1 call, `rng(2026090701)`
  pattern) per width.
- Fail-closed: any mother-build/audit failure → that arm `NOT_ATTEMPTED`
  with reason; no improvisation, no alternate construction.

## 8. Budgets and workspace

- `≤8h` operator wall, `≤1500` decoder calls, `120s` watchdog per call,
  peak RSS `<2GiB`. Estimate: n64 `1 + 2·3·4 = 25` calls; each scaling arm `1 + ≤2·3·4 ≤ 25`
  calls; MIXED extension ≤8. Expected total `<90` calls.
- All output under one unique
  `workspace/d5_g1_l1_discriminator_r1_<uuid>/`: scripts, command log,
  manifest, compact scalar JSONs. No raw rows, symbols, beliefs, or
  per-block payload dumps.
- Adaptive stop: once a terminal class (§9) is unambiguous, stop spending
  calls (in particular, skip scaling arms after recovery, and skip decoder
  arms entirely under CAL-insufficiency).

## 9. Stop rules and terminal classes (exactly one)

- `L1_ESTIMATOR_CONTRACT_RECOVERABLE_AT_N64`: held-out winner recovers at
  `m<64` per §6 bar with reproducible paired signal → additive
  layered-prior candidate for independent review.
- `BLOCK_LENGTH_SCALING_RECOVERS_L1`: n64 fails per §7 trigger but a larger
  development block recovers at a nonzero-rate disclosure → block-geometry
  successor proposal; G2 not started.
- `L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64`: CAL-info-present (below) yet
  honest estimators fail through square disclosure at n64, and scaling arms
  fail (or are fail-closed) → D5 route-stop with n64-stop content.
- `CAL_L1_INFORMATION_INSUFFICIENT`: winner meanNLL within `2×SE` (across 4
  folds) of uniform chance `5.0` bits, i.e. NOT `(5.0 − mean > 2·SE)` →
  decoder arms skipped, D5 route-stop proposal.
- `MIXED_OR_UNRESOLVED_L1_CAUSE`: only with the one named irreducible next
  test — repeat the ambiguous `2/4` (estimator, disclosure) point with 4
  additional paired seeds `2026090604..0607`; combined `≥6/8`
  exact+syndrome upgrades that point to recovered, else it stands failed
  and the procedure continues. (If winner-only recovery occurs while the
  held-out winner fails, the same extension applies to the recovering
  estimator's point before claiming recoverability.)
- Final-gate mapping: recoverable → `INDEPENDENT_G1_L1_ESTIMATOR_REVIEW`;
  block-scaling → `G1_BLOCK_GEOMETRY_ROUTE_REVIEW`; either stop class →
  `D5_ROUTE_STOP_REVIEW`; unresolved → `G1_L1_ROUTE_DECISION`.

## 10. Prohibitions

No VAL read/use; no formal G1 rerun/resume or CLI `--phase`; no G2/n1024
formal run, real IR, or Release; no formal-root write/hash/move/rename;
no VOID read; no seed search, unconstrained sweep, model zoo, or
decoder-success estimator selection; no frozen `src/experiments/tools`
modification; no new dependency/framework/infrastructure; no push.
