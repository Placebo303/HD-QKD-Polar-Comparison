# V72P1-ADP Execution Packet Addendum — CANDIDATE (IMPLEMENTATION_NOT_STARTED / EXECUTE_NOT_AUTHORIZED)

**Repository**: `HD-QKD_Polar_Comparison`
**Branch**: `formal-ir-mainline`
**Cycle ID**: `V72P1-ADP`
**Change ID**: `formal-ir-v72p1-soft-joint-binary-adapter`
**Kind**: `PACKET_ADDENDUM_CANDIDATE` — closes two blockers (file list + numeric freeze) for synthetic qualification only
**Required Base SHA**: `fb441f0f95a4d2268fa0f1bcce2db6fce83bc615`
**Accepted Plan SHA**: `73efd91f379b5abdeda675c36d1a054f59ff89ff`
**Packet Base SHA**: `f03e160c270765cee6ddbe0ff2765426ae0468a6` → addendum base `fb441f0f` (HEAD == origin/formal-ir-mainline required, verified `fb441f0f95a4d2268fa0f1bcce2db6fce83bc615`)
**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1`, `used_2m false`)
**Lifecycle**: `PACKET_ADDENDUM_CANDIDATE_REVISED / IMPLEMENTATION_NOT_STARTED / EXECUTE_NOT_AUTHORIZED` — R1–R9 修订版（原 base `fb441f0f`，原版本 `ea82423f`；REVISE verdict 后修订，待 re-review）
**Authorization After Acceptance**: `IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION_ONLY` — does NOT authorize real data, 2M/TEST/holdout, formal decoder, or `run_01`
**Formal Execution**: `false` | **Real Data**: `false` | **RUN_01 Authorized**: `false`

> 本文件为本轮唯一允许新增的文件。不得修改任何既有文件，不得实现代码、运行测试、运行 decoder、创建输出。本 addendum 经独立接受后才允许后续实现；本轮自身仍为 CANDIDATE，不授权实现与执行。

---

## 0. Addendum Scope & Ponytail Lite Principle

- **Ponytail lite**: 最少文件，优先复用 V71 (`scripts/v71_soft_joint_factor.py` + `test_v71_soft_joint_factor_kernel_small.py`) 与 V72P0 (`scripts/v72p0_soft_joint_binary_synthetic.py` + `test_v72p0_soft_joint_binary_synthetic_small.py`) 的已验证 log-domain / sparse-CSR / tiny-exhaustive 基础设施。
- 若一个实现文件、一个测试文件、一个 synthetic CLI 足够，不得增加抽象层、registry framework 或 verifier framework。
- 禁止 `src/`、`experiments/`、`tools/` 任何修改；禁止修改 V71/V72P0 已冻结代码、输出、docs；禁止修改已接受 OpenSpec 四工件；禁止修改既有 `results/`/`comparison_bench/outputs_comparison/`；禁止 `run_01`；禁止真实数据、2M、TEST、holdout。

---

## A. 精确文件清单 (Frozen — exhaustive, only additive allowed after independent ACCEPT)

### A1. 允许新增/修改的实现文件 — 恰好 1 个

| # | 精确路径 | 用途 | 约束 |
|---|---|---|---|
| 1 | `comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py` | 唯一 adapter 实现：承载 FrozenMotherSpec 9 / SoftJointConfig 8 / 11 arrays / 5-equation dataflow / float64 SPA + local_factor_extrinsic | 不得引入新依赖，复用 `numpy` 已有；`dtype float64` 固定；包含 `llr_clip`/`convergence_tol` 冻结常量；不得修改 `src/` 基线 |

- 禁止其他 `comparison_bench/src/` 新增；禁止在该文件外新增实现抽象。

### A2. 允许新增的 synthetic qualification CLI/runner — 恰好 1 个

| # | 精确路径 | 用途 | 约束 |
|---|---|---|---|
| 1 | `scripts/v72p1_soft_joint_synthetic.py` | 唯一 synthetic runner：执行 P1A/P1B/P1C/P1D synthetic 矩阵与解码冒烟，仅读 V72P0 mother CSR，不读 2M/TEST | 复用 V72P0 `generate_h_mother_sparse` 的 indptr/indices byte-identical 复用路径；SYNTHETIC_ONLY；`--registry v72p0_data_registry_synthetic.json` 复用；禁止真实数据分支 |

### A3. 允许新增的 test 文件 — 恰好 1 个

| # | 精确路径 | 用途 | 约束 |
|---|---|---|---|
| 1 | `test_v72p1_soft_joint_adapter_small.py` | 唯一测试文件：承载 T0/T1 全部语义 (T-DATAFLOW-1..5, T-CONFIG-1, T-MEMORY-1, plumbing/tiny/mother) | 位于 repo root（与 `test_v71_*`/`test_v72p0_*` 同级），`pytest -p no:cacheprovider` 可直接运行；不得隐式触发 production decoder；fake runner 显式注入仅在 synthetic 路径 |

- 总计允许文件数：**3 个**（1 实现 + 1 CLI + 1 测试）。超出此清单的任何新增均属越权，需另行补冻。

### A4. 禁止触及清单（重申，不可新增/修改）

- `src/**`, `experiments/**`, `tools/**`
- `scripts/v71_soft_joint_factor.py`, `scripts/v72p0_soft_joint_binary_synthetic.py`（V71/V72P0 冻结只读）
- `test_v71_soft_joint_factor_kernel_small.py`, `test_v72p0_soft_joint_binary_synthetic_small.py`（冻结只读）
- `openspec/changes/formal-ir-v72p1-soft-joint-binary-adapter/{proposal,design,tasks,specs/spec}.md`（已接受四工件只读）
- `docs/research_cycles/V72P1-ADP/{REVIEW_VERDICT.md,cycle_state.yaml,EXECUTION_PACKET.md}`（只读）
- `AGENT_PROJECT_MEMORY.md`, `docs/decision-log.md`
- 既有 `comparison_bench/outputs_comparison/**` 与 `results/**` 输出（禁止覆盖）
- 任何 `run_01`、`formal_ir_methods/*/run_01`、`2m`、`TEST`、`holdout` 采样

### A5. Additive Synthetic 输出目录及文件名 — 恰好 4 个文件于 1 个 additive 目录

**Additive 根目录**（仅 synthetic，不为 `run_01`）：

```
v72p1_synthetic_qual/
```

该目录为本轮 synthetic qualification 唯一允许输出根（additive，与既有 outputs_comparison/run_01 无冲突）。

| # | 精确路径 | 内容 | 禁止命名 |
|---|---|---|---|
| 1 | `v72p1_synthetic_qual/v72p1_manifest.json` | 合成运行 manifest：head/data_sha/FrozenMotherSpec/SoftJointConfig/11 arrays/prefix1111/checkpoint72/seed/mother byte-identical hash/wall/peak |  |
| 2 | `v72p1_synthetic_qual/v72p1_results.json` | 结构化结果：P1A plumbing / P1B tiny / P1C mother smoke / P1D loopy / 5-state first-match AND |  |
| 3 | `v72p1_synthetic_qual/v72p1_compact_report.md` | 精简可读报告（≤2页）：阈值、泄漏分解占位、`undetected` 隔离声明、复现指令 |  |
| 4 | `v72p1_synthetic_qual/v72p1_table.csv` | 表格摘要：case/wall/peak/finite/maxLLR/residual/classification |  |

- **明确不得命名**：`run_01`、`formal_run`、`real_*`、`holdout` 等；不得写入 `comparison_bench/outputs_comparison/` 下既有 `run_01` 目录。
- **失败证据不得另立文件**：失败快照统一写入同一个 `v72p1_results.json`（`status="BLOCKED"` + `failed_phase` 字段，见 §9）；**不存在 `partial_*` 等清单外输出授权**。输出清单保持恰好四个文件，无第五个。

---

## B. 缺失数值冻结 (Frozen — single value, no TBD/range/candidate)

### B1. `llr_clip` = `20.0` (float, `float64`)

| 项 | 值 |
|---|---|
| **冻结值** | `20.0` |
| **单位/类型** | LLR 限幅幅值，`float64`，以 `np.clip(llr, -20.0, 20.0)` 形式在 SPA 的 `variable_to_check`→`check_to_variable` 转换前及 `llr_out_from_excl` 后统一应用 |
| **数值来源（V72P1 新冻结的工程数值选择）** | `llr_clip=20.0` 是 **V72P1 新冻结的工程数值选择，不是复用值，也未被 V71/V72P0 验证过**。V72P0 仅验证了 check-side `prod` 截断至 `±0.999999`（对应 `2*atanh(0.999999) ≈ 14.51` LLR，精确值 `ln(1999999/1) ≈ 14.5087`）并在 `msg_c2v = 2*atanh(prod)` 时避免 `|prod|≥1` 的 `inf`，以及 tiny exhaustive posterior `1e-9` 精度。本值 `20.0` 的工程依据仅为 `tanh(10) ≈ 0.999999995` 仍严格 `<1`，且 `exp(±20) ≈ 2e-9..4.8e8` 落在 `float64` 安全区间，不触及 `exp` 下/上溢；V71 log-domain 侧 `1e-12` 归一化容差不构成对本值或本口径的验证 |
| **防止失效** | 防止 `tanh(llr/2)` 饱和至 `±1.0` 导致 `atanh` 非有限值、`check_to_variable` 出现 `inf/nan`、进而 `app_llr`/`syndrome_observed` 非有限 |
| **失败停止条件** | 若任一迭代后 `variable_to_check` / `check_to_variable` / `app_llr` / `factor_to_bit` 出现 `!finite`（`inf`/`nan`）或 `max|LLR| > llr_clip + 1e-12`，立即 `BLOCKED`，保留 evidence，不调参、不换 seed、不 rerun 包装 |

### B2. `convergence_tol` = `1e-6` (float, `float64`)

| 项 | 值 |
|---|---|
| **冻结值** | `1e-6` |
| **定义口径 (residual)** | `residual^{(t)} = max_{e} |check_to_variable^{(t)}[e] - check_to_variable^{(t-1)}[e]|` — 单次迭代后全部 `nnz=49620` 条 check→variable 消息的最大绝对变化量（`float64`，`nnz` 域上 `L∞` 范数） |
| **类型/单位** | LLR 空间绝对容差，无量纲；与 `max_total_iterations=720` 及 `warm_start=true` 联动：若 `residual < 1e-6` 则该 checkpoint 提前收敛进入下一 checkpoint（warm_start 携带 `check_to_variable`）；否则跑满 `max_iter_per_checkpoint=10` |
| **数值来源（V72P1 新冻结的工程数值选择）** | `convergence_tol=1e-6` 同样是 **V72P1 新冻结的工程数值选择，不是复用值，也未被 V71/V72P0 验证过**：V71 的 `1e-12`（归一化/自排除精确性）与 V72P0 tiny 的 `1e-9`（穷举对照 posterior 精度）是不同语义的容差，均未验证 SPA 迭代残差门限。`1e-6` 仅为严于常见 DE `1e-4` 的工程收敛选择，与 `llr_clip=20` 配合在 `float64` 下稳定判敛且不因浮点噪声假收敛 |
| **为何不做 grid search** | 按指令首选复用已验证稳定区间，不做 grid search/参数优化/seed hunting；`1e-6` 为单一冻结值，非范围/候选 |
| **失败停止条件** | 若 `convergence_tol` 未按上述 `L∞(c2v delta)` 口径实现（如误用 `app_llr` delta 或相对容差），或出现 `residual` 非有限，或阈值被代码侧篡改，立即 `BLOCKED` |

- 两数值均为 **V72P1 新冻结的工程数值选择**（见上），适合 `float64` SPA，防止 `tanh/atanh` 非有限值；`dtype="float64"` 已在 `SoftJointConfig` 冻结。
- **SPA clip 双层防护（强制）**：SPA 实现必须始终在 `atanh` 输入处执行 `clip(prod, -1+eps, 1-eps)`（`eps` 取 `1e-12` 量级），不得仅依赖 `llr_clip` 防止 `atanh` 非有限；`llr_clip` 与 prod clip 是两层独立防护，缺一即 `BLOCKED`。
- 不得留下 `TBD`/`placeholder`/`范围`/`多候选`；后续实现必须字面等于上述冻结值。

---

## 1. P1A Plumbing 精确命令、Seed、输入与 PASS 条件

**目标**：验证 pack/prefix/incremental/tag 确定性与 mother 复用，非性能评估。

| 项 | 冻结值 |
|---|---|
| **唯一确定性 seed** | `20260902`（本 addendum 全局唯一 seed，见 §5） |
| **输入** | `v72p0_data_registry_synthetic.json` 复用（`data_sha 84d62779`, `Q1024 N1024 Nbit10240 M9036`），`indptr/indices` 自 `scripts/v72p0_soft_joint_binary_synthetic.py:generate_h_mother_sparse` 确定性生成，见 §6 |
| **命令 (P1A)** | `python scripts/v72p1_soft_joint_synthetic.py --phase P1A --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json` |
| **烟雾前置** | `python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py scripts/v72p1_soft_joint_synthetic.py` |
| **PASS 条件** | (i) `pack`：`hard_bits → hard_symbols → hard_bits` 往返 `byte-identical`（`N=1024` 符号，`Nbit=10240` bits，`col_order sym*10+bit`）；(ii) `prefix`：`1111` 个 disclosure 前缀 `{160,168,…,9032,9036}` 与 `72` 个 checkpoint `{160,288,…,8992,9032,9036}` 计数精确；(iii) `incremental`：`syndrome_observed` 在 prefix 递增时单调扩展且与 `indptr/indices` 前缀切片一致；(iv) `tag`：精确复用 V72P0 口径 `hashlib.sha256(bits.tobytes()).digest()[:8]`，`tag` 与重建 `tag` 相等（`tag_bits=64`）；该 tag **仅用于 accepted synthetic tag 合同**，不新增通用 hash/verifier framework，**不改为 Toeplitz 或其他 tag**（避免改变已接受计划范围）；(v) `deterministic`：同 seed `20260902` 两次运行 `hard_bits`/`syndrome_observed` byte-identical；任一失败 → `BLOCKED` |

---

## 2. P1B Tiny Exhaustive

| 项 | 冻结值 |
|---|---|
| **k (checks)** | `{2,3}` |
| **n (bits)** | `{6,9}` （`total_bits = n = 6,9`） |
| **states** | `{64,512}` （`2^6=64`, `2^9=512` exhaustive，总计 `≤512`，禁止采样） |
| **trials** | `8` per `(k,n)` pair |
| **posterior tolerance** | `1e-9` （`max|BP_marginal - brute_exact_marginal| < 1e-9`，`float64` `L∞`） |
| **seed** | `20260902` 派生：`seed_p1b = 20260902 + k*100 + n*10 + trial`，确定性，无 hunter |
| **H 构造** | 复用 V72P0 `generate_h_small_tree(m=k, n=n, seed)` — 每变量度1 forest，保证 tree（acyclic），`is_tree(H)==true` 才纳入 PASS 统计；loopy 仅 descriptive，不授 PASS |
| **命令** | `python scripts/v72p1_soft_joint_synthetic.py --phase P1B --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json` |
| **PASS 条件** | 全部 `2*8=16` 试验中：`finite==true`、`maxLLR ≤ llr_clip`、`is_tree==true`、`observed_zero && observed_one`（P0A 7-item fail-closed 复刻）、`worst_marginal_delta < 1e-9`；`wall <1s`（见 §7 阈值联动，但 P1B 自身 wall 单独 `<1s`）；任一 trial `≥1e-9` 或非 tree 被计为 PASS → `BLOCKED` |

---

## 3. P1C Full Mother Synthetic

| 项 | 冻结值 |
|---|---|
| **Mother** | `9036×10240`，`nnz=49620`，`indptr 36,148 B + indices 198,480 B + data 49,620 B = CSR 284,248 B`，byte-identical 复用 V72P0（见 §6） |
| **Iterations** | `{1,3,10}` per checkpoint（`max_iter_per_checkpoint=10`，测试点 1/3/10 三档，与 `max_total_iterations=720` 一致） |
| **检查量** | `finite`（全部 `variable_to_check/check_to_variable/app_llr/factor_to_bit` 有限）、`maxLLR`（`max|app_llr| ≤ llr_clip`）、`residual`（`max|c2v^{(t)}-c2v^{(t-1)}| < 1e-6` 时判敛） |
| **Wall thresholds** | `iter=1 → <1s`，`iter=3 → <5s`，`iter=10 → ≤30s`（`wall` 为 `scripts/v72p1_soft_joint_synthetic.py` 内 `time.monotonic` 计时，`tracemalloc` peak `<2 GiB`） |
| **Seed/输入** | `seed 20260902`，synthetic prior `log_prior=log(1/1024)` + 确定性 `llr_10 = RNG(20260902).standard_normal(10)`（与 V72P0 `validate_local_factor` 同分布），不读真实 pairs |
| **命令** | `python scripts/v72p1_soft_joint_synthetic.py --phase P1C --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json` |
| **PASS 条件** | 三档迭代均 `finite==true` 且 `maxLLR` 截断有效且 `wall` 阈值内；逐迭代记录 `residual trajectory`（**有限即可，不要求单调**——loopy BP residual 不保证逐迭代单调下降，非单调不得判为实现错误）；`residual <1e-6` 仅表示该 checkpoint 提前收敛；跑满 `max_iter_per_checkpoint=10` 仍未低于阈值时记录 `converged=false`，**不得仅因 `converged=false` 判 `BLOCKED`，也不得因此伪造 PASS**；P1C 必须报告 `finite/maxLLR/residual/converged/iterations`；任一档 `!finite`/`>wall`/`maxLLR>clip` → `BLOCKED` |

---

## 4. P1D Small Loopy

| 项 | 冻结值 |
|---|---|
| **n** | `12` |
| **k** | `3`（checks） |
| **total_bits** | `12` （`n=12`, `2^12=4096` exhaustive，loopy 允许 `'descriptive'`，不授 tree-PASS） |
| **H 构造** | 在 P1B forest 基础上对 `n=12,k=3` 注入 1 条额外边形成单环（deterministic seed 派生），保持 `indptr/indices` 仍为 CSR 合法但 `is_tree==false` |
| **Exact comparison** | `BP_marginal (max_iter=10, llr_clip=20)` vs `brute_exact_llr (2^12 exhaustive)` 的 per-bit marginal LLR `L∞`，容差 `1e-9` 仅作记录（loopy descriptive），不作为 PASS 门限 |
| **Tolerance** | 记录 `worst_marginal_delta`（float64），不在 loopy 上判 `BLOCKED`（仅 P1B tree 上 `1e-9` 为硬门限） |
| **Seed/命令** | `seed 20260902`；`python scripts/v72p1_soft_joint_synthetic.py --phase P1D --seed 20260902 --registry v72p0_data_registry_synthetic.json --out v72p1_synthetic_qual/v72p1_results.json` |
| **测试命令（R5）** | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_small_loopy"` — 验证：`n=12, k=3`、`2^12=4096` exhaustive 完成、`is_tree==false`、`finite==true`、`wall≤5s`、`worst_delta` 仅写入 descriptive 字段（loopy `1e-9` **不是**硬 PASS 门禁） |
| **PASS 条件** | `finite==true`、`wall ≤5s`、exhaustive 完成；`worst_delta` 写入 `v72p1_results.json` descriptive 字段，不触发 `BLOCKED`（loopy 不授 PASS 为设计意图） |

