# V72P2D3 GF32 对照计划候选（基于 D1 映射表冻结）

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本入口仅记录待独立审查的计划，不是接受记录、实现授权或 decoder 授权。

- Repository：`HD-QKD_Polar_Comparison`
- Branch：`formal-ir-v72p1-addendum-clean`
- Base SHA：`e094f7e548380db4bfcbc1fe73472e670c32379a`
- Cycle：`V72P2D3-GF32`
- `development_execution_authorized: false`
- `formal_execution_authorized: false`
- `scientific_promotion: false`
- `accepted_plan_sha: null`
- `implementation_sha: null`

上面的 SHA 字段仅是 AGENTS 要求的 Git 版本绑定，不承担数据或 artifact 内容校验。计划阶段只保留本入口和 OpenSpec 四工件共 5 个新增文件。禁止实现代码、decoder、真实数据或 parquet 读取、结果目录创建，以及对 V72P1、V72P2、D1、D2 已接受文件、`cycle_state.yaml`、memory、`src/`、`experiments/`、`tools/`、`results/`和既有 comparison 输出的修改。

Ponytail lite：禁框架，薄 adapter 唯一复用 v35 真核经 V54 链。不预设优胜者。

## 历史 kernel 与调用图冻结（R1–R5）

- **R1**：`HISTORICAL_KERNEL=v35 decode_row_layered_fftqspa` 码字域（长度 `n=1024` 的 GF32 码字向量）；输入 `(H, prior P(X), syndrome H*x)`，输出 `DecoderResult(x_hat, syndrome_ok, iterations 0..max, final_beliefs + runtime/status)`；`0` 为初值即满足，仅 syndrome 等式停止，无 residual；`warm` 仅 `(n,32)` log-belief 初值（`check_to_var` 恒零初值，非 message carry），V54 生产恒冷启动（`warm_beliefs=None`）。
- **R2**：唯一 kernel 精确复用 V54 链（L1 `_dec_l1/H1` 经 `get_l1_prior_p_u1_given_b` 的 `P(U1|B)`，`q=softmax(final_beliefs)`；L2 三 stage `H_base/joint/total` 同 `prior_l2=q@P` 经 `get_l1_app_prior_l2`，`max90/damping1.0`；生产恒 `decode_fn=None`）；禁 argmax 冒充/固定 hard/写死 iters/mock 进生产/简化 decoder/称 binary 为 GF32（binary 仅 Arm A）/改历史 kernel。
- **R3**：薄 adapter 只做映射/矩阵/prior 方向/syndrome（`s1/s_base/s_joint/s_total` Alice 侧，经 `syndrome_of_gf32`）/调真核/字段统一（`get_gf32_field` 即 v35 `GF2mField.create(32)` poly37）/stage 编排/diagnostics；生产直调真迭代函数；返回 `x_hat/syndrome_observed/ok/iterations_used/residual 或 NOT_RECORDED/finite/runtime/stop/candidate_changed/vs_bob`，不伪造缺失字段（`hard/iters/syndrome_satisfied` 仅回兼容视图）。
- **R4**：每 stage cold start 严格复用：生产恒 `belief_warm=None`（`belief_warm` 不称 message carry，加 cold 语义测试）。
- **R5**：冻结历史顺序与每层五元组：L1（`U1=high/MSB`，Bob 侧 `y1`，`P(U1|B)`，`s1=H1*u1`，输出 `x_hat_u1+q`，恒进 L2，重组 `q=softmax`）→ L2（`U2=low/LSB`，Bob 侧 `(u1,b)` 经 `q`，`prior_l2=q@P`，`s_base/s_joint/s_total`，输出各 stage `x_hat`，base-失败→joint、joint-失败→total，重组 `layers_to_symbols`）；L1 失败仍进 L2（恒用 `q`），L2 按历史短路（base 满足跳过 joint/total；joint 满足跳过 total；syndrome-only）。

调用图（生产，`decode_fn=None`）：`symbols_to_layers/factorize_f03（u1=high/u2=low）→ get_gf32_field（v35 poly37）→ nested H（H1-16 + 184/192/200）→ V54 P(U1|B)/q@P（s1/s_base/s_joint/s_total 经 gf32_syndrome）→ history_decode（冷启动）→ run_g_layer/run_l1_stage/run_l2_incremental_chain（含 q 重组与短路）→ write_contrast_outputs`。

## 目标与科学问题

D1 已明确并冻结为唯一基线：GF32 q32 poly37 可复用、5+5 `s=32*u1+u2`、H_base184/190/192+H1-16、nested Δ8+8、layered vs incremental 正交、90 硬帽 damping1.0 无 tolerance、prior TRAIN-only VAL 需适配 CAL 禁回灌、泄漏 `5*m+80+64`、V64 verify 纯函数可复用、V64 归因禁定论。

