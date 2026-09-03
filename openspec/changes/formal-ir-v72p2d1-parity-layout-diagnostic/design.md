# V72P2D1 frozen design

Base: HEAD=ba0df2d3bea4147574e0b8224480f45c93505178 == live remote, branch formal-ir-v72p1-addendum-clean.
Reuse (Ponytail lite): existing mother loader + V70 hierarchical_P/select_lambda +
V72P1 run_decoder. No new BP kernel, framework, cache, hash体系. No src/ change.

## 1. P0 / base

Freeze-time重验步骤 (按序执行, 任一步FAIL即revise-required, 不进入S1):
  F1 `git diff HEAD --quiet`为空 (tracked无修改).
  F2 `git diff --cached --quiet`为空 (staged无暂存).
  F3 `git status --porcelain`字面allowlist仅允许本change自身untracked
  (harness check_git_allowlist字面实现, 单测覆盖; prefix见harness ALLOWED_GIT_PREFIXES):
     `?? openspec/changes/formal-ir-v72p2d1-parity-layout-diagnostic/`,
     `?? scripts/v72p2d1_parity_layout_diagnostic.py`,
     `?? scripts/test_v72p2d1_parity_layout_diagnostic.py`,
     `?? docs/research_cycles/V72P2D1-PARITY/EXECUTION_PACKET.md`,
     `?? docs/research_cycles/V72P2D1-PARITY/REVIEW_VERDICT.md`,
     `?? docs/research_cycles/V72P2D1-PARITY/RESULT_SUMMARY.md`,
     `?? workspace/v72p2d1_*/` (若存在); 其余M/A/D/??即FAIL.
  祖父豁免 (B3): live库在冻结时已存在的allowlist外预存untracked仅记录不计PASS,
  freeze-time净检出必须字面通过; 任何新增untracked即FAIL. 测试live分支为描述性,
  字面逻辑由合成单测覆盖, 消除绕过冻结.
  F4 输出根 comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/不存在 (存在即拒绝, 不删除).
  F5 母图 9036x10240 nnz49620 check{4:1,5:4594,6:4441} deg2 9035 四环1196 collision1194
  (B2重算值, 通用check-pair定义; fake/真实同口径, 见§2).
  F6 V72P2 block0基线 72ckpt/334迭代/LADDER_EXHAUSTED/3100bit/620sym/9036+64+71可引用.
Any mismatch blocks implementation review (revise-required).

## 2. Mother A/B + 7项机械验证

- A = 原始母图 CSR (frozen).
- B construction (fixed, deterministic):
  col_map = arange(10240); rng=default_rng(20260902); # domain-separated: seed 20260902本诊断专用, 与V72P1/V72P2/CAL seed不复用, 仅决定本col_map
  col_map[1204:10239] = 1204 + permutation(9035).
  信息列0..1203与列10239不动. indptr_B = copy(indptr_A);
  indices_B = col_map[indices_A] (elementwise), 保持每行边顺序 (mapped order =
  original order mapped, 不重排). data全1. A/B各持自身CSR对象, 不共享可变indptr/indices.
- Check-degree {4:1,5:4594,6:4441} 与 deg2=9035 在B下不变 (列置换不改变行重/列重分布).
- Syndrome写死 (无开放语义): 设b为诊断块VAL1726-1729对应的10240固定Alice比特向量
  (1024 symbols×10bit展开, LSB first, 顺序固定); s_A = H_A·b (mod2, 9036行),
  s_B = H_B·b (mod2, 9036行). B臂用s_B, 禁用s_A混入B臂, 禁用s_B回代A臂.
  Decoder每臂输入仅为本臂当前syndrome prefix (rows 0..ckpt-1 of s_arm) + Bob prior (CAL共享);
  不见对臂syndrome, 不见Alice b/s全量.
- 同构不变性证明 (通用四环定义): 列置换π仅为变量节点重标记 v→π(v), 校验节点不动;
  边 (c,v)∈E_A iff (c,π(v))∈E_B, 故Tanner图 (C∪V,E)同构. 四环为长度4闭迹 {c1-v1-c2-v2-c1},
  在π下双射对应, 计数不变; collision (同组合定义下共享变量对的校验对计数)同理不变.
  因此M7预期 A1196/1194 B1196/1194 (B2重算修正). 若按布局敏感口径 (如按列序加权的局部环密度)会得不同数,
  本轮不采用该口径; 诊断假设改为检验置换是否移动阶梯结果/D5残差迭代数/D6翻转数/D7分组误差等
  布局敏感动力学量, 不预设B改善环数.
