# V72P2D3-GF32 R5 数学接口与码率审计

状态：`PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`

本文件是 R4 关闭后的 R5 路线入口。它只冻结审计问题和后续验收，不实现代码、
不读取 VAL/raw/parquet、不运行 decoder、不创建正式输出、不授予真实执行。R4
历史由 `OPERATOR_RETURN_R4.md` 保留，不在本文件重写。

## R4 关闭事实

R4 的真实命令在入口放行后被 terminal writer 的 `synthetic-only` 规则拒绝，返回
`exit=2`。本轮没有进入真实 GF32 kernel，因此：

- decoder attempts `0`，数据读取 `0`，披露 `0`；
- 正式输出目录和四文件均不存在；
- Pre-RESULT 为 `FAIL/BLOCKED`；
- 没有纠错、FER、SKR、information-limit 或因果结论；
- 不重试、不调参、不恢复 R4 授权。

terminal writer 是 deferred engineering blocker。它必须在本数学/码率审计结束后
另立最小工程变更，不得与本 R5 混合。

## 三个需要先闭合的 blocker

### B1：counts 方向

当前独立审查发现，CAL 统计路径使用了 `counts[Bob,Alice]`，而 V54 消费方按
`counts[Alice,Bob]` reshape/解释。R5 的唯一 canonical 定义为：

```text
counts[a,b] = count(Alice symbol=a, Bob symbol=b)
axis0 = Alice
axis1 = Bob
```

生产、prepare、fake 和真实 runner 必须遵守同一约定，禁止在调用处隐式转置。
必须用刻意不对称、可手算的联合分布验证：

```text
P(U1|B)    = P(high|Bob_side)
P(U2|U1,B) = P(low|high,Bob_side)
```

转置输入必须产生不同且可预测的结果；只检查归一化或只用对称数据不构成证据。

### B2：H1 实际输入

真实 CLI 当前存在以 `zeros((16,1024))` 作为 H1 的风险。该矩阵不能代表历史
V31/V54 方法。R5 必须恢复 QC-cyclic-projective 历史 H1，并验证：

- shape `(16,1024)`；
- 非零元素数大于零、每行非零；
- GF(32) 元素范围 `0..31`；
- GF(32) rank `16`；
- CLI 实际组装并传给 orchestrator/kernel 的对象来自历史 builder；
- `validate_nested_matrices` 拒绝全零 H1。

历史 builder 无法可靠重建时立即 `BLOCKED`，不使用替代矩阵继续。

### B3：旧码率与当前数据域未匹配

旧 GF32 预算为：

```text
H1:       16 rows × 5 = 80 bit
L2 max:  200 rows × 5 = 1000 bit
total:                    1080 bit
N:                        1024 symbols
total/N:                  1.0546875 bit/symbol
```

当前域必须通过与生产相同的 prior 链做 CAL-only 4-fold CV，分别审计：

```text
CE_L1        = H_model(U1 | B)
CE_L2_oracle = H_model(U2 | U1, B)
CE_joint     = CE_L1 + CE_L2_oracle
```

报告每 fold、均值和样本数，并与 L1 `80` bit、L2 `1000` bit、joint `1080` bit
比较 margin。`CE_L2_oracle` 只用于理论分层预算诊断，不是生产 decoder 性能。
模型 CE 不是信息论下界；`required > available` 只能记为
`MODEL_BUDGET_MISMATCH`，禁止写 information limit、GF32 failed 或
LDPC impossible。L1 不足不能只增加 L2。

## Prior 链一致性

prepare、fake E2E 和 production 必须调用同一 prior builder：

```text
counts[Alice,Bob] -> P(U1|B) -> L1 -> q=softmax(final_beliefs)
                    -> P(U2|U1,B) -> prior_l2=q@P -> L2
```

L1 使用 V54 `get_l1_prior_p_u1_given_b`，L2 使用 V54
`get_l1_app_prior_l2`。prior 只能接 physical Bob、当前 CAL 和冻结参数，不能接
Alice、oracle、旧 session 或 VAL 选参。概率先归一，floor 只保护 log。

现有 PREP 中同一 CAL 上的 custom P1/P2 CE 若保留，只能叫
`cal_resubstitution_nll_descriptive`；不能称 production validation，也不能替代
CAL-only held-out CV。

## 路线与任意数据边界

NB-LDPC 主线保留，但暂停 D3 真实执行和通用化。后续顺序冻结为：

1. 修复数学接口和真实 H1；
2. CAL-only 码率匹配；
3. 在匹配信道上做合成验证；
4. 做一个预注册的真实诊断；
5. 有真实信号后再做跨 session 和扩维。

“任意数据”分成四层：读入数据、估计匹配先验、构造适当码率、在预算内实现有效
纠错。目标是自动识别适用性并匹配参数，不保证任意数据都能高效纠错。

