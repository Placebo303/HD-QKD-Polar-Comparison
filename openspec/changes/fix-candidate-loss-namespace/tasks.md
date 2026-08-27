# tasks — fix-candidate-loss-namespace

**已批准（2026-08-25）。Q1–Q4 裁决结论已回填，决策记录见 proposal.md 顶部。**

约束：全程不覆盖 `results/` 既有产物与事件证据；冻结基线仅按 design §3 的最小触碰面修改；
T2/T3 仅在里程碑执行；每个任务完成后报告 delta（改动文件+命令+结果），不重复背景。

## Phase 0 — 决策与预检

- [x] T0.1（2026-08-25 完成）用户裁决：Q1=复验 16dB 共享 56 格；Q2=方案 A 全网格 121 格/档；Q3=隔离改名 `real_sequences_quarantined_20260825`（T5.3 执行）；Q4=`*_lossfix_v1`。记录见 proposal.md。
- [x] T0.2（2026-08-25 完成）G0 预检脚本化：四档 ttbin 主文件+`.1` 分片均存在且非零，
      sha256 已记录（见 `evidence/G0_precheck_report.md`）；归档 override 点指纹对账
      4×(120 匹配 + 1 失配@d1024_bw200，mismatch 仅记录)；MANIFEST 骨架落
      `evidence/MANIFEST_skeleton.csv`（因 results/ 写入禁令，暂不放 `results/real_sequences_ns/`）。
- [x] T0.3（2026-08-25 完成）跨档 joint_fingerprint 对账枚举受影响格：
      10∩16=56、6∩16=56、6∩10=40 与事件记录完全一致；6dB 并集精确值 **67**
      （事件记录为近似 ≈61；三档交集 29 格，容斥自洽）；20dB 共享=0。
      产物：`evidence/affected_cells.csv` + `.summary.txt`。另经 G2 字节级独立复核：
      跨档相同数组恰 304 = 2×(56+56+40)，与指纹枚举一致。

## Phase 1 — 工具确认与最小改动

- [x] T1.1（2026-08-25 完成）`export_sidecar_for_point` 增加可选 `pool_root` 参数
      （硬编码池路径仅存在于该函数 L1483 一处，故参数加在此处；materialize 经显式
      out_dir 接收，无重复参数）+ `run_e2e_pipeline.py --real-seq-pool-root`
      全链路透传（CLI→_run_extract_batch→worker init→export 调用）。默认行为不变；
      断言测试通过：不传参时 materialize_out_dir 与旧硬编码路径逐字符一致。
- [x] T1.2（2026-08-25 完成）新增 `tools/materialize_loss_namespaced_candidates.py`
      （src_tag 规范映射、per-tier override/pool_root/out_root、钉死 env 自由度、
      MANIFEST 增量更新、防混源写入守卫、--dry-run）。未对真实数据执行。
- [x] T1.3（2026-08-25 完成）新增 `tools/verify_candidate_namespace_gates.py`
      （G0/G1/G2/G3/G4 + affected-cells + self-test tamper 自检；注入重复字节/
      单字节漂移/档位序颠倒/溯源缺失均验证 FAIL）。
- [x] T1.4（2026-08-25 完成）冒烟：workspace/fix-candidate-loss-namespace/9b02514e-…/tests
      以合成 ttbin（patched reader，不触碰 results/）走通 物化→G1→G2+tamper 最小回路，
      pytest -p no:cacheprovider --basetemp=<task root> 4 passed。

## Phase 2 — 小样试点（T2）

- [ ] T2.1 选 6dB 的 3–6 格（含事件清单中的共享格与非共享格各若干）：
      双跑物化 → G1 字节一致 → 写入新命名空间。
- [ ] T2.2 与旧 candidate 同格对比：预期**不同**（源 ttbin 不同）但 map_sanity PASS、
      ser 量级合理；任何异常即停，回报阻塞。

## Phase 3 — 全量物化 + 门校验

