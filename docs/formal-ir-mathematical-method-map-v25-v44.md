# Formal-IR 数学方法图谱 V25–V44

> 仓库 `Placebo303/HD-QKD-Polar-pipeline` 分支 `formal-ir-mainline` HEAD `c51a21c0` 归纳文档。
> 只读归纳，不实现、不运行 decoder、不创建正式 outputs。
> 依据：`docs/nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md`、
> `docs/nbldpc-v32-main-review-verdict-20260822.md`、`docs/nbldpc-v35-successor-plan-20260824.md`、
> `openspec/changes/formal-ir-v38r1`–`v44` proposal/design/spec（含计画冻结定义）、
> `v42_summary.json` / `v43_summary.json` / `v43_records.json`。
> 语言：中文为主，公式与符号英文保留。

---

## 1. 基础概率模型

### 1.1 原始符号与经验计数

- Alice 符号：$A \in \mathcal{A}=\{0,\dots,1023\}$，200 ps / 1024-bin frame 内原始时间戳符号。$|\mathcal{A}|=1024=2^{10}$。
- Bob 观测：$B \in \mathcal{B}=\{0,\dots,1023\}$，完整 10-bit 符号。$B$ 是解码器唯一允许的信道输入，不得以 $U_{2,B}$ 等低维分量替代。
- 经验联合计数（V25 TRAIN，来源 `channel_counts.npz`，经 `load_v25_channel_counts()` 只读加载）：

$$C(a,b)=\#\{(A=a,B=b)\},\quad a\in\mathcal{A},\, b\in\mathcal{B}$$

对应经验联合分布 $\hat P(A=a,B=b)=C(a,b)/N$，$N=\sum_{a,b}C(a,b)$。所有条件分布由此导出；若需平滑，须在 OpenSpec 预注册 floor/backoff，事后不得调整。

### 1.2 F03 分解

固定可逆标签分解（natural labeling $L_N(A)=A$，本文以 $A$ 本身计）：

$$A = 32\,U_1 + U_2,\quad U_1\in\{0,\dots,31\},\;U_2\in\{0,\dots,31\}$$

$$U_1=\lfloor A/32\rfloor\;( \mathrm{GF}(32)\ \text{高5位}),\quad U_2=A\bmod 32\;(\mathrm{GF}(32)\ \text{低5位})$$

记 $\mathcal{U}=\{0,\dots,31\}$，$|\mathcal{U}|=32$。同样对 $B$ 有确定性分解 $B=32\,U_{1,B}+U_{2,B}$，但**解码器不得以 $U_{i,B}$ 代替 $B$** 调用后验。

F03 为编码分层，可逆：$(U_1,U_2)\leftrightarrow A$ 双射。不改变物理 200 ps/1024-bin 字母表。

### 1.3 完整 Bob 后验（唯一合法调用）

对源固定的计数矩阵 $C$，冻结先验函数（`get_conditional_posterior_l2`）：

$$P(U_2=u_2\mid B=b,\,U_1=u_1)=\frac{C(u_1\!\cdot\!32+u_2,\,b)}{\sum_{u_2'} C(u_1\!\cdot\!32+u_2',\,b)},\quad\text{分母 floor }10^{-15}$$

$$P(U_1=u_1\mid B=b)=\frac{\sum_{u_2} C(u_1\!\cdot\!32+u_2,\,b)}{\sum_{u_1',u_2'} C(u_1'\!\cdot\!32+u_2',\,b)}$$

$$P(U_1=u_1,U_2=u_2\mid B=b)=\frac{C(u_1\!\cdot\!32+u_2,\,b)}{\sum_{u_1',u_2'} C(u_1'\!\cdot\!32+u_2',\,b)}$$

三式满足 $P(U_1,U_2\mid B)=P(U_1\mid B)P(U_2\mid B,U_1)$。

**绑定不变式（V38P0 根因）**：`get_conditional_posterior_l2(counts, bob, u1)` 的第二参数必须为完整 $B\in\{0,\dots,1023\}$ 数组，第三参数为 $U_1$ 选择子。传入 $U_{2,B}\in\{0,\dots,31\}$ 为非法绑定，V38P0 45 条记录因此全部作废。后续所有哨兵 `bob_gt_31` / `captured_equals_bob` / `corrected_equals_direct` / `corrected_differs_u2bob` 均为此不变式的 decoder-free 证明。

所有后验仅依赖公共数据 $(C,B)$ 与公共构造的 $U_1$ 选择子；$u_{1,\text{Alice}}$ / $u_{2,\text{Alice}}$ 仅用于 syndrome 与 $exact_{L2}$ 判定，永不进入先验。

---

## 2. 信息论分解

### 2.1 Chain rule（F03，两层）

在条件公共元数据 $Z$（source/file/block 配置，公共已知）下：

$$H(A\mid B,Z)=H(U_1\mid B,Z)+H(U_2\mid U_1,B,Z)$$

记

$$H_1:=H(U_1\mid B,Z),\qquad H_2:=H(U_2\mid U_1,B,Z)$$

对 F03：$a_1=a_2=5$ bits。$H_1+H_2$ 在同一计数器/同一估计器下与 $H(A\mid B,Z)$ 在浮点误差内闭合（V25 M3-6 校验）。

参考码率（$f=1.3$ 假设，仅信息论参考，$a_i=5$ bits，$N=1024$ 符号，$H_i$ 为每符号条件熵 bits/symbol）：