- 7项机械验证 (S1, 全为FAIL即停; fake分支verify_M1_M7_fake与真实verify_M1_M7共用
  count_four_cycles/count_collisions, 口径一致声明):
  M1 shape/nnz: B为9036x10240 nnz49620, 与A一致.
  M2 check-degree分布 {4:1,5:4594,6:4441} 与A一致.
  M3 variable-degree分布一致, deg2=9035; col 0..1203与10239为原列 (逐列nnz/行集相等).
  M4 col_map双射: [1204:10239]为1204..10238全排列, seed=20260902可重现, 信息列恒等.
  M5 indptr逐元相等; indices_B == col_map[indices_A]; 每行边顺序保持.
  M6 CSR独立 + syndrome隔离: A/B indptr/indices为独立对象 (is-not共享);
     谓词为 recompute(H_A,b)==observed_A 且 recompute(H_B,b)==observed_B (逐bit mod2重算),
     任一臂mismatch即FAIL并阻断decoder.
  M7 四环/collision重算 (通用check-pair定义, fake/真实同口径, 共用
  count_four_cycles/count_collisions): A预期1196/1194, B预期1196/1194
  (B2重算值: get_mother_csr 9036x10240实测four_A=four_B=1196 coll_A=coll_B=1194;
  旧8452/8170与该口径不符已修正, 重算命令与值见本条, 不手填). 实际重算值写入results,
  不一致即FAIL并阻断执行 (先于decoder).
- Prefix/CSR数值: CSR284248 (indptr 36148 + indices 198480 + data 49620), 与V72P1一致.

## 3. 数据与先验 (CAL一次拟合, A/B共享)

- Session 20260123_1M_600k_0dB, registry v71_data_registry.json.
  CAL frame 702..1725 (每frame 256 pairs, 有序distinct, symbols 0..1023).
  诊断块 VAL1726-1729 (4 frames = 1 block, 即V72P2 block0槽位), non-fresh, 描述性复用.
  无替换、无跳号、无TEST. CAL/SMOKE不交叠.
- V70 select_lambda(a_cal,b_cal): 原有4 folds + 30点 1e-2..1e4网格, 全CAL refit.
  hierarchical_P全CAL拟合 C[b,a]/N_b/P_global. Freeze lambda后供A/B共享.
  预期 lambda=221.22162910704503 (精确相等, repr/bitwise) , CE=7.135005172802673 (容差1e-12, |实测-预期|<=1e-12) (回归参照).
  若实测不一致: 报告实际值, 不手填预期, 并视为复现不一致 (触发停B门禁, 见§5).
- prior_logp = natural_log(max(P,1e-300)行归一化后)[bob_symbols,:], Bob-only, 无Alice.
  CE = log2口径. prior/矩阵完整内容不落盘, 仅记lambda/CE/floor/seed/frame IDs/row counts.

## 4. Decoder与阶梯 (复用V72P1, 不改内核)

- FrozenMotherSpec 9字段 / SoftJointConfig 8字段 / 11工作数组 / five-equation dataflow
  与V72P1完全一致. run_decoder签名/字典不变.
- clip20 tol1e-6 float64. 每ckpt max 10次, 每臂 max 720次 (=len(residuals)累计).
  72 checkpoints {160,288,...,8992,9032,9036}早停不变: 仅检查当前candidate,
  不扫stale. 每臂独立零c2v启动, 臂内warm-start携带 (新边补零), 臂间不携带.
  顺序 A先B后 (串行).
- Alice: 全syndrome (frozen CSR, LSB first) + sha256(bits.tobytes()).digest()[:8] tag64.
  Decoder输入仅当前syndrome prefix + Bob prior.
- protocol_accepted = finite AND 当前syndrome一致 AND 当前tag一致. 收敛残差不作为accept条件.
  verified_exact_success = accepted AND oracle_exact; undetected = accepted AND NOT exact,
  永不并入success. ladder_exhausted / numeric_failure / decoder_error /
  budget_exhausted / invalid_input / not_attempted语义与V72P2一致.
- oracle (Alice equality / bit-symbol errors) 全部事后, 不影响prior/停止/accept.
- 披露计费与V72P2一致: 首160+tag64, 后续每CONTINUE 1bit + 增量syndrome rows;
  尾40/4; 已发布永不回滚; leak_IR=syndrome+tag, total_public=leak_IR+control;
  f_model_relative用CAL-CV CE作分母 (含失败attempts).

## 5. 预算与门禁

- 每臂600s, 整命令1800s (含CAL拟合+A+B+诊断+落盘). checkpoint发布前检查time/iter预算;
  单个checkpoint可超支, 超支后停在下一发布点前. wall实测记录, 不编造RSS/peak.
- CAL门禁 (继承V72P2 Bad-CAL-stops-without-decoder): 若CAL帧缺失/重复/非distinct/symbol越界/行数不符,
  或hierarchical_P/select_lambda返回非finite lambda/CE, 则A/B均记not_attempted (cal_failed),
  零decoder调用 (D1-D8记空, S8不执行A复现比较), 仍落盘终端恰四文件 (见§7失败态行).
- A门禁B: A出现 numeric/decoder_error, arm超时, 或A复现与V72P2 block0基线不一致
  (72ckpt/334迭代/LADDER_EXHAUSTED/3100bit/620sym/9036+64+71; 含lambda精确相等/CE 1e-12, 见§3), 则停B,
  B记not_attempted (gate_stopped_by_A), 不跑B. B超时/异常仅停B.
- 一次正式调用, 无rerun/tuning: 同--out第二次调用一律拒绝 (即使A已完成B被gate, 亦不续填B;
  新out即新run, 属本冻结外). 运行中candidate仅写workspace temp (见§7), 不覆盖已存在run目录.

