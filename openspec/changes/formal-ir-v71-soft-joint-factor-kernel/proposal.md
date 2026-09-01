# OpenSpec Proposal: formal-ir-v71-soft-joint-factor-kernel

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅计划四工件 + decoder-free 1024-state 纯因子核校验完整 posterior 保留 + 只读 ldpc_v5* audit A1-A6 分流 READY/ADAPTER/NOT_COMPATIBLE，不改1024维符号/GF32/验证框架，不跑 decoder 不构业务矩阵，仅验证 5 函数纯枚举 log-domain 因子核

**Domain**: Formal IR / soft-joint factor kernel verification (V70 同域直接后继，V67/V69 三预注册 Stage2 复用，V70 二进制 soft-joint 因子完整性已验证)

**Change ID**: `formal-ir-v71-soft-joint-factor-kernel`

**Cycle ID**: `V71-SJK` (soft-joint-factor-kernel), predecessor `formal-ir-v70-binary-soft-joint-feasibility` (`9bc34be64a2822c8babb4320efb47fc7e335a21a` V70 `PLAN_CANDIDATE/DECODER_FREE`) + `formal-ir-v67-multisession-feasibility-map` (`V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL` natural 5+5) + `formal-ir-v64-full-symbol-verification-correction` (`22/24 PASS`) + `binary-ldpc-v5` (`ldpc_v5*` 已冻结 read-only audit 对象)

**Branch**: `formal-ir-mainline`

**HEAD**: `6bc06d4d271b2418c5bfa6160f7840b58fc66b60` (动态绑定 `git rev-parse HEAD`; 已修正历史静态偏差 `历史三头`; `origin/formal-ir-mainline == HEAD` 40位重核，不一致阻塞; **rev A1 bench n_inv workload 1/9/1024 (n_inv=1024, kernel_calls=1024 , deterministic seed0) / A2 去 self 比较需真 extrinsic+10240 接口否则 ADAPTER_REQUIRED / A3 三状态 kernel/backend/capacity 分离 2M NO_INFORMATION (capacity FEASIBLE/MARGINAL/NO_INFORMATION)**)

**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点；V71 复用 V67/V69 三 session 的 `Stage2 CAL1024+VAL256` 作 AUDIT/KERNEL 完整性锚点，但 **Phase E benchmark 仅在 1M session 的 CAL1024+VAL256 上执行 1/9/1024 block 实测**，不换点，不换 bin/mapping，不新增 acquisition，不读 TEST)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于计划四工件 + decoder-free 1024-state 纯因子核 (5函数纯枚举 log-domain) + 只读 `ldpc_v5*` A1-A6 audit 分流 + D1-D10 不变量校验 + 1M CAL/VAL benchmark (1/9/1024 block, 30s/2GiB 路由阈) + f1.3 冻结 `f_actual NOT_MEASURED` + per-session 6终端/总体4态，四工件产出，不创建 `run_01`，不比较方法，不转 qualification，不启动 V72，任何 decoder 执行需独立 `PLAN_ACCEPT + EXECUTE_AUTH`

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 纯因子核 `v71_soft_joint_factor.py` (5函数 `numpy` 直算 1024 枚举 log-domain, `itertools` 无需, 不引 `scipy/sklearn/numba`) + 1 只读审计脚本 `v71_ldpc_v5_audit.py` (A1-A6 纯 AST/import 探针, `rg "decode_" 0 hits`) + 1 结果表 JSON + 1 双报告 AUDIT/KERNEL + 1 小测试；零 decoder/矩阵/新依赖，最短科学路径。laziest alternative: `numpy` + `logsumexp` 手写，不引外部数值库。

> **科学问题（冻结）**：于**完全冻结主体**（`n=1024, q=1024 (10-bit), GF32 poly37, H1 16×1024 rank16, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0 poly37, full-tag canonical 32*U1+U2(+U3) 扩展, leak Σw_i·m_i+64` 全只读，**不改维度/符号/q/GF/两层验证**）下，**验证 1024-state 纯因子核是否保留完整 1024-ary 联合后验**：定义 **extrinsic 冻结语义**（`extrinsic = log_posterior - log_prior` log域差分，不含信道因子，纯函数输入输出分离）+ **5 函数纯枚举 log-domain 因子核**（枚举 1024 态，logsumexp 归一，5 函数正交：先验/LLR/因子合成/归一/extrinsic，外推校验）+ **D1-D10 十不变量**（完备性/归一/边际保持/delta退化/链式/秩无关/数值稳定/确定性/TEST隔离/不变量正交） + **只读 `ldpc_v5*` A1-A6 审计**（接口/策略manifest/信道绑定/extrinsic兼容/运行时cap/披露计费，输出 `READY/ADAPTER/NOT_COMPATIBLE`），以 `1M CAL1024` 独立估计并在 `1M VAL256` 上以 `1/9/1024 block` 实测 `30s/2GiB` 路由阈验证 `D1-D10` 与 `ready` 路由，预算 `f1.3` 冻结且 `f_actual NOT_MEASURED`（不测真实披露 bits），每 session 6终端总体4态，产出四工件，不跑 decoder 不改 src 不读 TEST 不启 V72。

