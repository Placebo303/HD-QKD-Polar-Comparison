# Proposal — D14N Calibrated L1/L2 Discriminator (readiness, N201)

- Repo: `HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (no switch).
- Change: `v72p2d14n-calibrated-l1-l2-discriminator`.
- Track: `EXPLORE` (implementation/readiness planning; this call: OpenSpec docs only).
- Authority: `.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1_TASK_PACKET.md`
  (§1–§2 frozen contract, §3 N201, §5–§6);
  `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
  (accepted preregistration — transcribed exactly, not reinterpreted).
- Context (trusted, read-only): D14-FINAL VERIFIED PASS_WITH_FINDINGS
  (P prior switch, C corrigendum, R entropy reproduced + triple mismatch open,
  N Choice A). Reuse donors: D11 forward-app module/runner
  (plan/dispatch/transfer/oracle pattern), D12 finite-L1 module
  (degree cells/plan/gates pattern), D14 rate-audit helpers, D5/D7 canonical
  transfer/provenance/oracle, R2 construction/admission.
- This call: docs only. No code, no execution, no decoder/real-data calls
  (decoder calls 0), no commit, no push.

## Goal

Create the OpenSpec readiness artifacts (proposal, design, tasks, delta spec)
for the N calibrated L1/L2 discriminator, transcribing prereg §2 + packet §2
verbatim, so N202–N210 implement exactly the frozen contract with zero
scientific reinterpretation.

## Non-Goals (explicitly out of scope)

- n256 extension (belongs to a later packet, not this discriminator).
- New untested L2 family (L2 stays at the frozen D11 DV3 shape, not
  entropy-derived m=83).
- Generator change (Choice A: rates/rows derived from actual generator entropy;
  generator NOT changed).
- D7-H revival (NOT revived; §10 of prereg states reconsideration conditions only).
- The frozen 288-call batch, D7-H, real data, push (packet §1: unauthorized).
- Re-running D12 at CE-f1.2/m=118 (this re-tests L055-vs-L045 at the calibrated
  rate; it is NOT a rerun of D12).
- Hand-computed (n2,n3,E) counts in the freeze (emitted by the future runner's
  PROFILE_ONLY plan from the frozen rule + frozen seeds, verified at review).

## Impact scope

- Allowed files: `openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/**`
  only (this change's `proposal.md`, `design.md`, `tasks.md`,
  `specs/calibrated-discriminator/spec.md`).
- Forbidden: code/scripts/tests/roots/`AGENTS.md`/decision-log.
- Affected spec: new delta spec `calibrated-discriminator` (additive; no
  existing spec modified).

## Frozen contract (prereg §2 + packet §2, transcribed verbatim)

- n=128 only; L1 m=110; L045 control and L055 challenger (prereg §3).
- L1 rate math (Choice A, entropy-derived — stated, not recomputed, prereg §4):
  H_L1 = 4.286720430201375; entropy load n128 = 128 × H_L1 =
  548.700215065776 bits; frozen m_L1 = ceil(548.700215065776/5) = **110 checks**;
  disclosed = 550 bits; effective factor = 550/548.700215065776 = **1.00237**.
- L045/L055 degree cells (frozen D12 cells for n128, verified MATCH §verification):
  L045 71/57/313 `2^41+3^77`; L055 83/45/301 `2^53+3^65`.
- L2 DV3 (frozen D11 shape at n128, verified MATCH §verification): m=104,
  E=384, check allocation `3^32+4^72`.
- Seeds (fresh; absence re-confirmed §verification): L1 graphs `2026093401..06`
  (6); L2 graphs `2026093501..06` (6); blocks `2026093601..12` (12 paired).
  Pairing: L1-graph-i pairs with L2-graph-i (i=1..6); each pair × 12 blocks =
  72 cells; same 12 blocks feed L045-L1, L055-L1, L2-APP, L2-ORACLE (fully paired).
- Calls: 72 each for L045, L055, L2 APP and L2 ORACLE; exactly **288** planned.
  Setup units ≤26 (= 12 graph constructions + 12 block samples + 2 plan/manifest).
- Prior/decoder: candidate concentration-backoff prior only (P-switched
  entrypoints); GF32/poly37; row-layered cold decoder max_iter=90,
  damping=1.0; every non-oracle transfer requires `CHECK_UPDATED`; oracle is
  diagnostic and never gates (ungraded, EXCLUDED from all grading and routing gates).
- Metrics: exact/syndrome/source/target/joint/undetected remain separate;
  `undetected` isolated, never merged into success/FER.
- Six routing terminals + priority (prereg §7 verbatim, first match wins):
  1. engineering/resource violation → `N_ROUTE_BLOCKED_ENGINEERING`;
  2. NOT `L1-ADEQUATE` → `N_ROUTE_L1_CONSTRUCTION`;
  3. `L1-ADEQUATE` AND NOT `L2-JOINT-GOOD` AND NOT `ORACLE-ADEQUATE`
     (D11 L2-code-bottleneck pattern, O≤6) → `N_ROUTE_L2_DEGREE`;
  4. `L1-ADEQUATE` AND `ORACLE-ADEQUATE` AND NOT `L2-JOINT-GOOD` →
     `N_TRANSFER_BOTTLENECK_RECORDED`;
  5. `L1-ADEQUATE` AND `L2-JOINT-GOOD` → `N_ROUTE_SCALE_VALIDATION`;
  6. else → `N_ROUTE_AMBIGUOUS`.
- Budgets: ≤288 decoder calls; ≤26 setup; ≤1800 s wall total; ≤120 s per call;
  RSS <2147483648 B (<2 GiB); one process; CPU-only;
  no retry/resume/repair/seed search/tuning.
- Future root `workspace/v72p2d14_discriminator/20260914_r1` remains absent
  (confirmed absent §verification).
- Claim ceiling: synthetic diagnostic only; routes the next investment
  (L1 construction vs L2 degree design); no FER, leakage, SKR, real-data,
  qualification, promotion, optimality, or route-closure claim; grants no execution.

## Verification (this call, read-only)

- D12 cells MATCH: L045 n128 / L055 n128 cells verified against
  `openspec/changes/v72p2d12-finite-l1-degree/specs/finite-l1-degree/spec.md:20-23`,
  `design.md:62-64,92-120`, `proposal.md:73-75` — no mismatch, no STOP.
- D11 L2 MATCH: n128 m=104/E=384/`3^32+4^72` verified against
  `openspec/changes/v72p2d11-forward-app/specs/forward-app/spec.md:27-30` and
  `design.md:32-41` — no mismatch, no STOP.
- Seeds/root absence re-confirmed: repo content search for
  `20260934|20260935|20260936|v72p2d14_discriminator` returns only the
  authorizing packet, the prereg, and docs referencing this freeze
  (no code/script/test/workspace usage); direct read of the frozen root path
  returns `File not found` — no STOP.

## Acceptance criteria

- [x] N201: this `proposal.md` + `design.md` + `tasks.md` +
      `specs/calibrated-discriminator/spec.md` exist under this change dir only.
- [x] Every frozen value above transcribed exactly from prereg §2–§8 +
      packet §2 (transcription-verification table in the N201 return).
- [x] Explicit reused-helper list (D11/D12/D14/R2/D5/D7 symbols) + rejected
      duplication recorded in `design.md`.
- [x] `tasks.md`: N201 [x], N202–N210 packet-exact [ ].
- [x] No ambiguity/mismatch found; else STOP (none triggered).
- [x] Execution false, decoder calls 0, no commit/push.
