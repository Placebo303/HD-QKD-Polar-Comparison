# V72P2D3 Spec Delta：GF32 两层增量对照（syndrome-only）

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本 delta 绑定 base `e094f7e548380db4bfcbc1fe73472e670c32379a`，不合并、不替代已接受的 V72P1、V72P2、D1、D2 行为。本周期不实现、不运行 decoder、不读取 raw/parquet、不创建结果目录。

`base_sha/accepted_plan_sha/implementation_sha` 只承担 Git 版本绑定，不承担 data/artifact 内容校验。输出不得包含数据或 artifact 内容摘要、签名或其他校验字段。不预设优胜者。

## S-ARM：二臂对照

- **S-ARM-01**：系统 SHALL 以已存 D1 Arm A 作为 baseline A；A SHALL 只读复用，SHALL NOT 重跑。
- **S-ARM-02**：G SHALL 使用本 spec `S-MAP/S-GF32/S-PRIOR` 定义的 GF32 两层增量，同 VAL 块、同 CAL 域，一次运行；SHALL NOT 用 VAL 选参/调参/回灌。
- **S-ARM-03**：A 与 G 的对照 SHALL 为描述性表示对照；SHALL NOT 宣称单因素因果或优胜者。
- **S-ARM-04**：不得创建混合臂；不得事后调参、重跑或扩展 block。

## S-COMMON：输入与状态

- **S-COMMON-01**：block SHALL 是 session `20260123_1M_600k_0dB` 的 `VAL1726..1729` 四帧连续 1024-symbol D1 诊断块，标记 `non_fresh=true`；CAL SHALL 是同 session `CAL702..1725`；计划和测试阶段 SHALL NOT 读取 raw/parquet。
- **S-COMMON-02**：A mother/数值/ladder SHALL 复用 D1（9036x10240、nnz49620、72 点、10/ckpt、720/arm、float64/clip20/tol1e-6）。
- **S-COMMON-03**：Alice SHALL 仅提供 syndrome prefix 与结束后 posthoc oracle；Bob+CAL SHALL 仅提供 prior；诊断 SHALL 为 syndrome-only。
- **S-COMMON-04**：`tag_bits` SHALL 为 0，`tag_ok` SHALL 为 `NOT_APPLICABLE`；SHALL NOT 生成 tag 泄漏。

## S-MAP：映射

- **S-MAP-01**：`low` SHALL 为 bits0..4（u2），`high` SHALL 为 bits5..9（u1），`bit0` SHALL 为 LSB；方向 SHALL 绑定 v35 `factorize_f03`。
- **S-MAP-02**：`symbol` SHALL 为 `low+32*high`（即 `s=32*u1+u2` 其中 `u1=high/u2=low`），同方向、无 Gray、无置换。
- **S-MAP-03**：pack/unpack SHALL 满足 `+1024 roundtrip` 全值往返一致；任一歧义 SHALL 导致 `REVISE`。

## S-GF32：场、矩阵、decoder（R1–R2 唯一真核）