## Goal

以最短 decoder-free 路径完成 **1024-state 纯因子核校验完整后验保留 + ldpc_v5* 只读兼容地图**，为 V70 二进制 soft-joint 因子验证后是否可直接对接 `binary-ldpc-v5` 提供可验证证据：

### 1. 仅验证 1024-state 纯因子核保留完整1024-ary posterior，不改1024维符号GF32验证框架
- **冻结**：`n=1024, q=1024 (10-bit s∈[0,1023]), GF32 poly37, H1 16×1024 rank16 80b U=32*U1+U2, Lane C 184/190/192, H_inc Δ8, decoder 90/1.0, full-tag canonical` 全只读（`git diff -- src/ ==0`），处理点 `84d62779 legacy_v1` 单点，`per frame 256, BLOCK 1024, period 204800` 等同 V67/V70。
- **唯一变量**：纯因子核 `v71_soft_joint_factor.py` 的 5 函数 log-domain 因子合成（`log_prior 1024 + llr_10 → log_post 1024` 枚举1024态，`extrinsic = log_post - log_prior`），不改 `s` 本身，不引 `Gray/MET/protograph/SC`，不构业务 H。

### 2. 只读 `ldpc_v5*` A1-A6 audit 得 READY/ADAPTER/NOT_COMPATIBLE 分流
- **对象**：`comparison_bench/src/comparison_bench/formal_ir/ldpc_v5*.py` (`ldpc_v5.py`, `ldpc_v5_development.py`, `ldpc_v5_partition.py`, `codebook_v5_h2.py`, `ldpc_v5_predecessors.py` 等) 全只读（`git diff -- .../formal_ir/ldpc_v5* ==0`），`rg "decode_" audit脚本 0 hits`，不执行 `run_ldpc_formal_v5`。
- **A1-A6**：
  - A1 `interface_presence` — 探针 `ldpc_v5.py` 导出 `run_ldpc_formal_v5 / build_v5_policy_manifest / verify_v5_policy_manifest / validate_outcome_v5 / verify_public_payload_v5` 存在且签名稳定
  - A2 `policy_manifest_schema` — `policy_manifest.candidates[].policy_sha256 / decoder_sha256 / h1_binding` 字段存在且重建一致
  - A3 `channel_binding` — `channel_model.model_sha256 == selection_manifest.channel_model_sha256` 绑定一致
  - A4 `extrinsic_interface` — `ldpc_v5` 是否暴露 extrinsic 注入点或仅硬 syndrome（探针 `error_channel` 参数类型 `list[float]` vs `np.ndarray`，`plane_error_channel` 接口）
  - A5 `runtime_caps` — `caps {wall_s 10.0, decoder_calls 20, events 32}` vs 因子核 benchmark `30s/2GiB/1/9/1024 block` 兼容性（cap 不超限）
  - A6 `disclosure_accounting` — `ldpc_v5 OUTCOME_FIELDS` 中 `ldpc_syndrome_bits / h1/h2 / verification_tag_bits_component` 分解是否可容纳因子核 `extrinsic` 披露（不与 `key_dependent` 混计）
- **分流**：`READY` (A1-A6 全 PASS, extrinsic 零改直通) / `ADAPTER` (A1-A3 PASS 但 A4/A6 需适配层) / `NOT_COMPATIBLE` (A1/A2 失败或结构不匹配)，per session 独立，最坏取整。