$$R_{i,\text{ref}}=1-\frac{1.3\,H_i}{a_i},\quad m_i \approx \left\lceil\frac{f\,N\,H_i}{5}\right\rceil,\quad \text{泄漏 } leak_i =5\,m_i \approx f\,N\,H_i\ \text{bits}$$

应用于 $U_2$ 层时，$m_2$ 对应 $H_2$，**总泄漏必须包含全部层 syndrome**，不得只计高位；总效率 $f_{\text{total}} = 5(m_1+m_2) / \{N\,[H(U_1\mid B)+H(U_2\mid U_1,B)]\} = 5(m_1+m_2)/[N(H_1+H_2)]$。

### 2.2 四类信息的严格区分

| 信息类 | 符号 | 来源 | 是否计泄漏 | 是否可用于解码下一层 |
|---|---|---|---|---|
| 信道信息 | $P(U_i\mid B,Z,\cdot)$ | $C$ 与公共 $B$ | 否（$C$ 为公共先验，零额外通信） | 是，构造先验 |
| 校验约束 | $s_i=H_i\,x_i$ | Alice 侧 syndrome，公开 | 是，$m_i a_i$ bits | 是，$H_i,s_i$ 必入译码器 |
| Decoder message | $M_{H,s\to i}(u)$ | Tanner 图上迭代外信息 | 否（本地计算） | 是，仅当 $H,s$ 对应层真实存在 |
| Oracle 信息 | $U_1^{\text{true}}=u_{1,\text{Alice}}$ | Alice 真值 | 禁止入先验（仅 syndrome/exact 判定可用） | 否，真实协议不可得 |

混淆四者的典型错误：把 oracle $P(U_2\mid B,U_1^{\text{true}})$ 的性能归为“非 oracle 已达成”；把硬判 $\hat U_1(B)$ 产生的 $P(U_2\mid B,\hat U_1)$ 误作 soft；把无码估计 $q(U_1\mid B)$ 误作“已利用 $H_1,s_1$”。

---

## 3. 历史方法的统一表达

统一记一帧位置 $i$ 的 Bob 观测 $b_i$，经验计数 $C$ 固定。记

$$p_i(u_1):=P(U_1=u_1\mid B=b_i)=\frac{\sum_{u_2}C(u_1\! \cdot\!32+u_2,b_i)}{\sum_{u_1',u_2'}C(\cdots)}$$

$$p_i(u_2\mid u_1):=P(U_2=u_2\mid B=b_i,U_1=u_1)=\frac{C(u_1\! \cdot\!32+u_2,b_i)}{\sum_{u_2'}C(u_1\! \cdot\!32+u_2',b_i)}$$

$$p_i(u_2):=P(U_2=u_2\mid B=b_i)=\sum_{u_1}p_i(u_1)\,p_i(u_2\mid u_1)$$

所有方法均为对 $U_2$ 层提供给 $\text{decode\_row\_layered\_fftqspa}(H_{L2},\, \text{prior},\, s_{L2})$ 的 1024×32 先验矩阵的构造方式。

### 3.1 Oracle successive（V38–V42 oracle 臂能力上界）

$$\text{prior}^{\text{oracle}}_i(u_2)=p_i(u_2\mid U_1=u_{1,i}^{\text{true}})$$

- 依赖：$C$, $b_i$, $u_{1,i}^{\text{true}}$（Alice 真值，实践不可得）。
- 语义：successive 条件熵 $H_2$ 对应的理想先验，度量“若 L1 已知真值，L2 可达性”。
- 效率上界：V41 前所有 Lane C 保留信号均在 oracle 下测得；V42/V43 oracle 臂仍为上界对照。

### 3.2 V42 hard MAP（`cond_estimated_l1`）

$$\hat u_{1,i}:=\arg\max_{u_1}p_i(u_1),\qquad \text{prior}^{\text{V42}}_i(u_2)=p_i(u_2\mid \hat u_{1,i})$$

其中 $\hat u_{1,i}= \arg\max_{u_1}\sum_{u_2}C(u_1\!\cdot\!32+u_2,b_i)$，纯 $(C,b_i)$ 函数，无码，无泄漏。

- V42 定义冻结：$q^{\text{V42}}_i(u_1)=\mathbf{1}\{u_1=\hat u_{1,i}\}$（delta）。
- 本质：把 soft 分布坍缩为硬判，再条件。

### 3.3 V43 soft marginal（`cond_soft_marginal`）

$$\text{prior}^{\text{V43}}_i(u_2)=p_i(u_2)=\sum_{u_1}p_i(u_1)\,p_i(u_2\mid u_1)=\frac{\sum_{u_1}C(u_1\!\cdot\!32+u_2,b_i)}{\sum_{u_1',u_2'}C(u_1'\!\cdot\!32+u_2',b_i)}$$

即 $P(U_2\mid B)$ 的边缘化。纯 $(C,b_i)$，无码，无硬判，零额外泄漏。

- 实现：`marginal_counts[u2,b]=\sum_{u_1}C(u_1\! \cdot\!32+u_2,b)`，按 $b$ 归一。

### 3.4 V44 proposal 严格退化为 V43（无方法新颖性）

V44 冻结定义（design §7）：

