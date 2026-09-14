# Proposal — D13 L055 failure decoder ladder (readiness, D1301)

- Change: `v72p2d13-l055-decoder-ladder`
- Cycle: `V72P2D13-L055-DECODER-LADDER` (decoder-dynamics diagnostic on frozen
  failures; NOT a code-ensemble change and NOT a correction of any predecessor)
- Track: **implementation/readiness** (zero scientific calls; no D13 execution,
  no decoder calls, no root creation, no L2/D7-H, no real data, no commit/push).
  The future batch is `EXPLORE`.
- Authority (read fully first, frozen):
  `.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md`
  (§1–§4), `AGENTS.md` §1.2/§3/§5/§10.1.
- Predecessor (immutable, read-only context, never modified, never pooled):
  `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`
  (machine terminal `D12_SELECT_L055`, VERIFIED PASS_WITH_FINDINGS;
  root `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`).
  No successful D12 record enters the ladder; successes never enter the ladder.
- Branch: `formal-ir-v72p1-addendum-clean` (do not switch; no commit, no push).

## Goal

All 56 frozen L055 failures reached iteration 90. Determine whether they are
decoder-dynamics failures before changing the code ensemble. This change
freezes the complete D13 contract (56-identity selection, preserved
reconstruction fields, strict RL90 replay gate, exactly three ladder arms,
224-call ceiling, rescue counting/gates/ranking, seven terminals, future root,
budgets, claim ceiling) BEFORE any behavior edit, so D1304–D1310 can implement
readiness with zero scientific decoder calls.

## Non-Goals (hard prohibitions)

- No scientific decoder call in this change or any D1301–D1310 readiness step
  (zero D13 execution, zero decoder calls, zero D12 alteration, zero L2/D7-H,
  zero real-data contact). This task authorizes OpenSpec work, audit reads, and
  (for successors) focused fake tests and no-decoder planning only.
- No decoder duplication: D13 MUST import the existing accepted D12
  reconstruction and D7-X3 row-layered/flooding binders unchanged; no new
  decoder implementation.
- No damping tuning (damping-0.7 is an existing accepted parameter value only),
  no added arms, no seed search/repair/retry/resume, no rerun or
  re-thresholding of D12 evidence; predecessors stay contextual-only.
- No FER/leakage/SKR/qualification/promotion/publication/real-data/optimality/
  ensemble-optimality/forward-L2 claim; claim ceiling is a frozen synthetic L1
  decoder diagnostic only.
- No modification of predecessor roots, frozen baselines, `AGENTS.md`, or
  decision-log; no commit or push; no future-root creation in readiness.
- This change grants NO execution; the future batch still needs separate
  explicit authorization naming batch/branch/root/seeds/budgets.

## Impact Scope

- ADDED: `openspec/changes/v72p2d13-l055-decoder-ladder/` only (`proposal.md`,
  `design.md`, `tasks.md`, `specs/l055-decoder-ladder/spec.md`).
- READ-ONLY references: D13 packet §1–§4; D12 root
  (`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`:
  `decoder_records.csv`, `graph_records.csv`, `arm_summary.csv`, `manifest.json`,
  `summary.json`, `command_log.txt`); D12 module
  (`v72p2d12_finite_l1_degree.py`) + R2 helpers (`v72p2d10_mixed_degree_l1.py`,
  `scripts/v72p2d10_mixed_degree_l1_development.py`,
  `scripts/v72p2d12_development.py`); accepted D7-X3 binders
  (`v72p2d7_gf32_cross_layer_discriminator.py`,
  `v72p2d7_gf32_schedule_discriminator.py`); v35 decoder contract
  (`v35_algorithm_development.py`).
- FORBIDDEN: all code/scripts/tests/roots/results/predecessor
  artifacts/`AGENTS.md`/decision-log. A NEW additive change is used
  (preferred): D13 is a successor diagnostic, not a predecessor correction —
  existing changes are NOT amended.

## Frozen scientific design (packet §2, transcribed exactly)

Input root (read-only):
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Select exactly its L055 records with `exact=false`: 30 at n128 and 26 at n256.
Preserve graph/block identities, degree tables, coefficients, Model-F prior,
GF32/poly37 and cold initialization. No successful D12 record enters the ladder.

