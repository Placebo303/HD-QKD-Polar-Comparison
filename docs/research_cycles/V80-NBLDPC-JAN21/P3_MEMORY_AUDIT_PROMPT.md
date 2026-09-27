# P3 真实帧记忆/一致性审计 — 执行提示面（P3_MEMORY_AUDIT_PROMPT）— FROZEN, NOT GRANTED

- Track（恰其一）: **DECIDE**。本提示面不改变 PACKET 的 DECIDE 合约；无授权不得执行。
- 配套 prereg：`P3_MEMORY_AUDIT_PACKET.md`（§2 冻结科学输入、§2.5 容差槽位、§3 DECIDE 合约、§4 P3-gate 判定形式）。
- 基线 provenance：用户声明 `8e9c8526`；实际分支/HEAD 由 Q0 实测记录，不做 SHA 相等断言。
- 路线位置：③ 并行之 P3 侧；只冻结不执行；禁碰 P1 族/P4 包/S0.1 族/EXECUTION_PLAN/NOW/decision-log/AGENTS/`src/`。
- 零解码铁律：**0 decoder / 0 DE / 0 图构造 / 0 `tools/longrun_*|minrerun_*|routeA_*`**；仅统计量级访问。违反即 STOP-BLOCKED。

## 1. STOP 条件（任一即停，不执行）

1. `P3_MEMORY_AUDIT_PREREG_AND_AUTH.md`（或等价记录授权节）签字块空白，或授权未点名分支+数据集三源+容差数值（含 TBD 填数）+预算上限。
2. 目标机器根已存在（非 fresh），或 `results/`/`comparison_bench/outputs_comparison/` 快照与冻结记录不一致。
3. focused fake-only 测试未全过。
4. 任一禁碰文件在 diff 内，或 `git diff -- src/` 非空。

## 2. Pre-EXECUTE Q 清单（逐项记录证据；FAIL 阻塞执行）

- Q0 意向分支/HEAD：记录 `git branch --show-current` + `git rev-parse HEAD`（实测值，非锁）；确认发布分支政策（具名 formal-IR 分支，普通非强制；不碰 Polar 线）。
- Q1 包清洁：PACKET/PROMPT mtime 早于执行；TBD 容差已由主线程填数并 re-freeze（或仍 TBD→不得执行）；授权消息逐字记录。
- Q2 确切命令：冻结命令模板（uuid 占位，执行时一次性实例化）：
  ` .venv/bin/python -m <frozen_stats_module> --sources 1M,1.5M,2M --out workspace/P3_MEM/<uuid>/ --no-decode --seed <frozen> `
  （模块名以授权时冻结为准；本提示面不定模块名；命令含 `--no-decode` 硬开关，无解码路径。）
- Q3 预算上限：trio wall ≤ 5400 s / 单源 ≤ 1800 s / 单读 ≤ 300 s / RSS < 4 GiB / 每源读 ≤ 2 / 0 解码（PROPOSED；授权时确认为准）。
- Q4 目标输出 absence：`workspace/P3_MEM/<uuid>/` 不存在（`test -e` 为否）；`results/` 与 `outputs_comparison/` 计数的 before 快照已记录。
- Q5 focused 测试：fake-only 统计模块测试全过（形状/归一化/no-decode 守卫），输出粘贴。
- Q6 显式授权：用户授权逐字引用 + 授权覆盖的冻结臂序列（本包单臂：三源统计审计）。

## 3. 执行体（一次执行；统计量级；分源禁合并）

1. 在 fresh 根 `workspace/P3_MEM/<uuid>/` 内运行 §2-Q2 冻结命令一次；命令外任何真实数据访问禁止。
2. 计算 PACKET §2.2 四项统计量（三源各自独立）：超帧权重分布、逐列边缘/联合直方图、帧内/帧间 ACF + block-H 漂移、vs `gamma_f03` 生成器差异（χ²/TV/分位数）。
3. `gamma_f03.npz` + `gamma_f03_pb.npz` 只读；时延/PPP 仅描述性记录，不拟合；块数口径只用冻结池 500/691/911（census raw-stream 计数不得替代）。
4. 事件级数组（time/channel）不得落盘；结果 JSON 只存标量+直方图+序列统计量。
5. 不得声明任何预测结果；不得输出 FER/f/success/“预期通过”句；结果只含实测统计量 + 容差对照表 + P3-gate verdict。

## 4. 结果记录（RESULT.md 或等价 append-only 节 + 机器伪影）

- `RESULT.md`：命令逐字、种子、wall/RSS、读次数、0-解码声明、分源四项统计量表、T-C0..T-M4 容差对照（PASS/FAIL/INDETERMINATE）、P3-gate verdict、claim ceiling 重申（含“未证伪≠已验证 + 电池粒度”限定）。
- 机器伪影：分源 JSON（含直方图/ACF/漂移标量）、容差对照 CSV、PRE_EXECUTE.md（含 Q0–Q6 证据）。
- No-overwrite 证明：after 快照与 before 一致（`results/`、`outputs_comparison/` 字节/文件数不变）。

## 5. 独立 Pre-RESULT 清单（独立线程；FAIL 阻塞固化）

1. 计划阈值重核：T-C0..T-M4 每项由伪影标量重算（TV/χ²/ACF/斜率公式与 PACKET 一致）。
2. 泄漏公式分解：本包 N/A——显式标注“无泄漏计算”，不得编造分解。
3. `undetected` 隔离：本包 N/A——显式标注“无解码，无 success/FER/undecided 合并”。
4. 分源分解：1M/1.5M/2M 各自成表，无合并行；块数口径为冻结池口径。
5. 披露会计：prior/gamma 只读声明 + 时延/PPP 描述性声明 + 电池功率 caveat（SE、`|acf|` vs SE 倍数、帧内失明）齐备。
6. 计划语义 vs 伪影：P3-gate verdict 与 §4 决策树一致；FAIL 时含“不得合成 FER 当真实 FER + 先帧级条件化”句。
7. 禁区：`src/` diff 空、无预测句、无禁碰文件改动。

## 6. 二进制返回（仅二者之一）

- `COMPLETE`：全部冻结项完成 + Pre-EXECUTE PASS + 一次执行 + 结果记录 + 独立 Pre-RESULT PASS（含 verdict），或
- `BLOCKED`：失败命令 + 精确报错/traceback + 已试补救 + 需要主线程决策的**单一**事项。“仍在进行中”不是返回。

## 7. 授权签字块（BLANK — 未授权）

- 用户授权：`[BLANK — 未授权，不得执行]`
- 机器根 uuid：`[BLANK — 执行时一次性实例化 workspace/P3_MEM/<uuid>/]`
- Pre-EXECUTE verdict：`[BLANK]`
- 独立 Pre-RESULT verdict：`[BLANK]`
- 主线程接受：`[BLANK]`
