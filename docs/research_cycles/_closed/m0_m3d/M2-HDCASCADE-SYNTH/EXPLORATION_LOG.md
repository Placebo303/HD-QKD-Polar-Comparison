# EXPLORATION_LOG.md — G-M2-HDCASCADE-SYNTH（append-only）

Cycle: `G-M2-HDCASCADE-SYNTH` · Track: `EXPLORE` · HEAD 冻结时点：`8e9c8526`（执行前重测）
Claim ceiling：**“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**

---

## entry 0 — Pre-EXECUTE 冻结记录（T1 slice，2026-09-24；任一FAIL即STOP，EXECUTE未进入）

- Q0 分支/HEAD重测：`formal-ir-v72p1-addendum-clean` @ `8e9c852646087fe513bab45129a2f939e94f066e` == 基线 `8e9c8526`（`git branch --show-current && git rev-parse HEAD` 实测）。PASS。
- Q1 冻结目录diff：`git status --porcelain -- src experiments tools` → EMPTY。PASS（scoped）。树上其余预存脏项（4 tracked modified：`AGENT_PROJECT_MEMORY.md`、`docs/NOW.md`、`docs/decision-log.md`、`docs/troubleshooting.md`；untracked 他线 M0/P4/TIMING/M1/M2-REALCOMP/V80/p4-feas/same-data + M2三包/2方法/2测试/impl change）非本slice创建，按显式清单排除在外，未触碰。
- Q2 focused fake测试：`timeout 300 .venv/bin/python -m pytest -p no:cacheprovider comparison_bench/tests/test_m2_hd_cascade_fake.py comparison_bench/tests/test_m2_layered_binary_fake.py -q` → **9 passed**（HD 5/5 + layered 4/4），5.18s。PASS（HD部分5 passed）。
- Q3 预算：PROPOSED（未冻结，待主线程确认）——单臂wall 5400s（镜像M0每源帽；M0实测3409/3696/4672s）、批次ceiling 6×5400s、单臂timeout终态失败不重跑、RSS<4GiB、1CPU。`results/`、`outputs_comparison/`零新增写入（本slice前后`git status --porcelain`均空）。
- Q4 输出缺席证明：`ls -d workspace/m2hdc_*` → 不存在（执行前后两次实测）；uuid8冻结为 `3c0f660c`（保留未建根，EXECUTE blocked故未创建）。
- Q5 §2 pin快照：**BLOCKED** —— 待澄清表open（design §2：原文节号/精确定义/块长表真值全待核对）；无冻结`<synth_module>`（全仓唯一调用`run_hd_cascade`者仅其定义文件，无CLI/臂runner；新建=新代码+未冻结采样器选择，超出operator范围，未写）；`HdCascadeParams.seed`默认`20260415`代码标PLACEHOLDER；messages公式代码标provisional（无aperture claim）。operator未发明任何数值。
- Q6 授权块（PACKET §7）：**BLOCKED** —— 未收到用户原文verbatim，仅orchestrator转述句（见PACKET §7记录）；按“BLANK即未授权”视为未授权，EXECUTE保持STOP。

（以下不得预写：逐臂条目、收口 tally、repair 记录、batch-end review 均待执行后追加。）

---

## entry 1 — T1 重执 Pre-EXECUTE Q0–Q6 复验 + A1–A6 执行（2026-09-25；一授权覆全臂）