---

## 5. Deterministic Seed 唯一值

- **全局唯一 seed**: `20260902`（`YYYYMMDD`，与 `packet freeze 2026-09-02` 一致，单一值，无候选）。
- 派生：`P1B trial seed = 20260902 + k*100 + n*10 + trial`；`P1C/P1D` 直接使用 `20260902`；不得更换 seed 重试（见 §9 失败规则）。
- 复现：`np.random.default_rng(seed)`；`hashlib.sha256(f"V72P1-ADP-{seed}-{phase}-{k}-{n}-{trial}".encode()).digest()` 仅用于 H 行随机 `k_info` 选择（与 V72P0 同机制），确定性可重放。

---

## 6. V72P0 Mother 读取/复用与 byte-identical 检查

- **读取方式**：不重新构造新 mother。`scripts/v72p1_soft_joint_synthetic.py` 在首行 `from scripts.v72p0_soft_joint_binary_synthetic import generate_h_mother_sparse` 或等价 `import importlib.util` 动态加载 `generate_h_mother_sparse()`，调用一次获取 `stats["indptr"]` / `stats["indices"]` / `stats["nnz"]` / `stats["pivot_checks"]`。不得复制粘贴后改随机逻辑。
- **复用约束**：`M=9036`, `Nbit=10240`, `nnz=49620`, `CSR total 284,248 B` 必须与 V72P0 执行结果 byte-identical（`scripts/v72p0_soft_joint_binary_synthetic.py:generate_h_mother_sparse` 行为冻结）。
- **byte-identical 口径（R6 修正）**：byte-identical 必须对 `np.asarray(indptr, dtype=np.int32).tobytes()` 与 `np.asarray(indices, dtype=np.int32).tobytes()` **直接字节比较**；Python `list[int]` 相等只能证明元素相等，**不得称为 byte-identical**。`sha256(indptr_bytes + indices_bytes)` 仅作为 manifest 摘要记录；**直接 byte equality 才是 T0-8 的 PASS 证据**。不得重新实现或改变 V72P0 mother generator。
- **Byte-identical 检查（T0 阶段执行）**：
  ```python
  # 在 test_v72p1_soft_joint_adapter_small.py::test_mother_byte_identical
  import hashlib, importlib.util, pathlib
  spec0 = importlib.util.spec_from_file_location("v72p0", "scripts/v72p0_soft_joint_binary_synthetic.py")
  mod0 = importlib.util.module_from_spec(spec0); spec0.loader.exec_module(mod0)
  spec1 = importlib.util.spec_from_file_location("v72p1", "comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py")
  # v72p1 需暴露 get_mother_csr() -> (indptr, indices) 或直接复用 mod0.generate_h_mother_sparse()
  s0 = mod0.generate_h_mother_sparse(); s1_indptr, s1_indices = ... # v72p1 侧读取
  import numpy as np
  s0_ip = np.asarray(s0["indptr"], dtype=np.int32).tobytes(); s1_ip = np.asarray(s1_indptr, dtype=np.int32).tobytes()
  s0_ix = np.asarray(s0["indices"], dtype=np.int32).tobytes(); s1_ix = np.asarray(s1_indices, dtype=np.int32).tobytes()
  assert s0_ip == s1_ip and s0_ix == s1_ix  # byte-identical: direct bytes equality (list 相等不构成 byte-identical 证据)
  assert s0["nnz"] == 49620 and len(s0["indptr"])==9037
  assert all(s0["pivot_checks"][r] for r in [160,168,176,9036])
  ```
  任一项不等 → `BLOCKED`。`indptr`/`indices` 的 `int32` CSR 形式亦可在 `v72p1_synthetic_qual/v72p1_manifest.json` 中记录 `sha256(indptr_bytes + indices_bytes)` 供独立 review 比对。

