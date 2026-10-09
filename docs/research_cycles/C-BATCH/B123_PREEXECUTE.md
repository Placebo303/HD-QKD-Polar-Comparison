# B1–B3 Pre-EXECUTE — 零解码原始数据统计（DECIDE）

> Track: DECIDE（读已存原始 ttbin 事件；零解码，只统计，不解码、不生成密钥、不做新采集）。
> 授权指针：用户 2026-10-09 原话「一二轮都一块做，第三轮也让它看B2情况决定做不做」——
> 第一、二轮含 B1、B2、B3（见 `docs/SOFTWARE_NOW_20261009.md` §C 与
> `docs/prompts/SOFTWARE_NOW_20261009_PROMPT.md:13-17`）。
> B 组执行前不必再等用户确认，但仍先写本 Pre-EXECUTE 记录，事后做独立 Pre-RESULT。
> 上位规则：R1–R16 + R17（措辞：不写"首次"，不写"理论错误"，偏移按 μ 项解读）。

## 1. 冻结输入（10 个已存采集，只读）

- T2（2026-01-21，Type-II，base 变体，与 Z-2/C-0 同源同变体）：
  - `D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin`（T2-1M）
  - `D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin`（T2-1.5M）
  - `D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin`（T2-2M）
  - 注：T2-1M/1.5M/2M 是三段独立 3 s 采集
    （mtime 18:36:57 / 18:38:06 / 18:40:40，见 `docs/archive/v80/DATA_INVENTORY_20260921.md:22-24`），
    1M/1.5M/2M 指两路中最高的 singles，不是累计前缀。旧"伪重复"判断撤回（A4）。
- T0（2026-01-20，Type-0 nofilter，base 变体，与 1.21 同会话风格；若事件数异常则记录并改用 `.1` 变体，输出中显式声明实际变体）：
  - `D:/Data/Raw Data/2026.1.20/Type0_nofilter_500K_3s_2026-01-20_193050/Type0_nofilter_500K_3s_2026-01-20_193050.ttbin`
  - `D:/Data/Raw Data/2026.1.20/Type0_nofilter_1M_3s_2026-01-20_192857/Type0_nofilter_1M_3s_2026-01-20_192857.ttbin`
  - `D:/Data/Raw Data/2026.1.20/Type0_nofilter_1_5M_3s_2026-01-20_193255/Type0_nofilter_1_5M_3s_2026-01-20_193255.ttbin`
  - `D:/Data/Raw Data/2026.1.20/Type0_nofilter_2M_3s_2026-01-20_193411/Type0_nofilter_2M_3s_2026-01-20_193411.ttbin`
- Jan23（2026-01-23，`.1` 变体，与 Z-2/C-0 同源同变体；仅 B1 用，B3 不用）：
  - `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin`
  - `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin`
  - `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin`

## 2. 冻结设计（与 Z-2/M5/C-0 同链，只加统计）

- 冻结链：`read_ttbin_events` → `derive_alignment` 门控（`require_alignment_passed`；
  任一源 alignment blocked 则该源记 blocked、不配对、不 fallback）→
  `_pair_nearest_unique`（窗 200 ps，标称 offset 配对一次）→ `_frame_global`
 （span 204800 ps）。
- B1（Δ 分布形状与漂移）：配对残差 `Δ = pa − pb`（标称 offset 后，ps 分辨率）；
  5 ps 直方图（[−500,+500] ps）+ 样本矩/分位数；截断高斯、高斯+均匀、双高斯三拟合
  （截断到配对窗 ±200 ps，`math.erf` 显式截断修正，无新重型依赖）；尾部质量报告；
  每段按时间 3 等分估计 μ（三分均值/拟合 μ），报告漂移 max−min 及 SE。
- B2（软信息增益上限）：bw ∈ {100, 200, 400}（d = 2048/1024/512）；
  `H_bin = H(e)`（plug-in，e=(bb−aa) mod d）；
  精细相位 `f = (pb − tmin) % bw` 按 8 子 bin 分层，`H_fine = Σ (n_s/n)·H(e|s)`；
  增益 `G = H_bin − H_fine`；SE 来自 5 万对定种子子抽样 × 50 bootstrap（种子 20261009，
  如实报告子抽样量）；判据见 §5。