- **S-GF32-01**：场 SHALL 为 `q=32 poly37`，统一复用 v35 `GF2mField.create(32)` 数学；SHALL NOT 新定义多项式或改历史 kernel。
- **S-GF32-02**：矩阵 SHALL 为 `H_base=184`（1M；190/192 仅参照）+ `H1=16`，`H_total=200`，nested 前缀 `184/192/200`（Δ8+8）。
- **S-GF32-03**：layered（A 家族）vs incremental（G 两层增量）SHALL 正交，不得混合；G syndrome SHALL 经 `syndrome_of_gf32`，SHALL NOT 称 binary 为 GF32。
- **S-GF32-04**：G decoder SHALL 为 v35 `decode_row_layered_fftqspa` 码字域（长度 `n=1024` 的 GF32 码字向量；输入 `H/prior/syndrome`，输出 `DecoderResult(x_hat/syndrome_ok/iterations 0..max/final_beliefs + runtime/status)`，`0` 为初值即满足，仅 syndrome 等式停止），满足 `max_iter=90` 硬帽、`damping=1.0`、无 residual tolerance；BP SHALL 用自然 log，CE SHALL 用 log2；`residual` SHALL 为 `NOT_RECORDED`（真核无 residual，不伪造）；生产 SHALL 恒 `decode_fn=None` 直调真核。
- **S-GF32-05**：薄 adapter SHALL 唯一复用 V54 链 `L1(_dec_l1/H1，经 get_l1_prior_p_u1_given_b 的 P(U1|B)，q=softmax(final_beliefs))+L2(H_base/H_joint/H_total，同 prior_l2=q@P 经 get_l1_app_prior_l2)`；字段 SHALL 经 `get_gf32_field` 统一为 v35 `GF2mField.create(32)` poly37；syndrome SHALL 为 `s1=H1*u1/s_base=H_base*u2/s_joint/s_total`（Alice 侧，经 `syndrome_of_gf32`）；生产 SHALL 直调真迭代函数，每 stage cold start（恒 `belief_warm=None`，`belief_warm` 仅 `(n,32)` 初值，不称 message carry）；SHALL NOT argmax 冒充/固定 hard/写死 iters/mock 进生产/简化 decoder；三审查 SHALL 核真 kernel（import 探针 + tiny 已知答案含 `iterations==0` + stub/mock 零命中 + `np.argmax(prior` 零命中），否则 BLOCKED。
- **S-GF32-06**：历史顺序 SHALL 为 `L1(H1,P(U1|B)) → q=softmax(final_beliefs) → prior_l2=q@P → base → joint → total`；短路 SHALL 为 L1 失败仍进 L2（L2 恒用 q，不门控）且 base 满足跳过 joint/total、joint 满足跳过 total（syndrome-only；R5）；L1 结果不门控 L2（L2 恒用 q）。

## S-PRIOR：先验

- **S-PRIOR-01**：方向 SHALL 明确为 `P(high|Bob_side)=P(U1|B)` 与 `P(low|high,Bob_side)=P(U2|U1,B)`；生产 L2 prior SHALL 为 `q@P`（经 V54 `get_l1_app_prior_l2` 精确复用）；禁 Alice、禁旧 session、禁 VAL 选参；歧义 SHALL 导致 `REVISE`。
- **S-PRIOR-02**：builder SHALL 只接 physical Bob + 当前 CAL + 冻结参数；`K/P` SHALL 先正常归一；floor 只保护 log。
- **S-PRIOR-03**：SHALL 报告 `joint/low/high CE` log2 链式 `|CE_joint-CE_high-CE_low_given_high|<1e-9`，decoder 自然 log 转换显式；VAL 仅确认度量。

## S-ACCT：泄漏与计费

- **S-ACCT-01**：泄漏 SHALL 为 `leak=5*m_total+64=5*m_base+80+64`（`m_total` 含 H1：`200/208/216 → 1064/1104/1144`；等价 L2-only 行 `184/192/200 → 1064/1104/1144` 经 `leak_for_base`）；`tag_bits_published` SHALL 为 0。
- **S-ACCT-02**：G SHALL 分层报告 `x_hat/syndrome_observed/ok/iterations_used/residual 或 NOT_RECORDED/finite/runtime/stop/candidate_changed/vs_bob` 与 `total/control`；SHALL NOT 伪造缺失字段（无 Bob 层时 `vs_bob/candidate_changed` 为 null；`hard/iters/syndrome_satisfied` 仅为回兼容视图）；A 新指标 SHALL 为 null 附 `not_recorded_reason`。
- **S-ACCT-03**：V64 `compute_tag_64` SHALL 仅作只读 pure-function helper；SHALL NOT 计入泄漏或门禁；V64 归因 SHALL NOT 写成定论。

