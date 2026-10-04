# V72P2D1 parity-layout diagnostic (A/B) — frozen proposal

Status: FROZEN_PROPOSAL / EXECUTE_NOT_AUTHORIZED. Cycle: V72P2D1-PARITY.
Base: HEAD=ba0df2d3bea4147574e0b8224480f45c93505178 == live remote, branch formal-ir-v72p1-addendum-clean.
Predecessor: V72P2-VAL descriptive smoke (9 blocks, 0/9 LADDER_EXHAUSTED). V72P1 synthetic qualification intact.

## Goal

On one fixed non-fresh diagnostic block (VAL1726-1729 of session 20260123_1M_600k_0dB),
compare A=original mother vs B=degree-2-parity-column-permuted mother under a shared
CAL-only prior and the frozen V72P1 decoder/ladder, with wrapper scalar diagnostics
D1-D8. Decide only whether layout permutation alone moves the ladder outcome on this
block. Descriptive diagnosis only.

## Non-Goals

- No FER / SKR / information-limit / qualification / promotion claim.
- No new decoder kernel, BP schedule, damping, layered schedule, mother redesign.
- No fresh data, no tuning, no rerun, no second estimator, no threshold change.
- No framework / cache / hash / integrity-manifest体系 (Ponytail lite: reuse existing
  mother loader + V70 hierarchical_P/select_lambda + V72P1 run_decoder).
- No src/, experiments/, tools/, results/ modification; no overwrite of any existing output.

## Impact Scope

- NEW only: scripts/v72p2d1_parity_layout_diagnostic.py,
  scripts/test_v72p2d1_parity_layout_diagnostic.py,
  openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/四件 (proposal/design/tasks/specs/spec),
  docs/research_cycles/V72P2D1-PARITY/仅三文件 EXECUTION_PACKET.md/REVIEW_VERDICT.md/RESULT_SUMMARY.md.
- NEW output root only: comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/
  恰四文件 (manifest.json/results.json/table.csv/report.md). Test temp stays under
  workspace/独立目录, never touches production root.
- Affects no frozen baseline, no registry, no V72P1/V72P2 artifacts.

## P0 frozen (confirmed, must re-verify at freeze time via steps in design §1)

- Git gate: `git diff HEAD --quiet`空 (tracked clean) + `git diff --cached --quiet`空 (staged clean) +
  untracked字面allowlist仅含本change自身 (openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/,
  scripts/v72p2d1_parity_layout_diagnostic.py, scripts/test_v72p2d1_parity_layout_diagnostic.py,
  docs/research_cycles/V72P2D1-PARITY/EXECUTION_PACKET.md,REVIEW_VERDICT.md,RESULT_SUMMARY.md)
  及workspace/v72p2d1_* temp (若存在); 其余untracked即FAIL (B3字面逻辑见harness
  check_git_allowlist单测). Live库祖父豁免: freeze时已存在的本allowlist外预存untracked仅记录
  不计PASS, freeze-time净检出必须字面通过; 任何新增untracked即FAIL. Output dir
  comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/不存在.
- Mother 9036x10240 nnz49620 check{4:1,5:4594,6:4441} deg2 9035 四环1196 collision1194
  (B2重算值: get_mother_csr通用check-pair定义, A/B均为1196/1194; 旧8452/8170与该口径不符已修正, fake/真实同口径).
- V72P2 block0 baseline: 72ckpt / 334迭代 / LADDER_EXHAUSTED / 3100bit / 620sym / 9036+64+71
  (9036 syndrome + 64 tag + 71 CONTINUE = 9100 IR / 9171 public, full ladder exhausted).

## Minimal frozen delta