$$\text{raw}_q[u_1,b]=\sum_{u_2}C(u_1\!\cdot\!32+u_2,b),\quad q_i(u_1):=q(u_1\mid B=b_i)=\frac{\text{raw}_q[u_1,b_i]}{\sum_{u_1'}\text{raw}_q[u_1',b_i]}$$

$$\text{分母 floor }10^{-15},\ \sum_{u_1}q_i(u_1)=1$$

V44 先验构造（proposal 原文）：$P^{\text{V44}}_i(u_2)=\sum_{u_1}q_i(u_1)\,p_i(u_2\mid u_1)$。

**解析恒等式**：

$$\begin{aligned}
q_i(u_1) &= \frac{\sum_{u_2}C(u_1\! \cdot\!32+u_2,b_i)}{\sum_{u_1',u_2'}C(u_1'\! \cdot\!32+u_2',b_i)} = p_i(u_1)=P(U_1=u_1\mid B=b_i)\\
\therefore\ P^{\text{V44}}_i(u_2) &= \sum_{u_1}p_i(u_1)\,p_i(u_2\mid u_1)=p_i(u_2)=P(U_2=u_2\mid B=b_i)=\text{prior}^{\text{V43}}_i(u_2)
\end{aligned}$$

逐元素相等（分母 floor 仅在空列时生效，空列下 $p_i$ 与 $q_i$ 同步为均匀/ floor 产物，恒等式仍成立）。全帧矩阵 `prior_V44 == prior_V43` element-wise。

**结论（V44 处置依据）**：V44 不引入任何超出 $C$ 与 $B$ 的 L1 校验信息，不改变 $p_i(u_1)$ 或 $p_i(u_2\mid u_1)$ 的定义域，**方法学严格退化为 V43 的 soft marginal**，无论 $q_i$ 被称作“soft prior”/“无码先验”/“Bob-only soft”。数值等价性对应的数学 prior 已由 V43 18-call 诊断在冻结门禁下测试（V43 soft insufficient：`6/9` exact，1 wrong，不满足 `≥7/9` 且 `G3' zero-wrong`）；V43 已测试两者共同的数学 prior，V44 不值得重复测试。

此退化与 block 样本、矩阵、译码参数、阈值无关，为计数定义级恒等；V44 不提供新机制信息，fresh blocks 可能因样本波动得到不同门禁结果，但无法归因于算法进步。

---

## 4. 真实 soft-message multistage 的必要形式

仅当 $q_i$ 携带超越 $P(U_1\mid B)$ 的、来源于 **L1 非平凡校验图与 syndrome 的迭代外信息**时，soft 机制才超越 V43。

### 4.1 迭代 soft 先验的一般式

对位置 $i$ 与迭代轮 $t$：

$$q^{(t)}_i(u_1)\ \propto\ p_i(u_1)\;\cdot\; M^{(t)}_{H_1,s_1\to i}(u_1)$$

$$P^{(t)}_i(u_2)=\sum_{u_1} q^{(t)}_i(u_1)\,p_i(u_2\mid u_1),\quad \sum_{u_1}q^{(t)}_i=1,\ \sum_{u_2}P^{(t)}_i=1$$

- $p_i(u_1)=P(U_1\mid B=b_i)$ 为信道因子（V43 已有）。
- $M^{(t)}_{H_1,s_1\to i}(u_1)$ 为 L1 Tanner 图在 syndrome $s_1=H_1\,u_1^{\text{true}}$ 约束下、经 BP/FFT-QSPA 迭代 $t$ 后对变量节点 $i$ 的外信息（校验约束因子）。可写为对数域 $L^{(t)}_i(u_1)=\log p_i(u_1)+\log M^{(t)}_i(u_1)$。
- 归一化：$q^{(t)}_i(u_1)=\text{softmax}_{u_1} L^{(t)}_i(u_1)$，floor 仅防零。
- 完整可复用数学链（L1 APP → L2 mixture）：
  $$p_i(u_1)=P(U_1\mid B_i),\quad s_1=H_1\,u_1^{\text{Alice}},\quad L_i=\text{decode\_row\_layered\_fftqspa}(H_1,\,p,\,s_1).\text{final\_beliefs},\quad q_i=\text{softmax}\,L_i,\quad P_i(U_2)=\sum_{u_1} q_i(u_1)\,P(U_2\mid B_i,u_1)$$
  其中 `decode_row_layered_fftqspa(H, prior, syndrome).final_beliefs` 为可复用 L1 APP 来源：通用 $(H,\text{prior},\text{syndrome})$ 接口，返回每位置 32 状态 log-beliefs（$L_i$），非 L2 专用；$H_1$ 存在性不等于验收性（见 §5 分支 A）。

### 4.2 何时超越 V43

- 若 $H_1$ 空/退化（无校验行）、$s_1$ 未公开、$M^{(t)}\equiv 1$（均匀），则

$$q^{(t)}_i(u_1)=p_i(u_1)\ \Rightarrow\ P^{(t)}_i(u_2)=p_i(u_2)=\text{V43}$$

- 仅当 $M^{(t)}$ 来自真实 L1 parity-check graph、真实 syndrome $s_1$、真实 decoder messages（FFT-QSPA 行分层、阻尼等）且非平凡（至少一位置非均匀），才有

$$q^{(t)}\neq p(\cdot\mid B),\quad P^{(t)}\neq P(\cdot\mid B)$$

且差异可被 `arms_differ` / `mean_abs_diff` 观测。

### 4.3 泄漏与语义边界