## S-IO：未来实现、执行和 schema

- **S-IO-01**：实现精确只有：`comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`、`scripts/v72p2d3_gf32_contrast.py`、`comparison_bench/tests/test_v72p2d3_gf32_contrast.py`。不得新增 config/fixture，或修改 adapter/src/experiments/tools/results/旧输出。
- **S-IO-02**：输出根 SHALL 是 `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`，且只含 `manifest.json/results.json/table.csv/report.md`；不得覆盖 D1/D2 输出或创建 `run_01`。
- **S-IO-03**：manifest/results 顶层 SHALL 含 schema、cycle、`base_sha/accepted_plan_sha/implementation_sha`、session/block/CAL provenance、`non_fresh`、mapping/field/matrix/nested/decoder/prior/leakage、arms 和 claim boundary；三字段仅 Git 绑定，不得添加内容校验字段。
- **S-IO-04**：每臂 SHALL 含 status、rows/iters、syndrome、candidate、posthoc、accounting、runtime/RSS；checkpoint oracle SHALL 为 null 附 `oracle_runs_after_arm_end`。

## S-STOP：预算与状态机

- **S-STOP-01**：synthetic 全双层 SHALL 满足 `wall≤300s`、`peak_rss<2GiB`、误差 `≤15%`；超限 SHALL 为 `PLAN_REVISE_REQUIRED`。
- **S-STOP-02**：准备/输入校验失败时 G SHALL 为 `NOT_ATTEMPTED` 非零返回；G exception/nonfinite/RSS/timeout SHALL 为 `BLOCKED` 保留 artifact；普通耗尽 SHALL 为正常终态；A SHALL NOT 重跑。
- **S-STOP-03**：执行前 SHALL 通过独立 Plan Review、Implementation Review、Pre-EXECUTE，发布前 SHALL 通过 Pre-RESULT；本计划 SHALL NOT 授权执行。

## S-CLAIM：判别和边界

- **S-CLAIM-01**：终态 SHALL 为 `G_EXACT / G_COLLISION / G_IMPROVED_NO_SYNDROME / G_NO_MOTION` 四分支互斥；SHALL NOT 预设优胜者。
- **S-CLAIM-02**：`G_EXACT` SHALL 仅允许同路线小样本 confirmation plan，不直接进入 V73；SHALL NOT 作 FER/SKR/信息极限/LDPC 无效/图因果/GF32 优胜/跨 session 断言。
- **S-CLAIM-03**：文献 SHALL 保留 PEG `10.1109/TIT.2004.839541`、layered `10.1109/SIPS.2004.1363033`、`arXiv:1001.1826`、`arXiv:2305.08631`，以及 V54 `43/45`、V64 `22/24`、V5-C2 `384/384` 限定域；V67–V72P1 SHALL NOT 写成真实纠错成功。

## S-TEST：未来 synthetic 验收

- **S-TEST-01**：T0/D6 SHALL 覆盖 15 项清单（场统一 v35/映射/roundtrip/方向绑定 factorize/H/nested/归一+q@P/链式/隔离/硬帽+cold 语义+真核探针/GF32 符号方向/GF32 violation/短路/V64 只读/直接比较/schema），`py_compile`/import 无副作用，fake 仅显式注入的测试路径。
- **S-TEST-02**：D7 SHALL 断言全双层 `wall≤300s/peak<2GiB/误差≤15%` 与 RSS 采样口径。
- **S-TEST-03**：D8 SHALL 断言三审查核唯一真核（import+已知答案+stub/mock 零命中+argmax 零命中）。
- **S-TEST-04**：T2 SHALL 使用显式 fake（仅 orchestration 短路逻辑） 和 fresh workspace，覆盖 G 全双层、首次满足不早停、动态计费、final-candidate oracle 分类、四文件 schema、production path 门禁（生产 `decode_fn=None` 直调真核）；replay 排除 wall/RSS/timestamp/path。
