# Route B/C/D 下一步规划 — 自动可执行任务清单 (2026-08-19)

Status: PLAN (planner proposal; Route B 后续执行与 Route C/D 立项仍需用户决策)
依据: route-a-diagnostic-conclusion-20260816.md, route-b-m1b-result-20260816.md,
route-b-m2-real-search-result-20260816.md, route-b-m2-r06-parallel-result-20260816.md,
workspace/nbldpc_v18_b2_r063_par/、nbldpc_v18_b2_r065_par/,
nonbinary_v18_b2_structured_de.py (HEAD b5d05777)。

## 0. 关键数字（本计划所有判断的算术基础）

- q=16 folded 信道：H = 0.382911 bits/symbol，log2(q) = 4 bits/symbol。
- 当前 M2 搜索的 f(R) 公式（plain 全 syndrome）：
  `f = (1 - R) * 4 / 0.382911 = 10.4462 * (1 - R)`
  - R=0.50 → f=5.223（实测 5.2231 ✓）；R=0.55 → 4.7008（实测 ≈4.70 ✓）
  - R=0.60 → 4.1785（实测 4.1785 ✓）；R=0.62 → 3.970；R=0.625 → 3.917
  - **f≤1.3 需要 R ≥ 0.8756**（1 - 1.3/10.4462）
- 一般式：`f = (1-R) * log2(q) / H_fold(q)`。H_fold(16)=0.3829，H_fold(1024)=0.5470。
  - 同一 plain rate 下 q 越大 f 越差：R=0.6 时 q=16 → 4.18；q=1024 → 4.0/0.547 = 7.31。
  - 结论：**q=32/64/128 不是降 f 的杠杆**；f≤1.3 在 q=16 上需要 R≈0.876，
    在更大 q 上需要更接近 1 的 rate（先有高 rate 能力，再谈大 q）。
- Shannon 下限：leak ≥ H ⇒ f ≥ 1.0。f=1.3 是容量的 130%，长块 + 好 ensemble 可达，
  但 n=256 物理帧有有限长代价（plan 文档已定：工程上分帧拼接 n=512/1024/2048）。
- 度分布约束（nonbinary_v10_de.py 冻结语义）：K=8、dv∈[2,40]（**无 degree-1**）、
  每个 λ 权重 ≥ 0.01；concentrated 2-point check degree。
  dc_mean = mean_dv / (1-R)。R=0.8756 时 mean_dv≥2 ⇒ dc_mean≥16（Müller 式大 dc 区间，
  表示可行，非表示墙）。

## A) rate 细扫决策：停止；0.60 作为该代理的实用边界

- 0.61/0.62/0.625 细扫即使全部成功也只把 f 从 4.18 推到 3.92–4.07，对 1.3 目标无意义。
- 0.63 与 0.65 已各 8/8 seeds（pop=20, gen=20, n_samples=10000, max_iter=100）全部
  entropy_converged=False；plain irregular NB-LDPC 在该 folded 信道上的 DE 天花板
  位于 0.60–0.63 之间。
- 决策：**不做 0.61/0.62/0.625 常规细扫**。可选：仅做一次 0.62×4 seeds 的
  bracket 运行，唯一目的是把“plain 天花板”钉在 [0.60, 0.63] 内，供 B2 门
  定义引用；做完即关闭 plain-rate 扫描。
- 把 0.60（f=4.18，seed 2026081707）记录为 **M2 plain-ensemble 实用边界**，
  定性为“相对 R3 legacy f≈8–12 改善 2 倍、离文献 f≈1.1 仍差 3.8 倍”的诊断结论，
  不是效率里程碑。
- 可选 bracket 命令（与 r063 完全同预算，新 seed 段 2026082000..07）：
  `python -m comparison_bench.src.comparison_bench.cli.run_v18_b2_structured_de --mode real-search --q-small 16 --rate 0.62 --pop-size 20 --max-gen 20 --n-samples 10000 --max-iter 100 --seed 2026082000 --out-dir workspace/nbldpc_v18_b2_r062_par/seed_0`
  （PowerShell 8 路并行启动器见附录，输出结构与 r063/r065 的 pids.json+seed_N.log 一致。）

## B) 最高杠杆下一步：先做 3 向归因诊断，再谈任何新机制