- V43/V44 零额外泄漏：$C$ 为公共先验，$q$ 构造不发送新公开 bits。
- 真实 $\text{L1}\to\text{L2}$ soft 转移必计 $m_1\cdot5$ bits 的 $s_1$ 泄漏于总泄漏；若计 $R_{1,\text{ref}}$ 约 $1.3H_1/5$，则 $m_1 \approx \lceil f\,N\,H_1/5\rceil$（$f=1.3$ 时 $\lceil 1.3\,N\,H_1/5\rceil$）由 DE/有限长设计决定，$leak_1=5m_1\approx f\,N\,H_1$，$f_{\text{total}}=5(m_1+m_2)/[N(H_1+H_2)]$。
- 任何声称“soft 不计泄漏却超越 marginal”的机制，若无 $H_1,s_1,M$，必落回 V43 恒等式；若有 $H_1,s_1$，则泄漏必须入账。

---

## 5. 未来方法树（5 条分支，每条最小可测）

> V35 S2 经验：L2 正信息论盈余约 125–190 bits（$m_2\cdot5 - H_2$），DE 37–44 迭代可收敛，失败压缩于有限图/转换层。每条分支须在相同 V25 TRAIN 计数、相同 `1M/1p5M/2M` 源、相同 1024-length 块上对比，禁止在不同 fresh-batch 间做同块因果。

### 分支 A — L1 GF(32) soft-output + 单向 soft 转移（one-way soft transfer）

- 新增信息：$s_1$ 约束下 $M_{H_1,s_1\to i}(u_1)$ 的 per-symbol APP（L1 行分层 FFT-QSPA 软输出），非硬判。
- 所需码/消息：GF(32) L1 矩阵 $H_1$（$m_1$ 行，多项式 37，列重>2 规避 V31 trapping）、syndrome $s_1$、$p_i(u_1)$ 与 $M_i$ 的对数相加、归一 $q^{(1)}$、单次前向得 $P^{(1)}(U_2)$ 送 L2。
- 泄漏：$m_1\cdot5$（L1）+$m_2\cdot5$（L2），总计 $f_{\text{total}} = 5(m_1+m_2)/\{N\,[H(U_1\mid B)+H(U_2\mid U_1,B)]\}=5(m_1+m_2)/[N(H_1+H_2)]$，$N=1024$，$H_i$ 为每符号比特。
- 复杂度：L1 解码 $O(n\,d_v\,32\log32)$ + L2 解码一次；存 $q$ 32×1024。
- 可归因性强：唯一新增因子为 $M_{H_1,s_1}$，对照臂即 V43 marginal（$M\equiv1$），同块配对，$\Delta exact$ 与 `arms_differ` 直接归因。
- 主要风险：L1 自身在真实 $H_1$ 下不收敛（$R_1$ 超阈），$q^{(1)}\approx p$ 无增益；V42 已证 hard 失败 0/9，soft-marginal 亦不足，单向 soft 需证明 $M$ 非均匀。
- 最小可测实验：三源各 3 块（9×2=18 calls，配对：V43 vs A-$q^{(1)}$，同 $H_{L2}$、同 90/1.0），门禁 `G1'≥7/9, G2'≥2/3, G3'=0`，报告 $m_1$、$f_{\text{total}}$、$mean\_abs\_diff(q^{(1)},p)$、per-source exact、wrong。未通过即停，转 protograph。
- L1 APP 来源（可复用接口）：`decode_row_layered_fftqspa(H, prior, syndrome).final_beliefs` 为通用 $(H,\text{prior},\text{syndrome})$ 接口，返回每位置 32 状态 log-beliefs（$L_i(u_1)$），经 softmax 得 $q_i$，与 $H$ 是否原为 L2 专用无关；FFT-QSPA 非 L2 专用。
- H1 候选说明：`matrix_payloads` / `build_matrix_packet()["matrices"]["L1"]` 提供的 $H_1$ 候选（$m_1=16$）为现有候选，但尚未科学验收为当前 soft-transfer 的 $H_1$，不得默认其已验。

### 分支 B — 1–2 轮 L1↔L2 迭代（turbo-like iterative multistage）

- 新增信息：L2 解码软输出反馈至 L1（$U_2$ 约束反向修正 $U_1$），1–2 轮闭环。
- 所需码/消息：$H_1,s_1$ 与 $H_2,s_2$ 双图；前向 $q^{(t)}$ 如分支 A，回传 $r^{(t)}_i(u_2)$ 或对 $U_1$ 的外信息更新 $q^{(t+1)}$。
- 泄漏：与分支 A 同（两 syndrome 均计），不随迭代轮增加。
- 复杂度：2–3 次 L1+L2 解码串联，时延倍增；需调度（flooding vs layered）与阻尼搜索的 DE 门预筛。
- 可归因性中等：需分离“单向增益 vs 迭代增益”，设三臂对照（V43 / A单向 / B迭代）在同块上，方可归因迭代。
- 主要风险：错误传播（L1 错误 $q$ 污染 L2，L2 错误反馈再污染 L1），V32 B1 式的 likelihood mismatch 在闭环中放大；需 V32 式 operating-point 一致性审计先行。
- 最小可测实验：同 9 块三臂 27 calls（或分两阶段 18+18），报告每轮 $exact$ 增量、$errors\_final$ 轨迹、wrong 是否出现；任一臂 wrong 即停。

