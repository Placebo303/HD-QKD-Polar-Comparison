# OpenSpec Design: formal-ir-v66-single-segment-adaptive-nbldpc

**Lifecycle**: `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED` — **单 session 单源自适应 decoder-free 预冻结，m1<1024&&m2<1024 满秩嵌套 constructibility 先验，未执行 EVAL，已删 per-source 6/8**
**Cycle**: `V66-ADAPT` (single-segment-adaptive), predecessor `V65 new-session` + `V64 22/24 full-tag PASS (80c35647/6c7b00a9)`，HEAD `832e5394bb366927c779414ee5a08427bd740a2d` data `84d62779` 单 session `20260123_1M_600k_0dB`
**Feasibility**: `V54 43/45` 在 `2026-01-23` 域已证 `H1-16+L1APP+Lane C Δ8+Δ8+full-tag` 有效；`V55 0/90` 已定位跨 session 不兼容提示单段内自适应价值；`V65` 以新 session 两会话验证兼容性；`V66` 反向探索**同 session 内单源 CAL/VAL 自适应冗余**是否可在密封 `EVAL` 获 `19/24 undetected0`（overall），零 `decode_*` 调用闭环。
**Key judgement**: **单 session 单源内 `VAL CE` 估计的 `m1_raw/m2_raw` 经同家族 `+8` 调整后能否既满足 `m1<1024 && m2<1024 满秩嵌套披露 constructibility` 又满足 `EVAL 19/24 undetected0 overall`**；若 `m` 超限或不可构造则 `RATE_NOT_FEASIBLE`/`MATRIX_NOT_CONSTRUCTIBLE`，若不足 blocks 则 `DATA_NOT_READY`，均不进入 decoder。

## 1. 科学问题与关键判断

> 在**完全冻结主体**（`U=32*U1+U2 F03 5+5 natural, H1-16 rank16, Lane C ordinal-2 s38310x m2 184（单源）, H_inc Δ8 家族, decoder 90/1.0 poly37, full-tag canonical`）下，于**单 session `20260123_1M_600k_0dB` 连续数据段**内切 `CAL 24 + VAL 24 + EVAL 24 =72 overall`，以 `CAL` 重估 `P(U1|B)/P(U2|U1,B)`，以 `VAL` 上 `CE1/CE2` 得 `raw m1/m2 =ceil(1.3*1024*CE/5)`，同家族 `+8` 调整并通过 `m1<1024 && m2<1024 满秩嵌套披露 constructibility` decoder-free 校验后，冻结参数在**密封 `EVAL` 24 blocks** 上是否 `exact_full ≥19/24 overall && undetected==0`？**已删 per-source 6/8**。全程不以 `EVAL` 调参，保持 decoder-free 先验守卫。

- **对照**：`V13 2026-01-23` `H~0.80` 仅容量对照；`V64 22/24` 为 `full-tag` 语义对照；`V65` new-session `4096/512/120` 为跨 session 对照；`V66` 不沿用其统计，验证同 session 单源内 `CAL→VAL` 自适应。
- **不变量**：`dimension 1024 / bin200 / nearest legacy_v1 / channels A1/B5 / U=32*U1+U2 / Lane C / H_inc Δ8 / full-tag` 全冻结。
- **自适应性质**：纯 decoder-free，`CAL` 估计 `P`，`VAL` 独立得 `CE/m_raw` 并 `+8` 家族化，`EVAL` 密封一度量，单源判定，`72 overall` 内闭环。

