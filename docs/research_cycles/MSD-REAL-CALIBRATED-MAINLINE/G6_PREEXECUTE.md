# G-6 Pre-EXECUTE — RA 最优点真实一致性演示（DECIDE，附条件授权已满足）

> 条件：G-5 最优（RA-q5-gap0.08/m3.0/N=32768，f=1.140）相对当前 1.227 改善
> 0.087 ≥ 0.03 ✓。备选 N=16384 对照（同配置，代理 f=1.180）。

## 冻结配置
- A：RA-q5（P1 q-per-column + 双对角 accumulator，seed 0），gap 0.08；
- B：margin 3.0 PEG-BP + K2 rescue + 算术重建（S-3′设计）。
- 先验：三值模型（R1 T2-1M：p=0.23757，条件 p₋=0.00580，经验 pa）。完整符号口径。

## 块数冻结
| 段 | N=32768 | N=16384 |
|---|---|---|
| 4dB（干净） | 3 | 7 |
| 10dB（干净） | 0（跳过：30907<32768） | 1 |
| 0dB（再检验） | 8 | 16 |
合计 35 块。

## 一致带（代理预测）
- N=32768：0/300，f=1.140，E_L≈29745。N=16384：1/300，f=1.180。
- 真实预测：块成功译出 + E_L 落带内；不做 FER 估计。

## 预算与门
- 预算 **3600 s**；只跑一次；新输出根（验空后建）：`workspace/g6_real/g6_20261008/`。
- 门：一致性演示（成功块 + E_L 带内）。

## 冻结命令
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_g5_bakeoff --real --output-root workspace/g6_real/g6_20261008
```

## 检查单（执行前）
- [x] 用户附条件授权（改善 0.087 ≥ 0.03 满足）
- [x] 执行代码（--real RA 路径）+ 接线测试（合成对，契约通过）
- [ ] 输出根验空；分支/树干净（执行前提交冻结代码）
- [ ] 跑后独立 Pre-RESULT（R13）
