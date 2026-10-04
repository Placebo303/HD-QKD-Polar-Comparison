# Design: D14 Scientific Validity Reset R1 (P-spec)

Status: `P-SPEC ONLY`. No behavior edits, no execution, no decoder calls, no
commit, no push. All scientific inputs, thresholds, budgets, and authorization
boundaries are frozen by
`.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md`; this
design invents none. Line numbers below are the current read (verify by
symbol, not by line, at implementation).

## 1. Symbol map (current read, read-only)

- Rejected chain: `build_f_model` (core `:247–272`, per-cell
  `sm = counts + lam`) ← `prepare_model_f_prior` (core `:2449–2477`).
- Accepted chain: `build_f_model_concentration` (core `:275–306`,
  `P(a|b) = (counts[a,b] + lam*p_global[a]) / (n_b[b] + lam)`,
  `LAMBDA_STAR = 137.3823795883264` total per-Bob-column concentration) ←
  `prepare_model_f_prior_candidate` (core `:2480–2507`).
- Stale selection (three sites): `run_p0_cost_synthetic :2996`,
  `run_g1_synthetic :3011`, `run_g2_synthetic :3034` — each calls
  `prepare_model_f_prior(_c, _b)` after `_load_model_f_input_or_blocked`.
- Stale docstrings: `:2452` ("Sole production source of `(p_b, p_f)` …") on
  the rejected function; `:2488` ("Production phases keep calling
  `prepare_model_f_prior`.") on the candidate.
- `scripts/v72p2d5_gf32_rate_mother.py` is a thin CLI shim delegating to the
  three core entrypoints; it carries no estimator symbol and needs no change
  (successor verifies by grep).
- Grade literal: `GRADE_FAILED` → `G2_CURRENT_CONFIGURATION_FAILED` (core
  `:103`); historical root `workspace/v72p2d5_g2/20260906_r1/` (4 files,
  1320/1320 calls); accepted input
  `workspace/v72p2d5_model_f_input/20260907_r1/` (npz + summary json).

## 2. Phase P — prior-selection correction (code + focused tests, no execution)

- Delta: replace the called symbol at exactly the three sites with
  `prepare_model_f_prior_candidate(_c, _b)`; identical arguments, identical
  return contract `(pb, pf)`, identical downstream (`decode_fn` binding,
  `run_*_phase`, writers). No signature, threshold, seed, budget, or writer
  change.
- Docstrings: `:2452` reworded to historical-reconstruction-only (names the
  accepted chain as the production selection); `:2488` reworded to state the
  candidate is the production selection for P0/G1/G2. Nothing else in either
  docstring changes meaning.
- Legacy retention: `prepare_model_f_prior` + `build_f_model` stay
  behavior-identical (historical artifact reconstruction needs the identity).
- Tests (additive cases in
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` only): per
  entrypoint, spy/monkeypatch both estimators — candidate exactly once,
  legacy poisoned to raise and never called; fake `decode_fn`; explicit
  `out_dir` under `tmp_path`; asserts on the selected prior (finite,
  columns sum to 1, non-uniform on the accepted Model-F fixture, bitwise /
  numerically equal to direct candidate output on the same injected tables);
  one static regression assert that the three entrypoint bodies contain no
  `prepare_model_f_prior(` call — patterns require `(` immediately after the
  legacy stem so `prepare_model_f_prior_candidate(` never matches (D7-E `e03`
  precedent). Fake Model-F tables are test-only injected, never written to
  formal roots, never claimed as CAL-TRAIN.
- Isolation: unauthorized paths refuse before work; fake paths never import
  the production decoder; formal roots snapshotted unchanged; no formal-root
  creation; `*_execution_authorized` untouched.

## 3. Phase C — additive corrigendum (docs only, no execution)

- New file (additive, follows the `D7_F_CORRIGENDUM_R1.md` pattern):
  `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`.
- Additive pointer blocks (append-only sections; historical bodies
  byte-identical): one in the D5 root-cause record
  (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_WIDE_ATTRIBUTION_R2.md`),
  one in the D7 root-cause reset record
  (`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/OPERATOR_RETURN_R1.md`),
  each linking to the new corrigendum file.
- Required wording: root `workspace/v72p2d5_g2/20260906_r1` preserved
  unchanged (4 files, 1320/1320 calls); literal grade
  `G2_CURRENT_CONFIGURATION_FAILED` retained as the accurate description of
  the executed configuration; that configuration tested the rejected
  per-cell prior (X4/`run_g2_synthetic` → `prepare_model_f_prior`) and is
  therefore invalid as evidence for n=256 finite-length feasibility or route
  closure; supersession covers the scientific inference only, not the
  recorded execution; the prior defect is not claimed as the unique cause of
  all failures (other decoder/code failures can also yield zero recovery —
  decision-log 4119–4121).
- Additive status/pointer updates only: stale D5/D7 `cycle_state.yaml` status
  fields and decision-log / project-memory pointers gain append-only entries
  pointing at the corrigendum; no historical line rewritten.
- Proof: root file listing with the grade string, plus scoped `git status`
  showing the root and record bodies untouched.

## 4. Phase R — no-decoder calibration audit (module + run, no decoder)

- New module: `comparison_bench/src/comparison_bench/formal_ir/v72p2d14_rate_calibration_audit.py`
  (pure functions; imports — never copies — the accepted D8–D12 input and
  sampling helpers; successor records the exact import map), plus thin runner
  `scripts/v72p2d14_rate_calibration_audit.py`, plus additive tests
  `comparison_bench/tests/test_v72p2d14_rate_calibration_audit.py` (tiny
  math fixtures proving the entropy/CE/self-information equations, plus
  no-write/refusal checks in fresh basetemps).
- Inputs (read-only): accepted CAL-only Model-F artifact
  `workspace/v72p2d5_model_f_input/20260907_r1/` and the immutable synthetic
  records enumerated in `milestone_inventory.md` §5 (D8–D13 roots + G2
  historical root). No VAL/real/raw reads.
- Outputs on the frozen fresh root `workspace/v72p2d14_rate_audit/20260914_r1/`
  (proven absent before the run; never overwritten): CSV/JSON artifacts plus
  one concise `report.md`, covering —
  (a) L1/L2 generator entropy with equations, axes, units (bits),
  floor/renormalization order, and estimator identity;
  (b) CE constants with provenance and, for every frozen f/width/layer row,
  rows, disclosed bits, generator entropy load, nominal factor, and effective
  factor (frozen row tables: P0/G1 n=64 → 49/59 + 43/52; G2 n=256 → 196/215/235
  + 172/189/206; `rows = ceil(n*CE*f/5)`);
  (c) per-block self-information for the frozen D12 and D11 block identities,
  joined on the stored identity fields to exact/syndrome outcomes, with
  `undetected` kept isolated (never merged into success/FER);
  (d) quantile-binned success counts and correlations as descriptive
  diagnostics;
  (e) explicit separation of expected information load from finite-code /
  decoder success — `I <= disclosed bits` is never labeled sufficient;
  (f) cross-check of the hypotheses (L1 4.2867 / L2 3.2227 / 0.890 / 0.979 /
  1.068): exact reproduced values, or the mismatch with its cause. Numbers
  are recomputed, never copied.
- Run contract: zero decoder calls, zero new random blocks, zero seed search;
  CPU-only; wall/RSS recorded; frozen-ceiling STOP per proposal.

## 5. Phase N — frozen discriminator packet (docs only, no code, no run)

- Deliverable: `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
  (frozen, unauthorized), built solely from reviewed R evidence. It fixes:
  the rate/row choice — entropy-derived rates/rows on the actual generator,
  or a generator change to match the chosen CE, with the choice and its why
  stated; the arm set — L055 plus its frozen control on L1, plus an L2
  DV3/oracle (true-U1 prior) diagnostic that never gates PASS; paired blocks
  with multiple graph seeds; the batch size — only large enough to decide
  whether the next investment belongs to L1 construction or L2 degree design;
  preregistered thresholds, exact call list, fresh root path (proven absent),
  exact command, budgets within the frozen ceilings, and the claim ceiling
  (synthetic diagnostic only).
- Terminal: `READY_AWAITING_EXPLICIT_AUTHORIZATION`. No implementation code
  in N (any future runner belongs to a later authorized change reusing the
  D11/D12 runners); no D7-H revival — D7-H is reconsidered only after
  calibrated single-layer and forward baselines show alternating transfer
  addresses the remaining bottleneck (packet §7).

## 6. Review design

- P-review / C-review / R-review / N-review: focused, artifact-against-spec
  checks by an independent thread with actual artifact access (packet §8
  checklist, scoped to the phase).
- Final review: full §8 checklist — commit manifests/scope, entrypoint
  estimator selection, unchanged historical roots, corrigendum wording,
  both-layer entropy/rate arithmetic, per-block joins, next-batch
  thresholds/budgets, zero decoder/real-data calls — returning
  `EVIDENCE_ACCESS: VERIFIED`, a verdict, blocking findings, and exact
  corrections. Any FAIL blocks its phase; no publish-then-patch.

## 7. Explicitly not in design

Decoder execution of any kind; P0/G1/G2 reruns; new graph families, seeds, or
tuning; generic sweep/audit frameworks; hash/manifest/tag machinery;
copying hypothesis numbers as constants; merging `undetected`; D7-H work;
any authorization grant.
