# V72P2D5 G0 recovery Pre-RESULT review

Verdict: `PASS`.

The independently reviewed recovery evidence at
`workspace/v72p2d5_g0_recovery/20260906_r1/` contains exactly the four frozen
files and reports the legal decision `G0_RECOVERY_PASS`.

- Seeds: `2026090620..2026090627`, each exactly once.
- Attempted/completed/exact/syndrome-ok/finite: `8/8/8/8/8`.
- Decoder calls: `8`; historical decoder invocations: `1`.
- Exact failure fraction: `0.0`.
- Marginal/conditional errors: `1.5543122344752192e-15` /
  `1.4432899320127035e-15` (`<1e-12`).
- Chain error: `5.012611697980228e-16` (`<1e-10`).
- Exhaustive/factorization errors: `1.6653345369377348e-15` (`<1e-12`).
- Tree posterior error: `0.0`; tree MAP/finite/prior checks all true.
- Wall: `0.26224670000374317s` (`<=120s`); RSS unavailable and recorded null.
- JSON, CSV, report, and execution summary are mutually consistent.

Recovery authorization is closed and its single attempt is consumed. This
accepts G0 recovery only and advances to `P0_PACKET_REVIEW`; it does not
authorize P0, G1, G2, synthetic, real, or formal execution and makes no FER,
SKR, qualification, or promotion claim.