## 2. 冻结语义 — 主体与处理点零改（A/B 约束）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V54/V64 |
| m2 single-source frozen base | 184 (单源 20260123_1M_600k_0dB) | Lane C ordinal-2 `s38310x` (V54→V64 继承，V66 仅自适应起点，**单源生效**) |
| m1 | 16 | `V31-H1-QC-16×1024 rank16` |
| H_total base rows (L2) | 200 | `L2=184` 单源 |
| H_total full rows | 216 | `16+m2` 单源 |
| GF | GF32 poly37 | GF2mField |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 |
| 泄漏 base | `leak=5*(m1+m2)+64` | V64（**m1,m2 分别计**）|
| 译码 (冻结禁用) | `decode_row_layered_fftqspa 90/1.0 early-stop` | V43/V52 — 自适应期禁用直至授权 |
| U mapping | `s=32*u1+u2, U=32*U1+U2, F03 5+5 natural, U1=s>>5, U2=s&31, 每帧256` | V25/V38 |
| Verification | `full-symbol tag 32*U1+U2 compute_tag_64 canonical trunc64` 单64b | V64 22/24 PASS |
| 单段分段 | `CAL 24 + VAL 24 + EVAL 24 =72 overall` 单 `session_id=20260123_1M_600k_0dB` | V66 预注册（单源） |
| Data SHA | `84d62779` `d1024 bw200 nearest legacy_v1` | V55 authoritative |

**禁令**：`SHALL NOT` 任何 `decode_* / construct_*` 调 `m2/leak/decoder/prior/H1/Lane C/H_inc/Δ/verification`；零 decoder 直至 EVAL 授权；不引 `MET/protograph/SC`；不跨 session 拼接；`H` 仅同家族 `+8` 档调整；**已删 per-source 门禁**。

## 3. 数据角色 — 单 session 单源三切 CAL/VAL/EVAL（键为元组，development_replay 标记）

### 3.1 每段定义（overall 24/段，单源 72 total）

| 集合 | 来源 | overall blocks | frames | pairs | 说明 |
|---|---|---|---|---|---|
| CAL | `20260123_1M_600k_0dB` 前 24 blocks | 24 | 96 | 24576 | 主训练：`C_ab → P(U1|B)/P(U2|U1B)` |
| VAL | 同 session 中间 24 blocks，与 CAL 零重叠 | 24 | 96 | 24576 | 验证：`VAL CE1/CE2 → m_raw → m_family → 满秩嵌套` |
| EVAL | 同 session 后 24 blocks，与 CAL/VAL 零重叠 | 24 | 96 | 24576 | 密封：仅一度量 `19/24 undetected0 overall`，不参与先验/阈值 |

- **单 session 隔离**：`CAL||VAL||EVAL` 均同一 `session_id=20260123_1M_600k_0dB` 内连续窗口 `4×256 BLOCK`，`frame_id∈[0,F_s-1]`，`BLOCK 4 连续帧`，`K=F_s//4` 为可用完整 BLOCK 数；`72≤K` 为 `DATA_NOT_READY` 阈，`F=2130 K=532` 实测。
- **零重叠**：`CAL_key∩VAL_key==∅ && CAL∪VAL_key∩EVAL_key==∅ && CAL∪VAL∪EVAL_key∩(V13∪V48..V64)_key==∅` 键 `(source,session_id,frame_id)`，单源。
- **可复用旧数据**：`F_s` 来自 `v55_intake_20260828` 单 session `20260123_1M_600k_0dB`，`development_replay=true, replay_source=v55_intake_20260828` 显式，不作 fresh qualification。

### 3.2 数据就绪门（decoder-free，24/段 单源 72）

```
assert |CAL|==24 && |VAL|==24 && |EVAL|==24  overall 单源
assert CAL_session_id == VAL_session_id == EVAL_session_id == "20260123_1M_600k_0dB"
assert not cross_session_spliced
assert CAL_key∩VAL_key==∅ && CAL∪VAL∩EVAL==∅ && CAL∪VAL∪EVAL ∩ (V13..V64)==∅  (key=(source,session,frame))
assert F_s >=72*4=288 frames (72 blocks) else DATA_NOT_READY  # 实 2130 >>288
assert development_replay==true && replay_source=="v55_intake_20260828"
```