- [x] T3.1（2026-08-26 完成）按 Q2 裁决范围全量物化：10dB 121 格 ok=0 fail、6dB 121 格
      （--resume 复用试点 6 格）ok/fail=0、16dB **83** 格（现场裁决修订任务包"56"：
      affected_cells.csv 中涉 16dB 格=83，56 仅为单对计数；用户选 83 全清单）ok/fail=0。
      分离进程+日志+PID 见 workspace/fix-candidate-loss-namespace/p3_20260825_232345/；
      总耗时 59m22s。证据：evidence/phase3_materialization_report.md §1。
- [x] T3.2（2026-08-26 完成）chan_ll_table.npy 全格存在性确认 + 每档 ≥5 格溯源深检全过。
- [x] T3.3（2026-08-26 执行完毕，G3 结果 FAIL ⇒ 已按停止规则就地停）G2 新档互检 574 组
      零碰撞 PASS；指定旧参照对 6 对中 3 对零碰撞、3 对 90 数组碰撞已全部归因（污染方向
      证据，格格∈affected 清单）；G4 446 sidecar PASS。G3 修订门新数据 10/83 序违例 FAIL，
      旧数据同门 95/121 违例（含污染性精确相等）——判据问题非重建缺陷，待主线裁决，
      未调参未绕过未进 Phase 4。
      G3 二次修订版复跑（2026-08-26）：①0 精确相等 ✓、②均值序 0.2408>0.2255>0.2076>0.1725 ✓、
      ③2 格倒置 rel=2.2303% ≥2% ⇒ FAIL（d1024_bw150/d2048_bw150，阈值恰低于实测最大值
      0.23pp）；G4 复跑 PASS。详见 evidence/phase3_gates_rerun_report.md §5 BLOCKER，仍待裁决。
- [x] T3.4（2026-08-26 完成）MANIFEST.csv 定稿 325 行，表头追加 chan_ll_sha256 列，
      全量 sha256 从盘重算对账一致。

## Phase 4 — 重跑受影响档

> 并行度指示（用户 2026-08-25）：按主机逻辑核数尽可能多核并行（stage0 `--jobs`、stage1 `--workers`），
> 具体取值在启动前探测核数后冻结并记入产物溯源；科学参数不变（frames 300 / seed 20260228 / tag bits 64 / shards 16）。

- [~] T4.1（2026-08-26 启动，IN PROGRESS）stage0 重放索引重建按 10dB→6dB→16dB 三档顺序分离进程
      执行，指向 lossfix 候选目录（--candidate-dirs 新旗标）；首档 10dB 主 PID 9876 于
      01:52:41 启动，60s/300s 存活核验通过（15 python、聚合 CPU 6507s@300s）。
      记录：evidence/phase4_launch_record.md；并行冻结：evidence/phase4_launch_config.md。
- [~] T4.2（2026-08-26 随 T4.1 同进程链启动，IN PROGRESS）stage1 actual_ir + stage2 security，
      输出到 `four_loss_parts_frames300_lossfix_v1/`，frames300/seed/tag-bits 冻结不变。
- [ ] T4.3 20dB 档结论沿用既有产物，仅在汇总表中引用，不重跑。

## Phase 5 — 验证与收尾

- [ ] T5.1 跨档验证：新 master 表中任意两档同格输入哈希互异（G2 终检）；
      与 v3 参考趋势对照（量级/排序，不逐位）。
- [ ] T5.2 old-vs-new 报告：受影响档 SKR/leak 变化表 + 科学结论边界更新
      （哪些跨损失对比恢复成立）。
- [ ] T5.3 按 Q3 裁决处置残余共享池三目录（须显式授权后执行）。
- [ ] T5.4 更新 AGENT_PROJECT_MEMORY.md / decision-log.md / troubleshooting.md 相关条目；
      CURRENT_TASK.md 的 Pending decision 关闭。
- [ ] T5.5 memory triage（memory agent）；`/finish-change` 判定可归档性。

## Stop Rules

- 任一门 FAIL 且无法归因为脚本 bug ⇒ 停止并回报，不得调整科学参数绕过。
- 发现需求歧义 ⇒ 返回 planner/OpenSpec，不猜测。
- 任何对 results/ 既有路径的写入冲动 ⇒ 先取得用户明确授权。
