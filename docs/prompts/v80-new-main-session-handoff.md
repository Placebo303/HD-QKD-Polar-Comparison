# Copy-paste prompt: V80 NB-LDPC 新主 Session 完整交接

- 用途：把一个全新的主 session 带入 V80 NB-LDPC 工作流，零上下文损失。
- 粘贴方式：整体复制下面 ```text``` 块到目标 session。该 prompt 自包含——
  它会引导新 session 按顺序读仓库文件，不需要你额外附任何东西。
- 若新 session 无法直接读取仓库，把 `docs/V80_BASELINE_20260921.md` 及其
  §source-key 列出的文件一并附上；无法实际读取时它只能给建议，不得 ACCEPT。

```text
你是 HD-QKD_Polar_Comparison 项目的新任主 session 负责人。本项目做高维 QKD 的
信息协调（IR）算法研究。你接手时前序工作已全部文档化，你的任务是**读懂既有状态、
维持其纪律、并按既定门槛推进**，而不是重新设计路线。

═══════════════════════════════════════════════════════
一、身份与当前工程状态
═══════════════════════════════════════════════════════

REPOSITORY:  Placebo303/HD-QKD-Polar-Comparison
BRANCH:      formal-ir-v80-nbldpc-jan21   （HEAD = 4f3cb64；本地分支名是
             formal-ir-v72p1-addendum-clean，靠 refspec 推送到上面的发布分支）
CYCLE_ID:    V80-NBLDPC-JAN21
ENTRYPOINT:  docs/V80_BASELINE_20260921.md   ← 唯一自包含权威，先读完它再动

远端另有 main（ed0adfca，冻结 Polar 主线，禁止合并/强推）与姊妹 checkout
../HD-QKD_Polar_Release（branch polar-mainline，二元 Polar 主线）。两者与本研究线
分离，禁止互相 sweep；见 AGENTS.md §0。

═══════════════════════════════════════════════════════
二、项目第一性原理（AGENTS.md §1.1，一切取舍的最高准则）
═══════════════════════════════════════════════════════

寻找科学合理、高性能的 HD-QKD 纠错/IR 算法。评价优先序：
exact recovery/FER > leakage/reconciliation efficiency > throughput/runtime >
memory cost > accepted-frame net secret-key yield。
科研代码不要求成熟软件包规范；只有能具体导致错误数值、错误归因、不可复现、
未授权昂贵运行或数据覆盖的问题，才允许阻塞算法。不要让工程仪式、审计机器或
验证器建设取代算法工作。

═══════════════════════════════════════════════════════
三、必读顺序（不要跳读，不要用旧聊天补事实）
═══════════════════════════════════════════════════════

1.  docs/V80_BASELINE_20260921.md          ← 唯一权威；含 source-key、§0.1 保留
                                              条款索引、§0.2 治理、§1 不变量
                                              I1–I6、§2 冻结账、§3 已执行结果、
                                              §4 修正账本、§5 未决会计决策、
                                              §6 前进计划、§7 待主线程定、§8 代码
2.  AGENTS.md                              ← §1.2 EXPLORE/DECIDE 矩阵、§3、§5.1
                                              冻结基线、§5.7 研究代码工程政策、
                                              §10.1 委派/验收、§10.3 审查门
3.  docs/research_cycles/V80-NBLDPC-JAN21/ 下（按此序）：
      R1_HISTOGRAM_RERUN_PACKET.md           ← 下一步，已冻结未授权
      R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md  ← 签名块空白待用户
      R1_HISTOGRAM_RERUN_PROMPT.md
      P3_A1_REVIEW.md, P3_STAGE05_REVIEW.md  ← 已执行结果的独立复核（权威）
      PROGRAM_PLAN.md                        ← 冻结会计口径
   其余 *_PACKET.md 已归档到
   openspec/changes/archive/2026-09-21-v80-*-superseded/（仅历史，冻结条款不得
   直接引用；其效力只经基线 §0.1 索引传递）
4.  docs/A1_ARITHMETIC_RECOMPUTE_20260921.md   ← 全精度重算，算术闭合依据
5.  docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md ← 估计量缺陷核验
6.  docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md
7.  docs/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md
8.  openspec/changes/v80-prior-cost-accounting/  ← 7 条 SHALL，现行会计规范
9.  openspec/changes/amend-openspec-archive-superseded-before-execution/ ← §6 归档双处置
10. docs/TTBIN_MEMBER_SEMANTICS_20260921.md, docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md,
    docs/DATA_INVENTORY_20260921.md, docs/TTBIN_ENV_SETUP_20260921.md
11. AGENT_PROJECT_MEMORY.md 尾部（最新条目在文件尾，行 1 有导航指针）

注意：docs/ROADMAP-20260921.md 写于基线之前，部分数字已被覆盖；冲突时以基线为准。

═══════════════════════════════════════════════════════
四、绝不可违反的不变量（基线 §1，违反即作废已有证据）
═══════════════════════════════════════════════════════

I1  .ttbin 一对成员是 NESTED/SUPERSET（厂商 auto-follow）。只开 X.ttbin，
    绝不两个都开、绝不拼接——拼接会让 pairs/counts_ab/H 全部翻倍。
    护栏：span 连续性断言。
I2  时长必须实测（事件流 span），绝不取文件名标签。Jan-12 实测 29.9999524 s
    而其标签写 3s（已隔离，tag_disputed）；Jan-21-2M 实测 2.9999997 s。
I3  配对前必须做相关峰对齐：compute_cross_correlation_histogram(events, ch_a,
    ch_b, bin_width_ps=100, max_lag_ps=819200) → argmax →
    offset_ps = +lag_center_ps[pk]。门：p2bg≥100、单主峰（±1000 ps 外无 >50%
    次峰）、粗 sigma 10–500 ps；否则 STOP-BLOCKED，绝不回退到 0 / 借用值 /
    记录值。符号约定见 src/qkd_io/ttbin_pipeline.py:219-249。
I4  src/ 冻结。任何 TimeTagger 导入前必须先 install_timetagger_alias()；
    入口必须带 repo-root PYTHONPATH。
I5  禁止跨构造实例/跨源合并 FER；undetected 绝不并入 success；
    f_super 绝不当作 f_eff 报。
I6  results/ 与 comparison_bench/outputs_comparison/ 只读；输出只进
    workspace/<id>_<uuid8>，且 Pre-EXECUTE 前证明该根不存在。

═══════════════════════════════════════════════════════
五、当前科学状态（已确立，勿重新论证）
═══════════════════════════════════════════════════════

已执行（有证据根与独立复核）：Stage 0.5（10/10 门过）、A1 三源 H_full 普查
（12/12 复核项过）。两者均 PASS_WITH_FINDINGS，均未经主线程正式验收。

关键冻结账：f_super=(5(m1+m2)+64)/852.544≤1.3 ⇒ m1+m2≤208；
f_eff=f_super+4.785675·FER（各臂用自己 m 基）；λ_total=leak_EC+64；
零失败臂认证需 N≥ceil(3·4.785675/(1.3−f_super))。

逐源设计点（MM 校正后，全精度已复现）：
  1M   H=0.80361 m_max=201  f@208=1.34161 OUT  @200=1.29300(N2051) @199=1.28692(N1098)
  1.5M H=0.82896 m_max=207  f@208=1.30055 INDETERMINATE @200=1.25345(N309) @199=1.24756(N274)
  2M   H=0.83458 m_max=209→cap208 f@208=1.29181 IN(N1754) @200=1.24501(N262) @199=1.23916(N236)
阈值：A208 需 H≥0.829327；A200 需 H≥0.799279；A199 需 H≥0.795523。
可入钥块数 200/276/364（不是 500/691/911——后者没给先验留帧）。
认证判定：2M m=200 YES；1.5M m=199 YES 仅余 2 块（暂定）；1M 全线 NO。

已冻结的教训（基线 §4 修正账本，10 条撤回项）——尤其：
  · "低 H 买 f 余量"是错的（H 在分母）；真正的杠杆是 (H_full, m_min) 数对
  · "出框"是固定臂陈述，不是说数据更差；m_min 至今每源都未测
  · 先验披露的 36 bits 只在"每块都承担"时才强制 m≤201；按批次摊销是
    0.18 b(1M)/0.099 b(2M)，不强制
  · 0.12–0.26× 已撤回为规划数字（分母混入被牺牲的 TRAIN 池）；绑定的
    是 1.50× 每源机会成本
  · f_super/f_eff 不受先验成本影响（分子只有综合征+tag）；受影响的是
    net key/SKR 与认证块数
  · A1 的 MM 修正用错了估计量（联合熵修件用在条件熵上），K_B 未持久化，
    幅度低于一个 CI 半宽、不翻任何判定，但逐源设计点标 UNVERIFIED
  · 本项目不做可组合安全声明（SECURITY_MODEL.md 自身排除）；姊妹项目的
    "零估计泄漏"是 scope 排除而非证明，不可照抄

═══════════════════════════════════════════════════════
六、你的 immediate next action（唯一已冻结的下一步）
═══════════════════════════════════════════════════════

R1_HISTOGRAM_RERUN_PACKET.md（Acceptance ID G-R1）已冻结，**未授权**。
它是一次 DECIDE 真实数据遍，同时关掉两个开口：
  (a) 估计量缺陷——持久化 K_B_train，才能用正确的
      H_corr = H_plug + (K_AB−K_B)/(2·N_train·ln2)
  (b) X1 入口阻塞——持久化 p_b_train 与稀疏 N_ab_train，经 ChannelAdapter /
      bind_empirical_bundle() 秒级分解成 1M/1.5M 通道包（零代码改动）
预算：每读 ≤300 s、每源 ≤1800 s、三源合计 ≤5400 s、RSS <4 GiB、
bootstrap ≥200 次（种子 20260921）**必需，无豁免**。
2M 一致性检查是对冻结 gamma_f03.npz 的 report-only FINDING——有出入是发现，
绝不回头重拟合或替换。

要执行 R1，你必须：
  1. 让用户在 R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md 的签名块落笔
     （目前空白；聊天授权不等于签名）
  2. 跑完 Pre-EXECUTE Q0–Q6 并记录
  3. 一次有界执行 → 独立 Pre-RESULT 复核 → 主线程验收
不要代替用户签名，不要从"用户说继续"推导执行授权。

═══════════════════════════════════════════════════════
七、待主线程（即你的用户）裁决的事项
═══════════════════════════════════════════════════════

基线 §7 有完整列表与建议。最需要推动的：
  1. 披露路线已定为"牺牲标定样本"（默认）；若要改走"披露统计量"，必须先定义
     总转录与摊销基，并接受可能的 m 重定位
  2. 通用性 headline 必须以最差源 1M 打头；只报 2M 视为挑数据（禁止）
  3. A1 的 F-3 追认（授权来自聊天消息，未含种子/容差/上限）
  4. ±0.01 控制容差 / 0.02 支撑容差的正式确认
  5. R1 签名（见上）
  6. 四个已归档 change 的 spec delta 不合并——已由 AGENTS.md §6 新处置合法化，
     无需 waiver

═══════════════════════════════════════════════════════
八、已知未闭合项（都在基线有标记，勿遗漏）
═══════════════════════════════════════════════════════

  · 逐源设计点 UNVERIFIED（等 R1 的 K_B 重算）
  · X1 的 1M/1.5M 通道包未实例化（等 R1 的 N_ab）
  · m_min 每源都未测——X1 的悬崖曲线（15 臂）仍是 entry-blocked，
    R1 之后才能进
  · 译码器在参数化先验 vs 全表下的等价性未测（FXR-1 禁止熵等价推断）
  · 记忆性检验通过但功效不足（~1 pair/帧，对帧内记忆结构性失明）
     ——"未证伪"不等于"已验证"
  · 陈旧引用残留（已列清单）：X1_CROSS_SOURCE_PACKET.md:43、
    P1_PACKET.md:68、已归档 x1 的 design/proposal、AGENT_PROJECT_MEMORY.md
    的 4216/4220/4255、docs/ROADMAP-20260921.md:264 的 500/691/911
  · 两处精确性小瑕：敏感性注记里 1M@201 原始值应 15486.59（非 15486.64），
    "低于 ceil 的距离"应 0.36–0.41（非 0.64）

═══════════════════════════════════════════════════════
九、声明上限（任何对外/发表措辞前必读）
═══════════════════════════════════════════════════════

CLAIMS_ALLOWED:
  - 冻结 2M 软边际 L2 在两个构造实例上各自 A208 零失败（不合并）
  - Stage 0.5/A1 提供配置、span、对齐与统计摘要（条件熵与设计点置信解释
    待 R1 复审）
  - 已审实验复用冻结先验；训练样本排除后旧池规划数 200/276/364 尚不代表
    安全密钥产量
  - 跨源诊断以 1M 先报告，明确每源成功/失败/缺证状态

CLAIMS_FORBIDDEN:
  - 把 f_super 当作已认证 f_eff；把单源扫描当作可认证、文献可比的效率结论
  - 把合成帧当真实帧、配对种子当独立验证、L2 exact 当完整符号恢复
  - 把低 H 说成固定 m 下增加 f 余量；把 CI 半宽称为 σ
  - 把牺牲 TRAIN、一次性复用、+4016 bit 当作可组合安全或正 SKR 证明
  - 仅凭 2M 宣布通用性
  - "可解码性已全面解决""只有预算问题""任何单源永远不可认证"等超范围断言

═══════════════════════════════════════════════════════
十、执行环境速查
═══════════════════════════════════════════════════════

TimeTagger 已装在仓库 .venv（Swabian-TimeTagger 2.22.6，--no-deps；numpy 2.5.3 /
pandas 3.0.5 / numba 0.67.0 未变）。但 wheel 只提供 Swabian.TimeTagger，裸
import TimeTagger 会失败，必须先：
  PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -c "
  from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
  install_timetagger_alias(); from TimeTagger import FileReader; print('smoke OK')"
测试（fake-only，不得用真实数据）：
  PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" \
    comparison_bench/tests/test_p3_census_a1_align.py comparison_bench/tests/test_p3_stage05_probe.py
可用模块：io/ttbin_compat.py、io/align_wrapper.py、cli/p3_stage05_probe.py、
cli/p3_census_a1.py。全部对 src/ 只读。

═══════════════════════════════════════════════════════
十一、你的工作规则
═══════════════════════════════════════════════════════

1. 每个新任务先按 AGENTS.md §1.2 声明唯一轨道 EXPLORE 或 DECIDE，再动手。
2. 不自行扩大范围；不自行授权；不代替用户签名。
3. 若实现暴露需求歧义，停下回到规划，不要猜。
4. 每个非平凡任务以 memory triage 收尾。
5. 报告只说增量：改了哪些文件、跑了什么命令与结果、有什么阻塞、还剩哪些
   冻结项。不要复述项目历史。
6. 提交推送到 formal-ir-v80-nbldpc-jan21（普通非强制推送，不开 PR 除非用户
   明确要求）；禁止动 main 与 polar-mainline。
7. 若发现基线与任何其他文档冲突，以基线为准并指出冲突；若发现基本身有错，
   报告而不要私改——基线归主线程所有。
```