---

## 7. T0/T1 每条实际 pytest/py_compile 命令

### T0 — 编译/导入/字段/shape/计数/内存

| # | 命令 | 预期 PASS | 失败 → |
|---|---|---|---|
| T0-1 | `python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py scripts/v72p1_soft_joint_synthetic.py` | exit 0, no SyntaxError | BLOCKED — syntax |
| T0-2 | `python -c "import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as m; import scripts.v72p1_soft_joint_synthetic as s; print(m.__name__, s.__name__)"` | import ok, `__name__` 打印 | BLOCKED |
| T0-3 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_frozen_mother_spec"` | `FrozenMotherSpec` 恰好 9 字段，`tag_bits` absent | BLOCKED — config 违背 |
| T0-4 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_soft_joint_config"` | `SoftJointConfig` 恰好 8 字段，`tag_bits==64`, `warm_start==true`, `dtype=="float64"`, `llr_clip==20.0`, `convergence_tol==1e-6` | BLOCKED |
| T0-5 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_eleven_arrays"` | 11 arrays shape/dtype 精确等于 §4.5 表 | BLOCKED |
| T0-6 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_memory_recompute"` | `11 arrays 9466840`, `CSR 284248`, `grand 9751088` byte-identical | BLOCKED |
| T0-7 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_mother_dims"` | `9036x10240 nnz 49620 used_2m false` | BLOCKED |
| T0-8 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_mother_byte_identical"` | `indptr/indices` byte-identical to V72P0 §6 | BLOCKED |