不要直接切 q=32/64/128（第 0 节算术已排除其为降 f 杠杆），也不要先加预算。
最高杠杆是**把 0.63/0.65 未收敛的原因归因清楚**：是“结构化信道本身比同熵 QSC 难”，
还是“20 代小预算搜索找不到本可收敛的 ensemble”。两者指向完全不同的下一步。

### B-1（自动，决定性）：QSC 等熵对照实验
- 构造 H≈0.3829 的 QSC(q=16, p)：p=0.038 → H = h2(0.038)+0.038*log2(15) ≈ 0.3815。
- 用完全相同的搜索预算/种子跑 rate 0.63 与 0.65（structured 机制直接吃 w，
  QSC 就是 w[0]=1-p, w[d]=p/15 的特殊 structured 信道，零新机制）：
  `python -c "import numpy as np, json, sys; sys.path.insert(0,'comparison_bench/src'); from comparison_bench.formal_ir.nonbinary_v18_b2_structured_de import run_structured_de_search; q=16; p=0.038; w=np.full(q,p/(q-1)); w[0]=1-p; print(json.dumps(run_structured_de_search(q=q, rate=0.63, w=w, search_seed=2026082008, pop_size=20, max_gen=20, F=0.85, CR=0.7, n_samples=10000, max_iter=100, out_dir='workspace/nbldpc_v18_b2_qsc063_ctrl')['best_objective'], sort_keys=True))"`
- 判定规则（预注册）：
  - QSC 收敛 / folded 不收敛 ⇒ **信道结构是限制项** → 下一步是信道专用构造：
    per-symbol-class puncture（只 puncture 干净符号位）、LSB 公开两步法（Pacher 2016）、
    或把 B3-in-DE（见 B-3）作为主路线。
  - QSC 也不收敛 ⇒ **搜索/预算是限制项** → 下一步 B-2（搜索工程），然后重测。
- claim_boundary 仍写 diagnostic_only；不改冻结基线；与 0.63/0.65 同预算保证可比。
  这不是对 0.63/0.65 的 rerun/tuning（那些结果作为非提升证据原样保留）。

### B-2（若 B-1 归因到搜索）：搜索工程改进（预注册后再跑）
1. max-rate 目标：现有 objective 在固定 rate 下最小化 converged_iter；
   新增 rate-ladder 模式，early-stop 找出“最大可收敛 R”。
2. 暖启动：rate 阶梯从上一档 best_lambda 初始化（0.6 的 best 作为 0.65+ 的初始种群成员）。
3. 预算：pop 20→40、gen 20→40、n_samples 10000→20000、streak 20→30 仅用于“门”级
   复测；日常扫描保持现预算。放宽 dv 上限（40→64，DEGREE_MAX 已是 64）供大 dc 区间探索。
4. 全部作为新 change 的预注册实验，不构成对既有结果的调参重跑。

### B-3（文献语义校准，重要）：puncture/shorten 是“率适配”不是“降 f”
- Müller 2024 的 f≈1.078–1.14 是**按 QBER 分档的一组 mother code**（QBER 3% 档
  R≈0.9，即 m/n≈0.1）+ blind puncture/shorten 做档内细调
  （R_eff=(n-m-s)/(n-p-s)）。
- 固定 m 时 puncture 不改变 leak=m·log2(q)/n，即 f 不变；它只提升有效码率、
  支持 QBER 15–30% 区间适配（plan 文档 B3 原意）。
- 因此把 f 从 4.18 降到 1.3 的杠杆仍是 **mother rate 0.6 → ≈0.876**（plain），
  这正是 B-1/B-2 要回答的可行性问题；B3 的 puncture/shorten 在 DE 门 PASS 后
  作为率适配层进入（B2 门通过后立项，不提前做）。
- 泄漏记账一致性（AGENTS.md 5.5）：当前 f 用 H_fold=0.383 作分母但未计入
  6 个 MSB 平面（其编码成本 ≈ Σh2 ≈ 0.05 bits/symbol）。R=0.6 候选的
  全信道诚实 f ≈ (1.6+0.05)/0.547 ≈ 3.0。B2 门定义必须预注册这个两段分解，
  避免跨方法不可比。

