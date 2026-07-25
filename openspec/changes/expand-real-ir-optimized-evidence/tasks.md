# Tasks: expand-real-ir-optimized-evidence

## 1. OpenSpec Documentation
- [x] Create proposal.md
- [x] Create design.md
- [x] Create tasks.md

## 2. Data Consolidation
- [ ] Extract best Cascade configs per point from cascade_param_sweep_results.csv
- [ ] Extract best LDPC configs per point from layered_ldpc_param_sweep_results.csv
- [ ] Extract qLDPC reference results from qldpc_param_sweep_results.csv
- [ ] Consolidate scalability data from scalability/ and scalability_synth/
- [ ] Create method_comparison_by_frame_len.csv

## 3. Failure Region Analysis
- [ ] Analyze failure patterns across frame sizes and noise regimes
- [ ] Create failure_region_analysis.csv

## 4. Evidence Report
- [ ] Write docs/expanded-real-ir-evidence-20260615.md
- [ ] Include frame size coverage matrix
- [ ] Include best-config tables per method
- [ ] Include scalability analysis
- [ ] Include failure region analysis
- [ ] Include data provenance and traceability

## 5. Manifest
- [ ] Create expanded_evidence_manifest.json with source file references

## 6. Validation
- [ ] Run pytest
- [ ] Verify all CSV data matches source files
- [ ] Verify no existing outputs were modified
