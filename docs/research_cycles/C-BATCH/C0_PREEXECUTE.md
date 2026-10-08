# C-0 Pre-EXECUTE — 残余时延 δ 细粒度扫描（DECIDE，零解码）

> Track: DECIDE（读已存原始事件；零解码，只统计 p、p₋ 与误差支撑）。
> 授权指针：`docs/C_BATCH_PREREG_20261008.md` §4 C-0（"用户已随本计划批准"），
> 本批任务下达时用户重申"用户已随计划批准"。
> 上位规则：R1–R16；个位数失败计数写作「未定」（本步骤零解码，无失败计数）。

## 冻结输入（6 文件，与 Z-2 同源同变体）
- R1（2026.1.21，base 版）：
  `D:/Data/Raw Data/2026.1.21/Type2_1M_3s_2026-01-21_184040/Type2_1M_3s_2026-01-21_184040.ttbin`；
  `D:/Data/Raw Data/2026.1.21/Type2_1-5M_3s_2026-01-21_183806/Type2_1-5M_3s_2026-01-21_183806.ttbin`；
  `D:/Data/Raw Data/2026.1.21/Type2_2M_3s_2026-01-21_183657/Type2_2M_3s_2026-01-21_183657.ttbin`。
- 2026.1.23（.1 版）：
  `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_0dB_2026-01-23_174534.1.ttbin`；
  `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_4dB_2026-01-23_174758.1.ttbin`；
  `D:/Data/Raw Data/2026.1.23/Type2_1M_600k_3s_10dB_2026-01-23_174842.1.ttbin`。

## 冻结设计
- 冻结链（与 Z-2/M5 同序列）：`derive_alignment` 门控 → `require_alignment_passed`
  标称 offset → `_pair_nearest_unique`（符合窗 200 ps）配对一次 → `_frame_global`
  （span 204800 ps，bw ∈ {200, 400} → d ∈ {1024, 512}）。
- δ 扫描：δ ∈ [−100, +100] ps，步长 **5 ps**（41 点，满足预注册步长 ≤ 5 ps）；
  配对冻结，Bob 配对时刻平移 `pb + δ` 后重分帧，只改变分 bin 归属，
  隔离时钟残余的 bin 对准效应。
- 每点统计（仅此四项 + n 完整性）：`n`、`p`、`p_minus_cond`（Z-2 定义
  P(e=d−1|e≠0)，符号翻转源保留主导方向）、`support_size` + 支撑分布
  `top_errors`。不计算熵、不解码。
- 对照：T2-1M 在 δ ∈ {−100, 0, +100} ps 做 3 次重配对（offset+δ），
  界定冻结配对偏差（`repaired: true` 行）。
- 输出：`c0_rows.jsonl`（逐点落盘）+ `c0_summary.json`（41×2×6=492 冻结行 + 3 对照行）。

## 冻结命令
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_c0_delayscan --full --output-root workspace/c0_delayscan/c0_20261008
```

## 预算与墙钟
- 预算 **3600 s**（6 文件加载 ~10 min 既有先例 + 向量化扫描 + 3 次重配对；R7）。
- 计时 smoke：以第 1 个源（T2-1M，含对照）为 smoke；若单源耗时 ×6×1.5 超预算则中止。
- 输出根 `workspace/c0_delayscan/c0_20261008`：执行前验证不存在（2026-10-08 已验空 `False`）。
- 实际起止墙钟：执行时记录于 RESULT。

## 检查单（执行前）
- [x] 用户随 C 批计划授权 C-0（指针见顶）
- [x] 执行代码 + 合成自检通过（`--self-test` OK：p/p₋/支撑/分帧四断言）
- [x] 步长 5 ps ≤ 5 ps；统计项仅 p、p₋、支撑（+n）
- [x] 输出根验空；分支 `formal-ir-v72p1-addendum-clean`；树干净（仅新增 C-0 脚本未跟踪）
- [x] 冻结基线（`src/`、`experiments/`、`tools/`、`results/`）未动；新增文件仅 wrapper 加法
- [x] 跑后独立 Pre-RESULT（δ–p 曲线口径、校准增益措辞）—— PASS（见 `C0_ACCEPTANCE.md`）

## 结论上限（绑定）
- 本产物只支持描述性零解码统计（δ–p 曲线、每源最优 δ* 与 p 增益、支撑是否收缩）。
  不得由此直接得出 FER、协调效率、泄漏/净密钥、译码器选择、路线关闭或发表级 claim；
  此类结论需 C-2/C-3 在其门下另行给出。
