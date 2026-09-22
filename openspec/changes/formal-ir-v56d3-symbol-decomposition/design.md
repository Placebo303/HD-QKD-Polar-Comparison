# OpenSpec Design: formal-ir-v56d3-symbol-decomposition

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 符号映射分解**
**Cycle**: `V56D3` (symbol decomposition), predecessor `V56D2` `73bb2166`
**Branch**: `formal-ir-mainline` HEAD `73bb21669c1b76039a6981151d8cc0008dc778d0` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024)
**Provenance blocker**: `V56D2 run03` 执行期改 `src/qkd_io/ttbin_pipeline.py:compute_cross_correlation_histogram` 为 chunk 单次但 SHA 仍 `8d4df35c`，`src` 属冻结基线 — 需 revert 并移至诊断脚本内
**Feasibility**: `V56D2` 已证 `timing` 部分健康（`σ127ps p2bg 708/629/378`）但 `A==B 27-41%→27-42% calibration NLL 22-28` 未回落；`I(A;B)` 对置换不敏感，可判可逆重标记 vs 真退化；`fit 4/val 4` 与 5 族物理映射可在 `<5k` 候选内暴力闭环

## 1. 科学问题与关键判断

> V54 在 2026-01-21 域 `43/45`，V55 同方法同点新域 `0/90`；V56D0 猜 `A1/A2/B` 需分流，V56D1 补 raw `peak 窄127ps` 但 `p2bg 378-708<1000` 仍真，V56D2 校准 `A==B` 仍 `27-42% NLL 22-28` 未回落。若 `I(A;B)` 仍高而 `identity` 坍塌，则不是信道熵真增，而是**符号契约**（`mapping / bin_origin / frame_anchor / wrap_rule / Gray-binary / 32×32`）或更深 `pairing/frame` 错。

- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256` 为名义不变量
- **置换不敏感量**：`H(A), H(B), H(A|B)=H(A,B)-H(B), I(A;B)=H(A)-H(A|B)` 仅依赖 `C(a,b)` 的分布形状，对全局 `b'=π(b)` 不变（`H(A),H(B)` 不变，`I` 不变），可直接判真退化 vs 可逆重标记
- **可逆重标记判据**：`I` 保持 `V13 ~? bits`（`V13 H(A|B)~0.80`，`H(A)~10 bits` 时 `I~9.2`），且 `acc_map = mean(a==a_MAP(b))` 在 `val` 上显著高于 `acc_identity`（例 `27%→>60%`），且某物理 `π` 在 `val` 上恢复 `NLL/q_mass` ⇒ `SYMBOL_MAPPING_CONTRACT_ERROR`
- **非逐符号可逆**：`I` 仍高但 `acc_map` 亦低（`argmax` 仍弥散）或 `I` 已高但无物理 `π` 恢复 ⇒ `PAIRING_OR_FRAME_ANCHOR_ERROR`（`pairing` 把不同光子错配，或 `frame_anchor` 错位导致 `a,b` 跨帧对齐错，非逐符号置换可修）
- **真域迁移**：`I` 本身显著降低（`H(A|B)` 膨胀至 `~10` 或 `I→0`）⇒ `TRUE_ACQUISITION_DOMAIN_SHIFT`，届时才规划新 `prior/泄漏`（`channel_counts.npz` 重训 `TRAIN-only`、新 `m_total = floor((1.3*1024*H-64)/5)`）

