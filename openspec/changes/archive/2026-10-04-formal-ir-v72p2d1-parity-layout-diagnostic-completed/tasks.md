# V72P2D1 tasks — S0-S9 frozen matrix (EXECUTE_NOT_AUTHORIZED until R0)

Base: HEAD=ba0df2d3bea4147574e0b8224480f45c93505178 == live remote, branch formal-ir-v72p1-addendum-clean.
Scope: 只建OpenSpec四件 + scripts两文件 + docs/research_cycles/V72P2D1-PARITY/仅三文件
(EXECUTION_PACKET.md/REVIEW_VERDICT.md/RESULT_SUMMARY.md); 本轮即harness实现
(scripts/v72p2d1_parity_layout_diagnostic.py为冻结harness实现, 含真实路径;
scripts/test_...为focused fake测试).

- [ ] **S0 冻结/P0/编译**: Git门禁F1-F3 (`git diff HEAD --quiet`空 + `git diff --cached --quiet`空 +
  untracked字面allowlist本change自身六项 + workspace/v72p2d1_* temp, 见design §1;
  live库祖父豁免预存untracked仅记录不计PASS, freeze-time净检出必须字面通过; harness
  check_git_allowlist字面逻辑单测通过), 出目录
  comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/不存在,
  母图9036x10240 nnz49620 check{4:1,5:4594,6:4441} deg2 9035 四环1196 collision1194
  (B2重算值, 通用check-pair定义, fake/真实同口径),
  block0基线72/334/LADDER_EXHAUSTED/3100bit/620sym/9036+64+71可引用; py_compile通过.
  验收: P0复核记录 (F1-F6逐项) + compile PASS, 否则revise-required.
- [ ] **S1 列映射**: col_map[1204:10239]=1204+permutation(9035) rng=default_rng(20260902, 域分离专用),
  0..1203与10239不动, indptr复制, indices映射, 边顺序保持, 每臂独立CSR;
  M1-M7全PASS且A1196/1194 B1196/1194 (通用定义, 列置换图同构故环谱不变, 证明见design §2; 实测值报告, 不手填).
  验收: fake小图映射 (置换前后环数相等) + 真母图M1-M7脚本输出一致 (four_A=four_B=1196 coll_A=coll_B=1194).
- [ ] **S2 syndrome隔离**: 写死b为10240固定Alice向量, s_A=H_A·b, s_B=H_B·b (mod2), 每臂仅见本臂prefix + Bob prior,
  禁混用; D1/M6谓词为recompute(H_arm,b)==observed_arm. 验收: 交叉syndrome (H_A用于B) 测试必须FAIL/被拒绝;
  D1 mismatch_rows标量正确.
- [ ] **S3 prefix/阶梯**: 72 checkpoints不变, 每ckpt10次每臂720次, 迭代=len(residuals),
  warm-start臂内 (新边补零), 臂间零启动, A先B后. 验收: fake prefix切片/补零/718->2/0预算零调用测试.
- [ ] **S4 预算/门禁**: 每臂600s整命令1800s, 发布前检查, 单ckpt可超支; CAL坏/INVALID时双臂not_attempted(cal_failed)
  零decoder调用 (继承V72P2); A异常/超时/复现不一致则停B (B记not_attempted(gate_stopped_by_A)).
  同--out第二次调用一律拒绝, 不算rerun (不续填B). 验收: fake deadline停表 + CAL失败零调用 + A-gate-B逻辑测试; 真预算不改.
- [ ] **S5 诊断标量**: D1-D8 wrapper标量齐全 (D1重算/D2-D3 vsBob/D4 APP/D5 c2v/D6翻转/D7 deg2分组/D8 oracle),
  不含完整prior/矩阵/逐bit/逐边. 验收: 输出schema检查 + 全量禁项grep零命中.
- [ ] **S6 oracle隔离**: prior Bob-only (natural_log), CE log2; finite+syndrome+tag才accept;
  oracle事后, undetected隔离. 验收: oracle扰动不改accept/prior测试 + stale候选不可替代测试.
- [ ] **S7 输出**: 出根不存在才跑, 否则拒绝 (零文件); 分阶段文件表见design §7:
  运行中candidate仅workspace/v72p2d1_<uuid>/ temp不计入最终, 终端四文件落盘后删除temp
  (落盘失败才保留排障); 单一writer (write_terminal_outputs, _write_four为同义别名, report含bit/sym统一);
  终端 (成功/gate停/CAL失败/M失败/真实异常) 恰四文件
  manifest/results/table/report (失败态同为恰四, 未跑臂not_attempted + D空); 同--out第二次调用拒绝不续填.
  additive candidate指temp快照, 非输出根partial. 测试temp workspace独立 (pytest -p no:cacheprovider, fake only).
  fake注入缺decoder_fn必须raise禁回退真decoder (B4).
  验收: 已存在目录拒绝测试 + 四文件schema/行数 (results A/B两行, table两行) 检查 + 失败态四文件检查 +
  缺fake decoder raise测试 + 单writer/report统一检查 + temp清理检查.
- [ ] **S8 基线复现**: CAL一次拟合A/B共享, lambda221.22162910704503 (精确相等) CE7.135005172802673 (容差1e-12)
  为参照 (实测报告不手填); A必须复现block0基线 (72/334/LADDER_EXHAUSTED/3100/620/9036+64+71),
  否则停B记gate_stopped_by_A. 验收: A-vs-block0逐项diff (整数精确, CE 1e-12, 除wall外) 零超差.
- [ ] **S9 回归**: 现有V72P1回归全跑; 已知1秒计时失败保留为FAIL不改阈值不 claimed PASS,
  其余任一失败即阻断; 新focused tests全PASS且fake分支永不调用真实decoder/registry/生产输出
  (B4缺fake即raise; 真实路径已实现但fake测试永不调用, S9仅做赋值校验不跑真decoder).
  验收: 29-pass/1-known-fail基线 + 新测试全PASS记录.

## 全局禁止

改母图数字/seed/列范围、改CAL/VAL帧号、改clip/tol/dtype/10/720/72、手填lambda/CE/环数、
记全量prior/矩阵/逐bit、混用syndrome、oracle前置、改预算/CLI语义、覆盖输出、调参/rerun、
建框架/缓存/哈希体系、改src/experiments/tools/results、宣称FER/SKR/qualification/promotion.

## 验收 (本change冻结完成条件, 非执行验收)

四工件数字一致 (母图/seed20260902域分离/col_map/lambda精确/CE 1e-12/clip/tol/10/720/72/600/1800/
A1196/1194 B1196/1194同构(B2重算)/四文件单writer/D1-D8/S0-S9/syndrome写死b·s_A·s_B谓词),
CLI/预算/输出清单逐字一致, P0门禁F1-F6/基点/分支正确 (F3字面allowlist+祖父豁免),
docs三文件名 (EXECUTION_PACKET.md/REVIEW_VERDICT.md/RESULT_SUMMARY.md) 四件统一,
本轮即harness实现 (真实路径CAL一次拟合/VAL1726-1729双syndrome/共享prior/真CSR decoder/A门禁, 见design §3-§5).