Reconstruct each input and first replay `ROW_LAYERED_90_ALPHA_1`. Every replay
must match the stored baseline fields relevant to exact, syndrome, iterations,
provenance and failure identity. First mismatch blocks all ladder calls.

Then run exactly these three arms on every selected failure:

1. `ROW_LAYERED_360_ALPHA_1`;
2. `ROW_LAYERED_360_ALPHA_0_7`;
3. `FLOODING_360_ALPHA_1`.

Audit and reuse existing D7-X3 row-layered/flooding binders and D12
reconstruction; do not implement another decoder. CHECK_UPDATED provenance is
mandatory. Exact, syndrome-valid and undetected remain separate. Total
scientific ceiling: 56 baseline replay + 56×3 ladder = 224 calls.

For each ladder arm count rescues by width and total. `MATERIAL_RESCUE` means
total rescues ≥12 and ≥4 at each width. `MODEST_RESCUE` means total 3–11 with
at least one rescue at each width. `NO_RESCUE` means total ≤2. Other asymmetric
results are `RESCUE_AMBIGUOUS`. If multiple MATERIAL arms exist, rank by total
rescues, then worst-width rescues, then mean iterations among rescues, then
fixed arm order above.

Terminals: `D13_SELECT_RL360`, `D13_SELECT_RL360_DAMP07`,
`D13_SELECT_FLOOD360`, `D13_MODEST_DECODER_RESCUE`,
`D13_NO_MATERIAL_DECODER_RESCUE`, `D13_DECODER_RESCUE_AMBIGUOUS`, or explicit
engineering/resource blocked. A selected arm requires MATERIAL_RESCUE.

Future root:
`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`.
Budgets: ≤224 scientific calls; ≤8 setup; ≤1800 s wall; ≤120 s/call; RSS
<2147483648 B; one process; no retry/resume/repair/seed search/tuning.

Claim ceiling: frozen synthetic L1 decoder diagnostic only; no ensemble
optimality, forward/L2, FER/leakage/SKR, real data, D7-H or qualification.

## Acceptance Criteria (D1301–D1303)

- D1301: this OpenSpec change exists with packet §2 frozen verbatim (input
  root read-only, 56 identities, preserved fields, no-success rule, strict
  RL90 replay contract with first-mismatch block, exactly three ladder arms,
  224 ceiling, rescue counting per arm by width+total, MATERIAL/MODEST/NO/
  AMBIGUOUS gates verbatim, ranking order verbatim, seven terminals +
  eng-blocked with MATERIAL-required-for-selection, future root, budgets,
  claim ceiling); `tasks.md` shows D1301–D1303 `[x]`, D1304–D1310 `[ ]`
  packet-exact.
- D1302: exact 56-identity freeze from read-only audit of the D12 root
  `decoder_records.csv` with selector predicate `arm == L055 AND exact == false`;
  independently confirmed 30 at n128 + 26 at n256 = 56 total; every selected
  record at iterations = 90 (`max_iter`); stored baseline fields (exact,
  syndrome, iterations, provenance, failure identity) recorded; full
  56-identity list frozen in `design.md`. Any count/iteration mismatch → STOP
  with BLOCKED + raw evidence (no D1301 freeze on ambiguous input).
- D1303: read-only binder audit with semantic map (`path:line`) for the D12
  reconstruction entry, RL90 binder, RL360 binder (or parametrizable
  `max_iter`), damping-0.7 support (existing tunable parameter only — NOT
  tuned), flooding-360 binder, and CHECK_UPDATED provenance; explicit decoder-
  duplication rejection (D13 MUST import these binders unchanged). Any required
  binder missing/unaccepted → STOP with BLOCKED + raw evidence (packet STOP:
  missing accepted decoder binder).
- D1304–D1310 remain `[ ]`, packet-exact, for successor execution.
- Zero scientific calls; zero decoder calls; no root created; future root
  verified absent; no commit/push.
- STOP on identity/count mismatch, reconstruction ambiguity, missing accepted
  decoder binder, predecessor modification, decoder/scientific entry, root
  creation, failed review or dirty-file conflict.

## Tasks

See `tasks.md`: D1301–D1303 `[x]` (this change), D1304–D1310 `[ ]`
packet-exact for successors. If any task cannot be clearly specified, flag it
as needing exploration (`/opsx-explore`); no task here is small enough to
implement directly outside the frozen pipeline.
