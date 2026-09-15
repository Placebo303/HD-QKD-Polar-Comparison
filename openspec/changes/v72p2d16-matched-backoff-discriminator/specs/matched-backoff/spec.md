# Spec delta — D16 one-point matched-backoff discriminator (readiness)

New additive delta spec `matched-backoff`. No existing spec modified. Normative for
D1603+; D1601/D1602 freeze only (no code, no execution here).

## SHALL (frozen D16 contract)

- The discriminator SHALL be n=128 only with exactly three cells: L045 at m=125,
  L055 at m=125, L2 DV3 ORACLE at m=94. Variable profiles SHALL be
  L045 71/57/E313, L055 83/45/E301, L2 128 degree-3/E384. Check allocations SHALL
  be exactly: L045 `2^62+3^63`; L055 `2^74+3^51`; L2 `4^86+5^8`. Every
  histogram SHALL sum to its (n, m, E) per design §3.
- Rate math SHALL be entropy-derived without changing the generator:
  `Load_L1=548.700215065776`, `Load_L2=412.508145233200`; disclosed 5m
  (L1 625; L2 470); effective factors SHALL be computed as
  disclosed/load (L1 `1.1390555039696448`; L2 `1.1393714413428093`;
  absolute gap `0.00031593737316448767`) and SHALL NOT be copied as rounded constants.
- Graph seeds SHALL be exactly L045 `2026094001..04`, L055 `2026094005..08`,
  L2 `2026094009..12` (4 disjoint seeds per cell per design §6); block seeds SHALL
  be exactly `2026094101..08` with the same 8 blocks feeding all three cells.
  No seed SHALL be added, replaced or re-rolled after any decoder result; no
  predecessor seed SHALL be reused.
- Construction/admission SHALL reuse the accepted connectivity-first constructor
  and A1–A6 predicates unchanged (exact histograms + socket balance; simple graph
  with min == design §3 min; one component; structural rank == m; GF32 poly-37
  rank == m; replay equality). Any predicate failure SHALL retain the cell record,
  exclude the graph before decoder dispatch, and make the batch
  engineering-blocked; failure SHALL NOT alter seeds.
- Coefficients SHALL follow `v10_seed(f"d10:coeff:128:{graph_seed}")`, one uniform
  nonzero GF32 draw per edge in sorted order, same rule all arms. Priors SHALL be
  the accepted CAL-only Model-F chain; blocks SHALL be sampled once per block seed
  via the accepted helper. L2 ORACLE SHALL use the accepted true-conditioned
  path (`oracle_l2_prior`) once per graph/block, marked `ORACLE`/diagnostic.
- The matrix SHALL be exactly 1 point × 3 arms × 4 graphs × 8 blocks = 96
  scientific calls with deterministic order (L045→L055→L2-ORACLE, graph,
  block ascending), built + validated before decoder binding. Setup SHALL be
  exactly/at most 22 (12 + 8 + 2). No predecessor pooling; batch tag SHALL prevent
  pooling with D15.
- The runner SHALL expose `--profile-only`, `--d16-batch`, default-false
  `--execution-authorized`, and `--verify`. Unauthorized refusal SHALL occur
  before root creation, decoder binding or Model-F load. `--verify` SHALL
  recompute A1–A6 for every stored graph with zero skip and fail nonzero on any
  partial or engineering-blocked root; it SHALL create no scientific root.
- Evidence SHALL use the frozen fresh root
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  (never overwritten; six-file D11/D12/D15 convention). Records SHALL carry layer,
  arm, rows, exact effective factor, graph/block identity, exact, syndrome,
  undetected, iterations, provenance and wall/resource fields. Metric isolation
  SHALL hold: exact primary, syndrome separate, `undetected` isolated and never
  merged into success/FER. L2 records SHALL be ORACLE and ungraded.
- Analysis SHALL report per arm/graph counts; Wilson intervals and paired
  L055/L045 discordances SHALL be descriptive only; L045 SHALL be descriptive
  only and SHALL NOT gate. NO asymptotic threshold SHALL be fit from one point.
- Routing SHALL implement exactly the six terminals with first-match priority per
  design §7 (`D16_ENGINEERING_BLOCKED`, `D16_L2_DEGREE_SIGNAL`,
  `D16_L1_CONSTRUCTION_SIGNAL`, `D16_MATCHED_BACKOFF_SUFFICIENT`, `D16_BOTH_WEAK`,
  `D16_AMBIGUOUS`); cell thresholds SHALL be ADEQUATE ≥24/32 + ≥2 graphs ≥6/8,
  WEAK ≤16/32 + ≥2 graphs ≤4/8, else MIDDLE; no single pooled count SHALL close
  the route.
- Budgets SHALL be: ≤96 scientific calls; ≤22 setup; wall ≤900 s; per-call
  ≤120 s; RSS <2147483648 B; one process; no retry/resume/repair/seed
  search/tuning/adaptive stop.

## SHALL NOT

- No production decoder call, no scientific batch, no output-root creation, no
  CAL/VAL/raw/real-data contact in readiness (D1601–D1602, D1606 fake-only,
  D1608 read-only).
- No APP/forward-transfer arm, no new L2 degree family, no n256, no generator
  change, no D7-H revival, no threshold fitting, no investment selection.
- No FER/leakage/SKR/qualification/promotion/real-data/optimality/publication
  claim; no reinterpretation of D15/D14N terminals; no predecessor pooling.
- No re-derivation of degree tables with different rounding; no seed change,
  replacement seeds, retry/resume, post-hoc threshold change, decoder feedback
  into construction, or coefficient repair/reseed.
- No copied decoder/GF32 kernels; no reimplemented transfer/provenance/oracle/
  admission semantics (reuse-only).
- No modification of frozen baseline, Model-F artifact, or any file outside this
  change dir; no commit or push in this readiness call.
