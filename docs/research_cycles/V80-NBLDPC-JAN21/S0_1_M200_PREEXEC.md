# S0.1 m=200 Pre-EXECUTE 记录（G-S01M200）— 2026-09-22 — FROZEN DRAFT, NOT AN AUTHORIZATION

- 任务 IDs：S01-1（packet）/ S01-2（prompt）/ S01-4（本 Pre-EXECUTE 包：runner + 单文件测试 + 本记录）。Acceptance ID **G-S01M200**。Track **EXPLORE**（合成、有界、可逆；`EXPLORE_HEAVY` 注记可选）。基线 **85e0771f**，分支 `formal-ir-v72p1-addendum-clean`（不切分支）。
- 入口：`S0_1_M200_PACKET.md`（§§1–11 冻结）+ `S0_1_M200_PROMPT.md`。本文件 = packet §10(c) Pre-EXECUTE Q0–Q6 的登记载体；执行时条目 0 逐字并入 `S0_1_EXPLORATION_LOG.md`。
- **本文件不是授权。授权块（§10(d)）留白 = 未授权。未授权不得执行任何解码。本任务全程零解码、零 commit、零 push、零签字。**
- 本任务新建且仅新建 3 件：`comparison_bench/src/comparison_bench/cli/s01_m200_runner.py`（P2 thin runner）、`comparison_bench/tests/test_s01_m200_runner.py`（P3 单文件 fake-only 测试）、本文件（P5）。无核改动、无执行产物（见 §P6 自检于返回报告）。

---

## §P1 范围与分支证据（命令原样输出）

```
$ git branch --show-current
formal-ir-v72p1-addendum-clean
$ git rev-parse --short HEAD
85e0771f
$ git status --porcelain            # 任务开始时（P1）
（空 — 工作树清洁）
$ test -e workspace/S0_1 && echo EXISTS || echo absent
workspace/S0_1 absent
```

完成后复测（P5/Q1 时点）：

```
$ git status --porcelain
?? comparison_bench/src/comparison_bench/cli/s01_m200_runner.py
?? comparison_bench/tests/test_s01_m200_runner.py
（+ 本文件创建后第 3 件：?? docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PREEXEC.md）
$ git diff -- src/ | wc -c
0
$ git status --porcelain -- src/ | wc -l
0
```

---

## §Q0 目标分支 — **PASS**

`formal-ir-v72p1-addendum-clean` @ `85e0771f`，与 packet 头部/基线一致；**未切分支**。证据见 §P1。

## §Q1 范围清洁 — **PASS**

- 显式任务文件清单（全部改动 = 下列 3 件 additive，全部 untracked-new）：
  1. `comparison_bench/src/comparison_bench/cli/s01_m200_runner.py`
  2. `comparison_bench/tests/test_s01_m200_runner.py`
  3. `docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PREEXEC.md`（本文件）
