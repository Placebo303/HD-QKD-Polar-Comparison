# G2 prior-configuration corrigendum R1 — inference scope of `G2_CURRENT_CONFIGURATION_FAILED`

> Authority: D14 Scientific Validity Reset R1 packet
> (`.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md`),
> VR-C (`openspec/changes/v72p2d14-scientific-validity-reset/specs/validity-reset/spec.md`),
> design Phase C (`openspec/changes/v72p2d14-scientific-validity-reset/design.md`
> §3), and decision-log 2026-09-14 D13 MODEST validity correction
> (`docs/decision-log.md:4113–4121`).
> This file is additive. It rewrites no historical artifact and changes no
> historical terminal string.

## Preserved record

- Root `workspace/v72p2d5_g2/20260906_r1` is preserved unchanged: exactly the
  four frozen G2 files (`results.json`, `table.csv`, `report.md`,
  `execution_summary.json`) from the single authorized X4 attempt with
  1320/1320 decoder calls (440 per f; 200 blocks per f; oracle subset 40
  per f), recorded in
  `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/X4_OPERATOR_RETURN_R1.md` §2–§4.
- Literal grade `G2_CURRENT_CONFIGURATION_FAILED` is retained as the accurate
  description of the executed configuration. No grade, counter, seed, row,
  budget, or execution record is altered by this corrigendum.

## Correction

The executed X4/G2 configuration tested the rejected per-cell prior:
X4 bridges directly to the D5 G2 entrypoint (`run_g2_synthetic`), which
selects `prepare_model_f_prior` (per-cell `sm = counts + lam`), despite the
accepted `LAMBDA_APPLICATION_CONTRACT_DEFECT` and its already-accepted
concentration-backoff candidate (`prepare_model_f_prior_candidate` /
`build_f_model_concentration`).

Therefore `G2_CURRENT_CONFIGURATION_FAILED` is invalid as evidence for n=256
finite-length feasibility or route closure. It describes failure of that
legacy per-cell-prior configuration only; it does not decide whether any
honest CAL-only estimator recovers at n=256, nor does it close any route.

Supersession covers the scientific inference only, not the recorded
execution: the attempt, its coverage (1320/1320 calls), its raw counters
(0 exact / 0 syndrome per f row), and its grade stand exactly as recorded.

The prior defect is not claimed as the unique cause of all failures: other
decoder/code failures can also yield zero recovery (decision-log 4119–4121).
No single-cause attribution is made here.

## Consequences

- Historical G2/D7 artifacts, manifests, summaries, tables, reports,
  authorization records, and the `G2_CURRENT_CONFIGURATION_FAILED` terminal
  string are retained byte-identical.
- Future citations of the X4/G2 result must carry this scope: failure of the
  executed rejected per-cell-prior configuration at n=256 (f ∈ {1.0, 1.1,
  1.2}, frozen rows 196/172, 215/189, 235/206), not a general n=256
  finite-length feasibility or route-closure finding.
- The D14 Phase P correction (production selection →
  `prepare_model_f_prior_candidate`) and Phase R calibration audit exist
  precisely because this legacy-configuration result cannot bear those
  inferences by itself.
