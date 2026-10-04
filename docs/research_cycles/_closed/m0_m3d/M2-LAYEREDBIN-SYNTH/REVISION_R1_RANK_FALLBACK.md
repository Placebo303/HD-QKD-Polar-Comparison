# M2-LAYEREDBIN-SYNTH 修订包 R1: rank 容忍 + numpy fallback (REVISION_R1_RANK_FALLBACK)

- 基线: `docs/research_cycles/M2-LAYEREDBIN-SYNTH/PACKET.md` (§§0–9)；分支 `formal-ir-v72p1-addendum-clean`，基线 HEAD `8e9c8526`；日期 **2026-09-24**；doc-only 起草，无 track gate（PACKET §2–§6 冻结值本文件不改，一字不动）。
- 性质: 科学输入变更。本修订包为 T2 12 臂授权执行依据；主线程明示接受指针: **BLANK（待签）**。

## R1 七条 (选项 A 重冻)

1. 支撑映射: 本地 `_h_from_triples` 由 triples 建二元支撑矩阵 (`H[r,c]=1`)；越界 fail-closed、空拒、重复塌缩置1、m_hint 须等 span。
2. coeff0 拒: `coeff!=0` 一律按支撑置 1 (2/512/1023 等 GF 标记按支撑处理，推翻旧 `==1` 冻结)；`coeff==0` 拒 (支撑空 → STOP)。
3. rank 域: 二元支撑 `GF(2)` 域 `rank∈{m_j-1,m_j}` GATED；仓内二元 rank helper (`codebook_v4.gf2_rank`) 计算支撑 H 的 `GF(2)` 秩；`rank<=m_j-2` 仍 STOP。
4. GF rank 忽略: PEG 返回不动，不读 PEG 的 `GF(1024)` rank 字段；rank 重算只读 triples/fc/girth。
5. twice: 支撑排序比较 (sorted `(r,c)` 支撑，coeff 归一化，零系数先拒)；不一致 → STOP-BLOCKED。
6. fc: 二元域声明 `fc==0` GATED (STOP-BLOCKED)；girth 仅记录不门控。
7. 返回语义: PEG 调用参数/种子/trials 字面量不动，PEG 返回字典不动；outcome 仍 13 键，双门语义 (success=exact+accepted+syndrome+toeplitz，undetected 独立) 不变。不重冻项沿用 T2-BLOCKER 冻结: LLR `p_assumed=0.02` / 综合征 / 盲段 stage_rows(A) / 会计映射 / Toeplitz 本地展开 / 异常 fail-closed (后端缺失或异常即 STOP，永不切 bit-flip)。

## rank∈{m-1,m} 容忍数学依据

- 冻结构造 `lam={2:1}` 列重恒 2 → 各列偶重 → 全行和 mod2==0 → 支撑 H 单维相关，秩 ≤ m_j-1；实测 m19→18、m20→19、m21→20 (`sum rows mod2==0 True`)。
- 故满秩门 `rank==m_j` 与 `lam={2:1}` 结构互斥 (Entry 2 BLOCKER)；容忍 `rank==m_j-1` 通过为列重 2 正则单维相关的最小放宽，`rank<=m_j-2` 仍 STOP。

## numpy fallback (assumed，非 ldpc)

- `BACKEND_ID` 精确字面量: `"numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)"` (`methods/binary_spa_numpy.py` + `resolve_spa_decode_fn` 缺席分支)；永不标 ldpc。
- fallback 结果为 assumed 先验 + 非 ldpc 后端，与真体数不可比、不可互换、不可合并；`backend_used` 仅经 log + metadata 侧车透出精确字面量，永不进 outcome dict (13 键以外零新增)。
- 本体 `spa_decode_production` STOP-BLOCKED 语义不动 (ldpc 缺席即 refuse，永不切 bit-flip)；对照口径以 `APPENDIX_SPA_NUMPY_FALLBACK_COMPARISON.md` 为准。

## 与冻结包关系

- Claim 固定句（逐字）：“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”
- PACKET §2–§6 冻结值 (F1 网格/种子/实例、F2 分配规则与 H 输入、F3 段表、F4 max_iter=300/streak=3 与 pins、F5 会计、F6 根政策) 本修订不改。
- 本修订仅重冻 R1 七条 + rank 容忍 + fallback 侧车口径；属科学输入变更，须主线程明示接受后方可作为执行依据；接受指针 **BLANK（待签）**。
