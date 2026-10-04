# G-M2-HDCASCADE-SYNTH — BATCH-END REVIEW (independent, EXPLORE)

- 日期: 2026-09-27 · 角色: 独立批末审查员（只读）· Track: `EXPLORE`（合成，6 臂）
- 审查时 HEAD: `ce85d61f`（执行时 HEAD `8e9c8526`；冻结目录两侧均 EMPTY，无冻结逻辑漂移）
- 本文件由主线程依独立审查员返回的结论归档；审查员本人未写任何文件、未运行任何译码器或臂 runner（含 `--dry`）、未开任何 `.ttbin`、未用 git 写操作、未触碰 `results/` 与 `comparison_bench/outputs_comparison/`。
- 关闭对象: `EXPLORATION_LOG.md` 末行「batch-end review：未做 … E8 待判」。

**裁决: FAIL。** 证据提升被阻断。操作员本身的边界行为是干净的（越界/未授权执行未发生），但**该批全部头条数字是 harness 人工制品**，不得作为方法测量引用。

## 1. PACKET §8 验收项 E1–E8

| 项 | 判定 | 依据 |
|---|---|---|
| E1 范围白名单 | PASS | `git status --porcelain -- src experiments tools` 空；`results/`、`comparison_bench/outputs_comparison/` 空；6 根 uuid8 与冻结值逐一相符，每根恰 3 文件 |
| E2 focused fake 测试 | PASS（依记录） | log 记 10 passed（`test_m2hdc_arm_runner_fake.py`）+ 5 passed（`test_m2_hd_cascade_fake.py`）；只读约束下未复跑 |
| E3 六臂/顺序/`nb_decode_calls` | PASS（含删失） | 恰 A1→A6，冻结网格，`--blocks 240` 启动宽度，无追加；6 根 `rows.json` 均 `nb_decode_calls=0`。`blocks_done=13`（非 240）是 bar-12 规则正常触发（`failures > bar` → 停），与姊妹批「CENSORED 是预期门行为、永不外推」先例同类，**不是范围偏离** |
| E4 种子逐字 | PASS | CSV 种子确认 `ARM_SEED[arm]+k`，k=0..12（A1 `2026095701..5713` … A6 `2026095706..5718`）。`hd_cascade.py:122` 的 `HdCascadeParams.seed` PLACEHOLDER 默认值被逐块覆盖（`m2hdc_arm_runner.py:716–728`），从未生效 |
| E5 预算 | PASS | 各臂 wall 0.1–0.2 s（帽 5400），RSS 0.152–0.153 GiB（<4 GiB），单次解码 ≪300 s；0 INCOMPLETE，无重跑/续跑 |
| E6 会计列 | PASS（见 N1） | CSV 具备全部机器列；RESULT md 具备 f 双线、λ 分解、两种消息口径、N_req、d/q/n_IR 分离列、`undetected` 单列 |
| E7 log 链 | PASS | entry 0（含 Q5/Q6 两项 BLOCKED）→ entry 1（复验 + 逐臂表 + 收口 tally + `repair 未用`）追加且完整，唯一未做者正是它正确地拒绝自审的本次审查 |
| E8 claim ceiling + 审查 | **FAIL** | 固定句在 6 份 RESULT md 与 log 中逐字齐备，未发现任何越级提升；但本审查在**科学有效性**上 FAIL 该批证据：各臂头条数字是 harness 人工制品（见 B1） |

## 2. BLOCKING

### B1 — 生产验证门被短路：100% `undetected` 是结构性的，不是实测的。阻断本批全部数字的提升。