## 2. 冻结语义 — V54 方法零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V55 |
| m2 per source | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 |
| GF | GF32 poly37 | GF2mField |
| H1 | V31-H1-QC-16×1024 rank16 80b | V31 |
| 泄漏 | base 1064/1094/1104 +40 +40 | m1=16+64b tag |
| 译码 (冻结禁用) | decode_row_layered_fftqspa 90/1.0 | V43/V52 — 诊断期禁用 |
| L1-APP | p via H1 BP TRAIN channel_counts.npz | V25 |
| Intake | d1024 bw200 nearest legacy_v1 A1/B5 单点 84d62779 | V55 |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder`；**零 decoder**；原 V55 90-block 已揭盲禁止重跑；`prior` 仍 `TRAIN-only`，不读新 TEST 做训练。

## 3. Provenance 修复 — chunk 优化移出 src（Phase 0）

- **现状**：`src/qkd_io/ttbin_pipeline.py:298-312` 为 chunk 单次（`all_lags = concat(t_B[lo:hi]-a) → hist`），旧版为 per-pair 逐次 `hist` 累加；执行期改 `src` 但未改 SHA `8d4df35c`，违冻结基线契约。
- **修复**：
  1. `src` **revert** 到冻结基线（per-pair 或冻结版 chunk 二选一，但必须与 `HEAD 73bb216` 一致）；优化保留为诊断脚本内联函数 `compute_corr_chunk()`，不在 `src` 留改动。
  2. **等价性小样本证明**：取 `≤1k` 事件（合成 `t_A/t_B` 或截断真实 `events`），分别调旧实现 `counts_old` 与新 `counts_chunk`，断言 `np.array_equal(counts_old, counts_chunk)` 逐 bin 相等；`n_bins=16384, bin100, max819200` 固定，`edges` 含 `max_lag` 闭合。
  3. **实际代码状态记录**：`git diff -- src/qkd_io/ttbin_pipeline.py` + `git rev-parse HEAD` + `git rev-parse origin/formal-ir-mainline` + `rg 8d4df35c` 0 hits 校验，写入 `v56d3_symbol_decomposition.json:provenance`。
  4. 若确认执行期确有偏差，则 `v56d2_calibration_run03.json` 追加 `provenance_deviation=true, overall=RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`，不作权威结果引用，后继诊断以 revert 后 SHA 为准。

## 4. 熵/互信息 — 置换不敏感诊断（Phase A）

- 输入：`comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*.parquet`（`alice_symbol/bob_symbol`，三源） + `workspace/v13r3fresh_20260816/.../pairs.parquet`（V13 参考） + `nbldpc_v25_20260818/run_04/channel_counts.npz`（仅对比，不训）
- 方法（decoder-free, ponytail: `numpy` 直算）：
  ```
  C(a,b) = #{a,b} 联合计数 (1024×1024)
  P(a,b)=C/N, P(a)=sum_b P, P(b)=sum_a P
  H(A)=-sum P(a) log2 P(a), H(B) 同
  H(A,B)=-sum P(a,b) log2 P(a,b)
  H(A|B)=H(A,B)-H(B), I(A;B)=H(A)+H(B)-H(A,B)
  ```
  置换 `b'=π(b)` 时 `H(B)` 不变（重标记），`H(A,B)` 不变（列置换），故 `I` 不变 — 可判真退化 vs 重标记。
- 产出：每源 `H(A)/H(B)/H(A|B)/I`（bits/symbol，双报 `×1024 = bits/block`），与 V13 `H(A|B)~0.80 I~9.2` 对比；若 `I` 仍 `>5 bits` 而 `acc_identity 27%` ⇒ 重标记/锚点错，非真熵增。

## 5. Identity vs 经验 MAP（Phase B）

- 定义：
  ```
  C_fit(a,b) = fit 4 frames 上的联合计数 (1024×1024)
  a_MAP(b) = argmax_a C_fit(a,b)  (每 B 的经验最可能 A)
  acc_identity = mean_{val}(a == b)
  acc_map      = mean_{val}(a == a_MAP(b))   # val 4 frames 上测，禁同帧
  ```
