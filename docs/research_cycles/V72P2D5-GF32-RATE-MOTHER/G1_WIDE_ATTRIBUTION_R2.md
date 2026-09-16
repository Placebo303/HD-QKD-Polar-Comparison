# G1 Wide Attribution R2 — lambda-contract defect with carried disclosure secondary

- Accepted result unchanged: `workspace/v72p2d5_g1/20260907_r2`,
  `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed=false`. This document explains the
  zeros one level deeper than R1; it changes no formal value, threshold, seed,
  authorization, or semantic. No formal rerun, no G2, no VAL use.
- Method: direct injected-function development diagnostics (`n=64`, accepted
  Model-F NPZ read-only, frozen mothers/decoder, one changed axis per
  control) + CAL-only estimator recomputation. No CLI `--phase`, no
  formal-root write, no VOID read.
- Evidence root (only workspace written):
  `workspace/d5_g1_wide_attribution_r2_5c38a20ae60b41ceb0b6a0d7757aa2aa/`
  (manifest, 7 scripts, scalar JSONs, discrepancy CSV, command log).
- Terminal class: **`LAMBDA_APPLICATION_CONTRACT_DEFECT`** (supersedes R1's
  `FINITE_LENGTH_DISCLOSURE_INSUFFICIENT` as primary; R1's bucket is carried
  as the downstream secondary, explicitly below).

## 1. Formulas

- D4R2-F estimation (selected): `P(a|b) = (counts[a,b] + lam * p_global[a])
  / (n_b[b] + lam)`, `lam* = 137.3823795883264` total concentration per Bob
  column, `p_global` = full-CAL Alice marginal. Inner 3-fold CV on F joint
  CE over grid30 `logspace(-2, 3)`; all 4 outer folds selected the same value.
- Accepted consumer (`build_f_model`): `sm = counts + lam` cell-wise, then
  column-normalize along `axis0`. Same scalar, applied to 1,048,576 cells:
  `1024 * lam ≈ 140,680` added per column vs `n_b ≈ 256` observed.
- Sizing: `rows = ceil(64 * CE * f / 5)`. Channel CE via `_ce_stats` with
  `AUDIT_FLOOR = 1e-300`; decoder floor `1e-15`.
- Mapping both sides: `symbol = low + 32*high`, `U1 = high`, `U2 = low`.

## 2. Provenance table (see `discrepancy_table.csv` for the full 20-row table)

| Quantity | Value | Source object | Smoothing | Population |
|---|---|---|---|---|
| D4 frozen CE L1/L2/joint | 3.814742 / 3.347605 / 7.162347 | D4R2 audit outer-F TEST means | backoff lam* (inner-CV) | TRAIN768/TEST256 frame-blocked CAL |
| Consumer CE L1/L2/joint | 4.99999 / 4.99966 / 9.99964 | accepted NPZ via `build_f_model` | per-cell lam* | full-CAL refit 262144 |
| Backoff same-counts CE | 4.2867 / 3.2227 / 7.5094 | same NPZ + D4R2 math | backoff lam* | same full-CAL refit |
| MI accepted / backoff | 0.00036 / 2.4831 bits | same tables | per-cell / backoff | same |
| Truth mass accepted / C1 | 0.03124 / 0.25445 | p1 + oracle-p2, seeds ..600..603 | per-cell / backoff | matched blocks n=64 |
| Prior fraction per-cell / backoff | 99.82% / 34.9% | `1024*lam` vs `lam` over `n_b=256` | — | column arithmetic |
| G1 frozen rows | 49/43 @1.0, 59/52 @1.2 | `results.json` == formula recompute | D4 held-out CE | width-64 f grid |

Unlike quantities are labeled, not subtracted: D4 CE (held-out NLL) vs
consumer CE (in-sample channel entropy) share units/domain but differ in
probability object; the like-for-like isolation is same-counts +
same-functional with only the smoothing axis changed (10.0 -> 7.51).

## 3. Controls and frontier (all paired, seeds 2026090600..03)

- W2 square (`m=n=64`, predeclared mother seed 2026090801, rank 64,
  audit STRUCTURE_BLOCKED): S0 delta-prior 1/1 (matrix+decoder sufficient
  with signal); SQ-oracle accepted prior 0/4 at 90 iters (uniform prior
  unrecoverable even at full determination). Frontier accepted:
  H2[:43] 0/4 (R1), H2[:52] 0/4 (R1), Hsq[:64] 0/4 (new). 5 calls.
- W4a calibration (0 calls): held-out joint CE on frozen D4R2 outer folds
  reproduces D4R2 exactly — C1 7.162347, C3 7.343949, C0 9.725388,
  C2 504.67 (catastrophic). Full-counts truth mass: C0 0.031, C1 0.254
  (L1 0.096 / L2-oracle ~0.25), C2 0.496 resub-overfit, C3 0.071.
  lam frozen (no new search, no VAL). Parquet read CAL-filtered (702..1725).
- W4b C1 matrix (16 calls): oracle-L2 frozen H2[:43] 0/4; oracle-L2 square
  4/4 exact+syndrome (3–10 iters); APP frozen 0/4 (L1 fails all 4).
- W4c C1 frontier (16 calls): L1 fails at 49/59/square 0/12 (mass 0.096);
  oracle-L2 at H2[:52] 2/4 (pass mass 0.28, fail mass 0.22–0.24).