## 6. 诊断D1-D8 (wrapper标量, 不记完整prior/矩阵/逐bit)

每臂每ckpt仅记标量; 最终每臂一行 + 全局对比行. 禁止完整prior_logp / CSR矩阵 /
逐bit LLR / per-edge消息落盘.

- D1 syndrome重算: 谓词 recompute(H_arm,b)==observed_arm (s_arm=H_arm·b mod2逐bit重算),
  记 match_flag + mismatch_rows. mismatch即本臂FAIL (M6联动, 阻断decoder).
- D2 vsBob符号: hard_symbols vs Bob symbols, 记 sym_errors (0..1024), sym_match.
- D3 vsBob比特: hard_bits vs Bob bits (Bob symbols按sym*10+bit展开), 记 bit_errors.
- D4 APP: app_llr finite_flag + max_abs + mean (3标量).
- D5 c2v: c2v finite_flag + max_abs + final_residual + iterations_used.
- D6 f2b/sum翻转: factor_to_bit finite_flag + n_flip_f2b (相对首ckpt符号翻转数) +
  n_flip_app. 仅计数, 不记向量.
- D7 deg2分组: deg2变量组 vs 非deg2组, 各记 bit_errors_deg2 / bit_errors_rest +
  mean_abs_app_deg2 / mean_abs_app_rest (4标量).
- D8 Alice错误/oracle: Alice-vs-Bob sym/bit errors (真误差), oracle_exact_flag,
  undetected_flag. Oracle事后, 隔离见§4.

## 7. 文件/CLI/输出 (冻结)

- 新建仅: scripts/v72p2d1_parity_layout_diagnostic.py (冻结harness实现, 本轮即实现真实路径,
  复用母图loader + V70 hierarchical_P/select_lambda (经V72P2 fit_full_cal_model) + V72P1 run_decoder真CSR调用),
  scripts/test_v72p2d1_parity_layout_diagnostic.py (focused tests, fake runner),
  本change四件, docs/research_cycles/V72P2D1-PARITY/仅三文件
  (EXECUTION_PACKET.md / REVIEW_VERDICT.md / RESULT_SUMMARY.md, 无多余文件).
- CLI冻结 (见proposal): --registry v71_data_registry.json --session 20260123_1M_600k_0dB
  --out comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab
  --arm-budget-s 600 --global-budget-s 1800. 无调参/覆盖/预算改写旗标.
- 分阶段文件表:
  | 阶段 | 位置 | 文件 | 计入最终恰四? |
  | P0拒绝 | 输出根不创建 | 零文件 | 否 (目录不存在) |
  | 运行中 | workspace/v72p2d1_<uuid>/ temp | candidate快照 (per-arm partial, 任意名) | 否 (终端落盘后删除, 落盘失败才保留) |
  | 终端成功 | 输出根 | manifest.json/results.json/table.csv/report.md | 是 (恰四, 单一writer) |
  | 终端A-gate-B | 输出根 | 同上恰四 (B行not_attempted(gate_stopped_by_A)+D空) | 是 |
  | 终端CAL失败 | 输出根 | 同上恰四 (双臂not_attempted(cal_failed)+D空, 零decoder调用) | 是 |
  | 终端M1-M7失败 | 输出根 | 同上恰四 (已测M值+未跑臂not_attempted(m_failed)+D空) | 是 |
  | 终端真实异常 | 输出根 | 同上恰四 (fatal_error + 已有M/臂状态 + D空/已有) | 是 |
  manifest.json (code/plan SHA, params, data身份/角色, command),
  results.json (A/B两行 + D1-D8标量 + M1-M7值 + 轻量per-ckpt标量log),
  table.csv (A/B两行), report.md (描述性总结, 含与block0基线对比; 单一writer内容统一, 含bit/sym).
  _write_four为write_terminal_outputs同义别名, 不再双writer分叉.
  无raw symbols/syndrome bytes/拟合矩阵. 输出根一旦创建永不覆盖; 同--out第二次调用一律拒绝,
  不算rerun语义 (不续填B, 见§5).
- 测试: pytest -p no:cacheprovider scripts/test_...; temp根 workspace/v72p2d1_<uuid>/独立;
  fake测试永不读真实registry/真实decoder默认路径/生产输出; fake注入缺decoder_fn必须raise
  禁回退真decoder (B4).

## 8. S0-S9总览 (明细见tasks.md)

S0冻结/编译/母图+P0(F1-F6, F3字面allowlist+祖父豁免); S1列映射+M1-M7 (B1196/1194同构, B2重算); S2 syndrome隔离+D1 (s_arm=H_arm·b谓词); S3 prefix/72阶梯/10/720;
S4预算/门禁 (CAL失败双停 + A-gate-B + 无rerun); S5 D1-D8标量/禁全量; S6 oracle隔离; S7输出恰四文件 (分阶段表);
S8基线复现 (A vs block0; lambda精确/CE 1e-12); S9回归 (V72P1 1秒计时已知失败, 不改阈值, 其它失败即阻断).