D2 正交分诊（L/I/P）之后，本计划只在同一固定非新鲜诊断块上比较二臂：已存的 Arm A（二进制基线 decoder0，只读复用）与新 G（GF32 两层增量，同 VAL1726..1729、CAL702..1725，禁 VAL 调参）。目标是检验 balanced 5+5 GF32 表示能否让候选逃离二进制 fixed point；不预设任一臂优胜，不作单因素因果断言。

## 冻结的二臂

| 臂 | 表示/图 | prior | decoder | 备注 |
|---|---|---|---|---|
| A | D1 原 H 二进制 | D1 M0 | decoder0（已存） | 只读复用，不重跑 |
| G | GF32 5+5 `low+32*high`，H_base184+H1-16 nested 184/192/200 | TRAIN 数学 + 当前 CAL `P(high\|B)/P(low\|high,B)` | 两层增量，90 硬帽，damping1.0，无 tolerance | 同 VAL 块一次，无 rerun |

Alice 仅 syndrome prefix + 结束后 posthoc oracle；Bob + CAL 仅 prior；无 tag（`tag_bits=0`、`tag_ok=NOT_APPLICABLE`）。

## 固定输入

- session：`20260123_1M_600k_0dB`；诊断块 `VAL1726..1729`（1024 symbols，`non_fresh=true`）；CAL `702..1725` 仅适配 prior。
- 映射：`low=bits0..4/high=5..9/bit0 LSB/symbol=low+32*high` 同方向（绑定 v35 `factorize_f03`，`u1=high/u2=low`），`+1024 roundtrip`；歧义则 REVISE。
- 场/矩阵：`q32 poly37`（统一 v35 `GF2mField`）、`H_base184+H1-16=200`、`184/192/200` Δ8+8；`190/192` 仅他 session 参照。
- decoder：唯一真核 v35 `decode_row_layered_fftqspa` 经 V54 链，G `90` 硬帽、`1.0`、无 tolerance、每 stage cold，自然 log；CE log2；`residual=NOT_RECORDED`。
- prior：`P(high|B)=P(U1|B)` 与 `P(low|high,B)=P(U2|U1,B)` 明确方向，生产 `prior_l2=q@P`（V54 精确复用），禁 Alice/旧 session/VAL 选参；报告 joint/low/high CE log2 链式，decoder 自然 log 转换。
- 泄漏：`5*m+80+64`（`m_total` 含 H1：`200/208/216 → 1064/1104/1144`；等价 L2-only 行 `184/192/200 → 1064/1104/1144`）；V64 verify 仅只读 helper；V64 归因禁定论。

## 诊断、计费与结果边界

G 每层独立报告 `x_hat/syndrome_observed/ok/iterations_used/residual 或 NOT_RECORDED/finite/runtime/stop/candidate_changed/vs_bob/posthoc/total/control`；`syndrome_ok = finite && kernel syndrome_ok && observed==target`（G syndrome 一律 `syndrome_of_gf32`）；首次满足不早停；oracle 只在结束后比较 final candidate。A 新指标 null 附因。公开计费 `syndrome+control`，无 tag。三臂/两层不相加。

终态四分支：`G_EXACT / G_COLLISION / G_IMPROVED_NO_SYNDROME / G_NO_MOTION`（定义见 proposal）。`G_EXACT` 仅允许同路线小样本 confirmation；其余仅描述性。禁止 FER/SKR/信息极限/LDPC 无效/图因果/GF32 优胜/跨 session 断言。

## 未来实现和执行的固定边界

未来实现精确使用 3 个文件：

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`
2. `scripts/v72p2d3_gf32_contrast.py`
3. `comparison_bench/tests/test_v72p2d3_gf32_contrast.py`

薄 adapter 唯一复用 v35 真核经 V54 链（L1/H1 + L2 三 stage + q@P），不新增框架，不改历史 kernel。真实输出根固定为 `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`，只含 `manifest.json/results.json/table.csv/report.md`，不覆盖 D1/D2 且不创建 `run_01`。D6 15 项 synthetic、D7 全双层 `≤300s/<2GiB/≤15%`、D8 三审查核真 kernel、D9 VAL G 一次、D10 四分支判别。执行前必须通过独立 Plan Review、Implementation Review、Pre-EXECUTE，发布前通过 Pre-RESULT；本计划不授任何执行权限。

## 审查出口

独立 Plan Review 必须覆盖 D1 映射一致性、GF32/矩阵/嵌套、decoder 硬帽、prior 方向无歧义、泄漏公式、V64 复用/归因边界、二臂正交性、syndrome-only 语义、final-candidate oracle 绑定、D6–D10、schema、禁止文件范围。任一合同无法证明即 `BLOCKED`；方向歧义即 `REVISE`。

successor/文献/历史边界按任务书：PEG `10.1109/TIT.2004.839541`、layered `10.1109/SIPS.2004.1363033`、`arXiv:1001.1826`、`arXiv:2305.08631`，V54 `43/45`、V64 `22/24`、V5-C2 `384/384` 限定域；V67–V72P1 不写成真实纠错成功。