扩维留在 backlog：先 `d=256,[4,4]`、保持 `N=1024`，再 `d=512,[5,4]`。
三层以上 APP 的相关性必须另立数学合同并用微型枚举验证，不能直接重复两层
`q@P` 并声称保留完整联合信息。

## R5 允许范围、验收和停止

R5 只允许计划和审计定义，以及 CAL-only 的标量结果；不允许读 VAL、调用
decoder、创建正式输出、修 terminal writer、实现扩维或授予真实执行。

验收分层：

- T0：py_compile/import、counts 轴、非对称手算 prior、转置反例、H1 非零/逐行
  非零/rank16、全零 H1 拒绝、decoder/data/VAL 调用为零。
- T1：CLI 实际 counts/H1 捕获；prepare/fake/production 共用 prior builder；
  L1 APP 进入 L2 `q@P`；Alice 替换但 Bob/CAL 固定时 prior 不变；oracle 不进
  prior；custom CE 使用描述性命名；正式输出根不存在。
- T2：CAL-only 4-fold CV、fold 零重叠、VAL loader=0、CE 链式关系和预算复算，
  只输出标量。

任一以下情况立即 `BLOCKED`：

- counts 语义仍不能唯一确定；
- 历史 H1 无法可靠重建；
- CV 读取 VAL；
- 任何 decoder 被调用。

本 R5 完成后，下一门是 `INDEPENDENT_R5_PLAN_REVIEW`；未通过前不得恢复
terminal writer 修复或真实执行。

## R5 实现与审计结果（2026-09-05，CAL-only 合成，VAL0 decoder0）

- 约束：禁 decoder 执行、禁读 VAL、可读 CAL；R4 授权已撤销
  （`r4_real_execution_authorized: false`）；不改 writer（`write_contrast_outputs`
  未动）、不授权（`cycle_state` 授权位未动）；正式根
  `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/` 不存在。
- 统一 counts：`counts[Alice,Bob]` axis0 Alice axis1 Bob，shape `(1024,1024)`；
  V54 语义不动，`reshape(32,32,1024)=(U1,U2,Bob)`，`P(U1|B)`/`P(U2|U1,B)` 同约定；
  禁双矩阵；`prepare`/`fake`/`real` 同一 `build_canonical_counts`（`fit` 已改
  `(a_cal,b_cal)`，转置构造已删）。
- 非对称手算：`counts[10,20]=3,[10,21]=1,[42,10]=1`，`P(A=10|B=20)=1.0`，
  `P(B=20|A=10)=0.75`，差 `0.25`（误差 `1e-12`）；`V54 P(U1|B)` 在 `B=20->U1=0`、
  `B=10->U1=1`，转置最大差 `~1.0` 必失败；CLI builder 同方向（`scripts` 用
  `build_h1_historical`，无 `_np.zeros((mod.H1_ROWS`）。
- 历史 H1：`16x1024 QC-cyclic-projective poly37 V31/V54 builder`，`nnz=2048`，
  每行 `128` 非零，`rank16`，值 `0..31`，全零 syndrome、`e0` syndrome 非零，
  CLI 捕获非零，全零 `validate_nested_matrices` 拒绝，fake spy 验证注入矩阵非零。
- 生产 prior 链：canonical counts+Bob 块，`L1 V54 get_l1_prior`，
  `L2 q` 来自真 L1 APP（`softmax(final_beliefs)`），禁 Alice/oracle；
  PREP resubstitution 改名 `cal_resubstitution_nll_descriptive`；
  CAL-only 4-fold CV held-out L1/L2/joint log2 loss，不读 VAL，报告均值/fold/样本数，
  禁自动改矩阵。
- 合成 CAL（`seed=20260905,n=4096,lam=1.0`，均匀独立最坏情形，描述性）：
  resub `CE_L1=2.350880/CE_L2=1.021631/CE_joint=3.372511 bit/symbol`；
  4-fold held-out均值 `CE_L1=6.422161/CE_L2_oracle=5.083351/CE_joint=11.505513`，
  folds `6.416225/6.476192/6.420708/6.375520`（L1），样本 `3072/1024`。
- 码率审计：预算 `H1 80/L2total 1000/total 1080 bit,N1024,1.0546875 bit/symbol`；
  `required=CE*N`，`available=预算`，`margin=available-required`，
  `ratio=required/available`；`L1 6576.29/80/-6496.29/82.20`，
  `L2 5205.35/1000/-4205.35/5.21`，`joint 11781.64/1080/-10701.64/10.91`，
  状态 `MODEL_BUDGET_MISMATCH`（禁下界/失败定论，L1 不匹配指出禁自动新矩阵）。
  详见 `R5_RATE_AUDIT.json`（标量）。
- 测试：`62 passed`（既有 `53` + R5 `9`：T0 `1`+T1 `7`+T2 `1`），VAL 读 `0`，
  decoder `0`，正式根不存在。实现文件
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`、
  `scripts/v72p2d3_gf32_contrast.py`、
  `comparison_bench/tests/test_v72p2d3_gf32_contrast.py`。
