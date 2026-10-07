# Z-3 Pre-EXECUTE — f(d,bw) 曲面 + 代表点真实一致性（DECIDE，收尾指示已授权）

> 授权指针：用户 2026-10-08 收尾指示（`docs/CLOSEOUT_PLAN_20261008.md` §2 Z-3
> "2–3 个代表点做一次真实一致性解码（DECIDE，同一授权，各点只跑一次）"）。

## 冻结设计
- 曲面：Z-2 的 p(d,bw) × Z-1 的 f(p) 内插（支撑为 {0,±1} 的点直接映射；
  宽窗点（bw50/100）标"未实现（模 2k+1 推广）"；d=32（p≈0.007）标解析锚定
  f→1，不测；高 p 点（≥0.46）标 disclose-all 体制 f≈1.0x，不测）。
- 密钥率侧：SKR = R_pair × max(0, 2−f) × H_AB（R_pair = 对数/3s；公式声明）。
- 真实代表点（2 点，各只跑一次）：(d=512, bw=400) × {4dB（p≈0.12），0dB
  （p≈0.124）}；N=16384（4dB 7 块，0dB 16 块）；PEG-dv3 gap0.12 + margin 3.0
 （Z-1 p=0.12 可达：3/300 f=1.43）；先验三值模型（p 取 Z-2 冻结值，
  pa 取同段 512 边际，声明）。
- 输出根（验空后建）：`workspace/z3_surface/z3_20261008/`。

## 冻结命令
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_z3_surface --full --output-root workspace/z3_surface/z3_20261008
```

## 预算
- 预算 **3600 s**（23 块真实解码 + 曲面组装）。

## 检查单（执行前）
- [x] 用户在收尾指示中授权 Z-3 真实解码（各点只跑一次）
- [ ] 执行代码 + 接线测试；输出根验空；分支/树干净（执行前提交冻结代码）
- [ ] 跑后独立 Pre-RESULT（R13：A+B+重建全对合）