- **事实**: `_run_planes_production` 无条件返回 `"accepted": True, "toeplitz_verified": False`（`comparison_bench/src/comparison_bench/methods/hd_cascade.py:224–229`）。统一门 `:280–281`（`success = exact and verified and accepted`; `und = accepted and not success`）因此对**每个**生产块给出 `success=False`、`und=True`，与译码质量无关——即使块被完全纠正（`exact_match=True`）也记为 `undetected`。授权路径正是经唯一生产调用点进入该函数（`m2hdc_arm_runner.py:906–927`，默认于 `:819–820`）。旁证：6 份 CSV 均 `exact_match=False ×13, accepted=True ×13, undetected=True ×13, block_fail=13`；`accepted (=successes+failed_verify, hd_cascade.py:359)` = 13 而 successes = 0。二阶缺陷：无条件 `accepted=True` 把「无验证器」状态转成 13 次**误接受**事件而非 13 次译码失败，是该状态最具误导性的呈现方式。
- **为何要紧**: FER=1.0、`f_eff≈6.06–6.09`、`undetected`=13/13、λ/messages 列**不含任何关于 HDC 校正质量的信息**。把它们当作方法测量（合成或其他）引用会得出错误科学结论；它们测的是一个 stub 门。
- **阻断范围**: E8；任何提升、排名、运行点选择、效率/泄漏/SKR 使用；任何把 `undetected`=13/13 当作误接受率的引用；任何进入 D1 条件化真实论证或（独立地）已暂停的 M2 D2 分支的输入。
- **最小下一步（只陈述，不设计）**: 一个**新冻结包**，二选一——(a) 接上真实 Toeplitz 验证（或对「探针无验证器」显式重定义 accept 语义并给出诚实状态名）后从新根重跑；或 (b) 对该 `assumed-v1` 基线作**诚实退役**。本包下不得再开臂。

### B2 — 授权到证据的缺口本身干净，但见证仅存于 log（仅在主线程须确认的意义上阻断）

entry 0 的 Q5/Q6 BLOCKED → entry 1 在 2026-09-25 逐字授权落字（PACKET §7-8）后复验 PASS，顺序诚实，且 entry 0 明确记录 EXECUTE 未进入，故**没有科学执行先于输入冻结**。离线审查员无法独立核验对话层见证；主线程对 entry 1 见证主张的接受是唯一剩余的授权事实。此项不改变 FAIL 判定（B1 独立阻断）。

## 3. NON-BLOCKING

- **N1** — `rows.json` 摘要缺 claim ceiling 句（存在 arm…verdict/gates/f/lambda/messages/N_req；缺 `claim_ceiling`/`notes`/`claim_column`；6 份 `rows.json` grep 固定句 = 0 命中）。6 份同目录 RESULT md 逐字携带，故未发生 ceiling 违规。建议后续 runner 把 ceiling 串镜像进机器摘要。
- **N2** — wall 文字不符：log entry 1 写各臂「~3 s」，RESULT md 记录 0.1–0.2 s。两者均 ≪ 5400 s 帽，预算 PASS 不变；归档时改正文字。
- **N3** — 执行后 HEAD 漂移：执行 `8e9c8526`（log Q0，两次复验）vs 审查时 `ce85d61f`；冻结目录两侧均 EMPTY。信息项；后续批末审查应在执行 HEAD 旁同时盖审查时 HEAD。
- **N4** — G-B 边界正确适用：A4 `f_super=1.30000774` > 1.3 → G-B FAIL，差 7.7e-06。按冻结规则算术正确（已重算），且说明名义式对刀刃敏感。无动作；门仅报告用。
- **N5** — 引用卫生：今后引用本批必须同时指名姊妹批 M2-LB 的「retained-assumed, no promotion」先例与 M2 裁决的 `assumed-v1` 限（发现 5），以免读者误当方法测量。

## 4. `undetected` = 13/13 的机制假设（排序）

