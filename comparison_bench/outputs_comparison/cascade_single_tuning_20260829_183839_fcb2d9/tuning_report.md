# Cascade Single Kernel Tuning Report

Generated: 2026-08-29T18:38:40.018483+00:00

Grid: adaptive_coeff=[0.5, 0.73] max_factor=[0.3, 0.5] passes=[3, 4] toeplitz_bits=[32]

SER=[0.02, 0.05] q=[4, 8] N=[64, 256] frames_per_point=2 total_jobs=64 elapsed_s=0.1

## Locked Default Config

```yaml
cascade_single_kernel:
  kernel: single
  block_size_policy: adaptive
  block_size_adaptive_coeff: 0.73
  block_size_caps: {'min': 8, 'max_factor': 0.5}
  lookback: fifo
  verification: toeplitz
  toeplitz_bits: 32
  seed_policy: domain-separated
  q_handling: auto
  num_passes: 3
  passes: [16, 32, 64]
  base_seed: 42
  caps: {'per_frame_s': 5, 'max_events': 100000, 'max_corrections': 4096, 'max_queue_pops': 10000}
```

Locked from Pareto: adaptive_coeff=0.73 max_factor=0.5 passes=3 toeplitz_bits=32 fer=0.000 leak/frame=61.5 thr=531929.6

## Pareto Frontier (FER / leakage / throughput)

Pareto-optimal = not dominated (lower FER, lower leak, higher throughput). Full grid in tuning_results.csv.

| adaptive_coeff | max_factor | passes | toeplitz | ser | q | N | FER | leak/frame | throughput |
|---|---|---|---|---|---|---|---|---|---|
| 0.73 | 0.5 | 3 | 32 | 0.02 | 8 | 64 | 0.000 | 61.5 | 531930 |
| 0.5 | 0.5 | 3 | 32 | 0.02 | 4 | 256 | 0.000 | 116.0 | 604558 |
| 0.73 | 0.5 | 4 | 32 | 0.02 | 4 | 256 | 0.000 | 125.0 | 615570 |
| 0.73 | 0.3 | 4 | 32 | 0.02 | 8 | 256 | 0.000 | 152.0 | 654927 |

## Notes

- Synthetic data: symmetric q-ary flips with given SER; Gray mapping; domain-separated seeds.
- Leakage is key-dependent disclosure (BLOCK_PARITY + BISECTION + VERIFICATION_TAG); toeplitz 32 simulated as leak-32 per verified frame.
- Throughput = input bits / runtime_s (includes Python overhead; compare relatively).
- Output additive under comparison_bench/outputs_comparison/cascade_single_tuning_*
