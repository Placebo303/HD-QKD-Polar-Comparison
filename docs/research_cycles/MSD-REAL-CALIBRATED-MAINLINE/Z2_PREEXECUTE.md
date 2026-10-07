# Z-2 Pre-EXECUTE — (d, bw) 重分帧零解码统计（DECIDE，收尾指示已授权）

## 冻结设计
- 对 R1 三源 + 2026.1.23 三段 ttbin，按 bw ∈ {50, 100, 200, 400, 6400} ps
  重分帧（span 固定 204800 ps → d ∈ {4096, 2048, 1024, 512, 32}；
  d=32 点符合窗远大于 bin，单独处理）。
- 每点：配对（冻结 M5 链；d=32 点配对窗不变，只 bin 变宽）+ 零解码统计
  （误差支撑、p、p₋、lag-1 无记忆性、事件率、H(e) 与 H(A|B) 闭合）；
  只存计数 JSON，不解码。
- 符合窗大于 1 bin 的点单独标出支撑与熵。
- 输出根（验空后建）：`workspace/z2_reframe/z2_20261008/`。

## 冻结命令
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_z2_reframe --full --output-root workspace/z2_reframe/z2_20261008
```

## 预算
- 预算 **3600 s**（30 点 × 配对/统计 ~2 min）。

## 检查单（执行前）
- [x] 用户在收尾指示中授权 Z-2（含真实解码的 Z-3 同理）
- [ ] 执行代码 + 输出根验空；分支/树干净（执行前提交冻结代码）
- [ ] 跑后独立 Pre-RESULT（统计口径）
