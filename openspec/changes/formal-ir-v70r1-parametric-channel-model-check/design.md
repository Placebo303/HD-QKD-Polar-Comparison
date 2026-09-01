# Design: V70R1 Parametric Channel Model Check

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` / `V72_NOT_STARTED=true`
**HEAD**: `13b38b7930be67465c03744491b86e31406a1669` **Data SHA**: `84d62779` **Predecessor V71**: `6bc06d4d..487be113` latest `487be113`
**Script**: `scripts/v70r1_parametric_channel_model_check.py` **Test**: `test_v70r1_parametric_channel_model_small.py`

## 1. 唯一被改变的量：估计器

冻结不动：`d=1024 / bw=200ps / nearest / legacy_v1` 处理点、`v70_data_registry.json` 的三 session 与 Stage2 帧、`N=1024`、`COLS=10240`、`TAG_BITS=64`、规划因子 `1.3`、V70 的三分流阈（`gap≥512` FEASIBLE / `0≤gap<512` MARGINAL / `required≥10240` NO_INFORMATION_MARGIN）、V71 的 kernel。

唯一变量是 `P(a|b)` 的估计器族。所有下游量（`required/gap/margin/classification`）都用**同一套公式**从各模型的 `CE_VAL` 导出，因此模型间差异可直接读作路线差异。

## 2. 三模型

### M0 — hierarchical table（权威基线，参数 1024²+1）

```
P(a|b) = (C_ab + λ·P_global[a]) / (N_b + λ)      N_b == 0 时回退 P_global
λ ← CAL 4-fold CV，LAMBDA_GRID = logspace(-2, 4, 30)
```

与 `scripts/v70_binary_soft_joint_feasibility.py:hierarchical_P` 逐位相同。**这是内建自检**：M0 在 VAL 上的 CE 必须复现 `v70_table.json` 的 `CE_full_VAL` 到 `<1e-9`，否则 `EVIDENCE_INVALID`。

### M1 — circulant empirical kernel（参数 1024+1）

```
K = (hist_δ + λ_K/1024) / (n + λ_K)              hist_δ = bincount((a−b) mod 1024)
P(a|b) = K[(a−b) mod 1024]
λ_K ← CAL 4-fold CV，同一 LAMBDA_GRID
```

M1 不假设核的形状，只假设**平移不变性**。它是 M2 的非参数上界：若 M1 也劣于 M0，说明信道不是位移不变的，M2 不可能更好——这正是终态 2 的判据构造。

CAL 每格期望计数：`262144 × 0.56 / 1021 ≈ 144`（按 V56 的 `other_mass≈0.56` 估），尾部格并非稀疏，1024 参数在 262144 样本下是良定的。

### M2 — wrapped unimodal + uniform background（参数 3+1）

```
shape_{μ,s}(δ) ∝ Σ_{p∈{-1,0,1}} g(δ_signed + p·1024 − μ)     # 环绕三周期
    gaussian: g(z) = exp(−z²/2s²)        laplace: g(z) = exp(−|z|/s)
