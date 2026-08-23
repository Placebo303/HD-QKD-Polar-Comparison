# Unit Correction to `nbldpc-v32-main-review-verdict-20260822.md` (2026-08-23)

Additive correction note. The original verdict file
`docs/nbldpc-v32-main-review-verdict-20260822.md` is preserved as-is on disk;
in-place rewriting of a persisted review record is avoided per project
additive-correction precedent (V8-60 annotation, V31 run_01/run_02 supersession,
operating-point audit v1/v2).

## What was wrong

Ground 2 of the original verdict stated B1 statistics as:

> NLL ≈ 229–245 bits/symbol against frozen reference entropies of ≈ 0.80–0.83 bits

The NLL unit was wrong: **229–245 is the raw posterior NLL mean per n=1024
block, not bits/symbol**. Per-symbol values are ≈ **0.224–0.239 bits/symbol**
(per-source ≈ 0.2239 / 0.2394 / 0.2387). The reference entropies are
per-symbol conditional entropies and should read ≈ 0.80–0.83 bits/**symbol**.
Downstream documents that copied the verdict's phrasing inherit the same error.

## Corrected statement (authoritative reading)

All 60 B1 records: initial→final L2 errors ≈ 235–252 → 458–480 (active
divergence), raw posterior NLL mean ≈ **229–245 bits per n=1024 block**
(≈ 0.224–0.239 bits/symbol) against frozen reference conditional entropies of
≈ 0.80–0.83 bits/symbol, posterior entropy ≈ 0.31 bits/symbol, anomaly flag
60/60. Over-confident wrong messages push message passing away from the truth.
This alone explains B1's divergence without invoking the QC graph.

## Scope

- Verdict logic, verdict-table entries, ACCEPT/REJECT items: unchanged.
- No numeric value changed; only units/naming corrected.
- Future citations shall use: "raw posterior NLL mean ≈ 229–245 bits per
  1024-symbol block (≈ 0.224–0.239 bits/symbol)".
- Related status fact (independently verified 2026-08-23 by coder-fast,
  read-only + focused tests): HEAD = `3110cb0e`
  ("fix(nbldpc-v32-audit-correction): enforce verifier semantic guards");
  commit touches only the audit-correction verifier CLI, its test file, and
  that change's tasks.md; docs/ untouched; focused suite 47 passed.
- Status update (2026-08-23, later the same day): F-G1 independent review
  ACCEPT; master ACCEPT recorded on commit `3110cb0e`; the correction change
  completed durable closeout and was archived
  (`openspec/changes/archive/2026-08-23-formal-nonbinary-ldpc-v32-operating-
  point-audit-correction/`, closeout commits `d76a55c3` + `b1171cc9`,
  candidate terminal `audit_corrected_rate_aligned_de_required`). This unit
  correction stands as the authoritative B1 NLL phrasing for all future
  citations: "raw posterior NLL mean ≈ 229–245 bits per 1024-symbol block
  (≈ 0.224–0.239 bits/symbol)".
