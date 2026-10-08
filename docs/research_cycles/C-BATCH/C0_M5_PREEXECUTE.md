# M5 Pre-EXECUTE — 前缀 δ 估计 + 跨采集稳定性（DECIDE，零解码）

> Track: DECIDE（读已存原始事件；零解码，只统计 p、p₋ 与误差支撑）。
> 授权指针：用户 2026-10-08 20:30 修订指令 M5（`C_BATCH_AMEND.md`）+ 原 C-0 授权
> （`C_BATCH_PREREG_20261008.md` §4 C-0）。
> 上位规则：R1–R16；零解码无失败计数（无"未定"触发项）。

## 冻结输入（6 文件，与 C-0/Z-2 同源同变体）
- R1 base 三源 + 2026.1.23 .1 版三段（路径见 `C0_PREEXECUTE.md`，此处不复述）。

## 冻结设计（与 C-0 的唯一差异：EST/TEST 时间切分）
- 冻结链：`derive_alignment` 门控 → 标称 offset 配对一次 → `_frame_global`
  （span 204800，bw ∈ {200, 400}）。
- 切分：配对输出单调，按时间取前 10,000 对为 EST，其余为 TEST。
- EST 上 δ ∈ [−100,+100] ps 步长 5 ps（41 点）全扫描，只统计 n/p/p₋/支撑；
  得 δ*_est；TEST 上只算 2 点（δ=0 标称 + δ*_est），得 p/支撑/p₋。
- 输出：`m5_rows.jsonl`（EST 41×12 + TEST 2×12 = 516 行）+ `m5_summary.json`。
- 稳定性问题：δ*_est 跨 6 源 spread + δ*_est vs C-0 全量 δ*（≤网格精度即稳定，
  前缀校准有效，无测试污染）。

## 冻结命令
```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_c0_prefix --full --output-root workspace/c0_prefix/c0_20261008
```

## 预算与墙钟
- 预算 **2400 s**（C-0 实测 1164 s；EST 切分后计算量更小，取 2x 裕量；R7）。
- 输出根 `workspace/c0_prefix/c0_20261008`：执行前验证不存在（2026-10-08 已验空）。
- 实际起止墙钟：执行时记录于 RESULT。

## 检查单（执行前）
- [x] 用户修订指令 M5 授权（指针见顶）+ 原 C-0 授权
- [x] 执行代码 + 合成自检通过（`--self-test` OK：切分计数/EST-TEST p 一致/支撑断言）
- [x] 复用已测函数（`compute_stats`/`frame_symbols`/`FILES` 来自已验收 C-0 脚本）
- [x] 步长 5 ps ≤ 5 ps；统计项仅 n/p/p₋/支撑（+top_errors 即支撑权重）
- [x] 输出根验空；分支 `formal-ir-v72p1-addendum-clean`；冻结基线未动
- [x] 跑后独立 Pre-RESULT（前缀-测试口径、稳定性措辞）+ RESULT（主线程组装）—— PASS（见 `C0_M5_ACCEPTANCE.md`）

## 结论上限（绑定）
- 只支持：δ*_est 跨源 spread、前缀 vs 全量 δ* 一致性、TEST 段在前缀 δ* 下的 p。
  不得直接得出 FER/效率/净密钥/路线关闭 claim；C-0 原结论是否修正由 Pre-RESULT 判定。
