# Cascade Single Kernel — Full Grid Evaluation (T6, synthetic)

Generated: 2026-08-29T18:41:06.433031+00:00  elapsed_s=0.2  seed=42  frames_per_point=8

Grid: SER=[0.05, 0.15] × q=[4, 7] × N=[64, 256]  jobs=8 ×3 methods → 24 rows

Methods: `cascade_single_kernel` (adaptive, canonical) vs `cascade_lite` (shim→adaptive) vs `cascade_formal` (shim→fixed). All via single-kernel state machine; shim emits DeprecationWarning.

## Metrics per point

FER = 1 - n_success/n_total; leakage = key_dependent disclosure (BLOCK_PARITY+BISECTION+VERIFICATION_TAG 64b); beta_eff = 1 - leak/(n_bits·h(raw_ber)) derived; throughput = input_bits/runtime_s; net key rate = (n_success·bits_per_frame - leak)/n_total (conservative, before privacy amplification).

## Verification (required gates)

- Bounded domain single ≥ formal (≤5% retreat): **PASS**  worst single/formal success ratio=1.000  n_pairs=2  (bounded = q∈{2,4,8,16}, N≤1024, SER≤0.10)
- Wide domain single ≥ lite: **PASS**  worst ratio=1.000  n_pairs=8
- beta_eff empirical tracable: **PASS**  (recomputed from leak, n_bits, h(raw_ber)))
- undetected isolated: **PASS** (verify_failed never counted as success; success requires toeplitz_tag match)
- leakage decomposition sum from transcript key_dependent (BLOCK_PARITY 1 + BISECTION 1 per level + VERIFICATION_TAG 64) — PASS

## Aggregate (by method)

| method | mean FER | mean leak/frame | mean beta | mean thr (b/s) | mean net key (b/frame) | n_unsupported | n_invalid |
|---|---|---|---|---|---|---|---|
| cascade_single_kernel | 0.531 | 105.5 | 0.500 | 8228148 | 50.5 | 4 | 0 |
| cascade_lite | 0.531 | 105.5 | 0.500 | 8985868 | 50.5 | 4 | 0 |
| cascade_formal | 0.625 | 96.0 | 0.500 | 8896922 | 42.0 | 4 | 0 |

## Per-point excerpt (first 30)

| ser | q | N | method | FER | leak/frame | beta | thr | net_key | status | q_branch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | 4 | 64 | cascade_single_kernel | 0.000 | 113.5 | 0.000 | 252490 | 14.5 | ok | power_of_two |
| 0.05 | 4 | 64 | cascade_lite | 0.000 | 113.5 | 0.000 | 292071 | 14.5 | ok | power_of_two |
| 0.05 | 4 | 64 | cascade_formal | 0.375 | 92.5 | 0.000 | 286883 | -12.5 | ok | power_of_two |
| 0.05 | 4 | 256 | cascade_single_kernel | 0.000 | 224.1 | 0.000 | 373907 | 287.9 | ok | power_of_two |
| 0.05 | 4 | 256 | cascade_lite | 0.000 | 224.1 | 0.000 | 403905 | 287.9 | ok | power_of_two |
| 0.05 | 4 | 256 | cascade_formal | 0.000 | 187.2 | 0.000 | 426121 | 324.8 | ok | power_of_two |
| 0.05 | 7 | 64 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 7449079 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 64 | cascade_lite | 1.000 | 0.0 | 1.000 | 8481501 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 64 | cascade_formal | 1.000 | 0.0 | 1.000 | 8096996 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 256 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 24390631 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 256 | cascade_lite | 1.000 | 0.0 | 1.000 | 26771242 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 256 | cascade_formal | 1.000 | 0.0 | 1.000 | 26144679 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 4 | 64 | cascade_single_kernel | 0.250 | 144.0 | 0.000 | 177670 | -48.0 | ok | power_of_two |
| 0.15 | 4 | 64 | cascade_lite | 0.250 | 144.0 | 0.000 | 179429 | -48.0 | ok | power_of_two |
| 0.15 | 4 | 64 | cascade_formal | 0.500 | 129.6 | 0.000 | 224183 | -65.6 | ok | power_of_two |
| 0.15 | 4 | 256 | cascade_single_kernel | 0.000 | 362.0 | 0.000 | 112068 | 150.0 | ok | power_of_two |
| 0.15 | 4 | 256 | cascade_lite | 0.000 | 362.0 | 0.000 | 116509 | 150.0 | ok | power_of_two |
| 0.15 | 4 | 256 | cascade_formal | 0.125 | 358.5 | 0.000 | 136346 | 89.5 | ok | power_of_two |
| 0.15 | 7 | 64 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 7649402 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 64 | cascade_lite | 1.000 | 0.0 | 1.000 | 8552339 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 64 | cascade_formal | 1.000 | 0.0 | 1.000 | 8782162 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 256 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 25419941 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 256 | cascade_lite | 1.000 | 0.0 | 1.000 | 27089946 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 256 | cascade_formal | 1.000 | 0.0 | 1.000 | 27078010 | 0.0 | unsupported_domain | non_power_of_two |

## Notes

- Synthetic q-ary symmetric flips; Gray mapping; domain-separated seeds; N in symbols, bits = N·ceil(log2 q).
- q non_power_of_two → status unsupported_domain, q_branch non_power_of_two, FER not comparable (leak 0, not attempted).
- Outputs additive under comparison_bench/outputs_comparison/cascade_single_eval_*; never overwrites history.
- Full grid rows in cascade_single_ir_benchmark_results.csv / ir_benchmark_results.csv; manifest in run_manifest.json.