### 3. 冻结 extrinsic 定义，Phase C 实现 5 函数纯枚举 log-domain
- **extrinsic 冻结**：`extrinsic[a] = log_post[a] - log_prior[a]` (log域差分，仅因子贡献，不含 `P(a|b)` 信道部分，外积 `Π factor` 的 log 叠加，经 `logsumexp` 归一后残差)，定义与 `ldpc_v5` 的 `error_channel` 语义正交，报告显式。
- **5 函数**（纯函数，无I/O/随机/全局状态，枚举1024，全 log-domain）：
  1. `log_prior_from_posterior(log_P_a_given_b: float[1024]) -> log_prior[1024]` — 归一化先验（`logsumexp` 校验 `Σ exp=1`）
  2. `bit_factor_from_llr(llr_10: float[10]) -> log_factor[1024]` — 每 `a` 的 `Σ bits_i(a)*llr_i` (`bits_i=(a>>i)&1`)
  3. `soft_joint_factor_kernel(log_prior[1024], llr_10[10]) -> log_post[1024]` — 主核：`log_unnorm[a]=log_prior[a]+Σ bits_i*llr_i`, `log_post = log_unnorm - logsumexp(log_unnorm)`
  4. `extrinsic_from_logs(log_prior[1024], log_post[1024]) -> extrinsic[1024]` — `ext - prior` 差分，`logsumexp(extrinsic + log_prior) == 0` 校验
  5. `validate_kernel(log_prior, llr, log_post, extrinsic) -> dict{checks}` — 触发 D1-D10 校验，返回各不变量 PASS/FAIL
- 纯函数校验：全零 `llr≡0 ⇒ log_post ≡ log_prior` (`max|Δ|<1e-12`)；delta `llr_i=±1e6` 定向 `a*` ⇒ posterior 退化 `a*` (`log_post[a*]=0` 其余 `-inf`)，与 brute-force 逐项 `|Δ|<1e-12`。

### 4. Phase D D1-D10 不变量（十不变量正交完备）
- D1 `completeness` 1024 枚举无丢：`∀s s== Σ bit_i<<i` 且 `len(log_post)==1024`
- D2 `normalization` 归一：`| Σ exp(log_post) -1 |<1e-12` & `logsumexp(log_post)==0±1e-12`
- D3 `marginal_preservation` 全零 `llr≡0 ⇒ log_post ≡ log_prior` `max|Δ|<1e-12`
- D4 `delta_concentration` delta `llr定向a* ⇒ log_post[a*]=0` 且其余 `< -1e2` 且 `|Δ|<1e-9`
- D5 `extrinsic_consistency` `extrinsic = log_post - log_prior` 且 `logsumexp(log_prior+extrinsic)==0±1e-12`
- D6 `log_domain_stability` `K=1e6` 时无 `exp overflow`，全程 log域 `logaddexp`，`isfinite` 校验
- D7 `determinism` 纯函数：同输入二次调用 `max|Δ|==0`，无随机/全局
- D8 `chain_closure` `CE_full` 与 `Σ CE_bit_i - D_bits` 链式 `|Δ|<1e-9`（复用 V70 的 `P(a|b)` 估计，仅校验不改预算）
- D9 `test_isolation` `used_test==False` 且 `rg -i "test.*read|read.*test" 0 hits` 且未导入 TEST 数据
- D10 `orthogonality` 十不变量彼此正交：任一 FAIL 不掩盖他项，报告逐项分解

### 5. Phase E 仅 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈
- **范围**：仅 `1M` session 的 `stage2_CAL[1024] (262144 pairs) + stage2_VAL[256] (65536 pairs)` 原样（复用 V69/V70 注册表，不新增 acquisition），不测 `1p5M/2M` 的因子核时延，仅作 audit 分流输入。
- **benchmark**：对主核 `soft_joint_factor_kernel` 在 `1M CAL/VAL` 上分 `block ∈ {1, 9, 1024}` 符号块批量（`1` = per-symbol, `9` = per-plane-batch, `1024` = per-frame）各计 `wall_s` 与 `peak_MiB` (tracemalloc 或 `resource` 估)，`log_prior` 固定为 `1M CAL` 上 `λ*` 的 `P(a|b)` 对应值，`llr_10` 取 `0` 与 `seed0 deterministic N(0,1)` 两档，**每档固定 1024 次 `soft_joint_factor_kernel` 调用（`n_inv=1024`），`wall` 取两次 llr 档的 median**。
- **路由阈**：`wall_s ≤30s` 且 `peak ≤2048MiB` 对 `1024 block` 在 `1M VAL256` 全量 (`256*1024` 符号) 上测一次；任一 block  size 超限则 `E_PERF_BLOCKED`，报告三档明细与 `per invocation ns`。

