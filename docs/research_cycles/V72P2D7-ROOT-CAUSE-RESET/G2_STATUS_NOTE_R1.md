# G2 status note R1 — pending, not failed, skipped, or superseded

> Authority: D7 root-cause and route-reset R1 packet §7 A05 and §4.

G2 remains the accepted-plan n=256 length discriminator. Its status is
`G2_PENDING_NOT_FAILED_NOT_SKIPPED_NOT_SUPERSEDED`, and its runtime status is
`G2_RUNTIME_UNVERIFIED`.

Accepted D5 plan matrix (frozen, unchanged by this change):

- n = 256; f = `(1.0, 1.1, 1.2)`;
- rows L1 `(196, 215, 235)`; rows L2 `(172, 189, 206)`;
- block seeds `2026091000..2026091199` (200 blocks);
- graph seeds L1 `2026090501`, L2 `2026090502`;
- APP 200 and oracle 40 per f (1320 calls total);
- resource ceilings: single call 120 s, G2 total <= 3600 s, peak RSS < 2 GiB;
- four-state grading preserved: `G2_SYNTHETIC_QUALIFIED`,
  `G2_INCONCLUSIVE`, `G2_CURRENT_CONFIGURATION_FAILED`,
  `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`; no unconditional `ROUTE_DEAD`.

Runtime estimation rule: only measured or scaled probes that are explicitly
authorized later may produce a G2 runtime estimate. P0's 485-second
projection is not a reliable G2 runtime estimate. No G2 execution is
authorized by this change; X4 requires separate explicit authorization and
independent Pre-RESULT review.
