# V24 Structured Single-Edge DE Optimization — M0–M2 Gate Report (2026-08-18)

Status: COMPLETE -- FAIL (single_edge_bounded_optimization_failed)

## Pre-registered packet (frozen)

- Channel: V17 q=1024 structured, `H_V17=0.5499550439219351 bits/symbol`.
- Search band: design rate `R in [0.9375, 0.94140625]`, `f_total <= 1.3`.
- Single-edge `lambda/rho`, 1–8 non-zero degrees/side, lambda degree 2..64,
  rho degree 2..512, weights quantized /64.
- Proposal generator: `SeedSequence([24000,k])` per attempt k, lambda first
  then rho, exact NumPy call order (integers -> choice -> full -> multinomial).
- Budget: 8192 attempts, first 512 unique valid candidates.
- Screen: seeds [24001,24002], n=200, max_iter=50.
- Refine: seeds [24003,24004,24005], n=1000, max_iter=150.
- Holdout: seeds [24101..24105], n=2000, max_iter=200; all-five-seeds PASS rule.
- M0: read-only validation of accepted V8 corrected trace + V17 channel.
- Resource gate: 24 h completed-DE-call ceiling; completion before ceiling.

## Evidence root

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/`

## Observed trajectory (up to gate completion)

- M0 mechanism gate: PASS.
- Valid unique candidates found in 8192 attempts: **135** (under the 512 cap).
- Screen: 270 evaluations, **0 converged**; final base-q entropy floor
  0.20–0.32.
- Refine: 24 evaluations (8 candidates x 3 seeds), **0 converged**; entropy
  ~0.29–0.30.
- Finalists (pre-holdout declaration): 4 candidates
  (ids 1257, 2740, 1816, 3719), all non-converged in refine.
- Holdout: 20 evaluations (4 finalists x 5 seeds) — in progress.

## Terminal decision

**`fail`** = `single_edge_bounded_optimization_failed` (decision.json,
`nbldpc_v24_decision_v1`).

- M1/M2 resource gates: not blocked. Completed-DE-call accumulated time
  17530.5 s (4.87 h), well under the 24 h ceiling.
- Holdout: 4 pre-declared finalists (ids 1257, 2740, 1816, 3719) x 5 seeds =
  20 evaluations; **0 finalists converged on all five seeds** (final base-q
  entropy ~0.2919-0.2998, all above the 0.01 threshold).
- Read-only semantic verifier: `ok=True`, recomputed terminal state `fail`,
  no problems.

Claim boundary: DE-only asymptotic decision; no finite-code/FER/qualification/
promotion claim. This `fail` closes the bounded single-edge optimization at the
frozen V17 q=1024 structured channel/target f<=1.3. True MET, or adjusting
q / channel decomposition / f target, are separate user-authorized changes and
do not run automatically. No push was performed.