### 6. Phase F f1.3 冻结 f_actual NOT_MEASURED
- `f1.3` 为泄漏预算冻结参数：`required = ceil(1.3 * N * CE_full)` (`N=1024`, `CE_full` 取 `1M VAL` 上 `CE_full^{VAL}` bits/symbol) 仅用于 audit 中 `A6` 的 `disclosure` 对比参照，**不实测** `f_actual = actual_disclosure / (N*CE_full)`，所有 `f_actual` 字段统一记 `NOT_MEASURED`，报告显式 `f1.3 frozen, f_actual NOT_MEASURED`，门禁不以 `f_actual` 判。

### 7. 每 session 6终端总体4态 decoder-free
- 复用 V67/V69 三 session 的 `stage2_CAL/VAL` 仅作 audit/KERNEL 的分流输入（Phase E benchmark 仅 1M 实测），`CAL选VAL确认一次` 不变量在 `1M`上计 `CE/D/lambda` 描述性。
- **Per-session 6终端 first-match（优先级高→低互斥）**：
  1. `V71_EVIDENCE_INCOMPLETE` — 物化/帧256/provenance/`C_ab` 非有限/`1024枚举不足`/`logsumexp` 非有限
  2. `V71_MODEL_NOT_STABLE` — `λ` 触边 `[1e-2,1e4]` 或 `ΔCE>0.50` 或 `val_b_unseen>1%` 或 `D_bits < -1e-9` 或 `D10` 正交中有非 D3/D4 的 FAIL
  3. `V71_NOT_COMPATIBLE` — audit `A1/A2` FAIL 或 `D1/D2` FAIL（核不完备/不归一，结构不可接）
  4. `V71_KERNEL_READY_FEASIBLE` — `D1-D10 全 PASS` && audit `READY` && `E benchmark PASS` (`wall≤30s && peak≤2GiB` 对 1024-block)
  5. `V71_KERNEL_ADAPTER_FEASIBLE` — `D1-D10 全 PASS` && audit `ADAPTER` && `E benchmark PASS`
  6. `V71_KERNEL_HEAVY` — `D1-D10 PASS` 但 `E benchmark` 超限或 audit `NOT_COMPATIBLE` 以外残差（需适配或降 block）
- **总体4态（基于3 sessions 汇聚，Phase E 仅 1M 实测但分流仍基于三 session audit）**：
  1. `V71_OVERALL_EVIDENCE_INCOMPLETE` — 任一 session `EVIDENCE_INCOMPLETE`
  2. `V71_OVERALL_MODEL_NOT_STABLE` — 无 `EVIDENCE` 但任一 `MODEL_NOT_STABLE`
  3. `V71_OVERALL_KERNEL_READY` — `ready_count==3` (3× `KERNEL_READY_FEASIBLE`)
  4. `V71_OVERALL_KERNEL_ADAPTER_OR_HEAVY` — 否则（`adapter/heavy/not_compatible` 混成，需适配层或 kernel 降级），显式 `ready/adapter/heavy/not_compatible/evidence/model` 6 正交计数