- **不足 72 或任段 !=24**：`overall=V66_DATA_NOT_READY` 写 `v66_data_readiness.json` 后零估计停止，不伪造。
- **注册表**：`v66_data_registry.json` (`schema v66_data_v1, lifecycle PLAN_CANDIDATE, data_sha 84d62779, head 832e5394bb366927c779414ee5a08427bd740a2d`) 含 `per_source {20260123_1M_600k_0dB: {CAL_blocks[24], VAL_blocks[24], EVAL_blocks[24], session_id, F_s, K, development_replay, replay_source}, zero_overlap_verified}`。

### 3.3 选取理由

- `24 blocks/段 overall =24576 pairs/段` 在 `Q=1024` 下同 session 内 `VAL` 测 `CE` 可得 `m_raw` 自适应信号；单源 72 内闭环，不跨源拼接。
- `F_s 2130 frames=532 blocks` 远超 288 frames，可复用旧 session 但标记 `development_replay`。

## 4. 输入合同 — 严格复用 V56 权威算法（decoder-free，单源）

| 阶段 | 参数 | 冻结值 (V56 算法) |
|---|---|---|
| 1 | dimension | 1024 |
| 2 | bin_width | 200 ps |
| 3 | pairing | `nearest`, double-pointer `bin//1024` 消歧 |
| 4 | rule/mapping | `legacy_v1` |
| 5 | channels | `A:1 , B:5` (type2) |
| 6 | U mapping | `s=32*u1+u2, U=32*U1+U2, 每帧256` |
| 7 | frame anchor | `frame_start_ps / period 204800ps / floor_div` |
| 8 | H1/Lane C/H_inc | 只读冻结，不重估（单源 m2 184） |

- **只读复用**：`src.reconciliation.run_nbldpc_demo_point` 的 `legacy_v1` 物化算法不重写；`V66` 仅重估 `P(U1|B)/P(U2|U1B)`，不改 `H1/Lane C/mapping`。
- **帧级校验**：每帧 `alice[256], bob[256]` 各 `256 pairs`，`A==32U1+U2 && B==32V1+V2`。

## 5. 估计器 — 单一 CAL 重估 + VAL CE 门禁 + 同家族 +8（不依 EVAL，m1/m2 分别）

### 5.1 联合计数与全局先验 (CAL-only 单源)

```
C_ab = bincount2d(a_cal, b_cal)  shape 1024×1024, sum N_cal =24576
N_b = Σ_a C_ab  shape 1024
P_global(a) = Σ_b C_ab / N_cal  shape 1024
Q=1024
```

### 5.2 分层条件分布

```
P(a|b) = (C_ab + λ P_global(a)) / (N_b + λ) if N_b>0 else P_global(a)  # λ 可固定或 CAL 内择优，但仅 CAL
P(u1|b) = Σ_{u2} P(32*u1+u2 | b)  32×1024
P(u2|u1,b) = P(32*u1+u2|b)/P(u1|b) if >0 else 1/32
```

- `λ` 若择优则仅 `CAL` 内 `4-fold`，不以 `VAL/EVAL` 选择；本设计允许 `λ` 固定为经验值或 `CAL-CV` 择优但必须显式 `development_replay` 下报告。

### 5.3 VAL 交叉熵与 raw 冗余（VAL 门禁 单源）

```
CE_full = -E_VAL[ log2 P(A|B) ]  mean_VAL 24576 pairs
CE1 = -E_VAL[ log2 P(U1|B) ]
CE2 = -E_VAL[ log2 P(U2|U1,B) ]
链式校验 |CE_full - CE1 - CE2|<1e-9 else EVIDENCE_INVALID
m1_raw = ceil(1.3*1024*CE1/5)  ∈ [0,∞)  # 不 cap，单 plane
m2_raw = ceil(1.3*1024*CE2/5)
m_total_raw = m1_raw + m2_raw  不 cap 但仅报告
```

### 5.4 同家族 +8 调整（唯一允许的自适应，m1/m2 分别）

