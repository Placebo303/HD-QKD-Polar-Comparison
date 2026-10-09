# S-2 Pre-EXECUTE — {未校准,校准}×{硬,软} H(A|B) 2×2 表（DECIDE，零解码）

> Track: DECIDE（读已存原始 ttbin；零解码，只统计）。
> 授权：用户 2026-10-09 已授权本类零解码统计（"用户已授权本类零解码统计"），
> 仍按要求先写本 Pre-EXECUTE 记录，事后做独立 Pre-RESULT。
> 上位：R1–R17、`S1_VERIFY_LOG.md`（软输入 Bob 侧已核实；f 新规；网格锚定声明）。
> 网格：t0 取全段 `tmin`（与 B123/C-0 同口径）；校准只平移 Bob 时刻，网格固定。

## 1. 冻结输入（8 个源段；T0-1.5M/2M 沿用 B123 blocked，不重采不 fallback）

- T2（base 变体）：T2-1M / T2-1.5M / T2-2M（2026-01-21）。
- T0（base 变体）：T0-500K / T0-1M（2026-01-20）。
- Jan23（`.1` 变体）：0dB / 4dB / 10dB。
- 路径与 B123 同源同变体（见 `B123_PREEXECUTE.md` §1），此处不复列。

## 2. 冻结设计（与 Z-2/M5/C-0/B123 同链，只加前缀/测试切分）

- 冻结链：`read_ttbin_events` → `derive_alignment` 门控（blocked 则该源记
  blocked、不配对、不 fallback）→ `_pair_nearest_unique`（窗 200 ps，标称
  offset 配对一次）→ `_frame_global`（span 204800）。
- 前缀/测试切分：按配对时间顺序，前 **10000 对为前缀**（拟合专用），其余为测试。
  n_pairs ≤ 12000 的段（无；最小 10dB 30912）不适用此忧——全段 n 均远大于前缀。
- 前缀拟合（估计量写死）：core μ̂ = median(Δ_prefix)，
  σ̂ = 1.4826·MAD(Δ_prefix)（抗尾稳健），ŵ = mean(|Δ_prefix|>100 ps)
  （宽成分权重，σ₂ 固定 100 ps）。测试部分不参与拟合（R10 失配 hygiene）。
- 测试统计（bw ∈ {100,200,400}，d=2048/1024/512）：
  - H_hard_uncal：测试部分标称分帧 H(e)（plug-in）。
  - H_hard_cal：`pb+δ*` 重分帧 H(e)（δ*：T2 用 C-0 冻结值 −50/+50/+50；
    T0 用 B3 粗扫描值 −50/−50；Jan23 用 C-0 冻结值 −50/−50/−45）。
  - H_soft_uncal / H_soft_cal：同上两种分帧下按 Bob 精细位置 8 子 bin 分层的
    E[H(e|fine)]（B2 同口径，S-1 已核 Bob 侧）。
  - 参照列：前缀拟合律（DoubleGauss(σ̂,100,ŵ)+μ̂）的 A5 模型预测 hard/soft
   （标称/校准），只作参照，不作主数。
  - CI：测试部分定种子（20261010）子抽样 3 万 × 50 bootstrap，每格报
    四 H 的 95% CI（plug-in 偏倚为负向二阶，n≥20k 可忽略，如实声明）。
- R1 功效：CI 半宽即 MDE 的直接度量，随表附 n_test；不做解码器效应检验。

## 3. 冻结命令

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s2_softmap --full --output-root workspace/s_softmap/s2_20261009
```

自检（不读真实数据）：

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_s2_softmap --self-test
```

## 4. 预算与墙钟

- 预算 **7200 s（2 h）**。依据：B123 同链 10 源实测 2209 s；
  本任务 8 源 × 3 bw 单遍 + bootstrap（向量化），预计 < 20 min，2 h 为上确界。
- Smoke：第 1 源全量即 smoke；单源 ×8×1.5 超预算则中止。
- 输出根 `workspace/s_softmap/s2_20261009`：执行前验证不存在；存在则中止。
- 实际起止墙钟：执行时记录于 RESULT。

## 5. 检查单（执行前）

- [x] 用户已授权本类零解码统计（指针见顶）
- [x] 执行代码 + 合成自检通过（`--self-test` OK）
- [x] 统计项仅四 H + 前缀拟合参数 + CI（+n 完整性）；无解码、无 FER/泄漏/净密钥
- [x] 输出根验空；分支 `formal-ir-v72p1-addendum-clean`；冻结基线未动（加法脚本）
- [x] S-1 网格/μ 声明已写入日志（`S1_VERIFY_LOG.md` §5）
- [x] 跑后独立 Pre-RESULT（S2_ACCEPTANCE.md，独立线程）—— **PASS**
  （独立审查线程 2026-10-09：R-a…R-e 全 PASS，主线程将结论逐字转录存档于
  `S2_ACCEPTANCE.md`）

## 6. 结论上限（绑定）

只支持描述性 H(A|B) 2×2 表（经验主数 + 前缀模型参照 + CI）；
软相对硬的界增益方向由 CI 覆盖判定，不得直接报 FER/效率/路线关闭；
译码可实现性由 S-3 在其门下另行回答。