### 分支 C — 耦合/联合因子图（coupled / joint nonbinary factor graph）

- 新增信息：$P(A,B)$ 的联合约束与双层校验在同一图上联合推断，$U_1$–$U_2$ 边耦合（非两独立图）。
- 所需码/消息：联合 $H_{\text{joint}}$（如 $H_1$/$H_2$ 耦合或单一 GF(64)/GF(1024) 提升图的双层投影），迭代在统一图上，消息在 $U_1$–$U_2$ 间跨层传递。
- 泄漏：$m_{\text{joint}}\cdot\log_2 Q$，可联合优化 $m_1,m_2$ 分配（V35 S2 系综门：F02–F05×层序×泄漏分配的链式熵扫描 + empirical-P 非对称 MC-DE 筛）。
- 复杂度：单图但域更大/边更多，$Q\log Q$ 随域指数增长；需 MET/protograph 降低阈值。
- 可归因性弱：图结构、degree、lifting、调度多因子耦合，难单步归因；需先过 V35 S2 的 DE/entropy threshold 门再进有限实现 gate。
- 主要风险：设计空间爆炸，有限长 girth/ trapping 未控；V34 37/60 `converged_no_syndrome` 与 23/60 迭代饥饿在联合图上更敏感。
- 最小可测实验：纯 DE/熵计算门（不构图）：证明某 protograph/MET 在 empirical-$P$ 上阈值优于分离图且 $f\le1.3$；通过后再做 6-矩阵有限实现对比（V35 S3：一个 protograph lifting vs 一个 Block-MDS/QC，各 5 块）。

### 分支 D — GF(1024) 联合非二元码（joint GF(1024) coding）

- 新增信息：直接以 $A\in GF(1024)$ 为码符号，$B$ 为观测，单层联合纠错，无分层 conditioning。
- 所需码/消息：GF(1024) H（10-bit 域，多项式与 $Q\log Q$ 极高），直接先验 $P(A\mid B)$。
- 泄漏：单一 $m_{1024}\cdot10$，信息论极限 $H(A\mid B)$ 最低开销，无分层开销。
- 复杂度：$Q=1024$，每条消息 1024 长，每次校验 $O(Q\log Q)$，内存/时延最高；V19–V24 已证 bounded single-edge $\lambda/\rho$ 在 GF(1024) 无门限通过。
- 可归因性：与 F03 分层对比可归因“分层损失 vs 联合增益”，但 GF(1024) 自身阈值需先证。
- 主要风险：V24 已排除在冻结 V17 聚合信道、GF(1024)、bounded single-edge 空间内无 DE 门通过；需跳出该空间（MET、local/global 混合图、true protograph）才可能，风险最高。
- 最小可测实验：复用 V25 的 true empirical $P(A\mid B)$ 的 joint-DE 复算（不采样），报告 GF(1024) 阈值与 $H(A\mid B)$ 的 $f$；未过阈值即关。

### 分支 E — Protograph / MET 系综重设计（V35 主线）

- 新增信息：经 informed protograph/MET 系综优化的 degree 分布、lifting 与调度，使有限图阈值与 trapping 结构同时改善。
- 所需码/消息：MET $\lambda(\mathbf{x}),\rho(\mathbf{x})$、protograph 基矩阵、lifting（QC/Block-MDS）、damping/shuffled/layered 调度变体；L1/L2 可各一套。
- 泄漏：rate-adaptive 母码（乘性重复/ puncture/shorten，EPJ QT 2025；raptor-like 增量冗余）实现三源共享单一母结构、按帧实测 SER 只发必要增量泄漏，目标函数为 $accepted\_fraction\times(raw\_secret\_budget-actual\_leakage)/acquisition\_time$。
- 复杂度：设计期 DE 成本高，运行期与分支 A/B 同阶；构图需 girth 约束与黄金转换测试（V35 S3：$m,n\le64$ 暴力 log-BP 对照）。
- 可归因性：S0 残差拓扑解剖（只读，零解码，跨块重合/短环/未满足校验邻域）直接生成设计禁令，归因链完整。
- 主要风险：S2 系综门失败即关；S3 首次冻结 gate 失败后不得在同 confirmation 数据上调参。
- 最小可测实验：S2 门（不构图，纯 DE/熵）：F02–F05×层序×泄漏分配的链式熵扫描 + empirical-P 非对称 MC-DE 筛 protograph/MET（含 damping/layered 变体），判据为 block-error 结构代理+预估净 key-rate；通过后再进 S3 单一有限实现 gate（2 候选各 5 块，非 seed 搜索）。

---

## 6. 证据表（V38–V43，逐轮输入/矩阵/设置/结果/可说明与不可说明）

> 禁止将不同 fresh-block 批次写成同块因果。每行样本为独立批次，跨轮差异为**批次效应 + fresh-block 抽样方差**，非同块增量。