```
m1 = ceil_to_family(m1_raw, step=+8)  # H 家族中 ≥m1_raw 且 ≡ base (mod 8) 的最小可构造行数，Δ8 家族；若无则 MATRIX_NOT_CONSTRUCTIBLE
m2 = ceil_to_family(m2_raw, step=+8)
m_total = m1 + m2
# 禁止：round/floor/min_cap/EVAL 重选；仅上调至 +8 档；m_total 不单独判 feasibility
```

- **EVAL 禁用**：`m` 选择不读 `EVAL` 任何统计，违则 `EVIDENCE_INVALID`。
- **constructibility**：若 `m1_raw` 或 `m2_raw` 超出家族可构造上界（>1016 且无 +8 档）则 `MATRIX_NOT_CONSTRUCTIBLE`。

## 6. 满秩嵌套披露 decoder-free 先验校验（进 EVAL 前，m1/m2 分别 <1024）

```
assert m1 <1024 && m2 <1024  # 已从 m_total<1024 改为分别判
assert gf_rank(H1(m1)) == m1  (GF32 poly37, exact rank)
assert gf_rank(H2(m2)) == m2
assert nested(H_base, H_inc): H(m1),H(m2) rows ⊇ H_base 且 incremental rows 独立
assert disclosure == 5*(m1+m2)+64  (5 per row 10-bit? 按 V64 leak 语义 m_total=m1+m2)
if any fail: overall = V66_RATE_NOT_FEASIBLE  # 含 MATRIX_NOT_CONSTRUCTIBLE 子类 no family H
```

- `H(m)` 来自已冻结 `H1 + H_inc Δ8` 家族 `rank/nested` 已预验的集合，不新增矩阵；若 `m1` 或 `m2` 无对应 `H` 则 `MATRIX_NOT_CONSTRUCTIBLE` → `RATE_NOT_FEASIBLE`。
- `disclosure` 含 `tag 64` 单次，不重复；**m_total 仅衍生，不作 <1024 判**。

## 7. EVAL 密封门禁（未执行前仅冻结判定框架，已删 per-source）

| 门 | 判定 (per EVAL 24 blocks overall 单源) | 阈值 |
|---|---|---|
| exact_full | `exact_full ≥19/24 overall` | 79.17% **无 per-source** |
| undetected | `undetected_full_tag==0` | 0 |
| tag | `all exact → tag_ok_full==True` | 恒真 |
| disclosure | `disclosure ==5*(m1+m2)+64` 双校验 | per block |
| efficiency | `eff = disclosure / (1024*CE_full)` 报告 | 描述+门禁辅助 |

- **密封**：`EVAL` 度量为单次，不回灌 `P/m`；`ADAPTIVE_EVAL_PASS` 需同时 `exact` + `undetected0` + `tag` + `disclosure` 全过。

## 8. 终态机五选一（优先级高→低，互斥，已删 per-source）

```
if not materialization_ok or frame_256_violation or CE_chain_not_closed or provenance_fabricated:
    overall = V66_EVIDENCE_INVALID
elif K <72 or |CAL|!=24 or |VAL|!=24 or |EVAL|!=24:
    overall = V66_DATA_NOT_READY
elif m1>=1024 or m2>=1024 or rank_m1!=m1 or rank_m2!=m2 or not nested or disclosure!=5*(m1+m2)+64 or not constructible:
    overall = V66_RATE_NOT_FEASIBLE  # 含 MATRIX_NOT_CONSTRUCTIBLE 子类
elif EVAL executed && (exact_full<19/24 or undetected!=0 or not tag_ok):
    overall = V66_ADAPTIVE_EVAL_FAIL
elif EVAL executed && exact_full>=19/24 && undetected==0 && disclosure ok:
    overall = V66_ADAPTIVE_EVAL_PASS
else: # EVAL 未执行但前三态已过
    overall = V66_DEVELOPMENT_BENCHMARK_READY  # 允许申请 EXECUTE_AUTH 后度量 EVAL
```

