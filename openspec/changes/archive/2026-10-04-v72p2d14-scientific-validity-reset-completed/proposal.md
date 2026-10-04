# D14 Scientific Validity Reset R1 — Proposal (P-spec, planning only)

- Change: `v72p2d14-scientific-validity-reset`
- Authority: `.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md`
  (sole scientific authority; §1–§8). This proposal adds no scientific input,
  threshold, budget, or authorization beyond that packet.
- Track: `EXPLORE` (packet §1: no-write synthetic calibration; P/C
  implementation and R audit require no execution gate; the R run is no-decoder
  computation under the synthetic-diagnostics contract).
- Branch: `formal-ir-v72p1-addendum-clean` (do not switch; this call performs
  no commit and no push).
- Lifecycle of this call: `P-SPEC ONLY` — four OpenSpec artifacts, zero
  production-code edits, zero execution, zero decoder calls.

## Goal

Make the D14 validity reset executable by successors through four bounded
phases: (P) switch the three synthetic production entrypoints to the already
accepted concentration-backoff prior with a focused selection test; (C) attach
one additive corrigendum to the D5/D7 root-cause records superseding only the
G2/X4 scientific inference; (R) independently recompute L1/L2 generator
entropy, nominal-vs-effective rate factors, and per-block information load
with a small no-decoder audit; (N) freeze — without running — the smallest
paired L1/L2 calibrated discriminator that routes the next investment.

## Why

Per the accepted predecessors (trusted, not re-audited here): D13 closed the
decoder ladder as `D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER` with no arm
selected; `LAMBDA_APPLICATION_CONTRACT_DEFECT` rejects the per-cell prior
while `prepare_model_f_prior_candidate` / `build_f_model_concentration` is the
accepted chain; yet `run_p0_cost_synthetic`, `run_g1_synthetic`, and
`run_g2_synthetic` still select the rejected `prepare_model_f_prior`, so the
stored `G2_CURRENT_CONFIGURATION_FAILED` grade describes the executed legacy
configuration only and cannot establish n=256 finite-length failure; the
reported entropy/rate numbers (L1 4.2867, L2 3.2227, factors
0.890/0.979/1.068) are hypotheses to reproduce from artifacts, never constants
to copy. No further decoder route may be argued until prior selection,
rate calibration, and the G2 inference scope are reset on this branch.

## Predecessor context (frozen, carried — not re-decided)

- S1/S2 verified the §2 markers PRESENT; S3 committed groups 2/3/4 + manifest
  locally (ids `55ab6de` / `5f4b121` / `43308b8` / `ccc33eb` on top of
  `278fdf07`); group 1 deferred; group 5 STOPPED (carried decision, blocks
  neither P, C, R, nor N).
- Accepted Model-F input root: `workspace/v72p2d5_model_f_input/20260907_r1/`
  (`model_f_input.npz` + `model_f_input_summary.json`).
- Immutable history: `workspace/v72p2d5_g2/20260906_r1/` (4 files, 1320/1320
  calls, literal grade `G2_CURRENT_CONFIGURATION_FAILED`).
- D8–D13 milestone inventory: `docs/research_cycles/D14_VALIDITY_RESET/milestone_inventory.md`.

## Scope (P + C + R + N)

- **P — correct production prior selection.** Smallest delta: the three
  entrypoints select `prepare_model_f_prior_candidate` /
  `build_f_model_concentration`; two stale docstrings corrected; legacy
  `prepare_model_f_prior` retained untouched for historical reconstruction;
  focused-test contract (spy both estimators per entrypoint, fake decoder,
  fresh scratch, finite/normalized/non-uniform/bitwise-equal asserts,
  anti-return regression assert). No P0/G1/G2 execution.
