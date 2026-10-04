# Tasks — D15 Paired Finite-Length Margin Curve (readiness D1501–D1510)

Packet: `.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md`
Track: `EXPLORE` readiness planning for D1501–D1502 (docs only; no code, no
execution, decoder calls 0, no commit/push); future batch remains `EXPLORE`.
Scope for this call: `openspec/changes/v72p2d15-finite-length-margin-curve/**`
for D1501; hand-arithmetic for D1502. Code/scripts/tests/cycle-docs per packet
§§3–6 for D1503–D1510 (later calls only).

- [x] **D1501 OpenSpec first**: proposal/design/tasks/delta spec with equations,
  reuse map, rejected alternatives, full seed list, nine-cell matrix, §7 route
  vocabulary with conservative thresholds (highest matched-margin point +
  cross-point monotonic + multi-graph support; no single pooled count closes
  route), budgets (288/46/1800s/120s/2GiB/1-proc), invalid-inference rejections
  §2 verbatim, claim ceiling (no threshold fit, no investment selection, no
  D7-H/FER claims). Seeds/root/command frozen with absence proof (design §6).
- [x] **D1502 arithmetic proof**: exact-rational recomputation of loads
  (548.700215065776 / 412.508145233200), factors
  (L1 1.00237/1.03882/1.07527; L2 1.00604/1.04240/1.07877), sockets and all nine
  check allocations (L045 m114 `2^29+3^85`; L055 m114 `2^41+3^73`; L2 m83
  `4^31+5^52` / m86 `4^46+5^40` / m89 `4^61+5^28`; plus retained m110/m118
  cells); every histogram sums to n/m/E (§3 table all PASS);
  constructor-feasibility screen (§4: no gate forbids dc 4/5 or requires
  degree-2 checks; no gate requires n2>0; max dc 5 within ≤8 ceiling) — PASS,
  no STOP, no amend.
- [x] **D1503 reuse**: import D14N/D12 graph construction, admission,
  coefficients, Model-F sampling/prior and L1 dispatch. Use the accepted
  true-conditioned L2 oracle path directly; no APP transfer or copied
  decoder/GF32 kernel.
- [x] **D1504 plan**: construct all 288 identities before decoder binding; enforce
  paired blocks, fresh seeds, nine exact cells and no predecessor pooling.
- [x] **D1505 runner**: additive CLI with `--profile-only`, `--d15-batch`,
  default-false `--execution-authorized`, and `--verify`. Unauthorized refusal
  occurs before root creation, decoder binding or Model-F load.
- [x] **D1506 evidence**: fresh never-overwrite six-file root; minimal records
  carry layer, arm, rows, exact effective factor, graph/block identity, exact,
  syndrome, undetected, iterations, provenance and wall/resource fields.
- [x] **D1507 result analysis**: per arm/row/graph counts; Wilson intervals and
  paired discordances descriptive only; monotonicity violations reported, never
  repaired. Fit no asymptotic threshold from three points.
- [x] **D1508 route vocabulary**: preregister the conservative classification:
  `MARGIN_CURVE_L1_SPECIFIC`, `MARGIN_CURVE_L2_SPECIFIC`,
  `MARGIN_CURVE_FINITE_BACKOFF`, `MARGIN_CURVE_BOTH_WEAK`,
  `MARGIN_CURVE_AMBIGUOUS`, `MARGIN_CURVE_ENGINEERING_BLOCKED`. Thresholds use
  the highest matched-margin point plus cross-point monotonic evidence and
  require multi-graph support; no single pooled count may close the route.
- [x] **D1509 tests/profile**: fake-only boundaries, arithmetic, plan/pairing,
  no-APP proof, authorization refusal, writer/verifier, exact/syndrome/
  undetected isolation, every route terminal and collision priority.
  PROFILE_ONLY builds 36 graphs, prints the 288 plan and root absence with zero
  decoder calls.
- [x] **D1510 independent review**: actual artifact access; independently recompute
  arithmetic, all 36 admissions, seeds, plan, fake true branch, gates, budgets,
  refusal ordering and zero-production boundary.

Verification proportionality (packet §6): T0 compile + exact arithmetic fixtures;
T1 focused D15 plus directly reused D14N tests. Broad historical suites only on a
concrete focused conflict. Fake authorized true branch must complete 288/288 into
a scratch root and pass the verifier without entering production adapters.
Reviewer evidence must state `EVIDENCE_ACCESS: VERIFIED`; any blocking arithmetic,
admission, pairing, gate or production-boundary finding blocks readiness. After
PASS, one explicit-path local commit is permitted (NOT this call: no commit/push).
