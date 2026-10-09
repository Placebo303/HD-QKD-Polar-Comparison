# S-4d Pre-EXECUTE — 真实重跑（DECIDE，真实解码）

> Track: DECIDE（真实解码）。**本文件只交用户确认，不执行**：
> 用户确认后，主线程按序执行（段 0 修复门→段 1 smoke→段 2 冻结每格一次）。
> 上位：R1–R17、S-1（f 新规）、S-2（H 界）、S-3（level-A 冻结配置）、
> S-4a（约定未反 8/8；G1=recon=1.0；sgn|fine S 曲线；p_minus 用实测值规则）、
> S-4b（明文兜底合成验证通过）。

## 0. S-4c 决策（可选臂，defer）

- S-4c（e∈{−1,0,+1} 软 LLR 直入 A3 GF(3)单级）**defer**，理由：
  其动因是"绕开两级交接"，而 S-4a 已证交接精确（G1=recon=1.0，48/48 格）；
  明文兜底已保证全链；S-4c 留作后备（若本包编码臂仍失败再立项）。
- 本包矩阵不含 S-4c。

## 1. 冻结链（level-A 沿用 S-3，两级交接已验证精确）

- 分帧/校准/kept 对：与 S-3 同链（bw200，d1024，δ* 分源冻结，网格 t0=tmin）。
- Level-A（冻结，不重调）：N=4096，gap=0.18，两臂（硬统一 LLR / 软混合律
  LLR，S-2 前缀律分源），RA QA=5，numba min-sum-100，种子随格记录。
- Level-B arm P（明文兜底，S-4b 已验证）：level-A-ok 块的译码标记位
  （â0≠b0，部署口径）符号直接公开，L_B=标记数×1 bit；level-A 失败块即失败。
- Level-B arm C（修复编码臂）：**精细条件先验** P(sgn|fine 子 bin，
  S-4a S 曲线分源冻结，8 子 bin）+ 实例在合成门后冻结（下）。
  其余（H 结构族、K2 rescue、 pinned 非标记位）与 S-3 同。
- p_minus 类全局量一律用实测分源校准值（S-4a §4 规则），不用模型。

## 2. 数据与矩阵（每格只跑一次）

- 5 源：T2-1M / T2-1.5M / T2-2M / 0dB / 4dB（bw200，校准后；块数同 S-3：
  128/179/239/65/28 @N=4096）。
- 矩阵：L-A{hard,soft} × L-B{plain,fixed} = 20 格；硬链（hard/plain、
  hard/fixed）即对照臂，与软链配对 McNemar。
- 每格真实只跑一次；块行落盘；U 单列永不并入。

## 3. 冻结命令（确认后按序；段 0 为条件门）

```text
# 段 0（修复门：实现精细条件 level-B；在 S-1 代理 + 参数化合成上验证条件失败率≈0；
# 门 FAIL 则段 2 只跑明文臂 + 硬对照，编码臂记合成阴性、不上真实）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s4d_fixverify --gate --output-root workspace/s4d_fix/s4d_gate_<date>
# 段 1（R7 smoke：T2-1M 每臂每 L-B 各 2 块，≤300 s；定段 2 预算 = 实测×块数×1.5，封顶 4 h）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s4d_rerun --smoke --output-root workspace/s4d_rerun/s4d_smoke_<date>
# 段 2（冻结执行）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s4d_rerun --full --gate-root workspace/s4d_fix/s4d_gate_<date> --output-root workspace/s4d_rerun/s4d_<date>
```

- 新增文件（加法，确认后才写）：`formal_ir/msd_s4d_fixverify.py`（门）、
  `formal_ir/msd_s4d_rerun.py`（runner，复用 S-3 level-A + S-4b 明文记账）；
  测试 `tests/test_s4d_rerun.py`（T0/T1 合成）。
- R1 功效：同 S-3（N=4096 每源 >100 块主源；0/4dB 小样本只报大效应 + 精确 CI）。

## 4. 预算与墙钟

- 段 0（合成）：≤ 3600 s。段 1：≤ 300 s。
  段 2 封顶 **4 h**（S-3 实测 1644 s 同量级；精细条件译码同成本类）。
- 输出根 fresh 纪律（脚本内写死；tune类补充只许加法新文件）。

## 5. 报告（冻结口径）

- 每格：全链泄漏（L_A+L_B+rescue 分解）、FER 精确 CI（Clopper-Pearson）、
  净密钥（R16 Net_seg）、McNemar（软 vs 硬，分 L-B 臂）、附带 f
  （f_hard=L/H_bin，f_soft=L/H_fine，H 取 S-2 测试部分分源值——首次可算的全链 f）。
- 第一真实全链软信息净密钥（明文臂保底；编码臂若过门则并列）即论文主结果候选。
- 结论上限：单点真实矩阵，不报泛化；S-4c 仍为后备，不在本包声称。

## 6. 检查单（执行前，主线程在确认后逐项打勾）

- [ ] 用户已确认本 Pre-EXECUTE（含 §4 预算封顶、§2 矩阵、段 0 条件门语义）
- [ ] 段 0 门结论已出（过门→双臂；FAIL→明文臂单行，编码臂记合成阴性）
- [ ] 新增 runner + 测试通过（T0/T1），`--smoke` 通过且输出根 fresh
- [ ] 冻结基线零 diff；输出根验空；分支正确
- [ ] 跑后独立 Pre-RESULT（S4D_ACCEPTANCE.md，独立线程）

## 7. 请用户确认的事项（本批返回条件中的那一个决定）

- 是否按本包执行 S-4d（含段 0 条件门语义、§4 预算封顶、§2 矩阵）。
  确认后主线程执行（段 0→段 1→段 2），跑后做独立 Pre-RESULT。
  附带：S-4c defer 是否同意（若不同意，S-4c 需另立实现包，不在本包内）。