- `git status --porcelain` 除上述 3 件外**零条目**：无外源 `openspec/changes/binary-ldpc-v5-*` 脏项（packet 提及的外源脏树在本时点不存在）、无任何已跟踪文件修改。
- `git diff -- src/` = **EMPTY**（0 字节；`git status --porcelain -- src/` 0 行）⇒ 不变量 I4 满足。
- 禁碰文件均未修改（由上述 git 状态覆盖）：`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`.gitignore`、`README.md`、`AGENTS.md`、`src/`、`experiments/`、`tools/`。
- 实现未改任何冻结模块/行为：runner 对 `b2f/b2g/o1/s2c/peg/v28` 全部**只读复用**（无 monkeypatch、无分支改动、无补常数）；冻结行为差异点仅存在于本 additive 模块自身（无默认生产解码、双旗标门、F6 基码 rank 门）。

## §Q2 冻结契约 F1–F10 逐项核对 — **PASS**（代码面）

| # | 冻结项 | 落点（runner 常量/函数 = `s01_m200_runner.py`） | 测试钉 | 状态 |
|---|---|---|---|---|
| F1 | 恰两臂 R1=2026092001 / R2=2026092011，分报禁合并 | `ARMS` + `parse_arm`（未知臂 rc=2）；`--instance` 逐臂强制 | `test_parse_arm_frozen_two_arm_table` | ✓ |
| F2 | m=200 单点；A208 rows[0,200) nested；非 A200；不披露 rows[200,208) | `S01_M=200`、`S01_A208_M=208`；`construct_and_pin` 切片+排除；`--m` 强制 200 | `test_f6_base_code_excludes_rescue_rows`（逐 triple 断言 row<200）+ decode 假件内每块断言 | ✓ |
| F3 | 240 块；seeds `2026095601+idx`；stream `o1_blk:{seed}` | `S01_BLOCK_BASE/S01_N_BLOCKS/S01_STREAM`、`block_seed`、`stream_seed`；`--blocks/--seed-base` 强制 | `test_frozen_literals_seeds_budget_accounting` | ✓ |
| F4 | `gamma_f03.npz`+`gamma_f03_pb.npz` 只读、永不 refit、零 ttbin | `CHANNEL_NPZ/CHANNEL_SOURCE`；仅经冻结 `s2c.bind_empirical_bundle`；无任何其他数据路径 | 同上（路径字面量）+ `test_dry_pins_*` + `test_source_has_no_realdata_or_heavy_workflow_paths` | ✓ |
| F5 | b2f verbatim 先验 + v28 `decode_error_domain_posterior(…,300)` 300/streak3、exact_match、无 genie/argmax/L1 | `run_execution.decode_fn = b2f.decode_block_marginal`（冻结函数逐字调用，m=200 基码） | 行为面由假件契约钉（本任务不接生产解码；冻结函数本体由 b2f 既有测试覆盖） | ✓（接线面） |
| F6 | A208 fc=0/rank208/twice-identical；基码 rank(rows[0,200))=200 REQUIRED；girth 记录不设门 | `construct_and_pin`（双次构造比对、fc、rank、`rank_fn` 基码门，逐一 `STOP-BLOCKED` rc=2，先于任何解码） | `test_f6_construct_gates_stop_before_any_decode`（fc/rank/twins/nm/基码 199 五路全拒、零解码） | ✓（代码面）；实测跑 = Q5 PENDING |
| F7 | f_super=1064/852.544=1.24803；f_eff=f_super+4.785675·FER（逐臂自身 k）；绝不混报 | `F_SUPER/CONTENT_BITS/LEAK_BITS/F_EFF_SLOPE/f_eff_for`；md 强制两行分立 | 字面量断言 + `test_all_success_outputs_and_markdown_contract`（两行存在且不同） | ✓ |
| F8 | key-eligible 只引用不消耗；N_req=277 report-only；不作认证主张 | `N_REQ`、`n_required_frozen()`（算术漂移即 refuse）、`CLAIM_CEILING` | `n_required_frozen()==277==ceil(3·4.785675/(1.3−1.24803))` | ✓ |
| F9 | 禁 bar-12 早停；解完全部 240；bar-12 仅 report-only | 主循环无任何 k 阈值分支；`BAR12` 仅入 `route_ctx` 文案 | `test_no_early_stop_all_240_even_all_fail`（240 全败仍 240/240 COMPLETE） | ✓ |
| F10 | 非 exact_match 计 fail；undetected 单列永不并入 success | `failures`/`undetected` 双计数；CSV/JSON/md 三处分立字段 | `test_undetected_separate_never_merged_no_early_stop`（160/80 分账） | ✓ |

预算/停止（§5）同表钉：wall 3600 → `INCOMPLETE-wall`；单调用 300 s 超时 = 终态块计 fail 不续跑；decode 异常 = 终态不重试；RSS≥2 GiB 终态；root 非 fresh 拒绝（无 resume 结构）；`results/`、`outputs_comparison/` 拒绝 —— 见 `test_wall_cap_*` / `test_per_decode_overrun_*` / `test_decode_error_*` / `test_rss_budget_*` / `test_root_refusals_*`。

## §Q3 输出缺席 + rg 命中 + 保护根快照 — **PASS**

1. **输出缺席**：`workspace/S0_1/` **不存在**（家族级缺席 ⇒ 冻结的两个臂根 `workspace/S0_1/S01-R1_6e48f11e`、`workspace/S0_1/S01-R2_b74322cf` 必然缺席）。dry 运行自身 `roots.family_exists=false` 且零写入。
2. **`rg 'S01_|S0_1_M200'` 文件级命中**（`rg -l … -g '!.git'`）：
   ```
   comparison_bench/src/comparison_bench/cli/s01_m200_runner.py   ← 本包执行面
   comparison_bench/tests/test_s01_m200_runner.py                 ← 本包测试
   docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PACKET.md      ← 本包
   docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PROMPT.md      ← 本包
   docs/research_cycles/V80-NBLDPC-JAN21/S0_1_M200_PREEXEC.md     ← 本文件（创建时新增命中）
   docs/NOW.md:14: `S0_1_M200_PACKET.md`、`S0_1_M200_PROMPT.md`）… ← 基线 85e0771f 既有指针行（未修改，见下）
   ```
   命中**全部**限于 S0.1 包族（packet/prompt/preexec/runner/test）+ `docs/NOW.md` 第 14 行一条**基线已提交、未被本任务修改**的包族指针（`git status` 证明 NOW.md 无改动；packet §8 禁改 NOW.md ⇒ 未违反）。无任何其他文件命中。
3. **保护根快照（字节级，Q3 时点；P6 复测一致）**：
   - `results/`：0 文件 / 0 字节。
   - `comparison_bench/outputs_comparison/`：**1446 文件 / 554423395 字节**。
   - 既有证据根（只读不碰）：`p3_census_3954637c` 4986021 B；`p3_stage05_ee32030a` 216643 B；`r1_histogram_5e2a91c4` 248409 B；`workspace/x1_*` 共 16 目录 / 36213603 B（packet 记 15，实测 16，登记为观察值，不改冻结项）。
4. `git diff -- src/` **EMPTY**（0 字节）。

## §Q4 focused 单文件 fake-only 测试 — **PASS（输出附下）**

- 冻结文件名（packet/prompt 占位在此冻结）：`comparison_bench/tests/test_s01_m200_runner.py`
- 单文件命令（prompt §0.2 逐字形式，填入冻结文件名）：

```
$ PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_s01_m200_runner.py -q
...................                                                      [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /mnt/d/Code/HD-QKD_Polar_Comparison/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: cache_dir
  
    self._warn_or_fail_if_strict(config_option_name)
      self._warn(f"Unknown config option: {key}", stacklevel=2)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 1 warning in 5.28s
```

（warnings 为已知良性 pytest `cache_dir` 配置提示，AGENTS §8 已记。）测试性质：**全 fake-only** — 构造/解码/rank/信道四类注入件全部显式传入 tmp 信道为合成 npz；零生产解码、零真实数据路径、零冻结模块改动；`-p no:cacheprovider`。E5：此输出须原样并入批次日志条目 0。

## §Q5 dry 零解码 pins — **字面量面 PASS；F6 构造实测面 PENDING（占位，Grant 前须补跑）**

- 运行命令与完整输出（零解码，`decode_calls: 0`，rc=0）：

```
$ PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner --dry
{
 "arms": {"arms": {"S01-R1": 2026092001, "S01-R2": 2026092011}, "m": 200,
          "reporting": "separate per instance; pooling incl. 6+4 FORBIDDEN"},
 "budget": {"bar12_report_only": 12, "batch_ceiling_s": 7200, "cpus": 1,
            "n_req_report_only": 277, "per_decode_cap_s": 300,
            "rss_cap_gib": 2, "wall_cap_s_per_arm": 3600},
 "channel": {"access": "read-only via frozen bind_empirical_bundle; never refit; pure synthetic (packet F4)",
             "g1_shape": [32, 1024], "g2_shape": [32, 32, 1024],
             "sidecar": "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03_pb.npz",
             "source": "2M"},
 "channel_path": "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz",
 "construction_pins": {"command": "… s01_m200_runner --dry --construct-pins",
   "gates": {"a208_four_cycles": 0, "a208_rank": 208, "a208_twice_identical": true,
             "base_rank_required": 200, "base_rows": "rows[0,200)",
             "girth": "recorded-not-gated"},
   "status": "PENDING (rank==200 dry placeholder — NOT run in this pass; zero decode either way)"},
 "decode_calls": 0,
 "frozen_accounting": {"content_bits": 852.544, "f_eff_slope": 4.785675,
   "f_super": 1.2480294272201786, "f_super_formula": "(5*200+64)/852.544 = 1064/852.544",
   "f_super_literal": "1.24803", "leak_bits": 1064, "n_req_report_only": 277},
 "mode": "dry-zero-decode",
 "roots": {"family": "workspace/S0_1/", "family_exists": false},
 "seeds": {"block_base": 2026095601, "blocks": 240, "first": 2026095601,
           "last": 2026095840, "stream": "o1_blk:{seed}",
           "stream_first_matches_frozen": true},
 "verdict": "DRY-PASS (zero decode; literal pins; F6 construction pins PENDING)"
}
RC=0
```

- 判定：
  - ✅ **gamma 只读**：经冻结消费件 bind PASS（2M、g1 (32,1024)、g2 (32,32,1024)、sidecar 同胞 `gamma_f03_pb.npz`；read-only、never refit、零 `.ttbin`）。
  - ✅ **seed 钉**：base 2026095601、240 块、first 2026095601 / last 2026095840、stream `o1_blk:{seed}` 首元素与冻结推导一致。
  - ✅ **预算钉**：3600 s/臂、7200 s 总、300 s/单调用、RSS 2 GiB、1 CPU、bar-12=12（report-only）、N_req=277；f_super 实算 1.2480294272 ≡ 字面 1.24803。
  - ⏳ **F6 构造实测（A208 fc=0/rank208/twice-identical + 基码 rank(rows[0,200))==200 + girth 记录）= rank==200 dry 占位，本任务未实测**（P2 规格即占位；两实例 A208 三钉为 b2f/b2g manifest 既有 pin 的重申，**新增实测量仅基码 rank==200**）。**Grant 前由主线程补跑唯一零解码命令并把输出并入日志条目 0**：
    ```
    PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner --dry --construct-pins
    ```
    任一实例非 PASS ⇒ STOP-BLOCKED（packet F6），不得授权。该命令零解码（无 decode_fn 存在于 dry 路径）、纯内存构造、不写任何根。
  - 拒绝门已单测：未归一化信道 bind ⇒ rc=2（`test_dry_pins_refuse_unnormalized_channel`）。

**Q5 状态 = PARTIAL**（字面量 PASS ∪ 构造实测 PENDING）。按 packet §10(c)，Q5 全 PASS 是签署授权块的前置；本文件停在门前，不代跑、不代签。

## §Q6 — **PENDING（挂在主线程门前）**

包与 prompt 列出 Q0–Q5 具体项而 Q6 未拼写；按 §10 尚未闭合的余项登记为 Q6：

- (a) 入口前置 **H0.1 = SATISFIED**：`051e3687` “hygiene: H0.1 commit X1 scoped tree + F1 fix + G0=B log” 在基线 85e0771f 祖先链中（`git log` 证据），X1 scoped 提交已完成，**无需豁免**。
- (d) 授权块结构 = 就位且**全空白**（见下）；预算确认 = **全未勾选**。留白 = 未授权（不得自行填写）。
- Q5 构造实测补跑（见上）= 未完成。
- ⇒ **Q6 = PENDING**；整包状态 = **READY-FOR-GATE（等 Q5 构造补跑 + 主线程签署）**。

---

## § 冻结臂根（UUID 在此冻结；缺席已证明）

| 臂 | 实例 | 冻结根 | 缺席 |
|---|---|---|---|
| S01-R1 | 2026092001 | `workspace/S0_1/S01-R1_6e48f11e` | ✅（家族不存在，2026-09-22 复证） |
| S01-R2 | 2026092011 | `workspace/S0_1/S01-R2_b74322cf` | ✅（同上） |

臂序冻结 R1→R2，各一次调用；两实例分报，禁合并（含 6+4）。任何根在授权前被创建 ⇒ Q3 失效，STOP。

## § 冻结命令（runner 路径 + UUID 在此填入 prompt §1.6 占位）

- 零解码 pins（**Grant 前**，可重复跑）：
  ```
  PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner --dry
  ```
- F6 构造实测（**Grant 前必跑一次**，零解码；输出并入日志条目 0）：
  ```
  PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner --dry --construct-pins
  ```
- 授权后生产臂（prompt §1.6 模板参数**逐字**；追加 runner 强制的双旗标 —— 无旗标逐字调用 = rc=2 拒绝，此即“无默认生产解码”）：
  ```
  PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner \
    --execute-real --execution-authorized \
    --arm S01-R1 --m 200 --instance 2026092001 --blocks 240 --seed-base 2026095601 \
    --root workspace/S0_1/S01-R1_6e48f11e
  ```
  ```
  PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m comparison_bench.src.comparison_bench.cli.s01_m200_runner \
    --execute-real --execution-authorized \
    --arm S01-R2 --m 200 --instance 2026092011 --blocks 240 --seed-base 2026095601 \
    --root workspace/S0_1/S01-R2_b74322cf
  ```
- Q4 测试（单文件，可重复）：
  ```
  PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/test_s01_m200_runner.py -q
  ```

## § 预算确认（**全部待勾选；unspent budget ≠ authorization**）

- [ ] 单臂 wall ≤ **3600 s**（单窗口）
- [ ] 批次总 ≤ **7200 s**
- [ ] 单调用 ≤ **300 s**（超时 = 终态，块计 fail，不续跑）
- [ ] RSS < **2 GiB**
- [ ] **1 CPU**
- [ ] 零 `.ttbin` / 零真实数据 / 零 `results/` 与 `outputs_comparison/` 写入

## § 授权块（空白待签；未填 = 未授权；verbatim 承 packet §10(d)）

- Acceptance ID `G-S01M200`；grant verbatim：________；臂根 UUID（R1/R2）：`S01-R1_6e48f11e` / `S01-R2_b74322cf`（本文件 §冻结臂根已登记，签署时确认）：________；预算确认（≤3600 s/臂、≤7200 s 总）：________；日期 / 主线程：________。

---

**未授权不得执行。** 本文件不授权解码、不授权测试长跑、不授权 commit/push、不授权任何 P1 臂。Q5 构造补跑未完成 + 授权块留白期间，生产路径双旗标调用一律 rc=2（已由 `test_cli_refuses_before_anything` 钉死）。