P(a|b) = (1−ε)·shape((a−b) mod 1024) + ε/1024
```

`δ_signed = ((δ + 512) mod 1024) − 512`，使核在环上居中，避免 0/1023 边界把 ±1 肩劈开（V13 的 `mass_−1 = 0.238` 正是落在 index 1023 上）。

**拟合是确定性网格**，无随机、无 VAL 参与：
- `μ ∈ arange(-4, 4, 0.25)`（33 点）— 允许亚 bin 中心偏移（V13 的 `peak_center=-50ps` 在 200ps bin 上就是 −0.25 bin）
- `s ∈ logspace(log10 0.05, log10 8, 40)`
- `ε ∈ linspace(0, 0.999, 200)`，对固定 `(μ,s)` 向量化一次算完取最小

外层 33×40 次，每次一个 `(200,1024)` 的向量化 CE 计算。

**族选择**：Gaussian 与 Laplace 两族在计划中预注册，由 **CAL 内 4-fold CV** 二选一（每折在 3 折上完整重拟合），VAL 只用被选中的族确认一次。不看 VAL 后择优。

## 3. 只需直方图

M1/M2 的 `P(a|b)` 只依赖 `δ = (a−b) mod 1024`，因此

```
CE_model = − Σ_δ hist_eval[δ]/n · log2 K(δ)
```

CAL 拟合和 VAL 评估都只消费 1024 格直方图，不重扫 pairs。M0 仍需完整 `1024×1024` 计数。这使得样本需求曲线（6 个 CAL 前缀 × 3 模型）成本可接受。

## 4. 诊断量

| 量 | 定义 | 用途 |
|---|---|---|
| `CE_*_VAL` | VAL 上的观测交叉熵 | 主判据 |
| `CE_*_CAL` / `cal_val_nll_gap` | `CE_VAL − CE_CAL` | 过拟合量 |
| `map_accuracy_VAL` | M0: `argmax_a P(a|b)`；M1/M2: `hist_VAL[argmax K]/n` | 描述 |
| `fano_upper_bound_diagnostic` | `h₂(Pe) + Pe·log2(1023)` | **上界诊断，非 H 的估计** |
| `required` | `ceil(1.3·1024·CE_VAL)`，不 cap | 路线 |
| `f_max_channel_ceiling` | `(10240−64)/(1024·CE_VAL)` | 与规划 f 分离 |
| `n_parameters` | `1024²+1 / 1024+1 / 4` | 估计代价 |
| `sample_curve` | CAL 前缀 32/64/128/256/512/1024 帧各自仅重拟合 μ/s/ε（λ/λ_K/M2族固用全量1024帧CAL选出值，不做每前缀4-fold重选）→ 同一 VAL 的 CE <!-- ponytail: 固参版sample_curve，每前缀仅重拟合μ/s/ε，λ固用全量CAL值；不做每前缀4-fold重选以避免小样本高方差与O(6×4)成本，待大样本再考虑每前缀重选 --> | 终态 4 证据 |

**显式非声称**：脚本落盘 `ce_decomposition_claimed: false`。报告中不得出现"模型 KL = CE − H_true"一类分解；只写 observed CE、模型间 CE 差、Fano 上界。

## 5. 规划 f 与实测 f 的分离

`TARGET_F_PLANNING = 1.3` 是具名常量，仅用于把 `CE` 换算成 `required`。`f_max_channel_ceiling` 只由 `CE` 与 10240 预算决定，与它无关。本变更 decoder-free，**不产生任何 `f_actual`**；任何报告 `f_actual` 的字段必须为 `NOT_MEASURED`（与 V71 同口径）。

## 6. 先验（来自 V56 诊断，非本轮结果）

`diagnosis_v55_domain.json` 在 8 帧/源上给出 `mass_0 = 0.4149/0.3755/0.2749`。取 M2 的退化形式 `K = (1−ε)δ₀ + ε/1024`，由 `mass_0` 定 `ε` 得闭式 CE `≈ 6.83 / 7.20 / 8.10`，对应 `required ≈ 9093 / 9585 / 10784`。若在 Stage2 帧上成立，1p5M 会从 `MARGINAL(193)` 变为 `FEASIBLE(655)`，命中终态 3。

**这是预期，不是结果**：（a）来自 V56 的 8 帧/源，与本轮 CAL1024/VAL256 帧不同且样本小三个数量级；（b）δ₀ 是 M2 的下界形式，真实 M2 带 ±1 肩（`mass_±1≈0.011` 高于背景 `≈0.002`）应更好；（c）若背景非均匀，M1 会优于 M2。三条都由本轮实测覆盖。

## 7. 守卫 R70R1-01~10

- **R70R1-01** CAL/VAL 帧完全复用 `v70_data_registry.json` 的 `stage2_CAL/VAL_frame_ids`，断言 `len(CAL)==262144 && len(VAL)==65536`，每帧 256 对。
- **R70R1-02** M0 复现 V70 `CE_full_VAL` `<1e-9`，否则 `EVIDENCE_INVALID`。
- **R70R1-03** λ / λ_K / M2 族全部 CAL-only 选择，`used_val_in_selection == false`，`used_test == false`。
- **R70R1-04** M2 族二选一由 CAL 4-fold CV 决定，VAL 只确认一次；网格 `MU_GRID/SCALE_GRID/EPS_GRID/M2_FAMILIES` 预注册冻结。
- **R70R1-05** `required` 显式 `ceil`，不 cap 在 10240；`gap = 10240 − required` 显式。
- **R70R1-06** 三分流阈与 V70 一致（`≥512` / `[0,512)` / `required≥10240`），不新设阈。
- **R70R1-07** 不声称 CE 分解；`ce_decomposition_claimed == false`；Fano 仅作上界诊断。
- **R70R1-08** 五终端 first-match 互斥且完备，overall 同序聚合。
- **R70R1-09** decoder-free：`rg "decode_" 0 hits`，不构业务矩阵，不创建 `run_01`，不启 V72，`git diff -- src/ == 0`。
- **R70R1-10** 四工件 + 脚本 + 小测试齐全，`py_compile` PASS，`pytest` PASS，报告与 json/csv 行对等，无 TBD。

## 8. 与 V71/V72 的关系

V71 已 `KERNEL_READY_FEASIBLE`（`6bc06d4d..487be113` latest `487be113`），successor `v71_ldpc_v5_integration`。V70R1 与 V71 正交：V71 验的是 factor kernel 的数值正确性与复杂度，V70R1 验的是 `required` 的口径。**V72 的 mother code 码率由 `required` 导出**，所以 V70R1 必须在 V72 冻结码率之前判定：若终态为 3，V72 应直接按更低的 `required` 设计；若为 5，V72 按 V70 现值推进。`V72_NOT_STARTED=true`，V70 数值不变，不运行解码。