| 周期 | 输入条件 | 矩阵 | Decoder 设置 | 主要结果（冻结门禁） | 能说明什么 | 不能说明什么 |
|---|---|---|---|---|---|---|
| **V38P0** | 15 共享块（1M 360101–105 等，V25 TRAIN，oracle-L1），15/winner×3 lanes | 27 候选 / 每 lane 1 winner | GF32 poly37, FFT-QSPA row-layered, $max\_iter=30$, $\alpha=1.0$，**错误绑定** $u_{2,B}$ 替 $B$ | 无效（事后判 INVALID） | 仅作反例：后验绑定错误导致 45 记录不可用 | 不可作任何 Lane 优劣结论 |
| **V38R1** | 同 15 块，重算正确绑定 $B$，oracle 仅 | 每 lane 1 winner（381101/201/301 等 9 矩阵） | 同上，$30/1.0$ | Lane C 14/15, Lane B 9/15, Lane A 0/15（median residual 0/0/115）| 正确绑定下 Lane C/B 数值反弹；单 seed/单批次信号 | 不能区分架构稳健 vs 幸运 seed/block；不能分离 C vs B |
| **V39** | **新 15 块** 390101–105/201–205/301–305，非重叠；oracle 仅 | Lane C 9 seeds + Lane B 9 seeds（18 矩阵，配对 by ordinal）+ V31 baseline 15 calls | 同上 $30/1.0$，105 calls | Lane C 33/45, Lane B 31/45；C1/B1 均未过（阈 $36/45$ 且每 ordinal≥12/15 且每 cell≥4/5）；6 个 `NEITHER_EXACT` 全在 1M；终态 `V39_NO_ROBUST_ROUTE_SIGNAL` | 单 seed 信号不稳健；1M 瓶颈；$30$ 迭代帽嫌疑 | 不能归因于 C/B 结构本身 vs 迭代帽（V40 问） |
| **V40 Phase A** | 12 instances（V39 的 6 对 NEITHER_EXACT，各 lane×ordinal，1M） | 6×1M matrices（ordinal 1/2/3） | **仅** $90/1.0$，同场其余冻结 | 5/12 rescued，$W_A=0$，`CAP_MATERIAL` 触发，跳过 Phase B | $30\to90$ 迭代帽是 material factor | 不能说 Lane B/C 已稳健 |
| **V40 Probe** | **新 3 块** 390106/206/306，各 lane ordinal-2 代表矩阵 | 6 代表矩阵（ordinal 2 / source） | $90/1.0$ | 5/6 exact（C 3/3, B 2/3, 零 wrong），`V40_PROBE_CONFIRM_ALLOWED` | 扩展设置在全新块上仍有信号，允许**一次** confirmation | 不能说已确认（仅允许提 V41） |
| **V41** | **新 9 块** 390107–109/207–209/307–309，oracle 仅，重叠检查 42 seeds 禁止 | Lane C/B 各 ordinal-2 代表矩阵（6 唯一） | $90/1.0$，18 calls | Lane C 8/9（3/3/2）保留，Lane B 6/9 未过，零 wrong；`V41_C_ONLY_RETAINED` | Lane C 在更长批次上独立保留，Lane B 不保留 | 不能说 Lane B 优/劣于 Lane C（非优劣检验）；不能说真帧 FER |
| **V42** | **新 9 块** 390110–112/210–212/310–312，**配对双条件**（同块共享采样） | Lane C ordinal-2（3 矩阵） | 同 $90/1.0$，18 calls | oracle 7/9（$G2$ 在 1p5M 1/3 未过），estimated 0/9；$l1\_map\_acc\approx0.9925$；`V42_GO_STRUCTURE / BOTH_ARMS_GATES_FAILED` | hard MAP $\hat U_1$ conditioning 全败；oracle 在新批次亦不稳（1p5M＜2/3） | 不能把 1p5M oracle 失败归为 hard-MAP 机制（两臂同败）；不能说“换 soft 就过” |
| **V43** | **新 9 块** 390113–115/213–215/313–315，**配对双条件** | Lane C ordinal-2（3 矩阵） | 同 $90/1.0$，18 calls | oracle 8/9 pass，soft-marginal 6/9 fail（$G1$ 6＜7 且 $G3$ 1 wrong），paired：both=5、oracle-only=3、soft-only=1、neither=0（`soft_only_exact`=1）；`V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`；`needs_1p5m=false`（本批 oracle 1p5M 2/3 恰过） | soft marginalization 不足；V42 的 hard 失败非“硬判本身”可由 marginal 挽回；oracle 在本批回升但跨批次方差大（V42 7/9 vs V43 8/9 vs V41 negligible 1p5M 波动） | **不得**把 V42 的 $M$ 批次与 V43 的 $M'$ 批次写成“hard $0/9\to$soft $6/9$ = soft 修复 hard 6 块”的同块因果；两轮样本不相交，差异含批次效应。亦不得把 V44 未测的 $q=P(U_1\mid B)$ 读作已测；V43 已测试两者共同的数学 prior，V44 不值得重复测试 |

补充：V42 的 `paired_outcomes` 中 oracle 5/6 块为 0 残差，estimated 全 $136$–$320$；V43 中 soft wrong 在 `390114`（4 残差 wrong codeword）、oracle wrong-free。所有 `pairing_errors_initial_equal=true`，`errors_initial` 与 selector 无关的校验成立。

---

## 7. V44 处置建议

### 7.1 处置判定：NO NOVEL MECHANISM — 停止当前 18-call 计划

