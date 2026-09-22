# D15 Paired Finite-Length Margin Curve — Readiness R1 Task Packet

## 1. Identity and boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d15-finite-length-margin-curve`
- Work type: implementation/readiness; future batch track `EXPLORE`.
- Accepted predecessor:
  `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`.
- This packet authorizes OpenSpec, additive implementation, fake-only tests,
  PROFILE_ONLY, refusal checks, independent readiness review and a scoped local
  commit. It authorizes zero scientific decoder calls and no future batch.

## 2. Scientific question

At n=128, when L1 and L2 are compared at approximately the same effective
disclosure factors, does failure remain L1-specific, move to L2, or chiefly
follow finite-length margin? This packet estimates a small margin curve before
any new degree search.

The audit must explicitly reject these invalid inferences:

- D14N L1 1.002 versus L2 1.261 is not a layer comparison.
- `I <= disclosed bits` is not sufficient for decoding.
- One near-entropy point cannot prove a construction defect.
- D12 absolute success cannot be compared to D14N without the rate change;
  relative L055-versus-L045 evidence remains descriptive.

## 3. Frozen proposed matrix for implementation review

Use the accepted generator entropies, without changing the generator:

- `H_L1 = 4.286720430201375` bits/symbol; n128 load
  `548.700215065776` bits.
- `H_L2 = 3.222719884634378` bits/symbol; n128 load
  `412.508145233200` bits.
- Three row points chosen by exact integer rows, not copied rounded factors:
  - L1 m=`110,114,118`, disclosed `550,570,590`, effective factors computed
    from the load (approximately `1.002,1.039,1.075`).
  - L2 m=`83,86,89`, disclosed `415,430,445`, effective factors computed from
    the load (approximately `1.006,1.042,1.079`).
- Arms per point: L1 L045, L1 L055, and L2 DV3 ORACLE single-layer diagnostic.
  No APP arm: cross-layer transfer would reintroduce the L1 success confound.
- Variable profiles: L045 71/57/E313; L055 83/45/E301; L2 DV3 128 degree-3,
  E384.
- Check allocations derived exactly:
  - L045: m110 `2^17+3^93`; m114 `2^29+3^85`; m118 `2^41+3^77`.
  - L055: m110 `2^29+3^81`; m114 `2^41+3^73`; m118 `2^53+3^65`.
  - L2: m83 `4^31+5^52`; m86 `4^46+5^40`; m89 `4^61+5^28`.
- Four fresh graph seeds per arm/row point and eight fresh paired block seeds.
  Planner must select explicit disjoint ranges, prove absence, and freeze them
  before implementation. The same eight blocks feed all nine cells.
- Exact future calls: 3 row points × 3 arms × 4 graphs × 8 blocks = 288.
- Setup ceiling: 36 graph objects + 8 block samples + 2 plan/manifest = 46.

If independent arithmetic or constructor feasibility contradicts any table,
STOP before code and return the exact calculation; do not silently amend it.

## 4. Required implementation tasks D1501–D1510

- **D1501 OpenSpec first**: proposal/design/tasks/delta spec with equations,
  reuse map, rejected alternatives, full seed list, matrix, gates and budget.
- **D1502 arithmetic proof**: exact-rational recomputation of loads, factors,
  sockets and check allocations; confirm every histogram sums to n/m/E.
- **D1503 reuse**: import D14N/D12 graph construction, admission, coefficients,
  Model-F sampling/prior and L1 dispatch. Use the accepted true-conditioned L2
  oracle path directly; no APP transfer or copied decoder/GF32 kernel.
- **D1504 plan**: construct all 288 identities before decoder binding; enforce
  paired blocks, fresh seeds, nine exact cells and no predecessor pooling.
- **D1505 runner**: additive CLI with `--profile-only`, `--d15-batch`, default-
  false `--execution-authorized`, and `--verify`. Unauthorized refusal occurs
  before root creation, decoder binding or Model-F load.
- **D1506 evidence**: fresh never-overwrite six-file root; minimal records carry
  layer, arm, rows, exact effective factor, graph/block identity, exact,
  syndrome, undetected, iterations, provenance and wall/resource fields.
- **D1507 result analysis**: per arm/row/graph counts; Wilson intervals and
  paired discordances descriptive only; monotonicity violations reported, never
  repaired. Fit no asymptotic threshold from three points.
- **D1508 route vocabulary**: preregister a conservative classification:
  `MARGIN_CURVE_L1_SPECIFIC`, `MARGIN_CURVE_L2_SPECIFIC`,
  `MARGIN_CURVE_FINITE_BACKOFF`, `MARGIN_CURVE_BOTH_WEAK`,
  `MARGIN_CURVE_AMBIGUOUS`, `MARGIN_CURVE_ENGINEERING_BLOCKED`. Thresholds must
  use the highest matched-margin point plus cross-point monotonic evidence and
  require multi-graph support; no single pooled count may close the route.
- **D1509 tests/profile**: fake-only boundaries, arithmetic, plan/pairing,
  no-APP proof, authorization refusal, writer/verifier, exact/syndrome/
  undetected isolation, every route terminal and collision priority.
  PROFILE_ONLY builds 36 graphs, prints the 288 plan and root absence with zero
  decoder calls.
- **D1510 independent review**: actual artifact access; independently recompute
  arithmetic, all 36 admissions, seeds, plan, fake true branch, gates, budgets,
  refusal ordering and zero-production boundary.

## 5. Budget proposal

- Scientific calls: exactly/at most 288.
- Setup: exactly/at most 46.
- Wall: ≤1800 s; per call ≤120 s; RSS strictly <2 GiB.
- One CPU process; no retry/resume/repair/seed search/tuning/adaptive stop.
- Fresh result root and exact command are selected and frozen during D1501,
  kept absent through readiness.

## 6. Review and commit discipline

- T0 compile and exact arithmetic fixtures; T1 focused D15 plus directly reused
  D14N tests. Broad historical suites only on a concrete focused conflict.
- Fake authorized true branch must complete 288/288 into a scratch root and
  pass the verifier without entering production adapters.
- Reviewer evidence must state `EVIDENCE_ACCESS: VERIFIED`; any blocking
  arithmetic, admission, pairing, gate or production-boundary finding blocks
  readiness.
- After PASS, one explicit-path local commit is permitted. No push, branch
  switch, full-tree staging, line-ending normalization or mixed-hunk guessing.

## 7. Return contract

Return only:

`D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`

with exact entropy/row/factor/socket tables; selected seeds; 36/36 admission;
288/46 plan; route thresholds and justification; reuse/duplication map; tests,
fake true branch, PROFILE_ONLY, refusal and independent verdict; future
root/command/budgets; zero production calls; commit/no-push/exclusions.

Do not create an execution authorization prompt, run the real batch, select L1
or L2 investment, revive D7-H, or make FER/leakage/SKR/real-data/qualification/
optimality/publication claims.
