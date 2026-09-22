# Spec delta — calibrated L1/L2 discriminator (`calibrated-discriminator`)

## Purpose

Freeze the D14N calibrated discriminator contract (packet §2 + prereg §2–§8
verbatim) before any behavior edit. Normative keywords SHALL/SHALL NOT below
bind N202+ implementation and N210 review. Transcribed exactly from the accepted
preregistration; any ambiguity or mismatch is a STOP for main-thread
adjudication, not permission to edit thresholds or inputs.

## Scope and choice

- SHALL run n=128 only; n256 is out of scope. SHALL NOT change the generator
  (Choice A — entropy-derived rows, NO generator change).
- SHALL re-test L055-vs-L045 at the calibrated rate; this is NOT a rerun of D12
  (D12 ran CE-f1.2, m=118). SHALL NOT create a new untested L2 family (L2 stays
  at the frozen D11 DV3 shape, not entropy-derived m=83).
- SHALL NOT revive D7-H. SHALL NOT execute the frozen 288-call batch, touch
  real data, commit, or push under N201–N210 readiness.

## Rate and rows

- SHALL state (never recompute): H_L1 = 4.286720430201375; entropy load n128 =
  548.700215065776 bits; frozen m_L1 = 110 checks; disclosed = 550 bits;
  effective factor = 1.00237. Provenance `entropy.json`.
- SHALL refuse CE-f1.0 rows (98/490/0.89302 under-disclosure).

## Graphs, seeds, cells

- SHALL realize L045 control (λ2=0.45) and L055 challenger (λ2=0.55) at the
  frozen m_L1=110 via the frozen D9 realization rule: L045 71/57/313
  `2^17+3^93`; L055 83/45/301 `2^29+3^81` (Freeze Amendment A1 — planner
  recompute CONFIRMED; supersedes the m=118 strings `2^41+3^77` / `2^53+3^65`;
  STOP on mismatch).
- SHALL build L2 DV3 at n128 on fresh seeds: m=104, E=384, variables all degree
  3, checks `3^32+4^72` (verified MATCH vs D11; STOP on mismatch).
- SHALL use exactly: L1 graphs `2026093401..06` (6); L2 graphs
  `2026093501..06` (6); blocks `2026093601..12` (12 paired, CAL-only Model-F
  artifact only). SHALL pair L1-graph-i with L2-graph-i (i=1..6); each pair ×
  12 blocks = 72 cells; the same 12 blocks SHALL feed all four arms (fully paired).
- SHALL admit every graph under A1–A6 via the accepted connectivity-first
  constructor and frozen coefficient rule
  (`COEFF_SEED = v10_seed(f"d10:coeff:128:{graph_seed}")`); admission failure
  engineering-blocks with no seed change.
- SHALL use the candidate concentration-backoff prior only (P-switched
  entrypoints); GF32/poly37; `max_iter=90` / `damping_alpha=1.0` / cold.
  Exact (n2,n3,E) counts SHALL be emitted by PROFILE_ONLY, never hand-computed;
  under Amendment A1 the normative targets PROFILE_ONLY SHALL verify are L045
  71/57/E313 `2^17+3^93` and L055 83/45/E301 `2^29+3^81` at m_L1=110.

## Calls and dispatch

- SHALL run exactly 288 decoder calls: 72 L045 + 72 L055 + 72 L2-APP + 72
  L2-ORACLE. Setup SHALL be ≤32 (= 18 constructions: 6 L045 + 6 L055 at shared
  L1 seeds + 6 L2; + 12 block samples + 2 plan/manifest; Amendment A1 supersedes
  ≤26, which counted seeds and conflated shared-seed profiles).
- SHALL share each paired block and graph identity across the four arms; L2 APP
  SHALL consume only CHECK_UPDATED L1 beliefs; L2 ORACLE SHALL use true-L1
  conditioning, be marked `ORACLE`/ungraded, and be EXCLUDED from all grading
  and all routing gates.
- SHALL fail closed unless every non-oracle transfer provenance is
  `CHECK_UPDATED`; uniform/prior-only fallback is forbidden.

## Metric isolation

- SHALL keep exact, syndrome-valid, L1-source-exact, L2-target-exact, and joint
  both-exact distinct; SHALL NOT merge `undetected`/syndrome-only outcomes into
  exact/success/FER.

## Gates, priority, terminals

- `L1-ADEQUATE(L055)` iff exact ≥18/72 AND ≥5/6 graphs have ≥2 exact AND no
  engineering/resource violation.
- `ORACLE-ADEQUATE` iff O ≥18/72. `L2-JOINT-GOOD` iff J (APP joint-both-exact
  pooled) ≥9/72. L045 pooled exact + paired discordances descriptive only,
  never gating.
- Routing (first match wins) SHALL be exactly:
  1. engineering/resource violation → `N_ROUTE_BLOCKED_ENGINEERING`;
  2. NOT `L1-ADEQUATE` → `N_ROUTE_L1_CONSTRUCTION`;
  3. `L1-ADEQUATE` AND NOT `L2-JOINT-GOOD` AND NOT `ORACLE-ADEQUATE` →
     `N_ROUTE_L2_DEGREE`;
  4. `L1-ADEQUATE` AND `ORACLE-ADEQUATE` AND NOT `L2-JOINT-GOOD` →
     `N_TRANSFER_BOTTLENECK_RECORDED`;
  5. `L1-ADEQUATE` AND `L2-JOINT-GOOD` → `N_ROUTE_SCALE_VALIDATION`;
  6. else → `N_ROUTE_AMBIGUOUS`.
