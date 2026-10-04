# Change Proposal: expand-real-ir-optimized-evidence

## Summary
Expand the real-data IR optimization evidence to cover a wider range of frame sizes (64, 128, 256, and optionally 512/2048 symbols) using the optimized Cascade-lite and Layered LDPC configurations from the previous phase. The goal is to produce a larger, traceable data package quickly, not to redesign algorithms.

## Motivation
The previous optimization phase established verified real IR success on 6 representative points at frame_len_symbols=64. To strengthen the evidence base for method selection, we need to:
1. Test scalability to larger frame sizes where positive empirical efficiency (β_eff > 0) may emerge
2. Confirm that optimized configurations remain effective across frame sizes
3. Build a traceable audit trail with per-stage config snapshots
4. Produce publication-ready CSV summaries and documentation

## Scope
- **Cascade-lite**: Run optimized configs (3-4 passes, seeded_random, best schedules) on expanded frame sizes
- **Layered LDPC**: Run tuned configs (parity_fraction=0.8-0.9, uniform, bsc_estimated) on expanded frame sizes
- **qLDPC Reference**: Run reference decoder on expanded synthetic and real data points
- **Polar Existing**: Import historical baseline where available for comparison
- **Frame Sizes**: 64, 128, 256, and optionally 512/2048 if data available and cheap
- **Output**: Additive outputs under `comparison_bench/outputs_comparison/expanded_real_ir_20260615/`

## Out of Scope
- Algorithm redesign or new method implementation
- Modification of original Polar code (`src/`, `experiments/`, `tools/`)
- Overwriting existing outputs
- Relabeling qLDPC reference as production success

## Success Criteria
- Expanded CSV summaries covering 4+ frame sizes with success, leakage, runtime, beta
- Per-stage config snapshots preserved in manifest
- Documentation explaining methodology and results
- All tests pass
- No existing outputs overwritten
