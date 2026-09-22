# V72P3G6-R2DIAG — DIAG_REPORT (DECIDE solidification, main-thread ACCEPTED)

> NON-CONFIRMATORY STAMP (first, binding): this is a same-pool follow-up
> diagnostic whose method was conditioned on the G6-R1 zero — disclosed bias.
> It is NOT a confirmation, NOT a generalization, NOT a route decision, and
> NOT an SKR claim. Any promotion / generalization / route / SKR use requires
> a FRESH pool (P-1p5M) untouched by this diagnosis.

Acceptance: DIAG_REPORT ACCEPTED (main thread) with D2-rules row-1 reading:
rate/code insufficient; prior NOT binding; schedule DEAD.

## Arms (frozen, n=128/arm)

- A0 AUDIT_POST_DECISION (0 decoder calls): true_weight range 119–128, mean
  123.70; truth-syndrome weight 85–94; r1_residual weight 82–94.
- A1 uniform prior, 90 iters: 128 attempted / 0 success / 0 undetected /
  0 verified-fail; iters used 90/90 (all exhausted).
- A2 model_f prior, 300 iters: 128 attempted / 0 success / 0 undetected /
  0 verified-fail; iters used 300/300 (all exhausted).

## Disclosure / efficiency (derived-only)

- Disclosure per arm: 68352 bits = 534 symbols × 128 (534 = 470 + 64).
- beta (A1): -0.24622678004125342 — derived-only, not hand-filled.
- beta (A2): -0.2945198929299142 — derived-only, not hand-filled.
- reconciled_net: 0 (both decode arms zero success).

## Row-1 reading (D2 rules, binding)

1. Rate/code: m = 94 rows vs mean truth weight 123.7 → ≈30 symbols short;
   rate/code insufficient.
2. Prior: A1-vs-A2 contrast is zero → prior NOT binding (prior contrast does
   not explain the zero).
3. Schedule: iter contrast (90 vs 300) is zero with no near-converge cluster
   → schedule DEAD (more iterations of this schedule do not recover).

## Budgets / execution envelope

- Scientific budget: 256/256 consumed (128 × 2 decode arms).
- Setup budget: 4/arm (audit arm setup only).
- Wall: A0 3.28 s / A1 109.01 s / A2 357.92 s; RSS ≤ 209 MiB; 1 process;
  no retry; single invocation per arm.

## Provenance

- Truth handling: post-decision audit only (A0); no in-loop truth use.
- Prior paths: per-arm frozen priors (A1 uniform; A2 model_f); no cross-arm
  leakage beyond the disclosed same-pool conditioning.
- Protected dirs clean (no overwrite of results/ or parent outputs);
  no commit/push from execution.

## Artifact paths

- Parent: manifest + summary (V72P3G6-REAL-CONFIRM parent record).
- A0/A1/A2 triples: per-arm manifest + summary + frame-result triple.

## Verification

- 128/128/128 rows verified, zero violations; aggregate PASS.