### T1 — 语义 (T-DATAFLOW-1..5, T-CONFIG-1, T-MEMORY-1 已在 T0 覆盖，T1 侧重 dataflow)

| # | 命令 | 语义 | 预期 PASS | 失败 → |
|---|---|---|---|---|
| T1-1 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_DATAFLOW_1"` | `factor_to_bit` 非零、`check_to_variable==0` 时 `variable_to_check[e]==factor_to_bit[v]` | assert PASS | BLOCKED — §4.3 eq3 违背 |
| T1-2 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_DATAFLOW_2"` | 同条件 `app_llr[v]==factor_to_bit[v]` 且 `app_llr` 不直接等于 `prior` | assert PASS，覆盖 “prior only once” | BLOCKED |
| T1-3 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_DATAFLOW_3"` | 翻转单 `syndrome_target[c]`，`check_to_variable` 符号/coset 变化（`syndrome_aware_spa`） | sign change observed | BLOCKED |
| T1-4 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_DATAFLOW_4"` | 仅改 `prior_logp`，`variable_to_check`/`app_llr` 仅经 `factor_to_bit` 路径变化，无 `prior plus sum(c2v)` 直连 | dependency probe PASS | BLOCKED — extra prior injection |
| T1-5 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_DATAFLOW_5"` | `factor_to_bit[sym,target_b]` 不受同位 `bit_to_factor[sym,target_b]` 影响，但受 `other_bits_excluding_b` 影响 | self-exclusion PASS | BLOCKED |
| T1-6 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_plumbing"` | P1A plumbing (seed 20260902) 确定性/前缀/tag 参见 §1 | PASS | BLOCKED |
| T1-7 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_tiny"` | P1B tiny `k=2,3 n=6,9 1e-9` §2 | PASS + wall<1s | BLOCKED |
| T1-8 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_mother_smoke"` | P1C `9036x10240 1/3/10` §3 | PASS + wall <1/<5/≤30s | BLOCKED |
| T1-9 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_v2c_self_exclusion"` | **v2c self-exclusion（真语义，非全零冒充）**：构造目标变量连接**至少两个 checks**，验证发往 check c 的 `variable_to_check` 消息**排除**来自 c 的 c2v、**包含**其他 check 的 c2v。不得用 T-DATAFLOW-1 的全零 c2v 情形冒充本测试 | PASS | BLOCKED — §4.3 eq3 违背 |
| T1-10 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_warm_start_carry"` | **warm-start**：checkpoint i+1 的初始 `check_to_variable`/`variable_to_check` 等于 checkpoint i 的终态，不重新清零（`warm_start=true` 语义） | PASS | BLOCKED |
| T1-11 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_iteration_cap"` | **iteration cap**：每 checkpoint ≤`max_iter_per_checkpoint=10`，总计 ≤`max_total_iterations=720`（checkpoint 数 72 × 10 = 720 一致性） | PASS | BLOCKED |
| T1-12 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_convergence_linf"` | **convergence 口径**：residual 严格定义为全 `nnz=49620` 条 c2v 消息的 `L∞` delta（`max|c2v^{(t)}-c2v^{(t-1)}|`）；`<1e-6` 才允许提前停止该 checkpoint | PASS | BLOCKED |
| T1-13 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "test_clip_finite_all_messages"` | **clipping/finite**：`factor_to_bit`、`variable_to_check`、`check_to_variable`、`app_llr` 全部 finite，clip 规则一致（`llr_clip=20.0` + `atanh` 输入 prod clip 双层防护，见 §B） | PASS | BLOCKED |
| T1-14 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_CONFIG_1"` | **T-CONFIG-1 落地**：FrozenMotherSpec 恰 9 字段 / SoftJointConfig 恰 8 字段 field sets exact，无交叉/重复，`tag_bits` 仅在 SoftJointConfig | PASS | BLOCKED |
| T1-15 | `pytest -p no:cacheprovider test_v72p1_soft_joint_adapter_small.py -k "T_MEMORY_1"` | **T-MEMORY-1 落地**：11 arrays `9466840` / CSR `284248` / grand `9751088` 按 dtype/shape 精确机械复算 | PASS | BLOCKED |