- 意义：`acc_map` 是在给定 `b` 条件下最优逐符号重标记的上界（任意 `π` 的最佳可达 `acc` ≤ `acc_map`，且 `acc_map` 对应 `π(b)=a_MAP(b)` 的任意扩展）。若 `acc_map - acc_identity >30%` 且 `acc_map>60%` 而物理 `π` 恢复，则为可逆重标记；若 `acc_map` 仍 `<50%` 而 `I` 高，则非逐符号可逆（pairing/anchor 错或需结构映射）。
- 划分：`calibration 8 frames [7,8,9,10,15,16,17,18]` 预注册一种 `fit=[7,8,9,10] val=[15,16,17,18]`（或交替 `fit=[7,9,15,17] val=[8,10,16,18]`，二选一预注册，本诊断取前者），**fit 上学 `a_MAP/π*`，val 上测**；另报 `fit+val` 全量仅作参考，不作分流依据。

## 6. 物理映射族枚举（Phase C）— 仅 5 族

| 族 | 语义 | 候选数 | 物理依据 |
|---|---|---|---|
| `global_shift` | `b'=(b+k) mod 1024` | 1024 | `bin_origin / delay` 整数 bin 错 |
| `global_xor` | `b'=b xor k` | 1024 | `Gray/binary` 位异或错位 |
| `axis_32x32` | `32×32` 两轴交换/翻转：`a=32*u1+u2`, `b'=32*u1'+u2'` 其中 `u1'∈{u1, 31-u1}`, `u2'∈{u2,31-u2}`, 且交换 `u1↔u2` | `≤8` | `F03 5+5` split 与硬件通道交错 |
| `gray_binary` | `b' = binary_to_gray(b)` / `gray_to_binary(b)` | 2 | `L02 Gray` vs `L01 natural` 序 |
| `u1u2_order` | `32*U1+U2` vs `32*U2+U1`（即 `a=32*U1+U2` 时 `b` 的 `U1/U2` 序反） | 2 | `Lane C` 标签序错 |

- 总候选 `≤2058`（`1024+1024+8+2+2`），可暴力枚举 fit→val。
- 方法：每族在 `fit` 上择 `k* = argmax_k acc_map_k_val?` 实际为 `argmax_k mean_{fit}(a==π_k(b))`（或最小 `NLL`  via `channel_counts.npz`），在 `val` 上报告 `acc_π/val, NLL/val, q_mass/val, mass_0±1/val`；**不任意 1024 置换**（`1024!` 禁止）。
- 恢复阈：`val` 上 `A==B>60%` 且 `NLL 22-28 → <5 bits/sym` 且 `q_mass 57-71%→<10%` 才算恢复；否则不判 `SYMBOL_MAPPING_CONTRACT_ERROR`。

## 7. 逐阶段流水核对（Phase D）— 定位首次坍缩

- 流水（decoder-free, 读 `pairs` 与 `ttbin`）：
  ```
  1. paired timestamps (t_A, t_B) — 算 I_raw = I(t_A 配对后时间差分布?) 实际用 C(a,b) 前的 I_paired = I 基于原始配对的联合？简化：用 dt 直方图 p2bg/σ 已有健康信号
  2. bin (200ps) — t→bin_idx = floor((t - t0)/200)
  3. frame anchor — bin_idx → (frame_id, symbol) via frame_start = peak_center vs global min, wrap floor_div
  4. symbol (legacy_v1) — Alice/Bob 各自 bin→symbol
  5. U1/U2 — symbol → (U1,U2) via F03 5+5 split (U1 = sym>>5, U2 = sym&31 或 Gray 序)
  ```
- 每阶段算 `I/acc`（如能在该阶段截断则停）：例如 `frame_anchor` 取 `peak_center` vs `global min` 两种，与 `t` 一致时 `I` 应仍高；若 Stage 3 后 `I` 坍塌而 Stage 2 前 `I` 高，则锚点错；若 Stage 1 已低，则 `pairing` 错；若 Stage 5 前 `acc_identity` 低但 `acc_map` 高且某 `π` 恢复，则符号序错。
- 产出：`per_stage {I, acc_identity, acc_map}` 列表与 `first_collapse_stage` 标记。

