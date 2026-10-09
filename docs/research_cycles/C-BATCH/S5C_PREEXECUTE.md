# S-5c Pre-EXECUTE — GF(5) 真实重跑（DECIDE，真实解码）

> Track: DECIDE（真实解码）。**本文件只交用户确认，不执行**：
> 用户确认后，主线程按序执行（smoke→full，每格一次）。
> 上位：R1–R17、S-1（f 新规；主度量泄漏+净密钥）、S-2（H 界）、S-5 任务包
> （S-5a/S-5b 冻结 + S-5c 配对要求）、S5_RESULT（GF5 选择）、S5B_RESULT
> （U 定义；GF5 天然覆盖正负 2）。

## 1. 冻结配置（合成验证完毕，见 S5_RESULT §3）

- 码：GF(5) RA-PEG 系综实例，N=4096，m=778（frac 0.19），种子 12192
  （已验证实例；标准系综，不是新码）。
- 先验：分源 S-2 前缀 DoubleGauss 律的逐符号 5-LLR（测试部分未参与拟合；
  A3 逐符号先验接口已加且等价测试通过）。
- 译码：A3 QSPA max_iter=100（合成验证同设置）。
- e∈{−2..2}→s=e mod 5；Alice 披露 syn=H·s（m·log2(5) bit/块）；
  Bob 由精细位置先验译码；â=b−ê；exact 打分；|e|≥3（质量 ~1e-9）诚实记 U。
- 对照：落盘 S-4d hard/plain 格（同分帧 N=4096、同 kept 对流 → 同块，
  不重跑，直接配对）。

## 2. 数据与矩阵（每格只跑一次）

- 5 源：T2-1M / T2-1.5M / T2-2M / 0dB / 4dB（bw200，校准后；块数 128/179/239/65/28）。
- 矩阵：5 格 GF5-soft（每格一次）vs 5 格 S-4d hard/plain（落盘对照）；
  McNemar 配对（同块；S-4d 块行有 okA/okB/exact，S-5c 块行同 schema）。
- 标注"已用数据上的再检验"；U 单列永不并入。

## 3. 冻结命令（确认后按序执行）

```text
# 段 0（R7 smoke：T2-1M 4 块，≤300 s；定段 1 预算 = 实测单块×639×1.5，封顶 2 h）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s5c_gf5 --smoke --output-root workspace/s5c_gf5/s5c_smoke_<date>
```

（注：当前 `msd_s5c_gf5.py` 只有 `--full`/`--self-test`；确认后补 `--smoke`
模式（4 块短跑，同冻结配置）再执行——实现差量子集，先声明。）

```text
# 段 1（冻结执行；B 由段 0 定，上确界见 §4）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s5c_gf5 --full --output-root workspace/s5c_gf5/s5c_<date>
```

- R1 功效：GF5 期望 FER≈0 vs 硬链 0.14–0.23 → 不一致对 ≈ 硬失败数（~90），
  高度可检；4dB 小样本（28 块）只报边际 + 精确 CI。

## 4. 预算与墙钟

- 段 0：≤ 300 s。段 1 上确界：段 0 实测单块成本 × 639 块 × 1.5，
  封顶 **2 h**（合成 QSPA 1.3–2.6 s/块；预计 20–40 min）。
- 输出根 fresh 纪律（脚本内写死）。

## 5. 报告（冻结口径）

- 每格：泄漏比特数（m·log2(5)/块求和）、FER 精确 CI、全链净密钥
  （R16：kept−L−tag）、McNemar（vs S-4d hard 同块）、附带 f
  （分母 S-2 H(A|B)，仅参考）。
- 预期（合成外推，非声称）：泄漏 ~0.44/对（S-4d 硬链 ~0.55–0.61），FER→0。
- 结论上限：单点真实矩阵再检验；S-4c 至此关闭（GF5 即其实现）。

## 6. 检查单（执行前，主线程在确认后逐项打勾）

- [x] 用户已确认本 Pre-EXECUTE（含 §4 预算封顶与 §2 矩阵）——2026-10-09"可以执行"
- [x] `--smoke` 模式已补且通过（T_med=1.26 s/块→预算 1204 s）；输出根 fresh
- [x] 冻结基线零 diff；分支正确
- [x] 跑后独立 Pre-RESULT（S5C_ACCEPTANCE.md：初审 R-b/R-c FAIL→返工→聚焦复审 PASS）

## 7. 请用户确认的事项（本批返回条件中的那一个决定）

- 是否按本包执行 S-5c（含 §4 预算封顶 2 h、§2 矩阵、§3 两段命令）。
  确认后主线程执行，跑后做独立 Pre-RESULT 并报告泄漏/FER/净密钥/McNemar/f参考。
