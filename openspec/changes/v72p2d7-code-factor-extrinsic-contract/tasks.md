# Code-factor extrinsic contract — tasks (freeze only, Phase B)

> Operator authority: Phase B (freeze) only, per
> `.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md`
> §5. Docs only, zero decoder calls, zero Model-F content reads, zero
> roots, zero identifiers, zero push, zero commits beyond the scoped docs
> commit. The EXT-01–EXT-06 acceptance matrix in `proposal.md` and the
> fixture families in `design.md` are authoritative for the later
> implementation; this file references them rather than restating them.

- [x] B-freeze — **Freeze before code (docs only, this change).** This
  change folder (`proposal.md`, `design.md`, `specs/`, `tasks.md`)
  freezing packet §5 in substance (formulas, enums, fields, no-persistence,
  cold/it0/warm, matrices, tolerances, compatibility, D7-H closed, file
  map) plus the cycle directory
  `docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/` with
  `D7_G_PREREG_R1.md` and `cycle_state.yaml` (D7-F keys adapted to D7-G;
  all authorization/promotion/decoder/result false; attempts zero; no
  identifier/root; predecessor D7-F acceptance;
  `next_gate: D7_G_IMPLEMENTATION_PENDING`). Single scoped commit
  `docs(d7-g): freeze code-factor extrinsic contract`.
- [x] C-impl — **Minimal implementation (complete).** New
  oracle module only at the frozen path (numpy-only; must not import the
  production check-update/extrinsic helper); producer/helper edits confined
  to `v35_algorithm_development.py` (additive optional fields + one narrow
  consumer helper); flooding fields only per the frozen decision rule
  (default DEFERRED). No change to hard decisions, stopping, iteration
  counts, `final_beliefs`, existing provenance, decoder numerics, or
  current return behavior beyond additive optional fields.
  Evidence: v35 diff +127/−0 additive (producer + helper, flooding
  DEFERRED); oracle `v72p2d7_gf32_extrinsic_oracle.py` new (numpy-only,
  zero production imports per F01 §2).
- [x] D-tests — **Tests (complete).** At minimum cover the
  packet §§7–8 list: every new enum/field at all decoder return sites;
  cold iteration 0, cold ≥1, max-iter, exception/nonfinite, warm paths;
  reconstruction identity and normalization; tree-exact oracle and loopy
  independent recurrence; posterior double-count negative control;
  no-returned-evidence exact factor-graph match; helper rejection matrix;
  existing BP provenance guards unchanged; existing D7-E/F outputs and
  frozen roots untouched; current consumers compile and retain prior
  behavior; static inventory preventing cross-layer consumers from using
  explicit extrinsic without their own future OpenSpec. Tiny synthetic
  decoder calls only.
  Evidence: contract suite 48/48; D7-A 14/14; BP-compat 14/14;
  BP-belief 22 passed + 1 field-list pin (T1 PASS-neutral, numeric tail
  2.43e-17); D7-E 38 passed + 2 (1 transitive pin, 1 env precondition);
  EXT-05a 2/2, EXT-06 4/4. D04 decisive: double-count gaps ≥5x floors;
  extrinsic transfer matches sum-product ≤3.34e-16; it0 neutral, no false
  lift; warm/unknown rejected.
- [x] E-reviews — **Independent reviews (complete).**
  Mathematical/implementation review verdict
  `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS`; then
  integration-readiness review verdict
  `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS`. Neither
  authorizes D7-H.

## Non-goals

- No execution authorization, no D7-G run, no result acceptance in this
  change.
- No scientific/budget/terminal/schema change beyond the frozen contract;
  no V35/D5/D6/D7-A/B/C/D/E/F edits; no D7-H freeze; no R1d/G1/G2 work.
