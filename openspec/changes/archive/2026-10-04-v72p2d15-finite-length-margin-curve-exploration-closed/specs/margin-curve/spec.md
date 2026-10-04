# Spec delta — D15 paired finite-length margin curve (readiness)

New additive delta spec `margin-curve`. No existing spec modified. Normative for
D1503+; D1501/D1502 freeze only (no code, no execution here).

## SHALL (frozen D15 contract)

- The curve SHALL be n=128 only with exactly nine cells: L045 at m=110/114/118,
  L055 at m=110/114/118, L2 DV3 ORACLE at m=83/86/89. Variable profiles SHALL be
  L045 71/57/E313, L055 83/45/E301, L2 128 degree-3/E384. Check allocations SHALL
  be exactly: L045 `2^17+3^93` / `2^29+3^85` / `2^41+3^77`; L055 `2^29+3^81` /
  `2^41+3^73` / `2^53+3^65`; L2 `4^31+5^52` / `4^46+5^40` / `4^61+5^28`. Every
  histogram SHALL sum to its (n, m, E) per design §3.
- Rate math SHALL be entropy-derived without changing the generator:
  `Load_L1=548.700215065776`, `Load_L2=412.508145233200`; disclosed 5m
  (L1 550/570/590; L2 415/430/445); effective factors SHALL be computed as
  disclosed/load (≈L1 1.00237/1.03882/1.07527; L2 1.00604/1.04240/1.07877) and
  SHALL NOT be copied as rounded constants.
- Graph seeds SHALL be exactly `2026093801..3836` assigned 4 disjoint seeds per
  cell per design §6; block seeds SHALL be exactly `2026093901..3908` with the
  same 8 blocks feeding all nine cells. No seed SHALL be added, replaced or
  re-rolled after any decoder result; no predecessor seed SHALL be reused.
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
- The matrix SHALL be exactly 3 points × 3 arms × 4 graphs × 8 blocks = 288
  scientific calls with deterministic order (point, L045→L055→L2-ORACLE, graph,
  block ascending), built + validated before decoder binding. Setup SHALL be
  exactly/at most 46 (36 + 8 + 2). No predecessor pooling.
- The runner SHALL expose `--profile-only`, `--d15-batch`, default-false
  `--execution-authorized`, and `--verify`. Unauthorized refusal SHALL occur
  before root creation, decoder binding or Model-F load. `--verify` SHALL
  recompute A1–A6 for every stored graph with zero skip and fail nonzero on any
  partial or engineering-blocked root; it SHALL create no scientific root.
- Evidence SHALL use the frozen fresh root
  `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`
  (never overwritten; six-file D11/D12 convention). Records SHALL carry layer,
  arm, rows, exact effective factor, graph/block identity, exact, syndrome,
  undetected, iterations, provenance and wall/resource fields. Metric isolation
  SHALL hold: exact primary, syndrome separate, `undetected` isolated and never
  merged into success/FER.
- Analysis SHALL report per arm/row/graph counts; Wilson intervals and paired
  discordances SHALL be descriptive only; monotonicity violations SHALL be
  reported, never repaired. NO asymptotic threshold SHALL be fit from three points.
- Routing SHALL implement exactly the six terminals with first-match priority per
  design §7 (`MARGIN_CURVE_L1_SPECIFIC`, `MARGIN_CURVE_L2_SPECIFIC`,
  `MARGIN_CURVE_FINITE_BACKOFF`, `MARGIN_CURVE_BOTH_WEAK`,
  `MARGIN_CURVE_AMBIGUOUS`, `MARGIN_CURVE_ENGINEERING_BLOCKED`); thresholds SHALL
  use the highest matched-margin point plus cross-point monotonic evidence and
  SHALL require multi-graph support; no single pooled count SHALL close the route.
- Budgets SHALL be: ≤288 scientific calls; ≤46 setup; wall ≤1800 s; per-call
  ≤120 s; RSS <2147483648 B; one process; no retry/resume/repair/seed
  search/tuning/adaptive stop.
- The future audit SHALL explicitly reject: D14N L1 1.002 versus L2 1.261 is not
  a layer comparison; `I <= disclosed bits` is not sufficient for decoding; one
  near-entropy point cannot prove a construction defect; D12 absolute success
  cannot be compared to D14N without the rate change (relative L055-vs-L045
  remains descriptive).

## SHALL NOT

- No production decoder call, no scientific batch, no output-root creation, no
  CAL/VAL/raw/real-data contact in readiness (D1501–D1502, D1509 fake-only,
  D1510 read-only).
- No APP/forward-transfer arm, no new L2 degree family, no n256, no generator
  change, no D7-H revival, no threshold fitting, no investment selection.
- No FER/leakage/SKR/qualification/promotion/real-data/optimality/publication
  claim; no reinterpretation of D14N/D12 terminals; no predecessor pooling.
- No re-derivation of degree tables with different rounding; no seed change,
  replacement seeds, retry/resume, post-hoc threshold change, decoder feedback
  into construction, or coefficient repair/reseed.
- No copied decoder/GF32 kernels; no reimplemented transfer/provenance/oracle/
  admission semantics (reuse-only).
- No modification of frozen baseline, Model-F artifact, or any file outside this
  change dir; no commit or push in this readiness call.
