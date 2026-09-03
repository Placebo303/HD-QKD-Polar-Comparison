# V72P2D2-TRIAGE PLAN_CANDIDATE (未接受, 不授权执行)

- Cycle: `V72P2D2-TRIAGE`. State: `PLAN_CANDIDATE`.
  `development_execution_authorized: false`,`formal_execution_authorized: false`,
  `scientific_promotion: false`,`accepted_plan_sha: null`,`implementation_sha: null`。
- 本文为计划候选入口,不是 `PLAN_ACCEPTED`,不授执行。任何实现/decoder 运行/
  raw-parquet 读取/结果目录创建均需另行明确授权。本文件仅新增,不改 D1/V72P1/V72P2
  的 `cycle_state.yaml`、结果、`OpenSpec`、memory。
- OpenSpec: `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/`
  (proposal/design/tasks/specs)。Design §1–§10、tasks T0/T1/T2 为执行依据候选,
  本文件只收敛入口参数与判别规则。

## Goal / Non-Goals / Impact Scope / Acceptance Criteria

- 同 proposal.md(Goal:单块正交区分 L 调度/I 对齐/P prior,不预设优胜者;
  Non-Goals:禁重跑 A、禁九块/FER/SKR/推广、禁混合调参、禁重构 adapter;
  Impact:本次仅 5 文件新增,未来实现上限 5 文件合一;Acceptance:见 proposal AC1–AC7)。
  此处不复制全文,以 proposal 为准。

## 冻结入口参数(候选值,执行需另行冻结)

| 项 | 候选值(依据) |
|---|---|
| 块 | VAL1726–1729,session `20260123_1M_600k_0dB`,registry `v71_data_registry.json`(D1 同块,非新鲜) |
| 基线 A | 复用 D1 Arm A 记录(334 iters/`LADDER_EXHAUSTED`/3100bit/620sym),禁重跑 |
| Ladder | 72 ckpt `range(160,8993,128)+[9032,9036]`(D1 同) |
| Edge 预算/数值 | `max_iter` 10/ckpt、720/臂;`clip` 20;`tol` 1e-6;float64;臂内 warm-start 新边置零(D1 同) |
| 图 | 9036x10240,nnz49620,check `{4:1,5:4594,6:4441}`,deg2 9035(D1 M1–M7) |
| M0 | lambda `221.22162910704503`,CAL-CV CE `7.135005172802673`(D1 同) |
| M2 | `laplace,mu=0.0,scale=0.2714417616594907,eps=0.562251256281407`(V70R1 1M CAL-only);VAL CE 6.7871 仅历史,允许变差 |
| I 参考 | 41/47/65、95/95 仅参考非门槛(路线研究试算,须重算留痕) |
| 时间预算(候选) | 臂 600s(D1 `ARM_BUDGET_S`/V72P2 `BLOCK_DEADLINE_S`依据);全局候选 2400s(4 臂×600 + 门禁余量,执行前另行冻结);D1 invocation 240.17s/1800s 仅作耗时依据,非授权 |
| 输出 | 新根恰四文件(manifest/results/table/report),禁覆盖,禁 `run_01`(本计划不建目录) |
| 接口 | 二选一 A(推荐零改动)或 B(最小修复 + 回归),未来单选 |

## 预注册判别(L/I/P,单块描述性)

- L 支持继续 layered 路线 ⇔ 出现候选 escape(任一 ckpt `candidate_vs_Bob flips>0`)
  或 violation 下降(末 ckpt violation < 首 ckpt)或验证成功;仅 runtime 变快不构成改善。
- I 冻结列映射并另做图设计 ⇔ 明显 escape 或 violation 下降;一次单块变化不宣称结构因果。
- P 记录 prior 影响 ⇔ 显著改变消息/翻转但仍不验证则停推广;无变化则削弱“仅 prior 模型致败”解释。
- 三臂皆无 hard-bit escape ⇒ 停 binary edge-level 微调,转 grouped-symbol mask BP
  tiny 排队或同块 GF32 对照;不加迭代/调 damping/扩样。
- 禁 FER/SKR/因果/M2 优胜/推广;`undetected` 隔离;不写三臂必胜。

## 后继与文献(描述性)

- Grouped-symbol mask BP:1024-state/mask/parity scalar/边缘化/binary SPA;
  约 41169 groups/轮约 42M 量级(估算);顺序 tiny→loopy→单块(见 design §8)。
- 文献:PEG https://doi.org/10.1109/TIT.2004.839541;layered
  https://doi.org/10.1109/SIPS.2004.1363033;spatial https://arxiv.org/abs/1001.1826;
  NB https://arxiv.org/abs/2305.08631(方向性引用,不构成路线接受)。
- 历史边界:V54 43/45、V64 22/24、undetected 0(同域真实成功,不转移);
  V5-C2 384/384 异域背景;V67–V72P1 非真实成功;V72P0 tiny 仅小树语义。

## 禁项重申

- 禁实现代码、禁运行 decoder、禁读 raw/parquet、禁真实执行、禁建结果目录、
  不改 V72P1/V72P2/D1 已接受代码结果 `OpenSpec`/`cycle_state.yaml`/memory、
  禁写 `PLAN_ACCEPTED`/授执行。数学合同未决记 BLOCKER,禁 TBD 猜测。
