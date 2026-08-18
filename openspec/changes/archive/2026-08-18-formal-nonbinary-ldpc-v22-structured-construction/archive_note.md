# Archive Note — formal-nonbinary-ldpc-v22-structured-construction

Status: ARCHIVED (closeout accepted, user-authorized archive 2026-08-18)

## Why archived
- V22 added structured DE harnesses and V22b high-degree MC-DE (degree cap up
  to 512). Evaluated selected plain/irregular and inherited SC-LDPC profiles at
  q=1024 on the V17 structured channel near rate 0.9375.
- The tested target-rate candidates did not converge under the current V22b
  kernel and recorded budgets. This is a negative result for those candidates,
  not a global impossibility proof.
- Finite construction was cancelled by DE gate. Finite Bob-only FER/V01 were
  NOT_RUN.

## Preserved
- Code: `nonbinary_v22_de_gate.py`, `nonbinary_v22_sc_de_gate.py`,
  `nonbinary_v22b_mcde.py`, `nonbinary_v22b_de_gate.py`, related CLIs/tests.
- Evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v22_20260816/`.
- Claim boundary: diagnostic_only, tested-candidate/current-kernel negative.

## Closeout review
- Independent read-only closeout review ACCEPT on 2026-08-17.
- Archive movement authorized by current objective on 2026-08-18.