### B-4（用户门）：B2 门正式定义与执行
- 新 OpenSpec change：目标 f≤1.3、mother-rate 阶梯
  {0.70, 0.75, 0.80, 0.85, 0.875}、QSC 对照、预算/停止规则、泄漏两段分解、
  合成根与 evidence 目录；按 no-rerun/no-tuning 纪律执行一次。
- 门 PASS 后才允许：B3 码构造（NB-QC 高码率 + puncture/shorten）与 q=32/64/128
  的 scaling 确认（此时才轮到 q 升级）。

## C) Route C/D 的自动推进与门禁分类

| 条目 | 能否现在自动 | 条件 |
|---|---|---|
| M2 收尾文档 + CURRENT_TASK 更新 + memory triage | 自动 | 文档/记账，无新 claim |
| 0.62×4 bracket（可选） | 自动 | 诊断性，同预算 |
| B-1 QSC 等熵对照（0.63/0.65） | 自动（建议） | 诊断性，同预算；claim 标 diagnostic_only |
| B-2 搜索工程改动 | 先写 OpenSpec 提案 | 新预注册实验，需用户批准 |
| B-4 B2 门（f≤1.3 阶梯）执行 | 用户门 | 新 change + 门定义批准 |
| B3 码构造 / q=32/64/128 | 用户门 | 依赖 B2 门 PASS |
| Route C1（MLC 分层小域）执行 | 用户门 | 新科学路线，plan 文档要求用户立项；可先自动写设计草案（每平面 DE 可行性 vs folded GF(16) 的对照设计） |
| Route C2（EMS vs log-FFT 基准） | 等待 | 需先有 B2/B3 选定的 ensemble |
| Route C3（硬件/吞吐预研） | 等待 | 显式依赖 C1/C2 科学结论 |
| Route D1（fresh 数据确认） | 阻塞 | 需用户新采集数据 |
| Route D2（冻结纪律保持） | 自动维护 | 纪律 + 文档，无执行 |
| Route D3（push） | 阻塞 | 需用户单独授权 |

## D) 自动执行优先级（Top 5）

1. **M2 收尾**：写 docs/route-b-m2-plain-boundary-20260819.md（0.60 边界、f=4.18、
   r063/r065 非提升证据引用、A 节停止决策），更新 CURRENT_TASK.md，memory triage。
2. **B-1 QSC 等熵对照**：rate 0.63/0.65 × 8 seeds 并行（约与 r063 同等墙钟），
   输出 workspace/nbldpc_v18_b2_qsc063_ctrl_par/、qsc065_ctrl_par/，写归因结论
   （信道结构 vs 搜索预算）。
3. **（可选，与 2 并行）0.62×4 bracket**：钉住 plain 天花板区间 [0.60, 0.63]。
4. **B-2/B-4 OpenSpec 提案草稿**：max-rate ladder、暖启动、预算档、f≤1.3 门定义、
   泄漏两段分解、停止规则；交用户批准（批准前不执行生产搜索）。
5. **Route C1 设计草案 + D2 纪律清单**：每平面 DE 可行性对照设计（V17 模型）、
   D1/D3 状态标注 user-blocked；执行等待用户立项。

## 附录：8 路并行启动器（与 r063/r065 输出结构一致）

```powershell
$rate = 0.62  # 或 0.63/0.65 QSC 对照时改调用的内联脚本
$root = "workspace\nbldpc_v18_b2_r062_par"
New-Item -ItemType Directory -Force $root | Out-Null
$jobs = 0..7 | ForEach-Object {
  $seed = 2026082000 + $_
  $out = Join-Path $root "seed_$_"
  New-Item -ItemType Directory -Force $out | Out-Null
  $p = Start-Process python -ArgumentList "-m","comparison_bench.src.comparison_bench.cli.run_v18_b2_structured_de","--mode","real-search","--q-small","16","--rate","$rate","--pop-size","20","--max-gen","20","--n-samples","10000","--max-iter","100","--seed","$seed","--out-dir",$out -RedirectStandardOutput (Join-Path $root "seed_$_.log") -RedirectStandardError (Join-Path $root "seed_$_.err") -PassThru -NoNewWindow
  [pscustomobject]@{seed=$seed; pid=$p.Id; out=$out}
}
$jobs | ConvertTo-Json | Set-Content (Join-Path $root "pids.json")
```
