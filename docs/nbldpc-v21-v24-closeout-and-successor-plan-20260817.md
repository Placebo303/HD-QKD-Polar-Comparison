# NBLDPC V21→V23 收口与 V24 后继计划（2026-08-17）

## 1. 当前状态与本轮权限

当前状态：`NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`。

本轮只授权规划与文档修正：不改代码、不运行 DE/FER、不产生科学输出、
不移动 archive、不 push。旧的全局“route unreachable”判断已 superseded；
现有结论只覆盖 tested candidates/current V22b single-edge kernel。

## 2. 收口总顺序

### CL01 — 科学结论修正

依赖：V20 audit、V21 summary、V22/V23 源码与证据只读审查。

输出：统一当前状态为 `NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`；明确
V23 未实现 true protograph/MET；旧全局不可达结论标 superseded。

验收：CURRENT_TASK、HANDOFF、MEMORY、review summary、decision-log 和
V21/V22/V23 change 文档一致。停止门：任何文档仍把 summary-only 证据写成
独立验证，或把 aggregate `lambda/rho` 写成 MET PASS/FAIL，则不得进入归档审查。

### CL02 — V21 未完成项分类

目标状态：`CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE`。

必须保留 S0/S1/S2：24/64、28/64、28/64，FER 0.625、0.5625、0.5625。
P0/P1 标 `CANCELLED_NOT_PRE_FROZEN`；runtime Alice-injection verifier 和 V01
标 `NOT_RUN_UNVERIFIED`；AST 测试仅是静态工程检查。

输出：V21 proposal/design/tasks 的修正状态。停止门：不得补跑缺失验证，
不得把执行后记录倒写成预注册。

### CL03 — V22 未完成项分类

目标状态：`CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE`。

结论只限已测候选/当前内核。finite I03 为 `CANCELLED_BY_DE_GATE`，finite
Bob-only E02 与 V01 为 `NOT_RUN`。

输出：V22 proposal/design/tasks 的修正状态。停止门：不得启动有限构造或
把低-QSC 控制结果当作目标 V17 信道 PASS。

### CL04 — V23 语义与证据覆盖修正

目标状态：`CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE`。

实现语义固定为 base-matrix-derived aggregate `lambda/rho` -> V22b；无拓扑/
edge-type state。I03 true MET `NOT_IMPLEMENTED`，V01 `NOT_RUN`。raw scan 只有
3 个矩阵；consolidated summary 的额外点缺少独立 raw/verify package。

输出：V23 proposal/design/tasks 的修正状态。停止门：不得称“protograph/MET
DE failed”或声称穷尽扫描。

### CL05 — 独立只读 closeout review

依赖：CL01–CL04 全部完成。

审查矩阵：

- CR01：状态字符串跨文档一致；
- CR02：V21 数值与验证缺口一致；
- CR03：V22 tested-candidate/current-kernel 限定和取消项一致；
- CR04：V23 实现语义、3-matrix raw coverage、summary limitation 一致；
- CR05：冻结源码/输出零修改，本轮无执行；
- CR06：所有未完成项分类为 cancelled/not-run/unverified，而非伪完成；
- CR07：V24 与收口路线之间无隐式执行或归档授权。

输出：独立 reviewer 的 ACCEPT 或具体 blockers。任一 blocker 未清零则停止。

结果（2026-08-17）：ACCEPT。CL01–CL04 与 CR01–CR07 通过；V24 P06 在两轮
blocker 修正后由第三次独立只读复审 ACCEPT。实际归档仍等待 CL06 用户授权。

### CL06 — 用户授权后的实际归档

依赖：CL05 ACCEPT + 用户明确 archive 授权。

顺序固定：V21 -> V22 -> V23。每一步移动后只做结构/链接/状态只读检查；
一旦发现路径冲突、未保存改动或结论漂移立即停止。本轮不执行 CL06。

## 3. V24 后继 change

OpenSpec 四件套：

- `openspec/changes/formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization/proposal.md`
- `openspec/changes/formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization/design.md`
- `openspec/changes/formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization/tasks.md`
- `openspec/changes/formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization/specs/formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization/spec.md`

V24 状态为 `FROZEN_PENDING_USER_AUTHORIZATION`（P01–P06 完成，P07 待用户）。
它只做 q=1024、冻结 V17 structured channel、
`R>=0.9375`、`f_total<=1.3` 的 bounded single-edge `lambda/rho` optimization。

### P — 规划冻结

验收 ID：P01–P07。冻结 accepted V8 trace 的只读验证、channel、H/rate/
leakage 公式、indexed proposal generator、degree/support/search 边界、预算、
stage-generic ranking、holdout、证据与资源门。独立 freeze review 已 ACCEPT；
P01–P06 已完成，下一边界是 P07 用户 execution authorization。

依赖：CL01–CL04 文档科学边界完成；不依赖实际 archive。

输出：冻结 OpenSpec + reviewer decision。停止门：任何参数不完整、V23 被
误写成 MET、或 finite/MET fallback 混入 V24，均不得实施。

### M0 — 机制、信道与记账门

M0 只读验证已接受的 exactly-once V8 corrected trace，不重新执行或替代 V8：

`openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_reproduction_trace_corrected.json`