- `V66_DATA_NOT_READY` 与 `V66_RATE_NOT_FEASIBLE`（含 `MATRIX_NOT_CONSTRUCTIBLE`）均不启动 decoder；`V66_ADAPTIVE_EVAL_PASS/FAIL` 仅在授权执行后产生。

## 9. 脚本与报告（decoder-free 守卫 + spike 回填无 TBD）

- **脚本1 `scripts/v66_data_readiness.py`** (decoder-free):
  `python scripts/v66_data_readiness.py [--pairs-root ...] [--out v66_data_registry.json]`
  → 单 session `20260123_1M_600k_0dB` 连续 72 检测 + `24/段` 切分与三重零重叠（键 `(source,session,frame)`） + `frame 256` 校验 + `development_replay` 标记，`rg "decode_" 0 hits`，`py_compile PASS`；输出 `v66_data_registry.json + v66_data_readiness.json` + 控制台 spike 摘要；不足 72 直接 `DATA_NOT_READY`。
- **脚本2 `scripts/v66_spike.py`** (decoder-free):
  `python scripts/v66_spike.py [--registry v66_data_registry.json] [--out v66_spike_summary.json]`
  → `CAL C_ab/P_global → P(U1|B)/P(U2|U1B) → VAL CE1/CE2/CE_full 链式 → m1_raw/m2_raw ceil → m1/m2 +8 aligned → m1<1024 && m2<1024 rank nested disclosure constructibility` 校验，`rg "decode_" 0 hits`，`py_compile PASS`；输出 `v66_spike_summary.json`（**已回填 CE1/CE2/raw/aligned/rank/nested/disclosure/constructibility，无 TBD**） + 控制台摘要；校验 `EVAL 未参与` 及 `m_raw` 未 cap。
- **报告 `V66_ADAPTIVE_REPORT.md`**：`CAL/VAL/EVAL 24/段 单源 provenance + development_replay + CE1/CE2/CE_full + chain_delta + m1_raw/m2_raw/m_total_raw + m1/m2/m_total aligned + rank_m1/rank_m2/nested/disclosure/constructibility + EVAL 密封门禁 19/24 undetected0 预冻结 + 五态` 与 `json` 一致，不扩大为 `FER/SKR`，**无 TBD**。
- **守卫**：自适应期零 decoder、单 session 单源不比较、原 `90` 已禁止复用外、**不创建 `run_01`**、不比较方法、不转 qualification；**四工件+registry+spike 已单独提交推送，新 Plan SHA 已生成**。

## 10. 与 V64/V65 衔接

- V64 `full-tag` 语义与 `H_total 200/206/208 / 216/222/224` 冻结构及 `22/24 PASS` 已固化（单源取 200/216）；V65 new-session 两会话为跨 session 对照；V66 单段单源自适应为**同 session 内单源 `CAL→VAL→EVAL` 自适应**分支，三者正交不互斥。
- 若 `V66_RATE_NOT_FEASIBLE`（含 `MATRIX_NOT_CONSTRUCTIBLE`）或 `DATA_NOT_READY` 则停留 `DEVELOPMENT_BENCHMARK`，不进入 EVAL。

## 11. 自由裁量 D1-D7

- D1 完全冻结主体（`H1/Lane C/Δ8/decoder/full-tag`），V66 仅适冗余档（单源 m1/m2 分别）。
- D2 单一 `P(U1|B)/P(U2|U1B)` 重估，不引第二 estimator。
- D3 泄漏 `m*5+64` 不增，`+8` 同家族上调，不 cap，**m1/m2 分别 <1024**。
- D4 数据 `24+24+24` 确定性单 session 单源切分，不搜索多划分。
- D5 `19/24 & undetected0 overall` 预注册阈，**已删 per-source**，不以总体平均替代。
- D6 不产生新矩阵/码参数，仅验证与判定，族不能覆盖则 `MATRIX_NOT_CONSTRUCTIBLE`。
- D7 本变更为 `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`，不产生 `run_01`，EVAL 时才 decoder。
