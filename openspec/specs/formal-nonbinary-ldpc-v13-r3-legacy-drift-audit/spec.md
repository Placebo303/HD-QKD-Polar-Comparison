## Historical implemented scope — formal-nonbinary-ldpc-v13-r3-legacy-drift-audit

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v13-r3-legacy-drift-audit-completed/specs/formal-nonbinary-ldpc-v13-r3-legacy-drift-audit/spec.md -->

## 1. Purpose

在用户明确授权的三份 `2026-01-21` legacy 数据上，用不变 R3 候选执行一次
漂移审计解码，量化漂移下的精确纠错表现。

<!-- Source: openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v13-r3-legacy-drift-audit-completed/specs/formal-nonbinary-ldpc-v13-r3-legacy-drift-audit/spec.md -->

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
