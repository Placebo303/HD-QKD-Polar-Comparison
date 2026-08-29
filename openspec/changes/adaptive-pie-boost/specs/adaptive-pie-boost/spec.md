# Spec: adaptive-pie-boost

## Capability: adaptive-pie-boost

### Requirement: per-file 双层自适应择优

- 系统 MUST 为每文件在 3 点 × 6 组合（18 候选）内做参数枚举与择优，候选维度为 `delay_override`（3 点）× `window_ps×anchor`（6 组合），枚举由 `tools/auto_ir_scan.py` 外层循环实现，留2核 `workers=max(2,cpu-2)`，不新增冻结基线透传参数。
- 系统 MUST 以 `max PIE_reconciled_net` 为主目标（扫描期以 `PIE_est` 代理），辅以 `min ser` 与 Wilson 95% CI 作不敏感区判定。
- 系统 MUST 对单候选失败跳过、单文件 18 候选全失败回退至 `per-tier 最优锚（T1c 10ps）` 并标记 `optimal_source=fallback_per_tier`，保证每文件必有可用参数。
- 系统 MUST 对 `pool_root/out_root/candidate_dir` 做 fail-closed 守卫：必须含 `adaptive_v1` 子串，否则拒绝。

### Requirement: 仅四组冻结基线最高 PIE 点位对比

- 系统 MUST 从冻结基线 `polar_e2e_results.csv`（`results/paper_grade_aggressive_v1` 或 `authoritative`）中每档提取 `PIE_practical` 最大行对应的 `(loss_db,d,bw,blk)` 共 4 点作为 frozen_max 清单，落 `evidence/gates_frozen.json` 并冻结。
- 系统 MUST 对该 4 点各自跑 18 候选自适应择优，产出 `per_file_scan_trace.csv`（72 行量级）与 `per_file_optimal_params.csv`（4 行），并以最优参数全链重跑至 `*_adaptive_v1` 增量根（`frames300/seed20260228/tag_bits64/shards16` 不变）。
- 系统 MUST 生成 `_adaptive_vs_frozen.csv`（4 行，列含 `loss_db,d,bw,blk,PIE_frozen,PIE_adaptive,ΔPIE,ser_frozen,ser_adaptive,Δser,beta_frozen,beta_adaptive,optimal_source,Wilson CI,significant_flag`），逐行 `ΔPIE = PIE_adaptive - PIE_frozen` 可复算，`beta` 非手填。
- 系统 MUST 保持 `results/paper_grade_v3` / `results/authoritative` / `*_lossfix_v1` / `*_aggressive_v1` 只读，全部新产物后缀 `*_adaptive_v1` 或聚合 `results/adaptive_v1/`，三目录物理隔离。

### Requirement: 门与可验证性

- 系统 MUST 通过 `G2` 跨档零碰撞、`G4` 溯源完整、`G_budget`（≤18/文件，`scan_wall_s<60s`）硬门；`G_adaptive` 为披露门（`mean/median/positive_frac/Wilson 显著数`），不阻断归档，仅决定结论措辞。
- 系统 MUST 满足 `pytest -p no:cacheprovider` 相关用例通过、`python tools/auto_ir_scan.py --help` 可打印含 `--pool-root/--scan-config/--objective/--budget-per-file/--frozen-manifest`。
- 系统 MUST 每阶段末通过 `reviewer-go` 独立审查（只出 findings）与 `data-lock/code-lock` 冻结点方可进入下一阶段。

## Verification

- `pytest -p no:cacheprovider --basetemp=workspace/adaptive-pie-boost/T0` guard/tamper 用例通过
- `per_file_scan_trace.csv` 72 行量级、Wilson CI 齐全、`scan_wall_s` 披露且 <60s
- `per_file_optimal_params.csv` 4 行、`_adaptive_vs_frozen.csv` 4 行对齐且可复算
- `results/adaptive_v1/*` 增量落盘且无旧根覆写（`git diff` 仅最小触碰面）
- `reviewer-go` T0–T3 报告 PASS + `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md` 更新