1. A=原始母图. B=仅9035个degree-2 parity列固定置换 rng=default_rng(20260902)
   col_map[1204:10239]=1204+permutation(9035), 信息列0..1203与列10239不动,
   indptr复制, indices映射 (indices_B = col_map[indices_A]), 保持边顺序,
   每臂自身CSR. seed 20260902为本诊断域分离专用 (与V72P1/V72P2/CAL seed不复用, 仅决定本col_map).
   Syndrome写死: b为10240固定Alice向量, s_A=H_A·b (mod2), s_B=H_B·b (mod2),
   每臂仅见本臂prefix + Bob prior, 禁混用.    机械验证7项 (design §2),
   预期 A1196/1194 B1196/1194 (通用check-pair四环/collision定义, fake/真实同口径;
   列置换为变量节点重标记, 图同构故环谱不变, 证明见design §2; 不一致即FAIL报告, 不手填).
   诊断假设仅检验布局置换是否移动阶梯结果/D5-D7等布局敏感动力学量, 不预设B改善环数.
2. 数据 session 20260123_1M_600k_0dB, registry v71_data_registry.json,
   CAL702..1725, 诊断块VAL1726-1729 non-fresh. CAL一次拟合A/B共享
   (本轮harness已实现: V72P2 load_registry/select_1m_session/read/validate复用 +
   fit_full_cal_model一次拟合, prior natural_log共享, VAL b→s_A=H_A·b/s_B=H_B·b).
   lambda预期221.22162910704503 (精确相等) CE预期7.135005172802673 (容差1e-12)
   (不一致报告实际值, 不手填). prior用natural_log, CE用log2.
   CAL坏/INVALID时A/B均记not_attempted(cal_failed), 零decoder调用 (继承V72P2语义, 见design §5).
3. run_decoder复用V72P1真CSR调用 (clip20 tol1e-6 float64, 每ckpt10次每臂720次, 72阶梯早停不变,
   A先B后, 独立零c2v臂内携带, 迭代=len(residuals), finite+syndrome+tag才accept,
   oracle事后, tag64bit; A须过compare_baseline_A门禁否则停B). 不改内核.
4. 预算每臂600s, 整命令1800s. A异常/超时/复现不一致则停B (B记not_attempted(gate_stopped_by_A)), 不跑B.
   CAL坏则双臂not_attempted(cal_failed), 零decoder调用.
5. 诊断D1-D8 wrapper标量 (design §6), 不记完整prior/矩阵/逐bit.
6. S0-S9矩阵 (tasks), 含S9回归 (V72P1 1秒计时已知失败, 不改阈值).

## Frozen CLI / budget / output清单

```
python scripts/v72p2d1_parity_layout_diagnostic.py \
  --registry v71_data_registry.json --session 20260123_1M_600k_0dB \
  --out comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab \
  --arm-budget-s 600 --global-budget-s 1800
```

- No other CLI flags change semantics; no tuning/budget-override flags.
- Budgets are soft deadlines checked before each publication; one checkpoint may overrun.
- 分阶段文件表 (明细见design §7): 运行中candidate仅在workspace/v72p2d1_<uuid>/ temp, 不计入最终计数,
  终端四文件落盘后删除temp (落盘失败才保留); 单一writer write_terminal_outputs (_write_four为同义别名,
  report含bit/sym统一);
  终端 (成功/gate停/CAL失败/M失败/真实异常) 在输出根恰四文件 manifest.json + results.json + table.csv + report.md
  (失败态同为恰四, 未跑臂记not_attempted + D空; P0拒绝时零文件, 目录不创建).
  No raw symbols / syndrome bytes / fitted matrix / per-bit arrays.
- 一次正式调用, 无rerun: 同--out第二次调用一律拒绝 (即使A已完成B被gate, 亦不续填B; 新out即新run, 属本冻结外).
- Tests: pytest -p no:cacheprovider scripts/test_v72p2d1_parity_layout_diagnostic.py
  (workspace独立temp, fake runner only, 不读真实registry, 不碰生产输出; fake缺decoder_fn必须raise禁回退真decoder).

Authoritative details in design.md / tasks.md / specs/spec.md. Any conflict → design.md为准,
但不得自行改变本proposal冻结数字.
