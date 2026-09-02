# Addendum Review Verdict: V72P1-ADP

**Repository**: `HD-QKD_Polar_Comparison`
**Branch**: `formal-ir-mainline`
**Cycle ID**: `V72P1-ADP`
**Review Kind**: `INDEPENDENT_ADDENDUM_REVIEW` (mechanical re-check)
**Reviewed Artifact**: `docs/research_cycles/V72P1-ADP/EXECUTION_PACKET_ADDENDUM.md` @ `ea82423f`
**Review Time**: 2026-09-02 (main-thread mechanical review; adoption authority: user/main reviewer)
**Reviewed Addendum Base**: `fb441f0f95a4d2268fa0f1bcce2db6fce83bc615` (HEAD parent, verified)

---

## 1. Verdict

- **verdict**: `ACCEPT_RECOMMENDED`（机械复核全部通过，无阻塞发现；采纳与授权由用户/主审决定）
- 本记录仅为机械复核发现，不自行推进 lifecycle；`cycle_state.yaml` 保持 `PLAN_ACCEPTED` 不变。

## 2. Mechanical Checks — 全部 PASS

| # | 检查 | 结果 | 证据 |
|---|---|---|---|
| C1 | HEAD == origin/formal-ir-mainline | PASS | 两者均为 `ea82423fe313c2ce3ef532fb48c87dc34e752e5a` |
| C2 | addendum base 为 HEAD 直接父提交 | PASS | `git rev-parse HEAD~1 == fb441f0f...` |
| C3 | accepted plan SHA 在历史中 | PASS | `73efd91f` 为 HEAD 祖先 |
| C4 | cycle_state 一致性 | PASS | `state: PLAN_ACCEPTED`，`accepted_plan_sha: 73efd91f...` 与 REVIEW_VERDICT / addendum 头部一致；`implementation_sha: null` 与 `IMPLEMENTATION_NOT_STARTED` 一致 |
| C5 | 旧/陈旧 SHA 0 命中（V55 教训） | PASS | `efd34ef` / `13b38b79` / `520b51c4` / `d91b3642` 在四工件 + cycle docs 范围均为 0 文件命中 |
| C6 | 目标输出不存在 | PASS | `v72p1_synthetic_qual/` 不存在；`comparison_bench/outputs_comparison/` 下无 `*v72p1*` 目录，无 run_01 |
| C7 | addendum 禁用模式 | PASS | `TBD`/`placeholder` 仅出现在禁止性表述本身（B 节标题与 L109），0 实际违规 |
| C8 | 冻结数值跨工件一致性 | PASS | 见 §3 |

## 3. 冻结数值复算（C8 明细）

- **内存表逐项复算一致**：prior_logp 8,388,608 + bit_to_factor/factor_to_bit/app_llr 各 81,920 + variable_to_check/check_to_variable 各 396,960 + hard_bits 10,240 + hard_symbols 2,048 + syndrome_target/observed 各 9,036 + factor_workspace 8,192 = **9,466,840 B**；CSR 36,148 + 198,480 + 49,620 = **284,248 B**；grand = **9,751,088 B**。与四工件、EXECUTION_PACKET（千分位写法）、addendum 全部一致。
- **checkpoint 72 验证**：`{160,288,...,8992}` 步长 128 共 70 个 + `9032` + `9036` = 72 ✓；checkpoint 集合是 disclosure prefix 集合的子集 ✓（128 = 16×8，落点均在 Δ8 网格上；9032 为规则格点 k=1109；9036 为 tail 终点）。
- **`llr_clip=20.0` / `convergence_tol=1e-6` / `seed 20260902` 仅存在于 addendum**：这是本轮 addendum 的设计目的（B 节补齐四工件中 `<float>` 占位的缺失数值），非一致性缺陷。四工件相应位置保持 `<float>` 占位与 REVIEW_VERDICT §3 的"future-implementation acceptance criteria"语义一致。
- `49620` / `prefix1111` / `checkpoint72` / `9466840`(或千分位写法) / `284248` / `9751088` 在六份相关工件中全部可检索命中。

## 4. 非阻塞观察（实现评审时必须落实）

- **O1（prefix/tail 语义统一）**：六份工件均写作 `Disclosure prefixes {160,168,...,9032,9036} count 1111 (regular +8 count 1110, tail 4)`。按 V70 `tail+n` 约定（族末行 = 最后 Δ8 格点 + 余行，`9036 = 160 + 8×1109 + 4`）作统一解释：**族 9036 行 = 1110 个 Δ8 规则行（160..9032）+ 4 行 tail（9033..9036）；disclosure 前缀 = 1110 个规则点 + 终点 9036 = 1111**。该解释下 count/set/tail 三者自洽。实现时 `T0-6`/`R72P1-04` 的前缀枚举必须固定为 `{160+8k | k=0..1109} ∪ {9036}`，不得实现为 1114（把 9033..9035 也当披露点）。
- **O2（四工件 lifecycle 行）**：tasks.md/spec.md 头部仍是 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`、Baseline `b1b2e9c5`。REVIEW_VERDICT §4 已显式接受此历史文本不改写，`cycle_state.yaml` 为权威 lifecycle。实现评审时以 cycle_state 为准，勿据四工件头部误判回退。

## 5. 授权边界重申

- 本 ACCEPT 建议**仅覆盖 addendum 的机械一致性**。若用户/主审采纳：后续授权范围为 `IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION_ONLY`（addendum §A 的 3 文件 + §7 T0/T1 + §1–4 synthetic smoke，SYNTHETIC_ONLY）。
- 仍不授权：真实数据（2M/TEST/holdout）、formal decoder、任何 `run_01`、调参/换 seed、覆盖既有输出、启动 V72。
- 正式执行前仍需 pre-EXECUTE / pre-RESULT 双重 review 门禁。
