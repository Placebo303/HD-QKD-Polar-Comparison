# V72P2D3-GF32 frozen execution packet

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Base SHA: `e094f7e548380db4bfcbc1fe73472e670c32379a`
- Accepted plan SHA: `e0cf5c6772e26c8de561584941e2fe6eea62666e`
- Implementation SHA: `e0cf5c6772e26c8de561584941e2fe6eea62666e`
- Cycle: `V72P2D3-GF32`
- Status: `FROZEN / EXECUTE_NOT_AUTHORIZED` until independent Pre-EXECUTE PASS.
  本包仅冻结操作合同，不授任何执行权限。

Scope: `docs/research_cycles/V72P2D3-GF32/` cycle docs only this commit.
实现文件冻结为既有三文件（`comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`、`scripts/v72p2d3_gf32_contrast.py`、`comparison_bench/tests/test_v72p2d3_gf32_contrast.py`），不改 `src/`、`experiments/`、`tools/`、`results/`、V72P1/D1/D2 已接受文件与既有 comparison 输出。不覆盖任何已有输出。

## 1. DATA（冻结）

- session: `20260123_1M_600k_0dB`
- CAL: `702..1725`，仅适配 prior（TRAIN 数学 + 当前 CAL `P(high|B)/P(low|high,B)`），禁 VAL 调参与禁回灌。
- VAL: `1726..1729`，`4x256=1024` symbols，`non_fresh=true`。同一固定非新鲜诊断块，同 VAL 一次，无 rerun。
- 映射方向绑定 v35 `factorize_f03`（`u1=high/u2=low`），歧义则 REVISE。

## 2. Arm A（冻结·复用）

- 复用 D1 已存 `decoder0`（二进制基线，原 H 二进制，D1 M0），只读复用，不重跑。
- A 新指标 null 附因。

## 3. Arm G（冻结）

- 表示：`low/high` 5+5，`s=32*u1+u2`（`u1=high/MSB`，`u2=low/LSB`，`symbol=low+32*high`）。
- 场：`q32 poly37`（统一 v35 `GF2mField.create(32)`，经 `get_gf32_field`）。
- 矩阵：`H_base184 + H1-16 = 200`，nested `184/192/200`（`Δ8+8`）；`190/192` 仅他 session 参照。
- decoder：唯一真核 v35 `decode_row_layered_fftqspa` 经 V54 链（L1 `_dec_l1/H1` + L2 `H_base/joint/total` 三 stage + `q@P`，生产恒 `decode_fn=None`）。
- 参数：row-layered，`max90` 硬帽，`damping1.0`，cold（每 stage `belief_warm=None`，`warmNone`，`check_to_var` 恒零初值），无 tolerance。
- 停止：每 stage syndrome 历史停止（syndrome-only，自然 log；CE log2；`residual=NOT_RECORDED`）；第一层失败历史短路（L1 失败仍进 L2 恒用 `q`；L2 base-满足跳过 joint/total，joint-满足跳过 total）。
- tag：无 tag（`tag_bits=0`、`tag_ok=NOT_APPLICABLE`）。
- 先验方向：`P(high|B)=P(U1|B)`、`P(low|high,B)=P(U2|U1,B)`，生产 `prior_l2=q@P`。

## 4. 计量（冻结）

- G 每层每 stage 独立报告：`active/iters/viol before-after/ok/changed/vs_bob/finite/runtime/RSS`。
- 另记：`final low/high`、重组（`q=softmax`、`layers_to_symbols`）、`posthoc oracle`、`vsBob`、`vsAlice`。
- Alice 仅 syndrome prefix + 结束后 posthoc oracle（final candidate）；Bob + CAL 仅 prior。
- 终态四分支 `G_EXACT / G_COLLISION / G_IMPROVED_NO_SYNDROME / G_NO_MOTION` 仅描述性；`G_EXACT` 仅允许同路线小样本 confirmation。禁止 FER/SKR/信息极限/LDPC 无效/图因果/GF32 优胜/跨 session 断言。

## 5. 泄漏（冻结）

- `5*m` rows 分层（`m_total` 含 H1：`200/208/216 → 1064/1104/1144`；等价 L2-only 行 `184/192/200 → 1064/1104/1144`），control 冻结，`tag0`。
- 失败不回滚。无 FER。公开计费 `syndrome+control`。三臂/两层不相加。V64 verify 仅只读 helper，归因禁定论。

## 6. 预算（冻结）

- `prep300` / `G300` / `invocation600`（秒），`RSS2GiB`。
- 失败 `BLOCKED`，不重试。无预算覆盖、无调参重跑。

## 7. 输出（冻结）

- 输出根：`comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`。
- 终态恰四文件：`manifest.json` + `results.json` + `table.csv` + `report.md`。
- 输出根必须事先不存在；存在则拒绝（零文件写入，不删除）。禁 `run_01`。不覆盖 D1/D2。

## 8. 执行授权占位（未生效）

- 占位提议：`execution_count_authorized=1`、`execution_count_completed=0`、`real=true`、`formal=false`、`promotion=false`。
- 生效条件：需独立 Pre-EXECUTE PASS 后才生效。在此之前 `development_execution_authorized=false`、`formal_execution_authorized=false`、`real_execution_authorized=false`、`scientific_promotion=false`，`state` 保持 `IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`。
- 测试仅 fake runner + tmp，永不触碰生产输出根。
