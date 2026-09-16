# T4 Pareto Report — cascade-beta-optimal-path

- Inputs: T2 `ir_benchmark_results.csv` (48 rows) + T3 `ir_benchmark_results.csv` (12 rows) = 60 rows
- Combined derived: beta_eff=beta_kernel, leak_per_bit=leak_total/(n*bps), qber=raw_ber
- Non-dominated definition: leak_per_bit↓, FER↓, throughput↑ (O(n²) scan)
- Pareto size: 16 / 60
- Validation: True — ok

## Thresholds

- β>0 rows: 23 (example max beta 0.9893 at n=5120 verify=64 block=64 parity=1 dataset=real FER=0.980)
- β>0.9 & FER<5%: **0 rows — NO_HIGH_VALUE_WITHIN_GRID**
  - max_beta in grid: 0.9893 (n=5120 v=64 b=64 p=1 real FER=0.980 leak_per_bit=0.8365)
  - 所需参数: 达到 max_beta 的配置为 n=5120, verify=64, block=64, parity=1, schedule=64,128,256,512

## Pareto Frontier (sorted by leak_per_bit)

| n | verify | block | parity | dataset | beta_raw | beta_eff | leak_per_bit | leak_total | FER | undetected | throughput | qber |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5120 | 32 | 32 | 1 | synthetic | 0.9663 | 0.9663 | 0.5456 | 27933 | 0.9800 | 0 | 2020338 | 0.01003 |
| 5120 | 32 | 64 | 1 | synthetic | 0.9520 | 0.9519 | 0.7689 | 39367 | 0.9650 | 0 | 2022809 | 0.00989 |
| 5120 | 64 | 64 | 1 | synthetic | 0.9525 | 0.9525 | 0.7716 | 39507 | 0.9600 | 0 | 2019758 | 0.01006 |
| 5120 | 64 | 64 | 1 | real | 0.9893 | 0.9893 | 0.8365 | 42831 | 0.9800 | 0 | 2023916 | 0.07637 |
| 5120 | 32 | 32 | 1 | real | 0.9891 | 0.9891 | 0.8502 | 43531 | 0.9800 | 0 | 2024527 | 0.07637 |
| 5120 | 32 | 16 | 1 | synthetic | 0.9306 | 0.9305 | 1.1145 | 57062 | 0.9500 | 0 | 2023050 | 0.00992 |
| 2048 | 64 | 32 | 1 | synthetic | 0.2253 | 0.2253 | 3.1017 | 63523 | 0.4800 | 0 | 204640 | 0.00989 |
| 2048 | 32 | 32 | 1 | synthetic | 0.2137 | 0.2133 | 3.1853 | 65235 | 0.4600 | 0 | 204615 | 0.01003 |
| 2048 | 32 | 16 | 1 | real | 0.4236 | 0.4234 | 4.9555 | 101489 | 0.6400 | 0 | 204655 | 0.02562 |
| 2048 | 32 | 16 | 1 | synthetic | 0.0000 | 0.0000 | 5.4596 | 111813 | 0.0800 | 0 | 205129 | 0.01006 |
| 2048 | 64 | 16 | 1 | synthetic | 0.0000 | 0.0000 | 5.5899 | 114481 | 0.0000 | 0 | 206285 | 0.00952 |
| 1024 | 64 | 16 | 1 | synthetic | 0.0000 | 0.0000 | 6.1979 | 63467 | 0.0000 | 0 | 288907 | 0.01018 |
| 256 | 32 | 32 | 1 | synthetic | 0.0000 | 0.0000 | 6.7207 | 17205 | 0.0000 | 0 | 398811 | 0.00934 |
| 256 | 64 | 16 | 1 | synthetic | 0.0000 | 0.0000 | 7.2566 | 18577 | 0.0000 | 0 | 435949 | 0.00941 |
| 256 | 32 | 16 | 1 | synthetic | 0.0000 | 0.0000 | 7.8027 | 19975 | 0.0000 | 0 | 443423 | 0.01059 |
| 256 | 64 | 16 | 2 | synthetic | 0.0000 | 0.0000 | 15.3078 | 39188 | 0.0000 | 0 | 450310 | 0.01031 |

## Three Recommendations (within Pareto)

- **吞吐最优** (max throughput): n=5120 v=32 b=32 p=1 real beta=0.9891 leak/b=0.8502 FER=0.980 thr=2024527
- **泄漏最优** (min leak_per_bit): n=5120 v=32 b=32 p=1 synthetic beta=0.9663 leak/b=0.5456 FER=0.980 thr=2020338
- **FER最优** (min FER): n=2048 v=64 b=16 p=1 synthetic beta=0.0000 leak/b=5.5899 FER=0.000 thr=206285

> 注: 三者均为 Pareto 非支配点; 若存在某一单目标更优但被支配的点, 说明其在另两目标上劣化。

## Figures

- `pareto_leak_vs_fer.png`: leak_per_bit vs FER, 红色为 Pareto
- `pareto_beta_vs_n.png`: beta_raw vs n, 红色 x 为 Pareto, 虚线为 β>0 / β>0.9 阈值

## Notes

- O(n²) 扫描已自检非支配性; undetected 隔离披露 (未计入成功)。
- n=5120 长帧虽将 verify_per_bit 降至 0.0006, 但 FER 仍 ~0.98, 表明单纯增大帧长未解决 Cascade 在 SER=0.02 下的纠错能力瓶颈。