- **H1（代码已证，解释 100% 速率）: 验证侧 stub。** `hd_cascade.py:224–229` 硬编码 `accepted=True, toeplitz_verified=False`；`:280–281` 随后对每个生产块强制 `und=True`。13/13 误接受率是**零译码信号内容的人工制品**。强度：演绎自代码，且与 6 臂 CSV 完全一致。
- **H2（叠加的呈现缺陷）: `accepted` 语义。** 无条件 True 的接受标志正是把「不可验证」变成「误接受」的东西。若 `accepted` 反映真实判定（或不可验证时为 False），同样的运行会读作 `failed_decode=13 / undetected=0`。这是该人工制品「最具误导性」而非仅「无信息」的原因。
- **H3（被遮蔽、不可评估）: `assumed-v1` 参数是否足够。** 统一 `[8,4]` × 10 面、`max_passes` 4、1 次 cross-sweep、provisional 消息规则（`hd_cascade.py:206–207,222–223`；`m2hdc_arm_runner.py:300–314`，均诚实标 `assumed`）对合成信道（2% 符号翻转均匀替换，`m2hdc_arm_runner.py:411–414`）可能够也可能不够；`exact_match`=0/13 与「参数太弱」和「调度/信道失配」都相容。H1 完全遮蔽该读数——**两个方向都不支持任何参数结论**。
- **H4（最弱，非速率解释项）: 标签/约定细节**（Gray 面序、种子推进）。已作为速率原因排除：逐块种子逐字为 `ARM_SEED+k`（单块路径 `frame_idx=0`，故 wrapper 的 `+frame_idx*104729` 在此为 no-op）。只影响可复现性注记，不影响 100% 速率。
- **可引用的定性判断**: 本批只能作为 **(a) 边界干净的 EXPLORE 执行记录** 与 **(b) 证明生产门按现实现无法成功的 harness 缺陷展品** 被引用——绝不可作为 HDC 的任何测量。

## 5. 可说 / 不可说（逐字）

**可以说**:

1. 六个冻结臂按序以冻结种子/流/信道包/预算运行；每臂由 bar-12 规则在 13/240 处删失，fails=blocks=13，stop 时 FER=1.0，undetected=13，`nb_decode_calls`=0，预算成立，无 repair/续跑，无保护根写入，无 INCOMPLETE。
2. 在 assumed-H 基上按包内名义式的名义算术（已重算，吻合 ≤5e-09）：A1 `f_super` 1.27885826 / `f_eff` 6.06453326 / `N_req` 680；A2 1.30324069 / 6.08891569 / inf；A3 1.27634973 / 6.06202473 / 608；A4 1.30000774 / 6.08568274 / inf；A5 1.27148786 / 6.05716286 / 504；A6 1.29494705 / 6.08062205 / 2842 — 其中 H 列标 `assumed`，`f_eff` 不得作为可认证值引用。
3. 所实现的生产路径无法返回成功（验证恒 False），故全部 13×6 `undetected` 事件是构造性的。
4. 固定句在 6/6 RESULT md 与 log 中逐字齐备；任何地方都无投影/外推 FER（只有「projected NEVER」的曲线标签）。

**不可说**:

1. 关于 HDC 的任何真实 FER/效率/泄漏/SKR；任何 HDC-vs-LDPC/NB 排名；任何「HD-Cascade（即使在合成上）失败」的方法证伪主张。
2. 把 `undetected`=13/13 当作该方法实测的误接受率。
3. 在 FER>0 时把 `f_super` 当效率引用；池化/跨臂速率；任何从 13 外推到 240 块；任何把这些数用于 D1 条件化真实推理或已暂停的 M2 D2 分支。

**逐臂重算**: 6 臂 blocks=13 / fails=13 / undetected=13 / FER=1.0 / `fails==blocks` 均由 CSV 确认；`f_super` 由 `(5m+64)/(1024·H)` 重算，6 臂吻合 ≤5e-09；G-A 全 FAIL（13>12），G-B 依 1.3 规则为 PASS/FAIL/PASS/FAIL/PASS/PASS，G-C 全 FAIL-expected（13 ≪ `N_req`）——log 表与 md 完全一致。`repair 未用` 已确认：log entry 1 + 6 份 `rows.json`（`repair_budget` "none used"）、单一时间戳的 3 文件根、连续种子——无未记录 repair、retune 或参数改动。

## 6. 阻塞

无。全部指派读取成功，无失败命令，无缺失产物（6 根 × 3 文件均存在且可解析）。唯一需主线程的决策是：接受本 FAIL 及其后果——本批仅作 harness 缺陷展品保留、不作提升，随后或立新冻结修正包、或对该基线诚实退役。
