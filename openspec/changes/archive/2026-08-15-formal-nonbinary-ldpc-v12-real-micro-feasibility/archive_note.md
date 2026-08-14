# V12 Archive Note (2026-08-15)

Change: `formal-nonbinary-ldpc-v12-real-micro-feasibility`

**Status**: ARCHIVED (2026-08-15) — terminal state **`source_partition_blocked`** preserved.

## Frozen semantics retained by this archive

- **Terminal state**: `source_partition_blocked` — the four-frame bw200
  micro-feasibility canary cannot be executed because the reconstructed
  traceable 10 dB pool is 100% covered by historical V4/V5 frame/payload
  identities (zero fresh eligible bw200 rows; identical union in both
  prepare runs RP01-RP03).
- **V12-X01/X02 unexecuted**: archived as `blocked`; they were never run and
  are NOT reopened by archiving.
- **v2 prepare package retained**: the official package at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
  remains authoritative and read-only (v1 intermediate deleted by explicit
  user decision).
- **Archive ≠ success**: archiving does not execute X01/X02, merge
  unattained requirements, or manufacture any success declaration.
- **Delta spec NOT merged**: `specs/formal-nonbinary-ldpc-v12-real-micro-feasibility/spec.md`
  is NOT synced into `openspec/specs/` (V9/V10 precedent — unattained
  requirements must not become canonical spec).
- V12 established no finite decoder correction, FER, qualification, or
  promotion claim.

## Reason for archiving

User decision (2026-08-15, goal P0): close out V12 as a formal
housekeeping step. The V13 retrospective diagnostics route and the P1
fresh-acquisition route are separate OpenSpec changes; V12's execution
identity is NOT reused.

## Future boundary

A future real canary would require a fresh acquisition and a new OpenSpec
change. Do not reopen V12-X01/X02.
