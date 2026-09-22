# T3 Long-Frame Report n=5120

Grid: 6 configs ×2 datasets (synthetic+real) × 200 frames each (proxy=False)
Elapsed 62.4s, q=1024 bps=10, n_input_bits per frame=51200

## Top paths by beta_raw_avg
| rank | verify | block | parity | schedule | beta_avg | beta_synth | beta_real | FER_avg | FER_synth | FER_real | leak_avg | thr_avg | v_per_bit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 32 | 32 | 1 | 32,64,128,256 | 0.9777 | 0.9663 | 0.9891 | 0.9800 | 0.9800 | 0.9800 | 35732.0 | 2022432.4 | 0.00063 |
| 2 | 64 | 32 | 1 | 32,64,128,256 | 0.9773 | 0.9656 | 0.9890 | 0.9800 | 0.9800 | 0.9800 | 36036.5 | 2020169.0 | 0.00125 |
| 3 | 64 | 64 | 1 | 64,128,256,512 | 0.9709 | 0.9525 | 0.9893 | 0.9700 | 0.9600 | 0.9800 | 41169.0 | 2021837.0 | 0.00125 |
| 4 | 32 | 64 | 1 | 64,128,256,512 | 0.9706 | 0.9520 | 0.9892 | 0.9725 | 0.9650 | 0.9800 | 41280.0 | 2021379.2 | 0.00063 |
| 5 | 32 | 16 | 1 | 16,32,64,128 | 0.9586 | 0.9306 | 0.9866 | 0.9650 | 0.9500 | 0.9800 | 55153.0 | 2023263.9 | 0.00063 |
| 6 | 32 | 32 | 2 | 32,64,128,256 | 0.9542 | 0.9301 | 0.9783 | 0.9775 | 0.9750 | 0.9800 | 72156.0 | 2013095.3 | 0.00063 |

## Beta thresholds
- First beta_raw>0: verify=32 block=32 parity=1 beta=0.9777 FER=0.980 leak=35732
- First beta>0.9: verify=32 block=32 parity=1 beta=0.9777 FER=0.980

## Ablation (fixed n=5120, isolated switch vs base verify32 block32 parity1)
Base beta=0.9777 FER=0.980

| label | beta | Δbeta vs base | FER | ΔFER |
|---|---|---|---|---|---|
| verify64→32 (block32 parity1) compare: v64 - base v32 | 0.9773 | -0.0004 | 0.9800 | +0.0000 |
| parity2→1 (verify32 block32) compare: p2 - base p1 | 0.9542 | -0.0235 | 0.9775 | -0.0025 |
| block64→32 (verify32 parity1) compare: b64 - base b32 | 0.9706 | -0.0071 | 0.9725 | -0.0075 |
| block16→32 (verify32 parity1) compare: b16 - base b32 | 0.9586 | -0.0191 | 0.9650 | -0.0150 |

## Cost: FER / undetected / throughput
- undetected (=n_failed_verify) isolated per row: all paths undetected=0 except high-FER cases with verify_failed=0 (decode failure not silent). No undetected counted as success.
- v32 b32 p1: FER 0.980 (synth 0.980 real 0.980) thr 2022432 bits/s
- v64 b32 p1: FER 0.980 (synth 0.980 real 0.980) thr 2020169 bits/s
- v64 b64 p1: FER 0.970 (synth 0.960 real 0.980) thr 2021837 bits/s
- v32 b64 p1: FER 0.972 (synth 0.965 real 0.980) thr 2021379 bits/s
- v32 b16 p1: FER 0.965 (synth 0.950 real 0.980) thr 2023264 bits/s
- v32 b32 p2: FER 0.978 (synth 0.975 real 0.980) thr 2013095 bits/s

## Long-frame error-correction assessment
- Despite n=5120 amortizing verify to 0.0006 bits/bit, FER remains high (>0.5) across all 6 configs for ser=0.02 real data. Parity leakage ~200k bits per frame, FER ~0.7-1.0 indicates Cascade with simple block schedule under high SER still not reaching reliable reconciliation; longer frame does not fix underlying error-correction capacity — need adaptive block / soft-info / IR optimization beyond framing.
