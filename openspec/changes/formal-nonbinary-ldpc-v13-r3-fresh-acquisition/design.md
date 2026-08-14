# Design: formal-nonbinary-ldpc-v13-r3-fresh-acquisition

## 0. Status

PLANNING（2026-08-15）。独立 freeze review ACCEPT 前禁止任何 prepare /
execute / verify 执行。本 design 全部条款在冻结后不可修改（除非经
amendment 流程 + 主线程授权）。

## 1. 数据源与 acquisition 设置（frozen）

- **数据源声明协议**：fresh 数据必须由用户/采集方提供，满足：
  - 10 dB Type-II、q=1024、Gray 256-symbol 配对帧格式（与 V13 历史数据
    相同的字段契约：`load_pairs_table` / `build_frame_batch` 可读）；
  - 采集时间戳晚于 V13 历史数据（2026-08-14 之前的历史身份一律排除）；
  - 来源路径/文件清单/时间戳在 prepare 时冻结记录（provenance）。
- **Window / stratum 设置**：
  - 主 stratum：**bw200**（与 V13 E01/A01 一致）；
  - 次 stratum：bw120、bw180（与 V13 A02 一致，仅作 cross-stratum 观察，
    不参与主判定）。
- **当前状态（2026-08-15 检查）**：`D:\Data` 下无 fresh 帧数据源
  （最新为 2026-07-28 JSI 测量，非帧配对数据）→ prepare 预计产出
  **zero eligible frames**（合法冻结结果，见 §5 停止规则；不构成失败
  重试，用户提供新数据后可重新 prepare——prepare 本身是确定性工具）。

## 2. 新 frame/payload identities（frozen）

- **身份命名空间**：`v13r3fresh-<stratum>-<uuid>`（uuid 由冻结种子
  确定性派生，seed 在 prepare plan 中冻结）。
- **排除验证（必须全过）**：新身份不得出现在以下任一历史锁中：
  - V4 10 dB/16 dB transfer locks（frame + payload identities）；
  - V5 development/partition role locks；
  - V13 characterization/development/retrospective_audit 角色台账；
  - V12 prepare 台账（2848 excluded frame + 2688 excluded payload）。
  复用 V12 `nonbinary_v12_real_partition.py` 的身份台账/排除机制
  （reuse before rebuilding；新数据源检查为新增薄层）。
- **角色隔离（frozen）**：characterization / canary / confirmation 三
  角色互斥（每行恰好一个角色），角色分配在 prepare 时预注册并冻结；
  任何歧义 → 按停止规则冻结（`blocked_role_ledger` 语义）。

## 3. 解码器不变式（frozen）

- 码本：`nbldpc_v13_r3_code_v1`（连通简单 check 图，170 checks、
  256 全 degree-2 变量、168x3+2x4、rank 170、seed 20260818）——
  **字节不变**（从 V13 源码原样导入，禁改）。
- 先验：QSC p=.20（**不变**）。
- 解码器接口：flooding FFT-QSPA 镜像循环（V13 D03 已验证）——
  **不变**。
- max_iter=100（**不变**）。
- 禁止：任何对候选/先验/迭代/接口的"fresh 数据适配"。

## 4. 执行规模（在 prepare 台账基础上预注册并冻结）

- 主判定基于 **canary 64 帧 + confirmation 128 帧**（若 eligible 帧
  充足；规模不足时按 §5 的 eligible 帧规则处理，**不**自适应放大）。
- 每帧一次解码，失败原样保留（`decode_failed` / 其他状态均计入分母）。

## 5. 停止规则（frozen）

1. **无 eligible frame**：prepare 产出 0 eligible 行 →
   `frozen failure`（`no_eligible_frames`），保留 prepare 包；
   不重跑、不扩大搜索、不替换数据。
2. **分布漂移**：fresh characterization（若 fresh 数据含 characterization
   角色）的 raw SER / bit-plane mismatch / conditional entropy 相对
   历史参考区间漂移超阈值（SER 均值偏差 > 0.03、或 entropy 偏差 >
   0.3 bits/symbol）→ `frozen failure`（`drift_exceeded`），失败原样
   保留。
3. **任一执行失败**（decode_failed、decoder_error、verifier 失败、
   账目/身份违规、非法执行）→ 对应包 `frozen failure` 并保留原样；
   禁止替换帧、调参、重跑。
4. **角色/身份歧义** → `blocked_role_ledger`（V12 语义），冻结。

## 6. 流程与判定（frozen）

```
冻结（本 design + tasks 全部条款）
  → prepare（确定性工具：数据源检查 + 身份台账 + 排除验证 + 角色分配，
     产出 frozen plan + ledger；zero-eligible 时产出 no_eligible_frames 包）
  → 主线程独立 review（对 plan/ledger/规模/停止规则逐项复核）
  → 单次 fresh execute（只跑一次；plan 冻结后禁止任何修改）
  → 一次只读 verify（verifier 不改任何字节）
  → 判定：
      全绿（canary+confirmation 全部 exact_correct，零 forbidden）
        → fresh-confirmed（最高状态；仍非 promotion/qualification）
      任一失败 → frozen failure（保留全部失败证据）
```

## 7. Claim boundary（frozen）

- 最高状态：**`fresh-confirmed`** —— 仅证明"R3 在 fresh 数据上仍能
  精确纠错"；不是 promotion、qualification、效率改进或任何比较结论。
- 效率：f≈12 不变；效率路线归 P2/V17 门。
- 所有产物 additive 于
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_*/`
  （或 change 的 evidence/）；冻结 `src/`/`experiments/`/`tools/`/
  `results/` 与官方 `formal_ir_methods` 根零改动。
