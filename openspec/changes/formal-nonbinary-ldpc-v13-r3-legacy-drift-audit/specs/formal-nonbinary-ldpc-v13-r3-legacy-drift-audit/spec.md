# Spec Delta: formal-nonbinary-ldpc-v13-r3-legacy-drift-audit

> 本 delta 仅在 change 完成归档时才可合并；claim boundary 只有
> `legacy_drift_audit`，不新增 fresh-confirmation 能力。

## 1. Purpose

在用户明确授权的三份 `2026-01-21` legacy 数据上，用不变 R3 候选执行一次
漂移审计解码，量化漂移下的精确纠错表现。

## 2. Requirements

- LDA-1: The change must claim only `legacy_drift_audit`; `fresh_confirmed`,
  `promotion`, and `qualification` must be false and absent as states.
- LDA-2: The frozen R3 codebook / QSC p=.20 / flooding FFT-QSPA / max_iter=100
  must remain byte-unchanged.
- LDA-3: Exactly the first 64 complete frames per source (frame_id ascending)
  must be pre-registered and executed once; failures are retained.
- LDA-4: Alice truth may be used only for the disclosed syndrome and the
  post-decode exact_correct check.
- LDA-5: The production run must write an additive package and must not
  overwrite any existing evidence.
- LDA-6: Verify must be read-only and fail on byte changes, missing rows, or
  claim-boundary violations.