- 全部 synthetic-only，无真实数据，无 `run_01`。
- 测试根目录用 `pytest -p no:cacheprovider`（Windows ACL 规避）；不得隐式触发 production decoder。

---

## 8. Additive Synthetic 输出文件（明确不得命名 run_01）

- **目录**：`v72p1_synthetic_qual/`（additive，与 `comparison_bench/outputs_comparison/*/run_01` 隔离）。
- **文件**（§A5 已列）：
  1. `v72p1_synthetic_qual/v72p1_manifest.json` — 包含 `schema v72p1_manifest_v1`, `head` (implementation SHA, acceptance 后填), `data_sha 84d62779`, `FrozenMotherSpec 9`, `SoftJointConfig 8 (llr_clip 20.0, convergence_tol 1e-6)`, `11 arrays`, `CSR 284248`, `prefix1111 checkpoint72`, `seed 20260902`, `mother indptr/indices sha256`, `used_2m false`, `no_run_01 true`。
  2. `v72p1_synthetic_qual/v72p1_results.json` — 包含 `P1A/P1B/P1C/P1D` 结构化结果、`finite/maxLLR/residual/wall/peak`、`worst_marginal_delta`、`five_state` 分类。
  3. `v72p1_synthetic_qual/v72p1_compact_report.md` — 精简报告：阈值、five-equation 回显、`undetected` 隔离声明、复现命令（含 seed 与 T0/T1 命令）。
  4. `v72p1_synthetic_qual/v72p1_table.csv` — 表格：`case, k, n, trials, worst_delta, wall_s, peak_MiB, finite, maxLLR, residual, classification`。