- Terminals SHALL be exactly the six labels above; SHALL NOT add, rename, or drop
  any label.

## Roots, command, budgets, ceiling

- Future root SHALL be exactly
  `workspace/v72p2d14_discriminator/20260914_r1/` (absent until separately
  authorized execution) with six-file shape (`command_log`,
  `decoder_records`, `graph_records`, `arm_summary`, `manifest`, `summary`)
  and future `batch_id == d14-discriminator-v1` (verifier rejects all else).
- Frozen exact command (unauthorized) SHALL be exactly:

```text
.venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/v72p2d14_discriminator/20260914_r1
```

- Budgets: ≤288 decoder calls; ≤32 setup units (Amendment A1; see Calls);
  ≤1800 s wall total; ≤120 s per
  call; RSS <2147483648 B; one process; CPU-only; no
  retry/resume/repair/seed search/tuning. Ceiling breach → STOP, re-scope, never tune.
- Claim ceiling: synthetic diagnostic only; routes the next investment; no FER,
  leakage, SKR, real-data, qualification, promotion, optimality, or
  route-closure claim; grants no execution.

## Reuse prohibitions

- SHALL import the §-reuse-map helpers (D11/D12/D14/R2/D5/D7) unchanged; SHALL
  NOT reimplement message semantics, q extraction, provenance token/guard,
  oracle conditioning, floor/renorm order, A1–A6 predicates, coefficient
  stream, or copy decoder/GF32 kernels. One construction path per frozen arm
  family.
- SHALL NOT execute N, bind a production decoder, load Model-F content, create
  the future root, modify predecessor roots, implement D7-H, commit, or push
  under this change's readiness tasks.

## Freeze Amendment A1 (normative deltas; retain + supersede, 2026-09-14)

- Retains the accepted prereg (never edited); supersedes ONLY: (i) L1 check
  allocations `2^41+3^77` / `2^53+3^65` (m=118) → `2^17+3^93` / `2^29+3^81`
  (m=110); (ii) setup ≤26 → ≤32 with PROFILE scope 18 graphs / 12 seeds.
- SHALL reject m_L1=118 (590 bits disclosed, effective ≈1.0753, destroys Choice
  A effective ≈1.0). SHALL keep variable counts 71/57/E313 and 83/45/E301.
- Unchanged and still binding: thresholds/gates/terminals/seeds/rate-math/
  claim-ceiling, 288 calls, wall/CPU/RSS limits, root/command, pairing,
  prior/decoder/admission/provenance contract, metric isolation, L2 DV3 shape.

## R2 authorized-path completion (normative deltas; retain + supersede, 2026-09-14)

Authority: R2 packet; rationale and completion scope: `design.md` §9. Track:
`EXPLORE` readiness planning (docs only; no execution, decoder calls 0).

- APP transfer-source profile: `L2_APP` SHALL source the **L055 challenger L1
  `CHECK_UPDATED` beliefs**, one per paired (pair, block) cell (72 calls, the
  single shared stream). Each APP call SHALL decode the shared DV3 L2 graph on
  the canonical forward-transfer prior mixed from that cell's L055 L1 belief.
  Sourcing from CONTROL, from both profiles, per-cell best-of, or from the
  oracle prior is FORBIDDEN (design §9.2). The fail-closed `CHECK_UPDATED`
  guard is unchanged.
- `L1-ADEQUATE` SHALL grade the **L055 challenger arm only** (exact ≥18/72 AND
  ≥5/6 graphs with ≥2 exact AND no engineering/resource violation). L045 pooled
  exact + paired discordances SHALL remain descriptive only and SHALL NOT gate.
- JOINT `J` SHALL be the pooled APP joint-both-exact over the 72 L055-fed APP
  cells (`L2-JOINT-GOOD` iff J ≥9/72, unchanged). ORACLE SHALL stay diagnostic
  ungraded and EXCLUDED from all grading and routing gates.
- CLI true branch: R204 SHALL replace the unconditional authorized-path
  `SystemExit` (`scripts/v72p2d14_discriminator_development.py` `main()`) with
  exactly one batch-orchestrator call + one never-overwrite writer. Unauthorized
  refusal SHALL remain before root creation, decoder binding, and Model-F load.
  The authorized launch form SHALL be the frozen command plus
  `--execution-authorized`.
- R202–R207 SHALL execute packet-exact per `design.md` §9.4 (narrow binder from
  §-reuse-map helpers only; 288-plan-before-binding orchestration; fake-run
  acceptance 288/288 + 32 setup + six files + verifier PASS + no-production-entry
  proof; boundary probe without decoding or future-root creation; independent
  re-review proving no `SystemExit`, 288/288, verifier PASS, future-root absent,
  zero production calls).
- Budgets unchanged: ≤288 decoder calls; ≤32 setup units; ≤1800 s wall total;
  ≤120 s per call; RSS <2147483648 B; one process; CPU-only; no
  retry/resume/repair/seed search/tuning. The future root SHALL remain absent
  through R2 (fake runs use fresh scratch roots only).