- C0 reference reused without repeat calls (R1 F2a/F2b/F3 + W2 square).
  C2 rejected on held-out catastrophe; C3 dominated by C1 on held-out
  (7.34 vs 7.16) and truth mass — no decoder spend justified.

## 4. Calls / resources / CAL-VAL boundary

53/1200 decoder calls (W2 5, W4b 16, W4c 32 incl. one duplicate deterministic
re-run logged in COMMAND_LOG); script+test wall ~51s of 6h; per-call max
~1.5s <= 120s watchdog; peak RSS 240,963,584 B < 2GiB. CAL-TRAIN only
(frames 702..1725); VAL frames never read (parquet filters) and never used
for selection/confirmation; lam selection basis is the frozen D4R2 nested CV.

## 5. Terminal class and causality

**`LAMBDA_APPLICATION_CONTRACT_DEFECT`** — earliest upstream cause
explaining all three phenomena: (a) D4-vs-consumer gap (same counts return
to the D4 family only under backoff); (b) APP+oracle double zero (both paths
share the destroyed prior; oracle bypass does not help because the prior
itself is uniform); (c) C0-vs-C1 square split (0/4 -> 4/4 L2 with only the
prior axis changed). Counterevidence considered: axis mismatch (rejected,
split maxerr 2.2e-16), genuine near-independence (rejected, backoff MI 2.48
bits; D4 F-gain-over-G 2.84 bits), decoder/matrix pathology (rejected as
primary: S0 + F1 pass with signal; rank full everywhere).
Carried secondary: finite-length disclosure inadequacy at n=64 even with the
corrected model — L2 needs 52–64 rows (vs frozen 43), L1 unrecovered at any
disclosure ≤64 with C1 priors (mass 0.096 below the BP threshold).
R1's bucket is thereby superseded as primary and preserved as the downstream
secondary: frozen rows were honestly sized under the D4 estimator, but the
consumer destroyed the information the sizing assumed.

## 6. Implementation (review-ready candidate, additive only)

OpenSpec `openspec/changes/v72p2d5-g1-information-recovery-r2/` (proposal /
design / tasks / specs written before code). Added
`build_f_model_concentration` + `prepare_model_f_prior_candidate` to the
allowed core module; frozen symbols, constants, seeds, thresholds,
authorizations, phases, and accepted artifacts untouched; production phases
keep calling `prepare_model_f_prior`. 8 new tests (defect pin, formula match,
frozen-consumer pin, limits, zero-column fallback, chain-split equivalence,
frozen-lam basis, prepare contract + formal-root isolation) green.
Compile + 8 new + 3-file D5 suite: 226 passed, 1 pre-existing failure
(`test_G1R01_fresh_root_literal_and_old_barred` asserts absence of the
accepted G1 root that has existed since Sept-7 acceptance; fails independent
of this change — stale expectation, out of scope, not modified).
Committed-path diagnostics on the accepted NPZ reproduce W4a C1 exactly
(7.5094/4.2867/3.2227, mass 0.25445): CANDIDATE_DIAGNOSTICS_PASS.

## 7. Rejected hypotheses

- `MODEL_F_CONSUMER_OR_AXIS_DEFECT`: axis part rejected (2.2e-16); consumer
  SMOOTHING part confirmed instead (narrower, upstream).
- `SMOOTHING_MODEL_INADEQUATE_FOR_SPARSE_1024X1024` as a modeling complaint:
  rejected as framed — the D4 backoff model is adequate (held-out 7.16);
  the failure is misapplication of its selected strength, not the model.
- `GENUINE_CAL_TRAIN_NEAR_INDEPENDENCE`: rejected (2.48–2.84 bits present).
- `DISCLOSURE_MOTHER_REGIME_INADEQUATE` as sole primary: rejected (C0 fails
  at square; C1 recovers L2 at square) — carried as secondary.
- `DECODER_OR_MATRIX_FAILURE_AT_FULL_DETERMINATION`: rejected as primary
  (S0 + F1); L1-at-square residual is a signal-threshold effect, named below.

## 8. Residual uncertainty + named discriminator

Whether any honest CAL-only estimator lifts L1 truth mass (currently 0.096)
past this decoder's n=64 threshold at ≤64 rows, or L1-at-64 is fundamentally
below the BP threshold regardless of estimator — discriminated by testing
further honest L1 estimators (e.g. wider-block scaling, not wider lam grids)
against the L1 square point. No further decoder spend authorized here.

## 9. Long-term route recommendation (one)

Promote the candidate backoff path through independent review, then run the
named L1 discriminator at n=64 before any disclosure/mother redesign or G2
talk: if L1 recovers under an honest estimator, resize rows from the
candidate model's own channel CE; if not, stop the n=64 two-layer route
(L2-only success at 52–64 rows is near-zero rate and not an operating
point) and move block geometry, not smoothing.

## 10. Additive pointer — G2 prior-configuration corrigendum (D14 VR-C, docs only)

> This section is append-only (2026-09-14, D14 C-impl). No line above is
> rewritten. The G2/X4 inference-scope corrigendum is recorded in
> `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`:
> root `workspace/v72p2d5_g2/20260906_r1` preserved unchanged (4 files,
> 1320/1320 calls); literal grade `G2_CURRENT_CONFIGURATION_FAILED` retained
> as the accurate description of the executed rejected per-cell-prior
> configuration; that result is invalid as n=256 finite-length feasibility /
> route-closure evidence; supersession covers the scientific inference only,
> not the recorded execution; no unique-cause claim.
