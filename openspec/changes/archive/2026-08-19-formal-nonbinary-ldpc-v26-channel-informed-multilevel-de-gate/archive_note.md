# Archive Note — formal-nonbinary-ldpc-v26-channel-informed-multilevel-de-gate

Status: **ARCHIVED (RUN_COMPLETE — pass_target_f13, 2026-08-19; V26R closeout applied; local commit, no push)**

## Why archived
- V26 ran the frozen small-scale channel-informed multilevel MC-DE gate on the two
  V25 preselected exploration points: A01 (F01 GF512+GF2) and A02 (F03 GF32+GF32),
  at f in {1.3, 1.6, 2.0}, lambda={2:1} + harmonic-exact concentrated checks.
- Terminal state: `pass_target_f13` — A02 (F03 GF32+GF32) converges f=1.3 on all
  2 layer x 3 source x 5 confirm seeds (30/30, final mean entropy 0.00000 bits/symbol);
  A01 f=1.3 fails on the GF2 residual layer and passes at f=1.6.

## V26R closeout (this archive reflects the closed-out state)
- Corrected efficiency definitions in proposal/design/spec/report/code:
  f_i=leak_i/H_i, leak_i=(1-R_i)log2(q_i)=m_i log2(q_i)/n, R_i=1-f_i H_i/log2(q_i).
- Independent read-only verifier `verify_run` recomputes 72 screen + 60 confirmation +
  A02@f=1.3 30/30 + rate/rho/seed/entropy/terminal; run_01 and run_02 both 0 mismatch,
  ok=true; persisted to each run's `readonly_verify.json` (canonical run_02).
- Fixed weak M1 references: iteration-0 test genuinely enters the MC-DE first round
  (`record_channel_entropy`, err_replay=0); centered GF2 BSC reference now clearly decides
  pass/fail (noiseless must converge; feasible-rate ~0.427 must converge; at-capacity
  ~0.714 must fail) instead of "both non-converge = agree".
- Implemented 24h completed-call resource gate (`RESOURCE_LIMIT_SECONDS` ->
  `resource_blocked`); not triggered in V26 (~44s screen + ~112s confirm).
- Explicit source<->delay metadata (`SOURCE_METADATA`: 1M/1p5M/2M -> delay_used_ps
  -50/+50/+50, n_pairs 512000/708352/933120) exposed in adapter / M0 detail / RUN_MANIFEST.
- Run roles: run_02 = canonical, run_01 = deterministic_repeat (RUN_MANIFEST + README).

## Preserved
- Code: `nonbinary_v26_channel.py`, `nonbinary_v26_mcde.py`, `nonbinary_v26_gate.py`,
  `nonbinary_v26_verify.py` (+ `nonbinary_v26_verify` reference tests in
  `nonbinary_v26_verify.py`), `test_nonbinary_v26_gate.py` (19 tests, all pass).
- Evidence:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/`
  (run_01 deterministic repeat + run_02 canonical, README, RUN_MANIFEST, readonly_verify).
- Report: `docs/nbldpc-v26-channel-informed-multilevel-de-report-20260819.md`.

## Successor boundary
- `pass_target_f13` only authorizes proposing an A02 (F03 GF32+GF32) finite-leakage-margin
  DE / construction change. Still no finite code / FER / qualification / promotion / MET.
- V27 is a NEW OpenSpec change (finite-leakage-margin DE gate) to be reviewed by the main
  thread; it is NOT executed here.
- No push.