- **禁止**：任何文件或目录命名 `run_01`、`formal_run`、`real_data`、`holdout`；禁止写入 `results/` 或既有 `run_01` 目录。

---

## 9. 失败规则

- **任一测试/数值/时间门禁 FAIL 立即停止**：T0/T1 任一 `pytest` 非 0、`py_compile` 非 0、`finite==false`、`maxLLR>20`、`residual` 非有限、`wall` 超阈（P1B>1s / P1C 1>1s/3>5s/10>30s / P1D>5s）、`indptr/indices` 非 byte-identical、`prefix1111`/`checkpoint72` 计数不符、`tag` 不 exact → 立即 `BLOCKED`，进入 `revise-required` / rework。
- **保留失败证据**：失败快照统一写入 `v72p1_synthetic_qual/v72p1_results.json`（`status="BLOCKED"`、`failed_phase=<P1A|P1B|P1C|P1D|T0|T1>`，含 `seed 20260902`, `head`, `wall`, `peak`, `worst_delta`, `finite`），不删除、不覆盖既有 additive 输出；**不得创建 `partial_*` 等清单外文件**（输出清单恰好四个文件，见 §A5）。
- **不调参、不换 seed、不 rerun 包装成功**：禁止修改 `llr_clip 20.0` / `convergence_tol 1e-6` / `seed 20260902` / 阈值以包装 PASS；禁止换 seed 重试；禁止 `rerun` 包装成功。修复需新 SHA 并重走独立 review。
- **日志**：失败时 `scripts/v72p1_soft_joint_synthetic.py` 以非 0 退出并在 stdout 打印 `BLOCKED: <reason> seed=20260902 phase=<P1A/B/C/D>`。

