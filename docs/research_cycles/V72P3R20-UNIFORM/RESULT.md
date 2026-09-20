# R20 Uniform-Prior DECIDE — Result (Y-ev, quoted)

Track: DECIDE. Solidification only; no execution/data/commit performed here.

## Execution evidence (operator-attested)

- Exit 0; wall 105.52s; RSS ~179MiB (OPERATOR-ATTESTED).
- Budgets: sci 128/128; setup 4 (≤8).
- Uniform outcome: 128 calls / 0 accepted / 0 undetected / 0 verified-success.
- Residuals: 91/97/100, mean 97.00, hist {91:2, …, 100:6} (operator-quoted).
- Iters mean 90.00 (pegged at cap).
- Disclosure 72192; net_secret −72192.
- Betas: −0.31624 / −0.36725 (derived-only, negative).
- Paired vs R9: mean Δ = +10.6406, median +9.0, improved(Δ<0) = 3, tied 2, worsened 123,
  min −2, max +96.
- Accepts: 0 vs R9 1 (reported, not gated).
- Verify: 128/0 (0 verified successes of 128).

## Provenance (no replacement / no retune)

- Zero replacement / zero retune: frozen uniform/90/m100 arm executed once as preregistered.
- Loader untouched: structural drop of the load path + zero `np.load` + `loader_calls=0`
  + npz mtime unchanged.
- Truth post-decision: outcome read from artifacts after execution; no pre-read tuning.
- R9 baselines sha `c75e27aa…`, byte-identical imports.
- Protected dirs clean; no commit/push performed.

## Artifact root (4-file UUID root)

Fresh root `workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8` containing:

1. `workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8/uniform_results.csv`
2. `workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8/paired_vs_R9.csv`
3. `workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8/run_manifest.json`
4. `workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8/OPERATOR_RETURN.md`

## Claim ceiling

Diagnostic-only. No FER/SKR/qualification/promotion/publication claim. No route-closing
decision beyond the recorded PRIOR-HELPS verdict under the corrected rule.

## Acceptance block

- Grant: single-consumption PRIOR-HELPS grant — consumed; no rerun/repair under this grant.
- Pre-EXECUTE: Q1–Q6 checked (branch, scope cleanliness, frozen contract, authorization,
  output absence, focused tests).
- Pre-RESULT: reviewer-go PASS with P9 CONFIRMED (sign-typo correction confirmed).
- Main-thread: ACCEPTED PRIOR-HELPS under the corrected rule
  (mean Δ +10.6406 > +5 AND modelF-better fraction 123/128 > 0.6).
