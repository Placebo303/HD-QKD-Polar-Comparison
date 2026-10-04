# Design: expand-real-ir-optimized-evidence

## Context

The previous optimization phase (`optimize-real-ir-methods-after-success`) established verified real IR success on 6 representative points at `frame_len_symbols=64`. The current evidence base covers:

- **Cascade-lite**: 6 representative real-data points (d8_bw180, d8_bw120, d8_bw50, d16_bw180, d16_bw100, d16_bw60) at frame_len=64, plus scalability data at frame_len=128 and 256
- **Layered LDPC**: Same 6 points at frame_len=64, plus scalability data at frame_len=128 and 256
- **qLDPC Reference**: Synthetic data at q=8,16,32 for frame_len=64,128; real data limited to low-noise points
- **Polar Existing**: Historical baseline imported for the 6 representative points

The expanded evidence phase aims to consolidate all existing data into a single traceable package and identify gaps for future expansion.

## Architecture

### Data Sources

1. **Optimized Cascade sweep** (`real_ir_success_first/cascade_param_sweep_results.csv`): 216 tasks, 6 representative points, frame_len=64
2. **Optimized LDPC sweep** (`real_ir_success_first/layered_ldpc_param_sweep_results.csv`): 240 tasks, 6 representative points, frame_len=64
3. **qLDPC reference sweep** (`real_ir_success_first/qldpc_param_sweep_results.csv`): 84 tasks, synthetic data
4. **Scalability real data** (`real_ir_success_first/scalability/ir_benchmark_results.csv`): frame_len=128, 256
5. **Scalability synthetic data** (`real_ir_success_first/scalability_synth/ir_benchmark_results.csv`): frame_len=2048
6. **Report tables** (`report_tables_v3/`): Best-by-point summaries across all methods

### Output Structure

```
comparison_bench/outputs_comparison/expanded_real_ir_20260615/
  expanded_evidence_manifest.json    # traceability manifest
  cascade_optimized_summary.csv      # best Cascade configs per point
  ldpc_optimized_summary.csv         # best LDPC configs per point
  qldpc_reference_summary.csv        # qLDPC reference results
  scalability_summary.csv            # frame_len scalability data
  method_comparison_by_frame_len.csv # cross-frame-size comparison
  failure_region_analysis.csv        # failure pattern analysis
```

### Key Design Decisions

1. **No new sweeps**: This phase consolidates existing data only. No new parameter sweeps are executed.
2. **Additive outputs**: All outputs go to a new directory. Existing outputs are not modified.
3. **CSV-only**: No code changes. Documentation and CSV summaries only.
4. **Traceability**: Each summary CSV includes source file references and config snapshots.

## Frame Size Coverage

| Frame Size | Cascade | LDPC | qLDPC | Polar |
|------------|---------|------|-------|-------|
| 64 | real (6 pts) | real (6 pts) | synth (q=4,8,16,32) | imported |
| 128 | real (scalability) | real (scalability) | synth (q=4,8,16,32) | - |
| 256 | real (scalability) | real (scalability) | - | - |
| 2048 | synth (d16) | synth (d16) | - | - |

## Risk Assessment

- **No algorithm risk**: No code changes, only documentation
- **Data integrity risk**: Low - reading existing CSVs only
- **Scope creep risk**: Medium - must resist temptation to run new sweeps
