# D4 设计：CAL GF32 模型码率审计（PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED）

状态：只描述一次合规审计，不实现、不运行 decoder、不读 VAL、不创建输出、不授权。绑定 predecessor D3 R5；base 为 plan-creation HEAD（Review 时 pin）。

## 1. 数据与 CV（冻结）

- CAL：同 session `20260123_1M_600k_0dB` 的 `CAL702..1725`，1024 帧 ×256 pairs = 262144 symbols。VAL loader 调用必须为 0（探针断言）。
- 划分：按帧序连续 4 折 outer `F0=702..957 / F1=958..1213 / F2=1214..1469 / F3=1470..1725`，每折 256 帧；外层 4 次 `train=768帧（其余3折） / test=1折连续256帧`；每个 outer TRAIN 内再按帧序连续切 3 确定性 inner folds（各 256 帧，帧序唯一，禁 shuffle/逐行随机/VAL）；nested 语义：counts+拟合只用对应 train，test 只算 CE；模型选择只用外层 mean；不跨帧打散、不按 symbol 随机 split。
- 确定性：fold 分配由帧序唯一确定；审计报告每折 `n_train/n_test` 样本数。
- 机械断言（冻结，测试必须覆盖）：(a) outer `TEST∩TRAIN=∅`；(b) inner `TEST∩TRAIN=∅`；(c) 全部 inner folds `⊆` 其所属 outer TRAIN；(d) 每 outer TEST=256 帧；(e) 四 outer TEST 并集=`702..1725` 全 1024 帧；(f) 每帧=256 pairs；(g) 同一 outer 下 3 inner folds 两两互斥；(h) 3 inner folds 并集=所属 outer TRAIN（768帧）。任一违反即 `BLOCKED`。

## 2. Canonical counts 与链式（冻结）

```text
counts[a,b] = count(Alice symbol=a, Bob symbol=b), axis0=Alice, axis1=Bob
symbol = low + 32*high, U1=high (MSB), U2=low (LSB), bit0=LSB
P(A|B)      : counts 按 Bob 列归一
P(U1|B)     : P(A|B) 按 U2 边际化
P(U2|U1,B)  : 按 (U1,B) 条件化
CE_L1       = -mean(log2 P(U1|B))
CE_L2_oracle= -mean(log2 P(U2|U1,B))   # 用真实 U1，仅分层预算诊断
CE_joint    = CE_L1 + CE_L2_oracle
chain check : |CE_joint - CE_L1 - CE_L2_oracle| < 1e-10
```

- 生产/V54 消费语义不变，不在调用点转置；本审计与未来生产共用同一 builder 口径。
- Floor 精确 `1e-300`（非量级/非约数）只保护 log：概率先正常归一，再 `max(P,1e-300)` 后取 log；unseen Bob 回退由各模型显式声明（见 §3）。

## 3. 模型 M0–M2 闭合 + 本轮 `M3_EXIT_AMBIGUOUS`（冻结）+ 数学合同与 lambda 反泄漏

M0<M1<M2 复杂度递增（M3 本轮已退出不参选），输入只允许对应 train counts + 冻结参数（禁 VAL/oracle/旧 session/TEST 回灌）：

- M0（最简，pin）：train 边际基线（`P_M0(a)=count_TRAIN(A=a)/n_TRAIN`，与 B 无关），unseen 处理 trivial；均匀 `P=1/1024` 另记 `uniform_lower_bound_descriptive` 下界对照，不参选、不进选择与路线。
- M1：全符号经验 `P(A|B)`（列归一 + 显式 Laplace/回退声明；lambda（Laplace/回退/收缩系数）为冻结常量或仅由对应 TRAIN 统计确定，禁 TEST/VAL/held-out 调参、早停或选模）。
- M2：GF32 两层分解 `P(U1|B) * P(U2|U1,B)`（与 V54 `get_l1_prior_p_u1_given_b / get_l1_app_prior_l2(q@P)` 同口径，审计端 `CE_L2_oracle` 用真实 `U1`；lambda 同 M1 统一口径）。
- M3（本轮直接退出，冻结）：无唯一定义，本轮直接记录 `M3_EXIT_AMBIGUOUS`，从审计中移除，审计在 M0–M2 上闭合，不得猜测替代；M3 不进选择、预算与路线。

数学合同（冻结）：counts 轴约定 + `P(A|B)→P(U1|B)/P(U2|U1,B)` 链式 + `CE=-mean(log2 P)` + 链式误差 `<1e-10` + 预算 `rows=ceil(N*CE*f/5)` 为同一合同；任一环节口径变更即 `REVISE`。
lambda 反泄漏（冻结）：lambda（Laplace/回退/收缩系数）SHALL 为冻结常量或仅由对应 TRAIN 统计确定；SHALL NOT 用 TEST/VAL/held-out 调参、早停或选模；inner 选择若用 lambda，必须只看 inner TRAIN 拟合 + inner held-out CE，不得窥视 outer TEST。