---

## 10. 后续 Implementation Operator 精确 COMPLETE/BLOCKED 返回格式

### COMPLETE（全部冻结项完成）

```
COMPLETE
ADDENDUM_ACCEPTED_SHA: <由本轮 addendum acceptance record 填入>
REQUIRED_IMPLEMENTATION_BASE_SHA: <由本轮 addendum acceptance record 填入>
ACCEPTED_PLAN_SHA: 73efd91f379b5abdeda675c36d1a054f59ff89ff
HEAD_SHA: <implementation commit SHA>
ORIGIN_SHA: <origin/formal-ir-mainline SHA>  # must == HEAD_SHA
CHANGED_FILES:
- comparison_bench/src/comparison_bench/formal_ir/v72p1_soft_joint_adapter.py (new)
- scripts/v72p1_soft_joint_synthetic.py (new)
- test_v72p1_soft_joint_adapter_small.py (new)
DATA_INCLUDED:
- v72p1_synthetic_qual/v72p1_manifest.json
- v72p1_synthetic_qual/v72p1_results.json
- v72p1_synthetic_qual/v72p1_compact_report.md
- v72p1_synthetic_qual/v72p1_table.csv
LLR_CLIP: 20.0
CONVERGENCE_TOL: 1e-6
CONVERGENCE_RESIDUAL_DEF: max|c2v^{(t)} - c2v^{(t-1)}| (L_inf over nnz=49620)
MOTHER_REUSE: byte-identical to V72P0 9036x10240 nnz49620 (direct int32 tobytes equality is the PASS evidence; sha256 recorded in manifest as summary only)
SEED: 20260902
IMPLEMENTATION_STARTED: true
TESTS_RUN: true  # T0/T1 all PASS per §7, walls < thresholds
DECODER_EXECUTED: true  # synthetic only (P1A/P1B/P1C/P1D), no real decoder
RUN_01_CREATED: false
NEXT_GATE: INDEPENDENT_IMPLEMENTATION_REVIEW (pre-EXECUTE / pre-RESULT still required before any formal run)
```

