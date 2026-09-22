# D14 Scientific Validity Reset R1 — Copyable Prompt

Work in repository `HD-QKD_Polar_Comparison` on branch
`formal-ir-v72p1-addendum-clean`. Execute the complete task packet:

`.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md`

Start read-only and follow Phases S–N in order. This authorizes the scoped local
milestone commits described in Phase S after manifest review, the OpenSpec and
implementation correction that switches P0/G1/G2 synthetic production
entrypoints to the already accepted concentration-backoff prior, additive G2/X4
corrigenda, and the no-decoder L1/L2 rate-calibration audit. It authorizes no
push and no production decoder, DE, G1/G2 rerun, real-data, CAL/VAL resampling,
D7-H, or next calibrated batch execution.

Treat the reported entropy and effective-rate numbers as hypotheses: recompute
them independently from the accepted artifacts and retain discrepancies. Keep
all historical roots immutable. Use explicit Git pathspecs only; never stage the
whole dirty tree or normalize unrelated files. Obtain one independent review
with `EVIDENCE_ACCESS: VERIFIED` before declaring the calibrated next batch
ready.

Return exactly under the packet contract. A frozen next execution packet grants
no execution; stop at
`D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
