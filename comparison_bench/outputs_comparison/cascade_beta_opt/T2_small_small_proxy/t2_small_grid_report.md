# T2 Small Grid Report (T2_small_small_proxy)

Grid: n=[256, 1024, 2048] × verify=[32, 64] × block=[16, 32] × parity=[1, 2] = 24 points
Frames per point: synthetic=50, real=50 (proxy=True)
Elapsed: 142.8s

## Top-3 paths by beta_raw (avg over synthetic+real)

| rank | n | verify | block | parity | schedule | beta_raw_avg | leak_total_avg | FER_avg | verify_per_bit |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2048 | 64 | 32 | 1 | 32,64,128,256 | 0.5831 | 45899.0 | 0.7400 | 0.00313 |
| 2 | 2048 | 32 | 32 | 1 | 32,64,128,256 | 0.5822 | 46625.5 | 0.7300 | 0.00156 |
| 3 | 2048 | 64 | 16 | 2 | 16,32,64,128 | 0.4630 | 124558.0 | 0.5300 | 0.00313 |

## Verify amortization theory (long frame)

Theory: verify bits amortized per input bit = verify / (n * bps). Longer n reduces per-bit overhead, improving beta.

- n=256: mean beta=0.0000, mean verify_per_bit=0.01875, mean leak_total=46237.4
- n=1024: mean beta=0.1034, mean verify_per_bit=0.00469, mean leak_total=115951.5
- n=2048: mean beta=0.3131, mean verify_per_bit=0.00234, mean leak_total=111471.8

Validation: 
- Trend n 256→2048 (verify=32,block=32,parity=1): PASS (n=256 beta=0.000, n=1024 beta=0.000, n=2048 beta=0.582)

Outputs: ir_benchmark_results.csv, t2_leak_decomposition.csv