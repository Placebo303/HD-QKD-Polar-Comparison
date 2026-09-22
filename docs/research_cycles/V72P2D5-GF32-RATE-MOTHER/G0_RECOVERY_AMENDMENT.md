# G0 Recovery Amendment — V72P2D5-GF32-RATE-MOTHER (prospective, Option B)

- Disposition: `workspace/v72p2d5_g0/20260905_r2/` stays byte-for-byte untouched;
  `numerical_status: NUMERICAL_PASS / lifecycle_status: PROCEDURAL_REVIEW_MISSING / result_acceptance: RESULT_NOT_ACCEPTED`.
  Original one-shot consumed. No overwrite/replay/rename/copy/promotion. Not a decoder/graph/FER/SKR/qualification/promotion failure.
- Purpose: prospective independently reviewed recovery-confirmation path repeating only tiny G0 math/decoder-interface checks
  under proper lifecycle, solely to restore G0 acceptance before P0. Not a statistical experiment.
  No change to graph/prior/thresholds/decoder params/roadmap.
- Frozen contract: `phase: g0-recovery`; `key: g0_recovery_execution_authorized`;
  seeds `2026090620,2026090621,2026090622,2026090623,2026090624,2026090625,2026090626,2026090627` (in order, no search/substitution/retry);
  output `workspace/v72p2d5_g0_recovery/20260906_r1/` (must not exist before authorized execution);
  command `python scripts/v72p2d5_gf32_rate_mother.py --phase g0-recovery`;
  files exactly `results.json, table.csv, report.md, execution_summary.json`.
- Decoder: historical `decode_row_layered_fftqspa`; `max_iter=90`; `damping_alpha=1.0`; `warm_beliefs=None`;
  no fake in authorized recovery (fake test-only); one historical adapter init per invocation; 8 calls one per seed; no CAL/VAL/real reads.
- Gates (identical to G0): marginal `<1e-12`; conditional `<1e-12`; chain `<1e-10`; mapping round-trip exact;
  exhaustive/factorization `<1e-12`; tree-vs-exhaustive posterior `<1e-12`; tree finite+MAP equal;
  all 8 hard outputs exact; all 8 syndrome pass; all 8 finite; `exact_failure_fraction=0`.
- Budget: outer `<=120s`; `RSS<2GiB` when available else null; timeout/resource gives `G0_RECOVERY_BLOCKED_RESOURCE`.
- Legal decisions only: `G0_RECOVERY_PASS`, `G0_RECOVERY_BLOCKED_MATH`, `G0_RECOVERY_BLOCKED_DECODER`, `G0_RECOVERY_BLOCKED_RESOURCE`.
  Never emit ordinary `G0_PASS` for the recovery dir.
- Order: `STRUCTURE accepted → G0 accepted → P0 cost preflight → G1 integration trend → G2 grading experiment`.
  Recovery acceptance required before P0. No P0 execution/auth here. P0/G1 must not share auth. G1/G2 separately gated. No auto-advance.
- Gates: Pre-EXECUTE and Pre-RESULT apply to recovery execution/solidification; FAIL blocks.
- Lifecycle now: `G0_RECOVERY_IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED / AWAITING_INDEPENDENT_IMPLEMENTATION_REVIEW`.