### 8. 本轮交付边界（四工件 + 双报告，decoder-free）
- 产出 `proposal/design/tasks/specs` 四工件 + `scripts/v71_soft_joint_factor.py` (5函数纯枚举 log-domain, `rg "decode_" 0 hits`) + `scripts/v71_ldpc_v5_audit.py` (A1-A6 只读探针, `rg "decode_" 0 hits`) + `v71_results.json` (per session `D1-D10/CE/D/lambda/audit_E/benchmark` + overall 4态) + `v71_audit_report.json` / `V71_AUDIT_REPORT.md` (A1-A6 per session) + `V71_KERNEL_REPORT.md` (D1-D10 + benchmark) + `test_v71_soft_joint_factor_kernel_small.py` (`py_compile PASS, pytest -p no:cacheprovider -q`) + `v71_manifest.json` + 控制台 6终端/4态摘要；**禁** `decode_/construct_H*` 业务调用、`run_01`、`H` 业务码构造、跨方法比较、改 `src/` baseline、调 `TEST`、启动 V72。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa/construct_H*_business/gf_rank_business/nested_business` decoder 或业务矩阵构造（脚本内 `rg "decode_" 0 hits`）；不改 `H1/Lane C/m2/H_inc/decoder/full-tag` 任一冻结量；不引 `MET/protograph/SC` 新码族；**不以 `required/margin` 是否 `<10240` 去构造业务 H**（仅作 A6 披露对照参照，不构 H）。
- 不读密封 `TEST` 的任何 `H/CE/NLL/MAP` 统计作 `P/required/rank` 选择，`λ` 择优仅 `1M CAL` 描述性，`VAL` 仅 D 不变量确认，违则 `EVIDENCE_INCOMPLETE`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（单点 `84d62779`）；`λ` 仅 `[1e-2,1e4] log10` 仅 `CAL 4-fold`，不扩；`H_bin` 不构，仅 audit `A6` 披露参照。
- 不宣称 `FER/阈值/SKR/晋升/安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，不直接进入 qualification，不作跨方法 rank，不以 `KERNEL_READY` 宣称码可译。
- 不改写/覆盖 `V13/V48–V71` 任何已有输出与终态（只读）；V67/V69 三 session 仅复用 Stage2，不重跑 Stage0/Stage1；Phase E benchmark 仅 1M 实测，不扩至三 session 全 benchmark。
- 不以总体平均替代 per-session 分流；不以 `V25 H` 作新域门禁，门禁用 `D1-D10` + `A1-A6` + `30s/2GiB` 路由阈。
- 不创建正式 `.../v71_*/run_01` decoder 执行；正式 decoder 需另起 OpenSpec + 独立 `EXECUTE_AUTH`。
- 不比较 Polar/Cascade/LDPC 方法；单 soft-joint 因子核内可行性探查，不作跨方法 rank。
- **不启动 V72**：任何 V72 `QUALIFICATION_PLAN_READY / run_01 / 阈/码族` 预冻结均禁止在本变更内声明或执行；V71 报告仅以 `successor ∈ {v71_kernel_adapter_design, v71_ldpc_v5_integration, recollect}` 指向，不创建 V72 目录或产出。
- 不实测 `f_actual`：所有 `f_actual` 字段 `NOT_MEASURED`，仅冻结 `f=1.3` 作参照。

## Scope