- **恒等式已证**：$q_i(u_1)=P(U_1\mid B=b_i)$ 的 V44 构造与 $p_i(u_1)$ 定义级一致，$P^{\text{V44}}(U_2\mid B)=P^{\text{V43}}(U_2\mid B)$ 元素级相等（§3.4）。V44 **无方法新颖性**，不满足“新增信息需来自真实 $H_1,s_1,M$”的必要条件（§4.2）。
- **证据覆盖**：V43 在相同三矩阵、相同 $90/1.0$、相同门禁下 soft-marginal 已判 `ORACLE_ONLY`（6/9 且 1 wrong，paired both=5/oracle-only=3/soft-only=1/neither=0）；V43 已测试两者共同的数学 prior，V44 不值得重复测试。V44 不提供新机制信息，fresh blocks 可能因样本波动得到不同门禁结果，但无法归因于算法进步。
- **泄漏语义已闭合**：V44 零额外泄漏（$C$ 公共先验）符合 V43，同为无码；故不存在“新泄漏换新性能”的权衡空间。
- **建议动作**：
  1. **立即停止** `formal-ir-v44-soft-prior-conditioning` 的实现与执行授权（不进入 `IMPLEMENTATION_CANDIDATE`，不申请 `EXECUTE_AUTH`，不产生 `run_01`）。
  2. 将 V44 归档为 `NO_NOVEL_MECHANISM` 处置，决议写入 `docs/decision-log.md` 与本图谱，OpenSpec 变更标记 `REJECTED / SUPERSEDED_BY_§4_CRITERION`。
  3. **不删除**已冻结的 V44 proposal/design，仅追加处置附录，避免事后误读为“曾有新机制”。

### 7.2 后继开放条件（唯一门）

仅当**找到真实可获得的、由 L1 syndrome/message 派生的 $q_i(u_1)$** 后，才创建后继 OpenSpec。形式化开放判据：

$$\exists\,H_1,s_1,M^{(t)}\ \text{s.t.}\ q^{(t)}_i(u_1)\propto p_i(u_1)\,M^{(t)}_{H_1,s_1\to i}(u_1),\ M^{(t)}\not\equiv1,\ \text{且 }q^{(t)}\neq p(\cdot\mid B)\ \text{在} >5\%\ \text{位置上}$$

并满足：

- $H_1$ 为冻结 GF(32) 非退化矩阵（行数 $m_1$、列重分布、girth 满足 V35 S2 门），$s_1=H_1u_{1}^{\text{true}}$ 计入总泄漏；
- $M^{(t)}$ 来自真实 L1 decoder（FFT-QSPA，$max\_iter\ge30$）的校验-变量消息，非手工加权；
- decoder-free 哨兵 `soft_prior_public_inputs` 升级为 `l1_message_source_is_H1_s1`，`carrier_identity` 校验 $q^{(t)}$ 确为 $p\cdot M$ 归一；
- 在同块配对下 `arms_differ` 非平凡且与 $M$ 的非均匀度相关。

未满足此门之前，任何“Bob-only 再加权”“温度缩放”“后验锐化”均属 V43 等价类，禁止以新 arms 名义立项。

### 7.3 若放行 V44 的后果（风险陈述）

- 浪费 18 calls 预算与 fresh-block 额度（当前 FORBIDDEN 已 60 seeds），产出与 V43 重复的终端（`ORACLE_ONLY / GO_STRUCTURE` 二选一），不推进 §5 任何分支。
- 误导后续归因：把“无新信息的重复失败”读作“soft prior 方向已穷尽”，掩盖真实缺口（L1 码/消息缺失）。

---

## 8. 数学自检（解析 + NumPy toy，不调用 decoder）

### 8.1 解析自检

1. **归一性**：$\sum_{u_1}q_i(u_1)=1,\ \sum_{u_2}p_i(u_2\mid u_1)=1,\ \sum_{u_2}P_i(u_2)=1$。分母 floor $10^{-15}$ 保非零，空列时均匀化仍归一。

2. **Delta 退化为 conditional oracle**：若 $q_i(u_1)=\mathbf{1}\{u_1=\hat u_{1,i}\}$（V42），则

$$\sum_{u_1}q_i(u_1)p_i(u_2\mid u_1)=p_i(u_2\mid \hat u_{1,i})$$

即硬判条件；$\hat u$ 来自 $p_i$ 的 MAP，仍无 $H_1,s_1$。

3. **Bob-only $q=p(U_1\mid B)$ 退化为 V43**（§3.4 恒等式）：$q_i=p_i\Rightarrow P^{\text{V44}}=p_i(U_2\mid B)$。

4. **非平凡校验消息才偏离 V43**：设 $M_i(u_1)$ 非均匀，则 $q^{(t)}_i\neq p_i$ 且

$$P^{(t)}_i-p_i =\sum_{u_1}(q^{(t)}_i(u_1)-p_i(u_1))\,p_i(\cdot\mid u_1)\neq0$$

（当 $p(\cdot\mid u_1)$ 随 $u_1$ 变化时）。反之 $M\equiv1$ 则差为零。

5. **无 Alice 泄漏**：所有构造仅输入 $(C,b_i)$ 与 $M_{H,s}$（后者仅依赖 $B$ 与公开 $s$），$u^{\text{true}}$ 未入 $q$。`captured_second_argument==bob` 哨兵等价于“先验不含 Alice”。

### 8.2 NumPy toy 验证（decoder-free，内嵌可执行片段）

