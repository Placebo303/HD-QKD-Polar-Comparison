# Spec: V70R1 Parametric Channel Model Check

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` / `V72_NOT_STARTED=true`
**HEAD**: `13b38b7930be67465c03744491b86e31406a1669` (`accepted_plan_sha` frozen `13b38b79`) **Data SHA**: `84d62779` **Predecessor V71**: `6bc06d4d..487be113` latest `487be113` `V71_KERNEL_ADAPTER_FEASIBLE / ADAPTER_REQUIRED` successor `v71_kernel_adapter_design`

## 1. 冻结常量

```
Q = 1024                    N_BLOCK = 1024
COLS = 10240                TAG_BITS = 64
TARGET_F_PLANNING = 1.3     # 规划因子，非实测效率
LAMBDA_GRID = logspace(-2, 4, 30)              FOLDS = 4
MU_GRID    = arange(-4.0, 4.0, 0.25)           # 33 点
SCALE_GRID = logspace(log10 0.05, log10 8, 40) # 40 点
EPS_GRID   = linspace(0.0, 0.999, 200)
M2_FAMILIES = ("gaussian", "laplace")
CE_VALUE_THRESHOLD = 0.10   CE_REJECT_MARGIN = 0.05
COST_SMALL_FRAMES = 64      COST_MODEL_TOL = 0.10   COST_TABLE_MIN = 0.50
```

三分流阈沿用 V70，不新设：`required ≥ COLS` → `NO_INFORMATION_MARGIN`；`gap < 0` → `HEAVY`；`gap ≥ 512` → `FEASIBLE`；否则 `MARGINAL`。

## 2. 数据契约

CAL/VAL 帧**必须**取自 `v70_data_registry.json`：`sessions[i].stage2_CAL_frame_ids`（1024 帧）与 `stage2_VAL_frame_ids`（256 帧），`provenance` 为同一 `pairs.parquet`。断言：每帧恰 256 对；`len(a_cal) == 262144`；`len(a_val) == 65536`；符号 `∈ [0,1023]`。任一不满足 → 抛错，不降级。TEST 不读。

## 3. 模型定义

```
M0  P(a|b) = (C_ab + λ·P_global[a]) / (N_b + λ)          N_b==0 → P_global
    λ ← argmin CAL 4-fold CV over LAMBDA_GRID            params = Q² + 1

M1  K = (hist_δ + λ_K/Q) / (n + λ_K)   归一化
    P(a|b) = K[(a−b) mod Q]
    λ_K ← argmin CAL 4-fold CV over LAMBDA_GRID          params = Q + 1

M2  δ_signed = ((δ + Q/2) mod Q) − Q/2
    shape(δ) ∝ Σ_{p∈{−1,0,1}} g(δ_signed + pQ − μ)       归一化
        gaussian g(z)=exp(−z²/2s²)   laplace g(z)=exp(−|z|/s)
    P(a|b) = (1−ε)·shape((a−b) mod Q) + ε/Q
    (μ,s,ε) ← 确定性网格 argmin CAL NLL
    family ← argmin CAL 4-fold CV over M2_FAMILIES        params = 3 + 1
```

`CE_model = − Σ_δ hist_eval[δ]/n · log2 max(K(δ), 1e−300)`（M1/M2）；M0 用 `− mean log2 max(P[b,a], 1e−300)`。

## 4. 选择隔离（硬约束）

- `λ`、`λ_K`、M2 的 `(μ,s,ε)` 与族**只在 CAL 上选**。
- VAL 只用于**一次确认**：三模型各自在全 CAL 上拟合后在 VAL 上评估一次。
- 落盘 `used_val_in_selection == false`、`used_test == false`。任一为 true → `EVIDENCE_INVALID`。
- λ 或 λ_K 落在 `LAMBDA_GRID` 边界 → `EVIDENCE_INVALID`（网格不扩）。

## 5. 派生量

```
required   = ceil(TARGET_F_PLANNING · N_BLOCK · CE_VAL)        # 不 cap
gap        = COLS − required                                   # 可为负
margin_gap = gap / COLS
f_max      = (COLS − TAG_BITS) / (N_BLOCK · CE_VAL)            # 信道上限
fano_ub    = h₂(1−acc) + (1−acc)·log2(Q−1)                     # 上界诊断
ΔCE        = CE_table_VAL − min(CE_circulant_VAL, CE_parametric_VAL)
```

## 6. 非声称条款（强制）

脚本与报告**不得**将 `CE` 写成 `H_true + KL` 并声称已分离两者。允许且仅允许报告：observed VAL CE、模型间 CE 差、MAP accuracy、Fano 上界诊断、CAL→VAL NLL gap。落盘 `ce_decomposition_claimed: false`。

`TARGET_F_PLANNING` 仅用于把 CE 换算为 `required`；不得被解释为达成效率。本轮 decoder-free，`f_actual` 一律 `NOT_MEASURED`。落盘 `planning_f_is_not_achieved_f: true`。

## 7. 终态（first-match，互斥且完备）

| # | 终态 | 条件 |
|---|---|---|
| 1 | `V70R1_EVIDENCE_INVALID` | M0 未复现 V70 `CE_full_VAL` `<1e−9`，或 CE 非有限，或 λ/λ_K 落边界，或选择隔离被破坏 |
| 2 | `V70R1_TRANSLATION_INVARIANCE_REJECTED` | `CE_circulant > CE_table + 0.05` **且** `CE_parametric > CE_table + 0.05` |
| 3 | `V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE` | `classification(best_parametric) != classification(table)` |
| 4 | `V70R1_PARAMETRIC_MODEL_NO_VALUE` | 以上均不成立（含 `ΔCE < 0.10` 且无路线变化；`sample_curve` 仅 descriptive-only，不触发终态） |

`best_parametric = argmin(CE_circulant_VAL, CE_parametric_VAL)`。Overall 按同序在三 session 聚合：取第一个计数非零的终态。

**后继绑定**：终态 3 → 参数化 estimator 进入 V77 自动适配器候选，且 V72 的 mother code 码率按新 `required` 设计；终态 2 或 4 → 保持 M0，直接进 `v71_kernel_adapter_design`；终态 1 → 阻塞，不进 V72。

## 8. 产出

```
v70r1_results.json     per_session[3] + terminal_counts[4] + overall + 非声称字段
v70r1_table.csv/.json  行对等，每 session 一行，三模型的 CE/acc/fano/required/gap/class/params
V70R1_PARAMETRIC_CHANNEL_REPORT.md
v70r1_manifest.json    guards R70R1-01..10
```

## 9. 守卫 R70R1-01~10

见 Design §7。全部 `true` 方可提交结果。

## 10. 禁止

见 tasks.md「本变更显式禁止」。要点：不重做输入合同、不读 ttbin、不换处理点、不用 VAL/TEST 择优、不 cap `required`、不改 `1.3` 宣称提效、不声称 CE 分解、不报 `f_actual`、不建 `run_01`、不启 V72、不改 `src/`。