1. **冻结主体与处理点零改（1024维符号纯因子核扩展，仅核验证）**：`n1024, q1024 (10-bit s), GF32 poly37, H1 16×1024 rank16 80b U=32*U1+U2, Lane C ordinal-2 s38310x m2 184/190/192, H_inc Δ8, decoder 90/1.0 poly37 early-stop (禁用), full-tag canonical, leak Σw_i·m_i+64` 全只读；`84d62779 legacy_v1` 单点；不引 V71 新码本以外的表示。
2. **只读 `ldpc_v5*` A1-A6 audit 得 READY/ADAPTER/NOT_COMPATIBLE**：`ldpc_v5*.py` 只读 AST/import 探针，`A1 interface / A2 policy_manifest_schema(去 self 比较，需真 extrinsic+10240 接口否则 ADAPTER_REQUIRED) / A3 channel_binding / A4 extrinsic_interface / A5 runtime_caps / A6 disclosure_accounting` 六项每 session 独立判定，输出 `READY/ADAPTER/NOT_COMPATIBLE` 分流，最坏取整，不执行 `run_ldpc_formal_v5`，**A3 三状态分离 kernel_status/backend_status/capacity_status，2M 固定 `NO_INFORMATION`**。
3. **冻结 extrinsic 定义 Phase C 实现 5 函数纯枚举 log-domain**：`extrinsic = log_post - log_prior` 冻结，5 函数 `log_prior_from_posterior / bit_factor_from_llr / soft_joint_factor_kernel / extrinsic_from_logs / validate_kernel` 枚举 1024 态，全零得 marginal、delta 得确定值与 brute-force 对照 `|Δ|<1e-12`，log域 `logsumexp` 归一，纯函数无 I/O/随机/全局。
4. **Phase D D1-D10 不变量**：`D1 completeness / D2 normalization / D3 marginal_preservation / D4 delta_concentration / D5 extrinsic_consistency / D6 log_domain_stability / D7 determinism / D8 chain_closure / D9 test_isolation / D10 orthogonality` 逐项 `PASS/FAIL`，任一 FAIL 触发 `MODEL_NOT_STABLE` 或 `NOT_COMPATIBLE`（D1/D2 抬至 `NOT_COMPATIBLE`）。
5. **Phase E 仅 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈**：仅 `1M` session 的 `CAL1024 (262144 pairs)+VAL256 (65536 pairs)` 上对主核 `soft_joint_factor_kernel` 分 `block 1/9/1024` 测 `wall_s/peak_MiB`，`wall≤30s && peak≤2048MiB` 对 `1024-block` 在 `1M VAL` 全量上判 `PASS`，超限 `E_PERF_BLOCKED`，三档明细报告 `per invocation ns`。
6. **Phase F f1.3 冻结 f_actual NOT_MEASURED**：`f=1.3` freeze 作 `required = ceil(1.3*N*CE_full)` 参照（`CE_full` 取 `1M VAL`，仅 A6 对比），所有 `f_actual` 字段 `NOT_MEASURED`，报告显式 `f1.3 frozen, f_actual NOT_MEASURED`，门禁不以 `f_actual` 判。
7. **终态 per-session 6终端 + 总体4态 + 路由阈审计**：每 session `EVIDENCE_INCOMPLETE > MODEL_NOT_STABLE(ΔCE>0.5/unseen>1%/D<0/D6 FAIL) > NOT_COMPATIBLE(A1/A2/D1/D2 FAIL) > READY_FEASIBLE(D1-10 PASS && READY && E PASS) > ADAPTER_FEASIBLE(D1-10 PASS && ADAPTER && E PASS) > HEAVY(E超限)`；总体 `EVIDENCE/MODEL/READY(3×)/ADAPTER_OR_HEAVY` + `ready/adapter/heavy/not_compatible/evidence/model` 6计数审计；`capacity_warning` 正交旗标仅描述不过门禁。
8. **四工件 + 双报告交付（DECODER_FREE）**：`scripts/v71_soft_joint_factor.py` + `scripts/v71_ldpc_v5_audit.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`) 输出 `v71_results.json + v71_audit_report.json + V71_AUDIT_REPORT.md + V71_KERNEL_REPORT.md + v71_table.csv/json`（每行 `session/CE/D/lambda/audit_A1-A6/D1-D10/benchmark/required/f1.3/classification` + 总体4态汇总）+ 控制台摘要，未创建 `run_01`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v71-soft-joint-factor-kernel/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v71_soft_joint_factor.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`) + `scripts/v71_ldpc_v5_audit.py` (`rg "decode_" 0 hits`, 只读 A1-A6) + 冻结注册表 `v71_data_registry.json` (复用 V69 三 session Stage2, Phase E 仅 1M benchmark) + `v71_results.json` (per session `D1-D10/audit_A1-A6/benchmark` + overall 4态) + `v71_audit_report.json` / `V71_AUDIT_REPORT.md` (A1-A6 per session) + `V71_KERNEL_REPORT.md` (D1-D10 + benchmark + 5函数校验) + `v71_table.csv/.json` (每行 `session/CE/D/lambda/audit/D1-D10/benchmark/classification` + 总体汇总) + `test_v71_soft_joint_factor_kernel_small.py` + `v71_manifest.json` + 控制台摘要。
- **只读依赖**：`v69_data_registry.json / v67_data_registry.json / v67_feasibility_table.json`（V69 三 session Stage2 帧集复用） + `v55_intake_20260828/pairs/*` 3 sessions + `comparison_bench/src/comparison_bench/formal_ir/ldpc_v5*.py` (`A1-A6` 只读探针) + `nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` 仅对照。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V71` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01`，零码参增量，不启动 decoder，不构业务矩阵，不重估计 V67/V70，不启动 V72**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`branch formal-ir-mainline` + `HEAD 6bc06d4d271b2418c5bfa6160f7840b58fc66b60` (动态绑定 `git rev-parse HEAD`; 已修正历史三头偏差 `历史三头`，predecessor `9bc34be6` 不变，`git rev-parse HEAD == origin/formal-ir-mainline` 重核) + `data 84d62779` + `predecessor V70 9bc34be6 / V67 FEASIBILITY_MAP_ACCEPTED / V64 22/24 PASS` 已绑定，显式声明 decoder-free、零 decoder/业务矩阵、1024-state 纯因子核、5函数纯枚举 log-domain、A1-A6 READY/ADAPTER/NOT_COMPATIBLE、D1-D10 不变量、1M CAL/VAL 1/9/1024 block 30s/2GiB 路由阈、f1.3 freeze `f_actual NOT_MEASURED`、per-session 6终端总体4态、四工件产出已声明。
- [ ] **冻结主体零改已验**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`，`n1024 q1024 GF32 poly37 H1 16×1024 rank16 80b U=32*U1+U2 F03 5+5 Lane C 184/190/192 H_inc Δ8 decoder 90/1.0 full-tag canonical leak Σw_i·m_i+64` 全只读，处理点 `84d62779 legacy_v1` 单点，`rg -i "gray|met|protograph|sc_coupling" scripts/v71_soft_joint_factor.py` 0 hits（除纯因子核注释），`rg "decode_|construct_.*business|gf_rank.*business|nested.*business" 0 hits` 已验（`ldpc_v5*` 只读探针不属业务 `construct`），`rg "TEST.*read|read.*TEST" 0 hits` 且 `used_test==False`。
- [ ] **只读 `ldpc_v5*` A1-A6 已验**：`A1 interface_presence / A2 policy_manifest_schema / A3 channel_binding / A4 extrinsic_interface / A5 runtime_caps / A6 disclosure_accounting` 每 session 独立 `PASS/FAIL`，分流 `READY(A1-A6 PASS) / ADAPTER(A1-A3 PASS, A4/A6 需适配) / NOT_COMPATIBLE(A1/A2 或 D1/D2 FAIL)` 已判定，`ldpc_v5*` 文件 `git diff ==0` 且脚本内 `rg "run_ldpc_formal_v5\(" 0 hits`（仅 import 探针，不执行），落盘 `v71_audit_report.json` 与 `V71_AUDIT_REPORT.md` 一致。
- [ ] **冻结 extrinsic + 5 函数纯枚举 log-domain 已验**：`extrinsic = log_post - log_prior` 已冻结定义，5 函数 `log_prior_from_posterior / bit_factor_from_llr / soft_joint_factor_kernel / extrinsic_from_logs / validate_kernel` 枚举 1024 态，全零 `llr≡0 ⇒ log_post ≡ log_prior` (`max|Δ|<1e-12`) 且 delta `K=1e6` 定向 `a*=0,511,1023 ⇒ posterior` 退化 `a*` (`log_post[a*]=0` 其余 `-inf`, `|Δ|<1e-9`) 二极与显式 1024 枚举 brute-force 对照 `max|Δ|<1e-12`，`logsumexp` 实现 `numpy.logaddexp.reduce` 无 `exp overflow`，纯函数无 I/O/随机/全局，`py_compile PASS`，`pytest` 小测试 PASS。
- [ ] **Phase D D1-D10 已验**：`D1 completeness / D2 normalization / D3 marginal_preservation / D4 delta_concentration / D5 extrinsic_consistency / D6 log_domain_stability / D7 determinism / D8 chain_closure / D9 test_isolation / D10 orthogonality` 逐项 `PASS/FAIL` 已在 `1M CAL/VAL` 上校验且与 `v71_results.json` 一致，任一 FAIL 按优先级抬至 `MODEL_NOT_STABLE` 或 `NOT_COMPATIBLE`，`D3/D4` 的 `1e-12/1e-9` 阈已验。
- [ ] **Phase E 仅 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 已验**：仅 `1M` session 的 `CAL1024 (262144 pairs)+VAL256 (65536 pairs)` 上对主核 `soft_joint_factor_kernel` 分 `block ∈ {1,9,1024}` 各计 `wall_s/peak_MiB`，`1024-block` 在 `1M VAL` 全量上 `wall≤30s && peak≤2048MiB` 判 `E_PERF_PASS`，超限 `E_PERF_BLOCKED`，三档 `wall_s/peak_MiB/per_invocation_ns` 已落盘且与 `V71_KERNEL_REPORT.md` 一致，`1p5M/2M` 未 benchmark 已验。
- [ ] **Phase F f1.3 freeze f_actual NOT_MEASURED 已验**：`f=1.3` frozen，`required = ceil(1.3*1024*CE_full^{VAL})` 仅作 `A6` 披露参照（`CE_full` 取 `1M VAL`），所有 `f_actual` 字段 `== "NOT_MEASURED"` 已验，`grep "f_actual.*NOT_MEASURED" v71_results.json` 命中且 `rg "f_actual.*[0-9]\."` 0 hits，门禁不以 `f_actual` 判。
- [ ] **Per-session 6终端互斥 + 总体4态已验**：每 session `classification ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, NOT_COMPATIBLE, KERNEL_READY_FEASIBLE, KERNEL_ADAPTER_FEASIBLE, KERNEL_HEAVY}` 按 `EVIDENCE > MODEL(D1-D10非D3/D4 FAIL) > NOT_COMPATIBLE(A1/A2/D1/D2 FAIL) > READY(D1-10 PASS && READY && E PASS) > ADAPTER(D1-10 PASS && ADAPTER && E PASS) > HEAVY(E超限)` 已判定；总体 `overall ∈ {EVIDENCE_INCOMPLETE, MODEL_NOT_STABLE, KERNEL_READY(3×READY), KERNEL_ADAPTER_OR_HEAVY}` 基于 `6 orthogonal counts (ready/adapter/heavy/not_compatible/evidence/model)` 已判定，报告 4态章节与 `json/csv` 一致。
- [ ] **四工件 + 双报告完整**：`v71_data_registry.json` + `v71_results.json` + `v71_table.csv/.json`（行对等，含 `session/CE/D/lambda/audit_A1-A6/D1-D10/benchmark/required/f1.3/classification` + `overall 4态` 汇总且与 json 一致，`capacity_warning` 正交 + `descriptive_diagnostics` 逐 session）+ `V71_AUDIT_REPORT.md` (A1-A6) + `V71_KERNEL_REPORT.md` (D1-D10 + 5函数 + benchmark) 已齐。
- [ ] `scripts/v71_soft_joint_factor.py` 与 `scripts/v71_ldpc_v5_audit.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`、`rg "construct_.*business" 0 hits`、`rg "gf_rank.*business" 0 hits`、`rg -i "met|protograph" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，`pytest -p no:cacheprovider -q test_v71_soft_joint_factor_kernel_small.py` PASS），输出 `results + audit + table + 双报告` + 控制台 6终端/4态摘要，**未创建 run_01，未构业务矩阵，未读 TEST，λ 不扩搜索，1024 枚举纯函数 brute 已验，D1-D10 已验，A1-A6 已验，1M benchmark 30s/2GiB 已验，f1.3 freeze f_actual NOT_MEASURED 已验**。
- [ ] 已停留在 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v71_*/run_01`（`ls` 不存在已验）且未创建任何 `.../v72_*/run_01`，不比较，不碰 `V48-V70` 块外，未转 qualification，未启动 V72，**四工件+registry+spike+双报告已单独提交推送，返回新 Plan SHA + per-session audit/D1-D10/benchmark + 各分流计数 + overall 4态**，等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01 不存在/py_compile/TEST 未读/D1-D10/5函数1024枚举 brute/ A1-A6/1M benchmark 30s/2GiB/f1.3 NOT_MEASURED/6终端+4态/CAL选VAL确认一次`）。

