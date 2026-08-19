# V26R closeout evidence (2026-08-19)

## Independent read-only verifier — `verify_run(root)`
- Rebuilds adapters from `channel_counts.npz` (run_04 / fallback).
- Re-runs M0 and M1 mechanism gates.
- Rebuilds the 72-call screen plan and recomputes every call.
- Builds the confirmation plan from the recomputed screen and recomputes all 60 calls.
- Checks A02@f=1.3 30/30, rate/rho/seed/entropy/final-state per call vs persisted
  artifacts (0 mismatch on both runs).
- Recomputes terminal state and compares to `gate.json`.
- Result: run_01 ok=true, run_02 ok=true (persisted to each run's
  `readonly_verify.json`; run_02 is canonical).

## Corrected efficiency definitions
f_i = leak_i / H_i, leak_i = (1-R_i) log2(q_i) = m_i log2(q_i)/n,
R_i = 1 - f_i H_i / log2(q_i).  `target_rate_layer` implements this; the wrong
`f=R/H`, `R=f*H` forms are rejected in proposal/design/spec/report.

## Fixed M1 reference tests
- `adapter_input_entropy_matches_iter0`: enters the real MC-DE first round
  (`max_iter=1`, `record_channel_entropy=True`), err_replay=0.0 (exact identity
  with the consumed channel), err_model≈0.009 < tol 0.03 (independent model draw).
- `gf2_bsc_reference`: noiseless BSC must converge; feasible-rate (f=2.0, rate≈0.427)
  must converge; at-capacity (f=1.0, rate≈0.714) must fail (not "both fail = agree").

## Resource gate
`RESOURCE_LIMIT_SECONDS = 24h` implemented in `_run_gated_stage`; not triggered
(screen≈44s + confirm≈112s).

## Run roles
run_02 = canonical, run_01 = deterministic_repeat (RUN_MANIFEST.json + README).

## Prohibitions respected
No degree search, finite codes, FER, MET, fresh qualification, raw `.ttbin`,
public residual, Alice-oracle, holdout tuning, push.