## 8. 三态分流（Phase E）— 互斥终态

```
if I_val < 2 bits/symbol 且 H(A|B)≈H(A):  # 互信息本身坍塌
    overall = TRUE_ACQUISITION_DOMAIN_SHIFT
    # 届时才规划新 prior/泄漏：重估 H(U1|B) H(U2|U1,B) → m1/m2/f
elif I_val > 5 bits 且 ∃ π∈phys_families 使 val 上 acc_π>60% 且 NLL 回落:
    overall = SYMBOL_MAPPING_CONTRACT_ERROR
    # 需修复 mapping/bin_origin/wrap/frame_anchor/Gray 契约，另冻新 TEST 再 qualification（原 90 永不重跑）
elif I_val > 5 bits 且 raw_timing 健康 (σ50-150 p2bg PARTIAL+) 且 ∀π∈phys val 上 acc_π<50%:
    overall = PAIRING_OR_FRAME_ANCHOR_ERROR
    # 非逐符号可逆，需查 pairing threshold/policy/direction 与 frame_start/sync/occupancy
else:
    overall = INCONCLUSIVE_NEED_DEEPER_STAGE  # 流水 deeper 或分源 MIXED
```

- 三态互斥，逐源可 `MIXED_BY_SOURCE`（例 `1M MAP可逆 2M pairing错`），总体取 `MIXED` 或 `INCONCLUSIVE`，不扩大为 `算法否定`。
- `TRUE_DOMAIN_SHIFT` 时才规划新 `prior/泄漏`；`SYMBOL_MAPPING` 时主算法仍不否定，仅修契约。

## 9. 校准脚本与报告（decoder-free 守卫）

- 脚本 `v56d3_symbol_decomposition.py` (本变更目录下, decoder-free): `python v56d3_symbol_decomposition.py [--pairs-root ...] [--v13-root ...] [--counts ...] [--out v56d3_symbol_decomposition.json]` → 固定 `fit=[7,8,9,10] val=[15,16,17,18]`（预注册）算 `H/I + acc_identity/acc_map + 物理5族 fit→val + 流水分段`，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow`，`py_compile` PASS；输出 `v56d3_symbol_decomposition.json` + 控制台摘要
- 报告 `SYMBOL_DECOMPOSITION_REPORT.md`: 每源 `H/I/acc_identity/acc_map/5族 val恢复/流水坍缩点` 与总体三态分流，数据与 json 一致，不扩大为 FER/阈值/SKR/晋升，显式 `原 90 已揭盲不可复用` 与 `主算法不否定`
- 守卫：诊断期 **零 decoder**、原 90 已揭盲保护、**不创建 run_01 decoder 执行**

## 10. 与 V55/V56D1/D2 衔接

- V55 `QUALIFICATION_RESULT 0/90` 已固化，不重跑；V56D1 `MIXED_BY_SOURCE` 与 V56D2 `calibration 8 frames` 已固化，V56D3 在其上做映射分解；`run03` 的 `PROVENANCE_DEVIATION` 标注后不作为后继输入。
- `V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 仍为对照（`workspace/v13r3fresh_20260816/sidecars`），不重发明。

## 11. 自由裁量 D1-D6

- D1 `I/H` 仅 `numpy` 直算，不引 `scipy`（ponytail: `numpy` 已装）
- D2 `fit/val` 固定 `[7,8,9,10]/[15,16,17,18]` 不搜索多划分（仅预注册一种）
- D3 物理 5 族已达最简，不扩任意置换（`1024!` 禁止）
- D4 流水分段取 `min(bin, frame_anchor, symbol, U1/U2)` 四段，不做更细 `sync/occupancy` 网格
- D5 `acc_map` 即 `argmax` 上界，不做 `Hungarian` 全局最优置换（物理族已覆盖可逆重标记）
- D6 不产生新矩阵/码参数，仅分解与判定，最简闭环
