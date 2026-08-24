# Archive: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

**Date:** 2026-08-24  
**Verdict:** `PASS / pass_rate_aligned_empirical_de`  
**Review:** ER1 `ACCEPT`; Codex main acceptance recorded  
**Lifecycle:** `ARCHIVED / SUCCESSOR_NOT_AUTHORIZED`

## Execution and evidence

- User granted one explicit `EXECUTE_AUTH` for HEAD `41d31151` and the frozen
  call-matrix digest `f90e57af...11905`.
- Official `run_01` executed exactly once: 30/30 calls PASS; all six
  source×layer cells PASS 5/5.
- Strict verify returned `consistent`, `problems=[]`, `records_checked=30`.
- Independent ER1 added only `readonly_review.json` and returned ACCEPT.
- Authoritative evidence is under
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/
  nbldpc_v33_rate_aligned_empirical_de/run_01/`.

## Scientific boundary

The accepted result is exact-rate, train-only empirical-P ensemble MC-DE for
F03/A02 at the V31 layer rates. It removes the ensemble/rate veto but does not
prove a fixed QC graph, decoder, FER, finite-code performance, net key rate,
qualification, or promotion. No rerun, tuning, decoder, finite-control, or
successor was executed.

## Delta-spec handling

The delta spec remains archived and is not merged into canonical
`openspec/specs/`: this was an audit/diagnostic gate, not a reusable production
method contract.

## Next boundary

V33 PASS permits only a new OpenSpec proposal for one corrected matched
empirical-P finite-control: same V31 QC packet and decoder, oracle L1,
20 blocks/source, fresh frozen seeds, and no tuning/rerun. Proposal,
implementation, execution, and scientific acceptance each require their own
review gates; none is authorized by this archive.

## Commit chain

`0a050066` freeze → `c7b63cea` implementation → `5b8cfef3` IR1 fixes →
`a2d16476` official evidence + ER1 + closeout → this archive commit.

