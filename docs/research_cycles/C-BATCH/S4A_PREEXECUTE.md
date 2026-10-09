# S-4a Pre-EXECUTE — 符号先验约定诊断（DECIDE，零解码）

> Track: DECIDE（读已存原始 ttbin；零解码，只统计，不解码）。
> 授权：用户已授权本类零解码统计（S 批授权链），仍按要求先写本 Pre-EXECUTE，
> 事后做独立 Pre-RESULT。
> 背景：S-3 全链 10 格 S=0，失败全在 level-B（1231/1231 okA 块 okB=False），
> level-A soft 639/639 通过。规划 session 判断大概率是第二级符号/映射约定
> 缺陷（全败太整齐；有"重建映射反写"前科；1.5M/2M 符号翻转；软对符号应最有用）。
> 本诊断用零解码统计验证该判断（判读规则见 §2）。
> 上位：R1–R17、`S1_VERIFY_LOG.md`（f 新规；本诊断不算 f）。

## 1. 冻结输入（8 源段，与 S-2 同源同变体；T0-1.5M/2M 沿用 blocked）

T2-1M / T2-1.5M / T2-2M（base）、T0-500K / T0-1M（base）、0dB / 4dB / 10dB（`.1`）。
路径见 `B123_PREEXECUTE.md` §1（此处不复列）。

## 2. 冻结设计（与 S-2 同链；真标记代替译码，通过块≈全集）

- 冻结链：`read_ttbin_events` → 对准门控（blocked 记 blocked、不 fallback）→
  标称配对（窗 200 ps）→ `_frame_global`（span 204800，bw ∈ {100,200,400}）。
  网格 t0=`tmin`；校准位移 `pb+δ*`（δ* 与 S-2 同值），网格固定。
- 零解码对应"第一级通过的块"：用**真标记**（e≠0，e=(bb−aa) mod d），
  不跑译码器（S-3 实测 soft level-A 通过率 100%，真标记≈通过集；如实声明此近似）。
- 统计（每源 × bw，分标称/校准两套分帧）：
  1. **软符号先验一致率**：Bob 猜 ŷ=b1^a0^1（p_minus>0.5 侧的 argmax，
     S-3 level-B 实际用的先验方向）vs 真实 y=a1，在真标记位置上的符合率；
     同时列反猜（ŷ=b1^a0）符合率。附 bootstrap 95% CI（种子 20261011）。
     判读（规划 session 事先写死）：≪50%（如 ~10%）→ 约定反了；
     ~50% → 软对符号无效；很高但 S-3 仍失败 → 查码与记账。
  2. **精细条件符号率**：P(sgn=−1 | marked, fine 子 bin)（8 子 bin），
     检验"靠近哪侧边缘决定 ±1"（规划 session 的物理直觉）+ ou先验是否该用
     精细条件式（S-4d 修复输入）。
  3. **标记数分布与符号率**：每块（N=4096 切分）marked 计数分布（均值/分位数）、
     sgn=−1 占比；与合成 DoubleGauss（S-2 前缀律，种子 20261011）对照。
  4. **位映射逐行核对**：在真值上验证 G1 关系 `a1==b1^a0^sgn`（sgn=(e==−1)）
     的成立率；验证重建规则（sgn=0→b−1，sgn=1→b+1；S-3 已修复项）的闭合率；
     分源列出 1.5M/2M 翻转侧是否自洽（offset 符号 + p− 方向）。
- R1 功效：一致率 CI 半宽即判读精度（n_marked~10^4–10^5，半宽 <0.01）。

## 3. 冻结命令

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s4a_signdiag --full --output-root workspace/s4_diag/s4a_20261009
```

自检（不读真实数据）：

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s4a_signdiag --self-test
```

## 4. 预算与墙钟

- 预算 **7200 s（2 h）**。依据：S-2 同链 8 源实测 1206 s；本任务统计量更轻
  （无 bootstrap 大回调之外的重分帧），预计 < 20 min，2 h 为上确界。
- Smoke：第 1 源全量；单源 ×8×1.5 超预算则中止。
- 输出根 `workspace/s4_diag/s4a_20261009`：执行前验证不存在；存在则中止。

## 5. 检查单（执行前）

- [x] 用户已授权本类零解码统计（S 批授权链 + 本轮任务包原话）
- [x] 执行代码 + 合成自检通过（`--self-test` OK）
- [x] 统计项仅一致率/精细符号率/标记分布/映射核对（+n、CI）；无解码、无 FER/泄漏/净密钥
- [x] 输出根验空；分支正确；冻结基线未动（加法脚本）
- [x] 跑后独立 Pre-RESULT（S4A_ACCEPTANCE.md，独立线程）—— **PASS**
  （独立审查线程 2026-10-09：R-a…R-e 全 PASS，主线程逐字转录存档）

## 6. 结论上限（绑定）

只报诊断统计 + 判读（约定反/无效/码账三分叉）；修复动作本身不在本包
（修复→合成+S-1 代理复验→S-4d 新包，用户确认后再跑）。
