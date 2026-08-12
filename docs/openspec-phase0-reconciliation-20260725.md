# OpenSpec Phase 0 Reconciliation — 2026-07-25

## Scope and verification boundary

This is a read-only reconciliation of the five active IR-comparison changes.
No benchmark, sweep, replay, Route A, or output-generating command was run.
The six pre-existing deleted tracked files under `workspace/pytest-tmp/` are
outside this reconciliation and were not restored, staged, or changed.

The safe suite excluding `test_evidence_package.py` passed: **15 passed**
(`python -m pytest comparison_bench\\tests --ignore=...\\test_evidence_package.py
-q -p no:cacheprovider --basetemp <temp>`).  The excluded test hard-codes the
tracked `workspace/pytest-evidence-test` path, so it is not evidence for a
clean full-suite result in this worktree.

## Evidence matrix

| Change | Verified evidence | Reconciliation result | Archive decision |
|---|---|---|---|
| `real-ir-success-first` | `metrics/success.py`, `test_success_classifier.py`, representative config/subset, `real_ir_success_first/run_manifest.json`, 24-row benchmark table, and `docs/real-ir-success-audit-20260615.md` | 32/34 task items are now independently evidenced: contract, representative-path outputs, status handling, method runs, and audit. The audit bounds the claim to six 4-frame points and keeps qLDPC reference-only. | Keep active: immutable-baseline and no-overwrite review evidence remain unchecked. |
| `optimize-real-ir-methods-after-success` | Sweep configs, 216 Cascade / 240 LDPC / 84 qLDPC rows, scalability outputs, `ir_v3_run_manifest.json`, and `docs/ir-optimization-report-20260615.md` | 14/14 task items are evidenced; failed statuses remain in the sweep tables. | Do not archive: the spec requires 256, 512, and 1024-symbol support, while verified outputs/report cover 128, 256, and synthetic 2048 only. |
| `expand-real-ir-optimized-evidence` | Seven files in `expanded_real_ir_20260615/`, report, and source-manifest hashes | 19/20 task items are evidenced. All six source hashes in `expanded_evidence_manifest.json` match their current `real_ir_success_first` sources; Cascade/LDPC minimum-leak selections and qLDPC classification preservation were recomputed successfully. | Keep active until the dependent CLI change has a clean direct test run and the change is finalized together. |
| `consolidate-real-ir-evidence-package` | CLI and 26-test source file, seven generated outputs, matching source hashes, selection recomputation | 26/26 implementation/verification task items are documented; AC1–AC7 and AC10 have current artifact/source evidence. `test_evidence_package.py` has not been rerun because it deletes/recreates a fixed tracked workspace path. | Do not archive: AC8 needs a clean direct pytest run and AC9 needs a before/after source non-modification proof. |
| `group-meeting-ir-large-comparison` | 9 summary CSVs, manifest, report with 16 sections, source/output hash prefixes all match | 21/29 task items and AC3–AC8 are independently evidenced. qLDPC feasibility rows are all `reference_only`; Polar is labeled historical. | Do not archive: low-dimensional datasets have 4 frames (not >=16); 128/256 regrouping yields 2/1 frames; two expected configs and package test are absent; no current 39-test result. |

## Verified details

- `cascade_optimized_summary.csv` and `ldpc_optimized_summary.csv` each have
  six rows; every row has `real_ir_success=True` and equals the source
  dataset's minimum `leak_EC_actual_bits` among successful rows.
- `qldpc_reference_summary.csv` has seven rows and preserves the source
  `success_classification` values.
- The group-meeting manifest's 9 output hashes and 21 source-sweep hashes
  match current files. This establishes provenance, not fulfillment of the
  pre-registered sample-size requirement.
- The frozen Polar baseline remains a required review gate. No claim that it
  was unchanged by every historical change is made merely from current output
  presence.

## Phase 1 handoff

Create one new `final-ir-method-selection` OpenSpec change before changing
behavior or running confirmation data. It must pre-register frame-identical
candidate comparison, leakage compatibility, tuning/confirmation separation,
sample-size limits, and a bounded decision rule. Do not use the existing
historical Polar import as a frame-identical confirmation baseline.
