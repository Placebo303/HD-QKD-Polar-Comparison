# D14 Scientific Validity Reset — Readiness R1 (compact readiness record)

- Authority: `.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md` (§1–§9); OpenSpec `openspec/changes/v72p2d14-scientific-validity-reset/` (proposal/design/tasks/specs).
- Track: `EXPLORE` (packet §1). Branch `formal-ir-v72p1-addendum-clean` (no switch; no commit/push in this call).
- Predecessors (trusted, not re-audited): D13 accepted `D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER`; `LAMBDA_APPLICATION_CONTRACT_DEFECT` accepted with candidate chain `prepare_model_f_prior_candidate`/`build_f_model_concentration`; G2/X4 legacy-prior caveat accepted; entropy/rate numbers are hypotheses to reproduce, never copy.
- Frozen contracts: packet §3 (S groups + STOP rule), §4 (P 3-site selection), §5 (C VR-C-03 a–e), §6 (R audit surface), §7 (N Choice A paired discriminator), §8 (verification + independent review), §9 (return contract).

## Evidence table S–N (D14-FINAL, EVIDENCE_ACCESS VERIFIED, not rerun)

| Phase | Evidence | Verdict |
|---|---|---|
| S | 4 local commits on `278fdf07` (`55ab6de`/`5f4b121`/`43308b8`/`ccc33eb`); 70 paths, 0 workspace/results/outputs; no-push verified (origin `d98db0e`, ahead-142 pre-existing); group1 deferred + group5 STOPPED uncommitted; corrected overlap sizes (decision-log 97 + extras; memory 99 + extras); 23-file content-diff, 1881 M CRLF/stat false-positives | PASS |
| P | 5 hunks (+7/-5) at `:2449`/`:2485`/`:2998`/`:3013`/`:3036`; signatures/bodies untouched; greps clean; D14P 4/4 rerun | PASS |
| C | Corrigendum 3059 B (VR-C-03 a–e verbatim); G1 §10 +12/-0; OPERATOR_RETURN §10; root re-hash match; grade literals; cycle-state additive; mixed-EOF-hunk finding (content-separable, future S3 splits by headers) | PASS_WITH_FINDINGS |
| R | Entropy recompute 7.509440314835753/4.286720430201376/3.222719884634378 (Δ≤1.8e-15, 4dp); legacy story confirmed; rows spot-match; triple mismatch +0.003/+0.001/+0.003 retained never copied; root 9/9; D12 24/432/221/0 + D11 120/720/0 undetected; separation stated; decoder 0, 0.7 s/175 MB; 10/10 rerun; repair disclosure recorded in log (run#1 sorted-of-dicts crash; run#2 multiplicity/P0-G1-dup/width-confound fixes; single rerun, inputs unchanged; root frozen) | PASS_WITH_FINDINGS |
| N | Prereg 203 lines; Choice A (110 rows, 550 disclosed, 1.00237); seeds/root absent; runner correctly absent; budgets within ceilings; thresholds + no-D7-H | PASS |

## Authorization (all false)

- Execution: false. Decoder/DE/real-data calls: 0. Staging/commits/push: none in this call.
- N root `workspace/v72p2d14_discriminator/20260914_r1/` absent; N command frozen unauthorized string only.
- OPERATOR_RETURN + `V72P2D7-ROOT-CAUSE-RESET/` dir untracked — noted for future S.

## Terminal

`D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION` (D14-FINAL recommendation; BLOCKING none; group5 STOPPED = §3 compliance; corrective rerun = non-blocking conditional satisfied by log disclosure).

## Next gate

Separate explicit batch grant (batch/branch/root/seeds/budgets) before any N execution; then DECIDE-gated Pre-EXECUTE/Pre-RESULT. No auto execution, no D7-H revival.

## Claim boundary

Synthetic diagnostic only; no FER/leakage/SKR/real-data/qualification/promotion/optimality/route-closure claim.
