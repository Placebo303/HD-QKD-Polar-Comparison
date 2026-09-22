# V72P3G6-R2DIAG — PREREG_AND_AUTH_CONDENSED (D2)

## D2 condensed preregistration

- Population: same pool as G6-R1 (follow-up diagnostic; disclosed bias).
- Arms: A0 audit (post-decision, 0 calls); A1 = (uniform prior, 90 iters);
  A2 = (model_f prior, 300 iters); n = 128/arm.
- Rules: D2 row-1 reading only (rate/code → prior contrast → schedule
  contrast); no promotion/generalization/route/SKR from this pool.
- Termination: stop at frozen n; no rerun/tuning on failure.
- Budgets: sci 256 total; setup 4/arm; wall/RSS envelope per DIAG_REPORT;
  1-proc, no retry, single invocation/arm.
- Commands: frozen per-arm invocations recorded in parent manifest.
- Tests: focused pre-execution checks per Pre-EXECUTE; verify triple
  128/128/128 zero-violation aggregate PASS.
- Stop rules: any Pre-EXECUTE FAIL blocks execution; any Pre-RESULT FAIL
  blocks solidification.
- Authorization: explicit main-thread grant, consumed-once for this frozen
  arm sequence only; not reusable for fresh-pool work.

## RULING lineage

- R6b arm-swap fix (binding): A1 = (uniform, 90), A2 = (model_f, 300) —
  orthogonal prior × schedule contrast; fail-closed admission (ambiguous
  arm identity → FAIL, no silent swap).
- RULING-1..3 carried (scope, authorization boundary, no-overwrite).

## Grant / promotion rules

- Grant-consumed-once: the authorization covering this frozen sequence is
  spent; any further execution needs a new grant.
- Fresh-pool promotion rule: promotion / generalization / route / SKR claims
  require FRESH pool P-1p5M untouched by this diagnosis.
