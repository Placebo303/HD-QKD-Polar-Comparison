# Change Proposal: optimize-real-ir-methods-after-success

## Summary
Optimize Cascade-lite, Layered LDPC, and qLDPC reference methods on real arrival-time high-dimensional QKD data. The objective is to lower public leakage, improve runtime/throughput, and test scalability by increasing frame size and scanning noise levels, while maintaining `real_ir_success=True`.

## Motivation
Having established verified real IR success in the previous phase, we must now optimize method configurations. Baseline parameters (like Cascade 4-pass and LDPC parity_fraction=1.0) are highly conservative and yield poor information efficiency (negative efficiency and high leakage). Tuning these parameters will map out the operational boundaries and determine the final optimal method.

## Scope
- **Cascade-lite**: Tune passes (4 vs 3 vs 2), block size schedules, permutation modes, and refine transcript leakage accounting to be exact.
- **Layered LDPC**: Sweep parity fractions down from 1.0 (to 0.9, 0.8, 0.67, 0.5), compare LLR modes and bitplane rate schedules, and diagnose plane-specific failures.
- **qLDPC Reference**: Test feasibility on easy real frames by adjusting check fraction and row weights.
- **Polar Baseline**: Align polar results to the same representative points and handle missing fields.
- **Scalability**: Test larger frame sizes (256, 512, 1024 symbols) to observe positive empirical efficiency ($\beta_{eff} > 0$).

## Success Criteria
- Optimized configs for Cascade-lite and LDPC achieve verified success with lower leakage on the representative set.
- Scalability sweeps successfully execute and report positive $\beta_{eff}$ on larger frames.
- A final optimization and selection report is published.
