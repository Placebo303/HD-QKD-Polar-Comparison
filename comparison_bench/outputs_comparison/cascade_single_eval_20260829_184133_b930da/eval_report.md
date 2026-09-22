# Cascade Single Kernel — Full Grid Evaluation (T6, synthetic)

Generated: 2026-08-29T18:41:33.286944+00:00  elapsed_s=0.1  seed=42  frames_per_point=4

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
| cascade_single_kernel | 0.500 | 104.2 | 0.500 | 6029360 | 55.8 | 4 | 0 |
| cascade_lite | 0.500 | 104.2 | 0.500 | 8043739 | 55.8 | 4 | 0 |
| cascade_formal | 0.625 | 95.9 | 0.500 | 8377435 | 48.1 | 4 | 0 |

## Per-point excerpt (first 30)

| ser | q | N | method | FER | leak/frame | beta | thr | net_key | status | q_branch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | 4 | 64 | cascade_single_kernel | 0.000 | 112.5 | 0.000 | 197455 | 15.5 | ok | power_of_two |
| 0.05 | 4 | 64 | cascade_lite | 0.000 | 112.5 | 0.000 | 281861 | 15.5 | ok | power_of_two |
| 0.05 | 4 | 64 | cascade_formal | 0.250 | 92.0 | 0.000 | 346578 | 4.0 | ok | power_of_two |
| 0.05 | 4 | 256 | cascade_single_kernel | 0.000 | 205.0 | 0.000 | 414390 | 307.0 | ok | power_of_two |
| 0.05 | 4 | 256 | cascade_lite | 0.000 | 205.0 | 0.000 | 419595 | 307.0 | ok | power_of_two |
| 0.05 | 4 | 256 | cascade_formal | 0.000 | 174.5 | 0.000 | 500452 | 337.5 | ok | power_of_two |
| 0.05 | 7 | 64 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 6310599 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 64 | cascade_lite | 1.000 | 0.0 | 1.000 | 7680000 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 64 | cascade_formal | 1.000 | 0.0 | 1.000 | 7710843 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 256 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 23594470 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 256 | cascade_lite | 1.000 | 0.0 | 1.000 | 23869460 | 0.0 | unsupported_domain | non_power_of_two |
| 0.05 | 7 | 256 | cascade_formal | 1.000 | 0.0 | 1.000 | 24517154 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 4 | 64 | cascade_single_kernel | 0.000 | 146.5 | 0.000 | 165599 | -18.5 | ok | power_of_two |
| 0.15 | 4 | 64 | cascade_lite | 0.000 | 146.5 | 0.000 | 166764 | -18.5 | ok | power_of_two |
| 0.15 | 4 | 64 | cascade_formal | 0.750 | 128.5 | 0.000 | 214271 | -96.5 | ok | power_of_two |
| 0.15 | 4 | 256 | cascade_single_kernel | 0.000 | 369.8 | 0.000 | 107729 | 142.2 | ok | power_of_two |
| 0.15 | 4 | 256 | cascade_lite | 0.000 | 369.8 | 0.000 | 111428 | 142.2 | ok | power_of_two |
| 0.15 | 4 | 256 | cascade_formal | 0.000 | 372.0 | 0.000 | 129499 | 140.0 | ok | power_of_two |
| 0.15 | 7 | 64 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 6796459 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 64 | cascade_lite | 1.000 | 0.0 | 1.000 | 7876922 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 64 | cascade_formal | 1.000 | 0.0 | 1.000 | 8170214 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 256 | cascade_single_kernel | 1.000 | 0.0 | 1.000 | 10648180 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 256 | cascade_lite | 1.000 | 0.0 | 1.000 | 23943884 | 0.0 | unsupported_domain | non_power_of_two |
| 0.15 | 7 | 256 | cascade_formal | 1.000 | 0.0 | 1.000 | 25430466 | 0.0 | unsupported_domain | non_power_of_two |

## Notes

- Synthetic q-ary symmetric flips; Gray mapping; domain-separated seeds; N in symbols, bits = N·ceil(log2 q).
- q non_power_of_two → status unsupported_domain, q_branch non_power_of_two, FER not comparable (leak 0, not attempted).
- Outputs additive under comparison_bench/outputs_comparison/cascade_single_eval_*; never overwrites history.
- Full grid rows in cascade_single_ir_benchmark_results.csv / ir_benchmark_results.csv; manifest in run_manifest.json.