- **C — immutable G2/X4 corrigendum.** One new additive corrigendum file,
  cross-linked from the D5 root-cause record
  (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_WIDE_ATTRIBUTION_R2.md`)
  and the D7 root-cause reset record
  (`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/OPERATOR_RETURN_R1.md`);
  historical root preserved byte-for-byte, literal grade retained,
  rejected-configuration scope stated, inference-only supersession, no
  unique-cause claim, additive status/pointer updates.
- **R — symmetric rate-calibration audit.** One small no-decoder audit module
  reusing accepted D8–D12 helpers, reading only the CAL-only Model-F artifact
  plus immutable synthetic records; persists L1/L2 generator entropy (with
  equations/axes/units/floor-order/estimator), CE constants with
  per-f/width/layer rows/disclosed/load/nominal/effective rows, per-block
  self-information joined to exact/syndrome for frozen D12+D11 blocks without
  undetected-merge, quantile diagnostics, load-vs-success separation (never
  sufficiency-labeled), and an L1/L2 cross-check vs the hypotheses with
  mismatch reporting; fresh additive audit root (CSV/JSON + one concise
  report). No decoder, no new blocks, no seed search, no real data.
- **N — freeze the next experiment, do not run it.** Docs-only frozen packet
  built solely from reviewed R evidence: entropy-derived rates/rows (or a
  generator change with stated choice + why), L055 + frozen control on L1 plus
  an L2 DV3/oracle diagnostic, paired blocks with multi-seed, batch sized only
  to route L1-vs-L2 investment, preregistered thresholds/calls/fresh
  root/command/ceiling, terminal `READY_AWAITING_EXPLICIT_AUTHORIZATION` with
  the root proven absent. No auto D7-H revival.

## Non-Goals

- No P0/G1/G2 execution or authorization; no production decoder, DE sweep,
  real data, CAL/VAL resampling, seed search, new random blocks, D7-H,
  L2 decoder batch, G1/G2 rerun, push, qualification, or publication claim
  (packet §1).
- No change to frozen D5 plans, seeds, budgets, call counts, G2 four-state
  grading, `exact_failure_fraction` naming, STRUCTURE/G0 behavior, or any
  D8–D13 terminal.
- No rewrite of any historical record, root, manifest, or grade string; no
  bulk commits; no `git add -A` / `.`; no line-ending normalization.
- No new defensive/audit/checksum/hash/tag machinery, sweep framework, or
  decoder tuning (per repository research-code engineering policy).
- No copying of the hypothesis numbers (4.2867 / 3.2227 / 0.890 / 0.979 /
  1.068) into code or records without recomputation.

## Impact Scope

- This call: `openspec/changes/v72p2d14-scientific-validity-reset/**` only
  (`proposal.md`, `design.md`, `tasks.md`, `specs/validity-reset/spec.md`).
- Successor P-impl: `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  (three call sites + two docstrings only) and
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (additive cases
  only). The `scripts/` shim delegates and carries no estimator symbol.
- Successor C-impl: one new corrigendum file plus additive pointer/status
  lines in the named D5/D7 records (historical bodies byte-identical).
- Successor R-impl+run: one new audit module + thin runner script + one new
  test file + one fresh additive audit root.
- Successor N-freeze: freeze docs under `docs/research_cycles/D14_VALIDITY_RESET/` only.
- Explicitly untouched by every phase: `src/`, `experiments/`, `tools/`,
  `results/`, all existing `workspace/` roots, `AGENTS.md`, frozen D5/D7
  plan files, `cycle_state.yaml` authorizations.

## Claim ceiling (binding on all phases)

Synthetic diagnostics only. P claims wiring selection, never performance. C
supersedes the G2/X4 inference, never the recorded execution. R reports
recomputed values or exact mismatches with cause; it never promotes
hypotheses to constants and never labels `I <= disclosed bits` sufficient
for decoding. N grants no execution and makes no route-closure, FER,
leakage, SKR, real-data, qualification, or promotion claim. The return string
`D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`
is emitted only when Phases P–N and the final independent review pass
(packet §9).

## Budgets (binding)

- P/C: zero execution — no decoder calls, no wall/RSS consumption beyond
  focused pytest in fresh basetemps.
- R: CPU-only no-decoder computation; wall time and peak RSS recorded in the
  audit log; exceeding the frozen single-phase ceilings (3600 s / 2 GiB)
  STOPs the run as out-of-scope and forces re-scoping, never tuning.
- N: batch bounded by the frozen ceilings (single call 120 s, total ≤3600 s,
  RSS < 2 GiB, ≤720 decoder calls, D10–D12 class); the exact frozen call
  count, thresholds, root, and command are fixed at N-freeze from reviewed R
  evidence and recorded before any authorization request.

## STOP rules (binding)

Per packet §8 plus: any requirement ambiguity STOPs to the planner (no
guessing); legacy-estimator reachability in any P test BLOCKs P-impl; any
modification to `workspace/v72p2d5_g2/20260906_r1` or any historical record
body STOPs C-impl; an R mismatch reported without a cause BLOCKs N-freeze;
N with a present root or any authorization flag refuses; any review FAIL
blocks its phase; any reached decoder/real-data path STOPs the phase with the
raw command/output and the single decision needed.

## Acceptance Criteria

- [ ] P-impl selects the candidate chain at all three entrypoints with the
  focused-test contract green and legacy retained; zero executions performed.
- [ ] C-impl adds the corrigendum with the required wording; historical root
  and grade literal verified unchanged; updates purely additive.
- [ ] R-impl+run persists the full required audit surface on a fresh additive
  root with zero decoder/real-data calls; hypotheses reproduced exactly or
  mismatches reported with cause.
- [ ] N-freeze fixes packet, thresholds, calls, root, command, budgets, and
  ceiling from reviewed R evidence only; root absent; no D7-H revival.
- [ ] Final independent review returns `EVIDENCE_ACCESS: VERIFIED` with a
  verdict over manifests/scope, estimator selection, unchanged roots,
  corrigendum wording, both-layer arithmetic, per-block joins,
  next-batch thresholds/budgets, and zero decoder/real-data calls.