### BLOCKED（任一冻结项阻塞）

```
BLOCKED
REASON: <one-line, e.g. T_DATAFLOW_3 syndrome flip no sign change | P1B wall 1.2s >1s | mother indptr mismatch | llr_clip !=20.0>
FAILING_COMMAND: <exact command from §7 or §1-4 that failed>
TRACEBACK: <exact error / assertion diff, 20 lines>
ATTEMPTED_REMEDIES: <what was tried, must not include tuning llr_clip/convergence_tol/seed/threshold>
BLOCKED_FILES:
- <file that would have been changed but is now BLOCKED>
SEED: 20260902
DECODER_EXECUTED: false
RUN_01_CREATED: false
NEXT_ACTION: main-thread decision (revise-required, new SHA, re-review)
```

---

## 11. 生命周期与授权重申

- **当前 addendum 状态**：`PACKET_ADDENDUM_CANDIDATE_REVISED / IMPLEMENTATION_NOT_STARTED / EXECUTE_NOT_AUTHORIZED`
- 本 addendum 修订版（R1–R9）经独立 re-review `ACCEPT` 后，还必须**依次完成以下授权记录，缺一不得开始实现**：
  1. 独立 addendum re-review `ACCEPT`；
  2. 单独记录 `ADDENDUM_ACCEPTED`（含 `ADDENDUM_ACCEPTED_SHA` 与 `REQUIRED_IMPLEMENTATION_BASE_SHA`，供 future operator COMPLETE 返回填入）；
  3. `cycle_state.yaml` 设置 `development_execution_authorized: true`（**仅限 synthetic qualification**）；
  4. `formal_execution_authorized` 保持 `false`。
- 上述记录完成前，允许的动作仅为 0（无）；**不得实现代码、不得运行测试**。
- 授权后的允许范围仅为 `IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION_ONLY`（即 §A 清单的 3 文件实现 + §7 T0/T1 + §1-4 synthetic smoke，全部 SYNTHETIC_ONLY）。
- **不授权**：真实数据（2M/TEST/holdout）、`formal decoder execution`、任何 `run_01`/`formal run`、网格搜索/调参/换 seed、覆盖既有输出、启动 V72。
- 任何 formal `run_01` 仍需独立用户 `EXECUTE_AUTH` + `pre-EXECUTE` / `pre-RESULT` 双重 review（`HEAD == origin == implementation SHA`, `ACCEPTED_PLAN_SHA` 重推导一致且 `rg <stale-SHA>` 0 hits, `run_01` 不存在, `py_compile`+T0 PASS）。

---

## 12. 权威合同校验行

`max_total_iterations 720 warm_start true dtype float64 prior_logp[N,Q] local_factor_extrinsic other_bits_excluding_b syndrome_aware_spa syndrome_target factor_to_bit[v] checkpoint_rows FrozenMotherSpec SoftJointConfig 11 arrays 5 equations prefix1111 checkpoint72 9036x10240 nnz49620 llr_clip 20.0 convergence_tol 1e-6 residual max_c2v_delta seed 20260902` — 用于 `rg` 一致性校验；实现侧 `rg "llr_clip|convergence_tol|local_factor_extrinsic|other_bits_excluding_b|syndrome_aware_spa"` 必须命中且值精确等于冻结值。

---

*Addendum revise time: 2026-09-02, operator V72P1-ADP packet addendum revision R1–R9 after independent review REVISE verdict. This revision only amends this file; no code, no tests, no decoder, no run_01 in this commit. Next gate: INDEPENDENT_ADDENDUM_REREVIEW.*