## Tasks

见 `tasks.md`（Phase A 注册表复用；Phase B 冻结主体 1024维纯因子核不重构；Phase C extrinsic 冻结 + 5 函数纯枚举 log-domain；Phase D D1-D10 不变量；Phase E 仅 1M CAL/VAL benchmark 1/9/1024 block 30s/2GiB 路由阈；Phase F f1.3 冻结 f_actual NOT_MEASURED；Phase G per-session 6终端总体4态；Phase H 四工件 + 双报告；Phase I 守卫 R71-01~11 + 单独提交推送新 Plan SHA + 不启 V72）。

## Lifecycle

`V64` 已 `22/24 full-tag PASS`；`V65` new-session 对照；`V66` 单 session `72` 自适应 `RATE_NOT_FEASIBLE`；`V67-MAP` 已 `V67_FEASIBILITY_MAP_ACCEPTED` 3 sessions 均 `NEAR_FULL`（natural 5+5）；`V68-BAL` 为**均衡 5+5 均衡性地图** decoder-free 预冻结（`252` 枚举 `max→sum→abs→lex`）；`V69-3L` 为**三层表示可行性地图** decoder-free 预冻结（`3^10=59049→37170` 升序唯一词典序）；`V70-BSJ` 为**二进制 soft-joint 因子完整性可行性地图** decoder-free 预冻结（`1024` 枚举纯函数 + `D_bits` + `required` + `10240` 嵌套族秩）；`V71-SJK` 为**1024-state 纯因子核校验完整 posterior 保留 + ldpc_v5* 只读兼容地图** decoder-free 预冻结，当前 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（验证 1024-state 纯因子核 5 函数 log-domain 枚举 + D1-D10 + 只读 `ldpc_v5*` A1-A6 READY/ADAPTER/NOT_COMPATIBLE + 1M CAL/VAL 1/9/1024 block 30s/2GiB 路由阈 + f1.3 freeze NOT_MEASURED，每 session 6终端总体4态，不跑 decoder 不构业务矩阵，不启 V72）；`V71` 本身不直接进入 qualification；任何 decoder / 新表示需另起 `EXECUTE_AUTH`。
