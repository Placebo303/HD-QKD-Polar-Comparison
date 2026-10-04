## Historical implemented scope — consolidate-real-ir-evidence-package

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-consolidate-real-ir-evidence-package-completed/specs/spec.md -->

### R1: Input Reading
- Read `cascade_param_sweep_results.csv` from `real_ir_success_first/`
- Read `layered_ldpc_param_sweep_results.csv` from `real_ir_success_first/`
- Read `qldpc_param_sweep_results.csv` from `real_ir_success_first/`
- Optionally read `scalability/ir_benchmark_results.csv` if present
- Optionally read `scalability_synth/ir_benchmark_results.csv` if present
- Read `ir_v3_run_manifest.json` from `real_ir_success_first/`

<!-- Source: openspec/changes/archive/2026-10-04-consolidate-real-ir-evidence-package-completed/specs/spec.md -->

### R2: Selection Logic
- Cascade/LDPC optimized summaries must select minimum `leak_EC_actual_bits` **only** among `real_ir_success=True` rows
- qLDPC must remain `reference_only` unless the source row says otherwise
- If a source file is missing, skip that output (do not error)

<!-- Source: openspec/changes/archive/2026-10-04-consolidate-real-ir-evidence-package-completed/specs/spec.md -->

### R3: Output Generation
All outputs go under `comparison_bench/outputs_comparison/expanded_real_ir_20260615/`:
- `cascade_optimized_summary.csv`
- `ldpc_optimized_summary.csv`
- `qldpc_reference_summary.csv`
- `scalability_summary.csv`
- `method_comparison_by_frame_len.csv`
- `failure_region_analysis.csv`
- `expanded_evidence_manifest.json`

<!-- Source: openspec/changes/archive/2026-10-04-consolidate-real-ir-evidence-package-completed/specs/spec.md -->

### R4: Manifest
The manifest must include:
- Source file paths
- SHA-256 hashes of each source file
- Source manifest config snapshots (from `ir_v3_run_manifest.json`)
- Output file list
- Timestamp and git commit

<!-- Source: openspec/changes/archive/2026-10-04-consolidate-real-ir-evidence-package-completed/specs/spec.md -->

### B1: CLI Invocation
```bash
python -m comparison_bench.cli.make_expanded_evidence_package \
  --input-dir comparison_bench/outputs_comparison/real_ir_success_first \
  --output-dir comparison_bench/outputs_comparison/expanded_real_ir_20260615
```
