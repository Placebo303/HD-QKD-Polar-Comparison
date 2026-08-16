# Route B M2 Control — equal-entropy QSC converges where folded structured fails

Status: COMPLETE — decisive diagnostic result

## Setup
- Channel A (real structured): q=16 folded V17/Gray `w`, H≈0.382911 bits/symbol.
- Channel B (QSC control): q=16 symmetric channel with p=0.038, H≈0.3815 bits/symbol (same entropy).
- Same DE budget: pop_size=20, max_gen=20, n_samples=10000, max_iter=100.
- Same-style 8-seed multi-start for each of rate=0.63 and rate=0.65.

## Result
- Folded real structured channel: **0/16 converged** (all previous r063/r065 runs failed).
- QSC control: **16/16 converged**, all in ~22–23 iterations, error_prob=0.

## Interpretation
- The failure of plain irregular NB-LDPC DE above rate≈0.60 on the folded real structured channel is **not a search-budget artifact**.
- The structured channel shape (per-bit-plane mismatch / Gray folding) is the limiting factor.
- Next scientific action should focus on **channel-structure-aware design** (e.g., per-symbol-class puncture, LSB public/two-step Pacher-style, or structured-DE with adapted edge labels), not blind DE budget scaling.

## Evidence
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/v18_b2_m2_qsc_ctrl_all_converged_20260816/m2_qsc_ctrl_summary.json`
- raw outputs under `workspace/nbldpc_v18_b2_qsc063_ctrl_par/` and `workspace/nbldpc_v18_b2_qsc065_ctrl_par/`
