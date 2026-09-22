# T3 Long-Frame Report n=5120

Grid: 6 configs ×2 datasets (synthetic+real) × 50 frames each (proxy=True)
Elapsed 61.7s, q=1024 bps=10, n_input_bits per frame=51200

## Top paths by beta_raw_avg
| rank | verify | block | parity | schedule | beta_avg | beta_synth | beta_real | FER_avg | FER_synth | FER_real | leak_avg | thr_avg | v_per_bit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 32 | 32 | 1 | 32,64,128,256 | 0.9151 | 0.8633 | 0.9670 | 0.9200 | 0.9200 | 0.9200 | 33197.0 | 510083.1 | 0.00063 |
| 2 | 64 | 32 | 1 | 32,64,128,256 | 0.9128 | 0.8634 | 0.9622 | 0.9200 | 0.9200 | 0.9200 | 35866.0 | 510610.8 | 0.00125 |
| 3 | 64 | 64 | 1 | 64,128,256,512 | 0.8873 | 0.8114 | 0.9633 | 0.8900 | 0.8600 | 0.9200 | 40836.0 | 510605.6 | 0.00125 |
| 4 | 32 | 64 | 1 | 64,128,256,512 | 0.8849 | 0.8061 | 0.9637 | 0.8900 | 0.8600 | 0.9200 | 40716.0 | 510758.8 | 0.00063 |
| 5 | 32 | 16 | 1 | 16,32,64,128 | 0.8333 | 0.7135 | 0.9530 | 0.8600 | 0.8000 | 0.9200 | 56002.0 | 510647.7 | 0.00063 |
| 6 | 32 | 32 | 2 | 32,64,128,256 | 0.8257 | 0.7263 | 0.9251 | 0.9200 | 0.9200 | 0.9200 | 71533.0 | 510802.3 | 0.00063 |

## Beta thresholds
- First beta_raw>0: verify=32 block=32 parity=1 beta=0.9151 FER=0.920 leak=33197
- First beta>0.9: verify=32 block=32 parity=1 beta=0.9151 FER=0.920

## Ablation (fixed n=5120, isolated switch vs base verify32 block32 parity1)
Base beta=0.9151 FER=0.920

| label | beta | Δbeta vs base | FER | ΔFER |
|---|---|---|---|---|---|
| verify64→32 (block32 parity1) compare: v64 - base v32 | 0.9128 | -0.0023 | 0.9200 | +0.0000 |
| parity2→1 (verify32 block32) compare: p2 - base p1 | 0.8257 | -0.0894 | 0.9200 | +0.0000 |
| block64→32 (verify32 parity1) compare: b64 - base b32 | 0.8849 | -0.0303 | 0.8900 | -0.0300 |
| block16→32 (verify32 parity1) compare: b16 - base b32 | 0.8333 | -0.0819 | 0.8600 | -0.0600 |

## Cost: FER / undetected / throughput
- undetected (=n_failed_verify) isolated per row: all paths undetected=0 except high-FER cases with verify_failed=0 (decode failure not silent). No undetected counted as success.
- v32 b32 p1: FER 0.920 (synth 0.920 real 0.920) thr 510083 bits/s
- v64 b32 p1: FER 0.920 (synth 0.920 real 0.920) thr 510611 bits/s
- v64 b64 p1: FER 0.890 (synth 0.860 real 0.920) thr 510606 bits/s
- v32 b64 p1: FER 0.890 (synth 0.860 real 0.920) thr 510759 bits/s
- v32 b16 p1: FER 0.860 (synth 0.800 real 0.920) thr 510648 bits/s
- v32 b32 p2: FER 0.920 (synth 0.920 real 0.920) thr 510802 bits/s

## Long-frame error-correction assessment
- Despite n=5120 amortizing verify to 0.0006 bits/bit, FER remains high (>0.5) across all 6 configs for ser=0.02 real data. Parity leakage ~200k bits per frame, FER ~0.7-1.0 indicates Cascade with simple block schedule under high SER still not reaching reliable reconciliation; longer frame does not fix underlying error-correction capacity — need adaptive block / soft-info / IR optimization beyond framing.
