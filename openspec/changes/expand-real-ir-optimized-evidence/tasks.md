# Tasks: expand-real-ir-optimized-evidence

## 1. OpenSpec Documentation
- [x] Create proposal.md
- [x] Create design.md
- [x] Create tasks.md

## 2. Data Consolidation
- [x] Extract best Cascade configs per point from cascade_param_sweep_results.csv
- [x] Extract best LDPC configs per point from layered_ldpc_param_sweep_results.csv
- [x] Extract qLDPC reference results from qldpc_param_sweep_results.csv
- [x] Consolidate scalability data from scalability/ and scalability_synth/
- [x] Create method_comparison_by_frame_len.csv

## 3. Failure Region Analysis
- [x] Analyze failure patterns across frame sizes and noise regimes
- [x] Create failure_region_analysis.csv

## 4. Evidence Report
- [x] Write docs/expanded-real-ir-evidence-20260615.md
- [x] Include frame size coverage matrix
- [x] Include best-config tables per method
- [x] Include scalability analysis
- [x] Include failure region analysis
- [x] Include data provenance and traceability

## 5. Manifest
- [x] Create expanded_evidence_manifest.json with source file references

## 6. Validation
- [ ] Run pytest — direct evidence-package pytest remains deferred because its fixture deletes/recreates a fixed tracked workspace path.
- [x] Verify all CSV data matches source files
- [x] Verify no existing outputs were modified