- 授权：用户 2026-09-25 原文“授权不用找我，我现在一并授权”落字 PACKET §7-8，主线程见证已确认；一授权覆 A1→A6，各 N=240。Track `EXPLORE`（合成）不变。
- Q0 分支/HEAD：`formal-ir-v72p1-addendum-clean` @ `8e9c852646087fe513bab45129a2f939e94f066e` == 基线 `8e9c8526`。PASS。
- Q1 冻结目录：`git status --porcelain -- src experiments tools` → EMPTY。PASS（执行后复测仍 EMPTY）。
- Q2 focused fake：`timeout 300 .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_m2hdc_arm_runner_fake.py -q` → **10 passed**；另 `test_m2_hd_cascade_fake.py` → 5 passed（合计 15）。PASS。注：须 `-o addopts=""` 覆盖 pytest.ini 内 Windows `basetemp`，否则 7 errors（环境问题，非代码失败）。
- Q3 预算/零生产：单臂 wall 5400s / 单 decode 300s / RSS<4GiB / 1CPU，总额 6×5400=32400s；`git status --porcelain -- results comparison_bench/outputs_comparison` → 空（执行前后皆空）。PASS。
- Q4 输出缺席：执行前 `ls -d workspace/m2hdc_*` → 不存在；`test ! -e` 逐根确认 01 `3c0f660c` / 02 `a1b2c3d4` / 03 `e5f60718` / 04 `9a8b7c6d` / 05 `5e4f3a2b` / 06 `c1d2e3f4` 皆缺席。PASS。
- Q5 pin 快照（§7-4 assumed-v1 verbatim）：F2 `[8,4]`×10 位面 / cross 1 / floor 1（`provisional_block_table` 实测）；F3 `max_passes` 4 / 块长下限 1 / 消息计数 `messages_actual` provisional / `max_cross_plane_sweeps` 1；F4 ARM_SEED A1=2026095701 … A6=2026095706（`M2HDC_ARM_SEED` 实测 verbatim）；bundle 只读 `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + sidecar `gamma_f03_pb.npz`（`PB_SIDECAR_NAME` 实测一致）；H 合成 F03（1M 0.801038 / 1.5M 0.825566 / 2M 0.832563）。PASS。
- Q6 零生产/闭环：执行仅读冻结 bundle（合成），未碰真实 `.ttbin`/真实 gamma；禁令（PROMPT §2）全守；一授权闭环确认。PASS。

执行命令（逐臂，`timeout 5400` 外层；bundle/sidecar/seed/flags 全冻结字面）：

```bash
timeout 5400 .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m2hdc_arm_runner --execute-real --execution-authorized --arm <M2HDC-…> --bundle docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz --pb-sidecar docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03_pb.npz --source-key <1M|1p5M|2M> --construct-instance 2026092001 --standalone --seeds "<5701..5706>+idx" --stream "o1_blk:{seed}" --blocks 240 --root workspace/m2hdc_<uuid8> --per-decode-timeout-s 300 --budget-s 5400
```

逐臂结果（A1→A6 冻结序；各 ~3s，wall 远低于 5400s；`nb_decode_calls` 全 0；`undetected` 单列隔离未并入 success）：

| 臂 | arm | 根 | verdict | blocks | fails | undetected | FER | f_super | G-A/B/C |
|---|---|---|---|---|---|---|---|---|---|
| A1 | M2HDC-1M-197 | `workspace/m2hdc_3c0f660c` | FAIL-early-stop (CENSORED) | 13 | 13 | 13 | 1.0 | 1.27885826 | FAIL/PASS/FAIL-expected |
| A2 | M2HDC-1M-201 | `workspace/m2hdc_a1b2c3d4` | FAIL-early-stop (CENSORED) | 13 | 13 | 13 | 1.0 | 1.30324069 | FAIL/FAIL/FAIL-expected |
| A3 | M2HDC-1.5M-203 | `workspace/m2hdc_e5f60718` | FAIL-early-stop (CENSORED) | 13 | 13 | 13 | 1.0 | 1.27634973 | FAIL/PASS/FAIL-expected |
| A4 | M2HDC-1.5M-207 | `workspace/m2hdc_9a8b7c6d` | FAIL-early-stop (CENSORED) | 13 | 13 | 13 | 1.0 | 1.30000774 | FAIL/FAIL/FAIL-expected |
| A5 | M2HDC-2M-204 | `workspace/m2hdc_5e4f3a2b` | FAIL-early-stop (CENSORED) | 13 | 13 | 13 | 1.0 | 1.27148786 | FAIL/PASS/FAIL-expected |
| A6 | M2HDC-2M-208 | `workspace/m2hdc_c1d2e3f4` | FAIL-early-stop (CENSORED) | 13 | 13 | 13 | 1.0 | 1.29494705 | FAIL/PASS/FAIL-expected |

- 收口 tally：6/6 臂得终态 verdict（全 CENSORED bar-12 early-stop，fails-at-stop/blocks-at-stop 已报，projected 无）；0 INCOMPLETE（timeout 未触发，无重跑）；repair 未用（`no repair path used`；至多一次预算未动）；输出恰 6 根×3 文件（`M2HDC_RESULT_*.md` + `rows.json` + `block_accounting.csv`）。
- A-CMPE：四列（attempted/exact_match/accepted/accepted_wrong）+ `undetected` 单列 + `f_super/f_notag/f_eff`（同臂 m 基，`f_eff=f_super+4.785675·FER`）+ `λ_total=leak_EC+64+救援+控制` + wall/RSS/每帧消息数 + `N_req` + `d/q/n_IR` 分离列，全于 `block_accounting.csv` 机器列与 RESULT md；Cascade 446 口径独立列、LDPC 3.14 非可比标注（6 枚 RESULT md 逐字在列）；claim 固定句 6 枚 RESULT md 逐字携带：**“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**
- 科学注记（非结论，仅现象记录）：生产译码路径下 6 臂首 13 块全 `accepted∧¬success`（undetected=13），触发 bar-12 早停；属合成单实例实测现象，不作任何真实优劣主张，待主线程研判。
- batch-end review：未做（operator 不做 acceptance，交主线程独立评审，E8 待判）。

---