冻结字段：q4/R0.75；published lambda exponents
`{1:0.107,3:0.245,6:0.192,9:0.034,18:0.207,25:0.161,27:0.049}`，对应 degrees
`{2:0.107,4:0.245,7:0.192,10:0.034,19:0.207,26:0.161,28:0.049}`；corrected
harmonic-exact rho `{24:.662342394447661,25:.33765760555233904}`；
dc_mean 24.32858932876873、integral_lambda 0.1644156159629844、
integral_rho 0.0411039039907461、reconstructed rate .75；
`n_samples=100000`、`max_iter=150`、seed 2026080418、p bounds 0.01/0.12、
`p_tol=0.0025`、strict entropy `<0.01` 连续 20 iterations、DET 0.069、容差
0.012、tolerance arithmetic
`0.0005+0.00125+0.005+0.005=0.01175<=0.012`、accepted proxy
0.06242187500000001、delta 0.006578124999999997、PASS。
同时冻结 V17 model `H=0.5499550439219351 bits/symbol` 与 rate/f 公式。

输出：fresh additive run manifest、accepted-trace read-only validation、M0
verifier report。停止门：任一失败 -> `mechanism_unverified`，M1/M2 禁止执行。
V24 不安排新的 QSC threshold regression。可选 T3 只读验证现有 V22b
iter30/n200 artifact，不执行 V8/V22b DE、不进入 M1 ranking，也不得改变 V8
evidence。

### M1 — 有界开发优化

single-edge lambda/rho 每侧允许 1–8 个非零 degree；variable degree<=64，
check degree<=512；rate search band `[0.9375,0.94140625]`。最多 512 个 unique
valid candidates、8192 attempts。attempt k 只建一个
`rng=default_rng(SeedSequence([24000,k]))`。冻结 degree arrays：lambda
`np.arange(2,65,dtype=np.int64)`、rho
`np.arange(2,513,dtype=np.int64)`。同一 rng 严格先 lambda 后 rho；每侧严格按
`s=int(rng.integers(1,9))` ->
`degrees=np.sort(rng.choice(frozen_degree_array,size=s,replace=False))` ->
`probabilities=np.full(s,1.0/s,dtype=np.float64)` ->
`counts=rng.multinomial(64-s,probabilities)+1` 消费。禁止 permutation、替代
choice API、改调用顺序或额外 RNG call。canonical key 为两侧升序
`degree:count` 串，candidate_id 为首次 attempt k；reject/duplicate 不影响后续。
V22/V23 baselines 不进入 M1/ranking，只能作独立 T3 control。

screen seeds 24001/2，refine seeds 24003/4/5。两阶段统一 ranking：
`(converged_count desc, worst_final_entropy asc, mean_final_entropy asc,
candidate_id asc)`；error/nonfinite 视为 non-converged 且 entropy=+inf。
`N_refine=min(8,N_valid)`、`N_finalist=min(4,N_refined)`；Nvalid=0 ->
`mechanism_unverified`。N_valid 只表示 DE 前 profile-valid 且纳入前 512 的
unique candidates，只检查 lambda/rho、degree、support、rate、f。DE error 或
nonfinite 仍消耗 valid-evaluation slot，按 nonconverged/+inf 排名，不改变
profile validity 或 N_valid。

输出：完整 proposal ledger、screen/refine records、pre-holdout finalist
declaration。停止门：禁止扩预算、换 seed、改 threshold、用 holdout 调参。

资源门：单次用户授权的 M0–M2 scientific invocation 内，只累计已完成 DE
call 的 `time.perf_counter` 时长；每个 call 完成立即追加 record，然后优先
检查全部冻结 evaluations 是否完成。若已完成，即使累计>=24 h 也正常计算
PASS/FAIL；仅当仍有必需 evaluation 未完成且累计>=24 h 时，才标
`resource_blocked` 且不启动下一 call。已在运行的 call 可完成并须先记录。
不设置 RSS 硬门；禁止缩预算或重跑。

### M2 — 独立 holdout

全部 `N_finalist=min(4,N_refined)` 使用不重叠 seeds 24101–24105，
`n_samples=2000`、`max_iter=200`。
候选必须在全部五个 seed 上 final base-q entropy `<=0.01` 才 PASS。

输出：全部 holdout records、gate decision、read-only semantic verification。
停止门：单 seed 失败即该候选失败；禁止平均、多数表决、替换、调参、重跑。

### M3 — 收尾

PASS 最高只能写 `ready_to_propose_finite_code_change`；FAIL 写
`single_edge_bounded_optimization_failed`；resource/mechanism blocker 不得
改写成科学 FAIL。同步 decision-log/handoff/memory，独立验收后再由用户选择
是否 archive V24。

## 4. V24 验收矩阵

- VA01：accepted V8 corrected trace 与 V17 channel/accounting 只读精确验证，
  无 V8 rerun；
- VA02：profile validity 仅由 lambda/rho/degree/support/rate/f 重算；DE
  error/nonfinite 不改变 N_valid 且消耗 evaluation slot；
- VA03：indexed SeedSequence generator、512/8192 预算、stage-generic ranking、
  min(8,Nvalid)/min(4,Nrefined) 无漂移；
- VA04：development 与 holdout seeds 严格不相交；
- VA05：所有 finalist 的五个 holdout seed 齐全；
- VA06：PASS/FAIL 从原始 records 可独立重建；
- VA07：additive/no-overwrite，invalid/failed/partial evidence 全保留；
- VA08：代码冻结区和旧输出零修改；
- VA09：无 finite code、FER、qualification、promotion 或 MET claim；
- VA10：engineering pass、DE pass、finite success、promotion 四层分离。
- VA11：completed-DE-call perf-counter 24 h 门与“完成优先于超时”顺序可重建，
  无 RSS 硬门。

## 5. 授权边界与后继

当前只完成 planning/docs 与 P06 独立 freeze review。下一动作是由用户决定
是否授予 P07 implementation + scientific execution authorization。DE PASS 前禁止 finite code/FER。
true MET 只能在 V24 FAIL 后另开 change，并再次取得用户明确授权。调整 q、
channel decomposition 或 f target 同样属于新的用户决策，不是 V24 fallback。