- B3（光源预试验 C-0b）：T0 四段 + T2 三段；T2 用 C-0 已落定 δ*（T2-1M −50 / 1.5M +50 /
  2M +50，`C0_RESULT.md` §1）做一步校准验证；T0 做 δ ∈ {−100..+100，步 25 ps} 粗扫描
  （bw200，零解码同口径）找 δ* 后报告校准后 p、误差支撑、H 分解；
  CAR 估计 `R_acc = S_A·S_B·W（W=200 ps）`、`CAR = R_c/R_acc`（公式显式声明，估计值）；
  H(A|B) 分解 `h2(p)+p·h2(p−)` 与 plug-in H(e) 对照。
- 输出：`b123_summary.json`（全量表）+ `b123_rows.jsonl`（逐段落盘）+ `b123_delta_hist.csv`
  （B1 直方图）+ `b123_soft.csv`（B2 分层表）；只统计，无熵外推、无解码、无 FER/泄漏/净密钥。
- R1 功效：B2 增益的 MDE 由 bootstrap SE 给出，随报告附样本量；B1/B3 为描述性统计，
  不做解码器效应检验。

## 3. 冻结命令

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_b123_stats --full --output-root workspace/b123_stats/b123_20261009
```

自检（不读真实数据）：

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_b123_stats --self-test
```

## 4. 预算与墙钟

- 预算 **7200 s（2 h）**。依据：C-0 同链 6 文件 41 点扫描实测 1164 s；
  本任务单遍配对 + T0 粗扫描 9 点（纯向量化重分帧），预计 < 20 min，2 h 为上确界。
- 计时 smoke：以第 1 个源（T2-1M 全 B1+B2）为 smoke；若单源耗时 ×10×1.5 超预算则中止。
- 输出根 `workspace/b123_stats/b123_20261009`：执行前验证不存在（2026-10-09 已验空 `False`，
  即不存在；见主线程记录）。若存在则中止，不覆盖。
- 实际起止墙钟：执行时记录于 RESULT。

## 5. 第三轮判据（事先写死，B2→A5/A6）

- B2 测得软信息增益 `G = H(A|B 的 bin) − H(A|B 的精细时间)` 在主要 bw（200 ps，
  其次 100/400 ps）上 **≥ 0.02 bit/符号，或 ≥ H(A|B) 的 3%**：做 A5 和 A6；
- 低于该阈值：只做 A5（理论速率工具仍有用），A6 记为负结果并写明数值；
- 结论写清样本量和置信区间（B2 输出含 n 与 bootstrap CI）。

## 6. 检查单（执行前）

- [x] 用户 2026-10-09 明确授权 B1–B3（指针见顶；DECIDE 执行前不必再等确认）
- [x] 执行代码 + 合成自检通过（`--self-test` OK，见执行记录）
- [x] 统计项仅 Δ 分布/拟合/漂移、条件熵增益、校准后 p/支撑/CAR/H 分解（+n 完整性）
- [x] 输出根验空；分支 `formal-ir-v72p1-addendum-clean`；树干净（仅新增 B 脚本 + 本包文档未跟踪）
- [x] 冻结基线（`src/`、`experiments/`、`tools/`、`results/`）未动；新增文件仅 wrapper 加法
- [x] 范围只统计：不解码、不生成密钥、不做新采集
- [x] 跑后独立 Pre-RESULT（B123_ACCEPTANCE.md，独立线程）—— **PASS**
  （独立审查线程 2026-10-09：R-a…R-e 全 PASS，主线程将审查结论存档于
  `B123_ACCEPTANCE.md`，原文逐字转录）

## 7. 结论上限（绑定）

- 本产物只支持描述性零解码统计（Δ 形状/漂移、软信息增益上限、两光源校准后 p/支撑/CAR）。
  不得由此直接得出 FER、协调效率、泄漏/净密钥、译码器选择、路线关闭或发表级 claim；
  软信息增益只报经验上限，不报可达速率（可达速率由第三轮 A5 在其门下另行给出）。
