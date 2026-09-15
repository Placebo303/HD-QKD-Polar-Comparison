# D15 Paired Finite-Length Margin Curve — readiness record R1 (no execution)

Authority: `.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md`
(§§6–§7 return/authorization discipline; packet §§1–§7 frozen, sole authority).
Track: documentation-only (no code, no execution, no D15 batch, no decoder/scientific
calls, no root creation, no staging/commits, no push).
Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
`formal-ir-v72p1-addendum-clean` (do not switch; commit separate, NOT this call).
This call (D1510B): documentation-only — two new record files in this directory
(`READINESS_R1.md`, `EXPLORATION_LOG.md`), one pointer append to the D14 log, and the
D1503–D1510 checkbox update in the D15 OpenSpec `tasks.md`.
Independent review result recorded here (D15-R1510): trusted VERIFIED, do not rerun.

Predecessor (immutable, read-only context):
`D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`
(present: decision-log:4257, memory:3907, D14 log:292).

## Frozen matrix (packet §3, transcribed)

- Generator entropies (generator unchanged): `H_L1 = 4.286720430201375`,
  `H_L2 = 3.222719884634378` bits/symbol.
- n128 loads: `548.700215065776` / `412.508145233200` bits (reviewer L2 diff
  3.4e-13 rounding).
- Row points (exact integer rows, factors computed from load):
  L1 m=`110,114,118`, disclosed `550,570,590`, effective ≈`1.002,1.039,1.075`
  (exact `1.00237/1.03882/1.07527`); L2 m=`83,86,89`, disclosed `415,430,445`,
  effective ≈`1.006,1.042,1.079` (exact `1.00604/1.04240/1.07877`, ≤5e-6).
- Pairing gaps: `+0.00367/+0.00359/+0.00350`.
- Arms per point: L1 L045, L1 L055, L2 DV3 ORACLE single-layer diagnostic. No APP arm.
- Profiles/sockets: L045 71/57/E313; L055 83/45/E301; L2 DV3 128 degree-3, E384.
- Check allocations (exact): L045 m110 `2^17+3^93`, m114 `2^29+3^85`,
  m118 `2^41+3^77`; L055 m110 `2^29+3^81`, m114 `2^41+3^73`, m118 `2^53+3^65`;
  L2 m83 `4^31+5^52`, m86 `4^46+5^40`, m89 `4^61+5^28`. All nine: count-sum=m,
  socket-sum=E; degree_cell asserts pass.
- Seeds (frozen, disjoint from priors): 36 graph (`3801-04` … `3833-36` per-cell
  ranges) + 8 blocks `3901-08` exact; wrong-cell seeds refused; same 8 blocks feed
  all nine cells; plan 288 (idx 0..287, 9×32, point-major) + batch-tag
  `d15-margin-curve-v1` enforced.
- Budgets: scientific exactly/at most 288; setup exactly/at most 46 (=36+8+2);
  wall ≤1800 s; per-call ≤120 s; RSS strictly <2 GiB; 1 CPU proc; no
  retry/resume/repair/seed search/tuning/adaptive stop.
- Claim ceiling: no threshold fit (0 hits); Wilson/paired descriptive-only, gate never
  sees them; monotonic-violation → AMBIGUOUS reported-never-repaired; no single pooled
  count closes the route; no L1/L2 investment selection; no D7-H revival; no
  FER/leakage/SKR/real-data/qualification/optimality/publication claims.

Invalid-inference rejections (packet §2, verbatim scope): D14N L1 1.002 vs L2 1.261
is not a layer comparison; `I <= disclosed bits` is not sufficient for decoding; one
near-entropy point cannot prove a construction defect; D12 absolute success cannot be
compared to D14N without the rate change (relative L055-vs-L045 evidence descriptive).

## D1501–D1510 evidence table (D15-R1510 VERIFIED)

| Task | Verdict | Evidence |
|---|---|---|
| D1501–D1502 | (prior, retained) | OpenSpec + arithmetic proof per tasks.md |
| D1503 reuse | PASS | is-identical (dispatch_l1, coefficient_seed, refuse_out_root, sample_matched_block, candidate prior, marginalize, floor_renorm, oracle_l2_prior, Q32/POLY37/90/1.0/1e-15/RSS/ROOT); no copied kernels; imports only r2/r3/d11/d12/d14n/d5; v35 lazy-runner-only |
| D1504 plan/gates | PASS | 288 plan; adequate ≥24/32 + ≥2×≥6/8; weak ≤16/32 + ≥2×≤4/8; middle neither; all six terminals reproduce; ENG priority |
| D1505 runner/refusal | PASS | reviewer ran: rc=2 pre-write/bind/load, no target, future absent |
| D1506 evidence | PASS | fresh never-overwrite six-file root; minimal records incl. exact/syndrome/undetected isolation |
| D1507 analysis | PASS | per arm/row/graph counts; Wilson/paired descriptive-only; violations reported-never-repaired; no threshold fit |
| D1508 vocabulary | PASS | six terminals preregistered; highest matched-margin point + cross-point monotonic + multi-graph support |
| D1509 tests/profile | PASS | 25/25 reviewer own basetemp; py_compile 3/3; PROFILE_ONLY 36 graphs + 288 plan + root absence, decoder 0; fake summary setup 46/calls 288 |
| D1510 review | PASS_WITH_FINDINGS | EVIDENCE_ACCESS VERIFIED; ARITHMETIC/ADMISSION (36/36, A1–A6, replay, 1 component, srank==m, gf32==m; L1 min_dc 2, L2 min_dc 4; replacements 0; wall ~2.39 s)/SEEDS/GATES/REUSE/No-APP (0 hits; ARMS len 3; no transfer_fn; oracle diagnostic-only ungraded)/REFUSAL/BUDGETS/NO-PRODUCTION (future root absent pre/post; FROZEN_COMMAND verbatim; decoder 0; PRODUCTION_ABSENT_KEYS hold) all PASS; BLOCKING none |

D14N-3FAIL adjudication: ENVIRONMENTAL NON-BLOCKING, out of D15 scope (materialized
authorized root trips absence guards; functional asserts passed; D15 touched nothing;
stale-world-state pattern). Non-blocking: stale runner comment (FROZEN_COMMAND flag
wording contradicts actual — code correct, fix in later docs touch); additive-clean scope.

## Authorization (all false)

- Future batch: NOT authorized. Future root absent (pre/post verified); frozen command
  remains an unauthorized string.
- Decoder/scientific calls this call: 0. No execution authorized by readiness.
- Commit/push: none (commit separate, NOT this call).

## Terminal

`D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`

## Next gate

The future 288-call batch requires a separate explicit batch grant (own Pre-EXECUTE).
No execution authorization prompt is created here.

## Claim boundary

Readiness only. No FER/SKR/qualification/promotion/publication claim; no route-closing
decision; no threshold, investment, or D7-H statement.