```python
# ponytail: toy is decoder-free, single file, no I/O, asserts only.
import numpy as np

def posterior_maps(counts):
    # counts: (1024, B) or (32*32, B) -> here (1024, 4) toy
    # returns p_u1_given_b, p_u2_given_b_u1, p_u2_given_b
    Q1 = Q2 = 4  # toy: A=Q1*Q2=16, U in 0..3
    B = counts.shape[1]
    raw_q = counts.reshape(Q1, Q2, B).sum(axis=1)  # (Q1, B) = sum_u2
    p_u1 = raw_q / np.maximum(raw_q.sum(axis=0, keepdims=True), 1e-15)
    # p(u2|b,u1)
    denom = np.maximum(counts.reshape(Q1, Q2, B).sum(axis=1, keepdims=True), 1e-15)  # actually per u1 sum_u2
    # simpler: for each u1, denominator = sum_u2 C[u1*Q2+u2,b]
    p_u2_given_u1 = np.zeros((Q1, Q2, B))
    for u1 in range(Q1):
        block = counts[u1*Q2:(u1+1)*Q2, :]  # (Q2, B)
        d = np.maximum(block.sum(axis=0, keepdims=True), 1e-15)
        p_u2_given_u1[u1] = block / d
    # marginal p(u2|b) = sum_u1 p(u1|b) p(u2|b,u1)
    p_u2_marg = np.einsum('ub,uvb->vb', p_u1, p_u2_given_u1)  # (Q2, B)
    return p_u1, p_u2_given_u1, p_u2_marg

def check():
    rng = np.random.default_rng(0)
    Q1 = Q2 = 4
    B = 6
    counts = rng.integers(1, 20, size=(Q1*Q2, B)).astype(float)
    p_u1, p_u2_given_u1, p_u2_marg = posterior_maps(counts)

    # 1) normalization
    assert np.allclose(p_u1.sum(axis=0), 1, atol=1e-12)
    assert np.allclose(p_u2_given_u1.sum(axis=1), 1, atol=1e-12)
    assert np.allclose(p_u2_marg.sum(axis=0), 1, atol=1e-12)

    # 2) delta q -> oracle conditional
    bob = 2
    hat = int(np.argmax(p_u1[:, bob]))
    q_delta = np.eye(Q1)[hat]  # one-hot
    p_delta = (q_delta[:, None] * p_u2_given_u1[:, :, bob]).sum(axis=0)
    assert np.allclose(p_delta, p_u2_given_u1[hat, :, bob])

    # 3) Bob-only q = p(u1|b) -> V43 marginal
    q_bob = p_u1[:, bob]
    p_bob = (q_bob[:, None] * p_u2_given_u1[:, :, bob]).sum(axis=0)
    assert np.allclose(p_bob, p_u2_marg[:, bob], atol=1e-12)
    # also equals raw marginal directly
    marg_direct = counts.reshape(Q1, Q2, B)[:, :, bob].sum(axis=0) / counts[:, bob].sum()
    # counts sum_u1 per u2: sum_u1 C[u1*Q2+u2]
    marg2 = np.array([counts[u1*Q2+u2, bob] for u1 in range(Q1) for u2 in range(Q2)]).reshape(Q1, Q2).sum(axis=0) / counts[:, bob].sum()
    # but p_u2_marg already equals that
    assert np.allclose(p_bob, p_u2_marg[:, bob])

    # 4) nontrivial parity message -> differs from V43
    M = rng.uniform(0.5, 1.5, size=Q1)
    M = M / M.sum() * Q1  # non-uniform, mean 1
    q_soft_msg = p_u1[:, bob] * M
    q_soft_msg /= q_soft_msg.sum()
    p_with_msg = (q_soft_msg[:, None] * p_u2_given_u1[:, :, bob]).sum(axis=0)
    assert not np.allclose(p_with_msg, p_u2_marg[:, bob])  # genuinely different when p(u2|u1) varies
    assert np.allclose(p_with_msg.sum(), 1, atol=1e-12)

    # 5) Alice leakage check: q never uses alice truth
    # (by construction, q depends only on counts and bob column)
    print("toy self-check PASS: delta->oracle, bob-only -> V43, msg -> differs, normalized, no alice.")

if __name__ == "__main__":
    check()
```

- **断言覆盖**：§8.1 的四条解析结论在 16-ary toy 上以随机计数逐元素验证；`bob-only` 与 `V43 marginal` 差值机器精度内为零，加入 `M` 后差值非零。
- **无泄漏**：`q` 构造闭包仅捕获 `counts` 与 `bob` 列，无 `u_true` 形参。
- **可复现**：`rng(0)` 固定种子，零 I/O，单文件可作 `python -m` 自检。

---

## 附录：术语与符号表

| 符号 | 含义 |
|---|---|
| $C(a,b)$ | V25 TRAIN 经验计数，`channel_counts.npz` |
| $p_i(u_1),p_i(u_2\mid u_1),p_i(u_2)$ | §3 定义的条件/边缘后验 |
| $q_i(u_1)$ | L1 软先验（V42 delta / V43-V44 $p(u_1\mid B)$ / §4 $p\cdot M$） |
| $H_i,s_i$ | GF(32) 校验矩阵与 syndrome（计泄漏） |
| $M^{(t)}_{H,s\to i}$ | L1 图校验约束外信息 |
| $exact_{L2}$ | $ \mathbf{1}\{ \hat x_2 = u_{2,\text{Alice}}\}$，唯一成功判据 |
| $wrong$ | $syndrome\_ok \land \lnot exact$，永不计为 success |

---

*本图谱为 V25–V44 的数学归纳冻结件；后续任何 soft conditioning 立项须先满足 §4 必要形式与 §7.2 开放判据，否则按 §7.1 处置。*