每模型（M0–M2）必须声明：估计子、平滑/回退规则、unseen Bob 行为、与 counts 轴约定的绑定测试。

## 4. 指标（冻结）

- 主指标：各折 `CE_L1 / CE_L2_oracle / CE_joint`（bit/symbol，log2），及 fold-mean/std/max-min/n。
- seen/unseen：held-out 每个 symbol 按其 Bob 值是否在 train 出现划分；报告 `seen_frac`、`CE_seen`、`CE_unseen`（unseen 用模型声明回退计算，不得删样本凑数）。
- 链式：每折 + mean 均满足 `<1e-10`，否则 `BLOCKED`。
- 现有同 CAL custom P1/P2 重拟合值如引用，只称 `cal_resubstitution_nll_descriptive`。

## 5. R5 复现门（冻结）+ 来源与根因

- R5 来源为 synthetic，故 `REAL_CAL_EXACT_MATCH=false`：`6.422/5.083/11.505` 只作同 fixture 公式复现基准（同 counts 轴约定 + 同 V54 链 + 同 CE 定义 + CAL-only），不作真实 CAL 精确匹配断言。
- 同口径（canonical counts + V54 链 + CAL-only）复算 R5：`CE_L1=6.422 / CE_L2_oracle=5.083 / CE_joint=11.505`。
- 容差：各 `|CE-ref|<1e-6`，且链式 `<1e-10`（`6.422+5.083=11.505` 精确相加）。
- 失败即 `BLOCKED`，不进入 M0–M2 比较、不做选择与路线判定；并记根因分类：口径偏离（轴/链式/CE）/ 数据域偏离（synthetic vs CAL702..1725）/ 实现偏离（平滑/回退/floor），不得调参凑数。

## 6. 选择规则（冻结）

1. 主键：`mean(CE_joint)` 最小。
2. 简单优先：`Δmean<0.02` bit/symbol 视为接近（R1冻结：按实现`SELECT_DELTA=0.02`冻结，不可调），取更简（M0<M1<M2，M3 已退出不参选）。
3. 稳定性数值门限（冻结）：`CE_joint` 跨外层折 `std>0.10 bit/symbol 或 max-min>0.20 bit/symbol` 即不稳定，显式标记并降级（不得仅凭单折最优选中）；报告 std 与 max-min。
4. 选择不自动转为矩阵/decoder 参数；只输出审计名次与路线输入。

## 7. 预算（冻结）

```text
N = 1024 symbols/block
f ∈ {1.0, 1.1, 1.2, 1.3}
required_bits(layer) = N * CE_layer * f
rows_required(layer) = ceil(required_bits / 5)   # GF32 每行 5 bit
available: L1 = 80 bit (16 行), L2 = 1000 bit (200 行), Total = 1080 bit (216 行)
rate_total = 1080/1024 = 1.0546875 bit/symbol
```

- 分层对照：`1024*CE_L1 vs 80`、`1024*CE_L2_oracle vs 1000`、`1024*CE_joint vs 1080`；同时报告 rows 表（4 种 f × 3 层）。
- `required>available` 只记 `MODEL_BUDGET_MISMATCH`，禁写 information limit / GF32 failed / LDPC impossible；L1 不足禁只加 L2。

## 8. 路线 A/B/C（冻结）

- A（fit）：`f=1.3` 时 L1/L2/Total 全层 `required≤available`（以选中模型 mean 计）→ 允许起草匹配合成信道计划；仍不授权真实诊断。
- B（仅低 f fit / marginal）：`f=1.0` 时全层 fit 但 `f=1.3` 时任一层 mismatch（即 ¬A∧¬C，典型 `f=1.0/1.1 fit 而 f=1.3 mismatch`）→ 只允许重预算/小诊断计划；真实诊断与通用化暂停。
- C（mismatch）：即使 `f=1.0` 仍任一层 `MODEL_BUDGET_MISMATCH` → 停止，后继仅 backlog（`d=256,[4,4]` 优先）；不保证任意数据高效纠错。
- A/B/C 互斥穷尽：`A=fit@1.3，C=mismatch@1.0，B=fit@1.0∧mismatch@1.3`，同一选中模型 mean 同一口径下有且仅一成立。
- “任意数据”四层（读入/先验估计/码率构造/预算内纠错）沿用 D3 R5 文字。

## 9. 执行边界与禁止（冻结）

- 允许：文档、计划、T0/T1/T2 测试定义、CAL-only 标量审计定义。
- 禁止：读 VAL（含 loader 调用>0）、调用 decoder（含真核与生产路径）、构造新矩阵（含全零 H1 替代）、引入 checksum/hash/tag/签名、创建正式输出/`run_01`、修复 writer、授予执行。
- 停止：counts 约定不唯一、M0–M2 任一不可手算验证、`M3_EXIT_AMBIGUOUS` 无显式退出记录、CV 读 VAL、任何 decoder 调用、R5 复现失败 → `BLOCKED`，不猜测、不替代、不重试。
