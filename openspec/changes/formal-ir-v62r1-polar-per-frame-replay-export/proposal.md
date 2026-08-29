# OpenSpec Proposal: formal-ir-v62r1-polar-per-frame-replay-export

**Status**: `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` — 仅冻结「Polar逐帧重放导出」计划与decoder-free可行性探针，不执行重放，不改Polar Release，不跑NB-LDPC，不算PIE/SKR
**Domain**: Formal IR / Polar per-frame replay export for V62 paired benchmark (V62前置)
**Change ID**: `formal-ir-v62r1-polar-per-frame-replay-export`
**Cycle ID**: `V62R1`
**Branch**: `formal-ir-mainline`
**HEAD**: `b37c78b7` (用户给出当前HEAD前缀，实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == <full-40>` 重核为准；不一致阻塞；本次推送新 Plan SHA)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 冻结处理点) — V62/V62R1共用锚点，Polar侧实际处理点以Phase A机械提取为准，Phase B逐块校验一致性
**Predecessor**: `formal-ir-v62-nbldpc-polar-reference-benchmark` (`V62P0`, HEAD `6a3b873e`, `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`) — 本变更为V62 paired benchmark的**前置重放准备**，不改V62/V55/V61终态；若本变更API不可用则V62保持 `COMPARISON_DATA_NOT_ALIGNED` 语义
**Lifecycle**: `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan四工件 + decoder-free API探针 + 空registry骨架，未获 `POLAR_REPLAY_EXECUTE_AUTH` 前禁止任何Polar重放执行

> ponytail lite: 本变更仅4 OpenSpec工件 + 1 decoder-free API定位探针 + 1 registry骨架(空)；无decoder执行、无矩阵改动、无新依赖(`numpy/pandas/pyarrow` 已装仅作探针)。laziest alternative: 若Phase A证实Polar Release无法「直接输入预构造256-symbol symbols + 逐帧返回 verification/leak/runtime/frame_id」，则直接落盘 `V62R1_POLAR_REPLAY_API_NOT_READY` 并停止，不手写伪接口、不伪造逐帧、不重跑TTBin、不展开V62 benchmark。

> **研究问题**：能否在**不改 `D:\Code\HD-QKD_Polar_Release` 任何文件**的前提下，从外层以**冻结Polar参数**直接输入**预构造的180个256-symbol frames**（对应未来V62的 `45×1024-blocks = 45×4 连续帧`）并**稳定产出每帧** `frame_id / decode_success / verification_pass / exact(null若无) / disclosure / runtime / frozen provenance`，以重开V62的逐帧对应公平对比？回答仅 `REPLAY_READY / POLAR_REPLAY_API_NOT_READY / EVIDENCE_INVALID` 三选一；`REPLAY_READY` 需Phase A机械验证通过且Phase B registry冻结且Phase C输出契约可机械校验。

## Goal

以最短可信路径冻结一条**只读Polar、精确180帧、一次重放**的外层导出通道，为V62 paired benchmark补齐逐帧真值层缺口：

1. **Phase A — decoder-free API可行性（只读定位，零手填）**：在 `D:\Code\HD-QKD_Polar_Release` 上机械定位Polar decoder入口（`file/function/key`）、冻结参数（code length / rate / list size / CRC / quant / iteration / `dimension/bin_width/pairing/threshold`）、输入格式（是否接受 `alice_symbol/bob_symbol` 已配对symbols而非重跑TTBin）、输出语义（每帧 `success/verification/disclosure/runtime/frame_id` 是否原生存在且稳定）、provenance绑定（`commit/version/processing_rule_version/pairing_path_tag`）。验证**可直接输入预构造symbols**且**每帧frame_id稳定可追**，且**每帧verification/leak/runtime可得**；任一不满足则 `V62R1_POLAR_REPLAY_API_NOT_READY` 停止，不伪造接口。
2. **Phase B — 公平数据注册（机械冻结，逐帧对应优先）**：从**兼容的development session**（非 `V55 intake_20260828` domain-incompatible）机械冻结 `15/source ×3 =45` 个 `1024-blocks`，每块对应 `4连续256-frames` 且**Alice/Bob symbols与Polar重放输入完全一致**，不用V55非legacy_v1输入，不按outcome选块，落盘唯一权威 `v62r1_paired_registry.json`（`block_id/source/frame_ids[4]/provenance/materialization_hash`），禁换块。
3. **Phase C — Polar逐帧输出契约（预算恰好180）**：冻结每256-frame输出 `frame_id/source/block_id/decode_success/verification_pass/exact(null若无)/disclosure_bits/runtime_s/frozen_param_provenance`，每1024-block聚合 `verified_accept=4帧全部success&&verification ?1:0`、`leak=Σ4 disclosure`、`runtime=Σ4`、`exact=4帧全exact?1:0否则null`；预算**仅180 frames恰好一次**（`L2 180 calls`语义对应V62的45×4），不运行NB-LDPC、不改Polar参数、不算PIE/SKR、不自动启动V62 benchmark；输出写入本仓 `comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/` 新additive目录，不写Polar Release。
4. **停止与门禁**：先实现探针+registry骨架与 `Pre-EXECUTE review`，未显式 `POLAR_REPLAY_EXECUTE_AUTH`（绑定精确实现SHA + registry hash + Polar commit + budget180）不得执行；`HEAD==origin==implementation SHA`、`ACCEPTED_PLAN_SHA`重推导、`rg <stale>` 0命中、`run_01`不存在、`py_compile+关键测试PASS` 均需记录后才授权。

**报告承诺（shall）**：proposal/design/tasks/specs显式承诺 — 若未来获授权执行，最终报告SHALL按 `overall + per-source` 分别包含 `per-frame明表明细(180行)` 与 `per-block聚合(45行)` 的 `verified_accept / disclosure / runtime / exact(null)`，`undetected隔离`语义在Polar侧同样适用（`verification_pass && !exact` 单独表若exact存在），`frozen provenance`完整双绑定，不算PIE/SKR，不扩claim。

## Non-Goals

- 不改 `D:\Code\HD-QKD_Polar_Release` 任何文件（`git diff -- ../HD-QKD_Polar_Release ==0` 语义只读）；不改Polar code length/rate/list/CRC/quant/迭代等任一冻结参，新增即 `EVIDENCE_INVALID`。
- 不运行NB-LDPC任何decoder（`rg "decode_nbldpc" 0 hits` 在重放探针/实现中）；不继续V55二阶段或V61安全数值；不以本变更产出直接宣称V62 `COMPETITIVE`。
- 不重估先验、不重跑TTBin配对（输入必须是已配对symbols）；不把V55 `256/frame`非`1024-block legacy_v1`输入当作兼容块。
- 不创建正式 `comparison_bench/outputs_comparison/formal_ir_methods/v62_*/run_01` 或NB-LDPC执行；本轮不创建Polar `run_01`正式输出，仅探针与空骨架。
- 不算 `PIE/SKR / finite-key / eps_sec / eps_cor / vis` 等派生指标；`beta_eff_empirical` 与PIE/SKR仅保留在V62侧 `POLAR_REFERENCE_PROXY` 语义，本变更不触。
- 不伪造对齐：无相同输入可重放或API不可逐帧返回时直接 `POLAR_REPLAY_API_NOT_READY` 停止，不以aggregate FER推导per-frame、不手填verification/leak/runtime。
- 不自动启动V62 paired benchmark；即使本变更 `REPLAY_READY`，V62仍需独立 `EXECUTE_AUTH`。
- 不做 `FER/阈值/SKR/安全/资格/晋升` 的扩大陈述；`verification tag` 仍按Polar既有语义记录，不升级为可组合安全证明。

## Scope

1. **冻结Polar侧只读语义（零改，V62锚点复用）**：
   - `n_frame=256 symbols` per Polar frame, `4×256=1024` per NB-LDPC block, `S=3 (1M/1p5M/2M), B=15, total blocks 45, total frames 180`。
   - Polar冻结参待Phase A机械提取并落盘：`polar_commit/polar_version/code_len/rate/list_size/crc_bits/quant/iterations/dimension/bin_width/threshold/pairing_rule`，每项 `file:line:expr` 或 `data_path:provenance`。
   - `dimension 1024, bin_width 200ps, pairing nearest legacy_v1, threshold_ps/effective_window_ps` 与data SHA `84d62779` 单点一致性校验。

2. **Phase A — API可行性（decoder-free，按序first-match）**：
   - **入口定位**：`rg "def decode|class.*Decoder|polar.*decode|run_polar|reconcile" D:\Code\HD-QKD_Polar_Release --type py -n` + `experiments/run_real_polar*.py` + `src/reconciliation/**` 只读扫描，记录Top3候选 `path:function:signature`。
   - **输入格式判定**：候选是否接受 `np.ndarray symbols [0,1024) shape (n_frames,256) 或 (180,256)` / `FrameBatch` / `pairs.parquet` 已配对输入，而非强制 `ttbin/raw pairs → pairing` 重跑；以 `inspect.signature` 与最小可构造symbols dry-run（不触decoder执行，仅 `py_compile + import + signature`）为准，禁止实际解码。
   - **输出语义判定**：候选是否原生返回每帧 `decode_success(boolean) / verification_pass(boolean) / disclosure_bits(int) / runtime_s(float) / frame_id(int stable)`；`verification_pass` 需可区分 `success但verify_fail` 与 `decode_fail`；`disclosure` 需 `bits/frame` 粒度非仅aggregate。
   - **frame_id稳定性**：输入frame顺序与输出 `frame_id` 一一映射可机械校验（`input_frame_ids == output_frame_ids` 有序相等）。
   - **未就绪停止**：若任一 `missing_per_frame_field ∈ {verification, disclosure, runtime, frame_id}` 或不支持预构造symbols直输，则 `overall = V62R1_POLAR_REPLAY_API_NOT_READY` 立即停止，落盘 `v62r1_api_readiness.json` 显式缺口，不伪造、不手填、不降级为aggregate拼帧。

3. **Phase B — 公平数据注册（机械冻结，未对齐停止）**：
   - **兼容源排除**：若来源为 `comparison_bench/outputs_comparison/v55_intake_20260828`（`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` 且 `256/frame` 非 `1024-block legacy_v1`）判 `V55_DOMAIN_INCOMPATIBLE` 禁用。
   - **处理点一致**：`dimension==1024, bin_width 200ps, pairing nearest legacy_v1, block 1024, frame 256, alice/bob ∈[0,1024)` 每块校验；`pairing_path_tag/threshold_ps` 与Polar侧一致。
   - **机械选块**：从兼容development session的可用超集 `K_avail` 中每源取 `15` 块，`15/source` 不按outcome选；若 `K_avail>15` 则分散 `index_j=floor(j*(K_avail-1)/14) j=0..14` 否则判 `V62R1_REGISTRY_INSUFFICIENT` 停止。
   - **registry权威**：`docs/research_cycles/V62R1/v62r1_paired_registry.json`（authoritative, `S=3 B=15 total45 / total frames180`），每块 `block_id, source, frame_ids[4] (strict increasing consecutive), held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, FRAME_LEN 256, sampling_mode=paired_polar_replay_v62r1, polar_source_path+polar_commit, materialization_hash=sha256(alice||bob) per block, provenance`；`frame_ids`全局唯一且与Polar输出 `frame_id` 将来一一对应。
   - **禁换块**：自registry落盘起任何换块/重采样即 `EVIDENCE_INVALID`。

4. **Phase C — Polar逐帧输出契约（预算恰好180，一次）**：
   - **每256-frame行**：`frame_id, source, block_id, decode_success(bool), verification_pass(bool), exact_truth(bool|null), disclosure_bits(int), runtime_s(float), frozen_param_provenance(polar_commit/version/params)`。
   - **每1024-block聚合**：`block_id, source, frame_ids[4], verified_accept=(4帧全部success&&verification ?1:0), leak=Σ4 disclosure, runtime=Σ4, exact=(4帧exact全真?1:0 else null若任一null else 0)`；**禁止由aggregate FER推导per-block**。
   - **预算硬帽**：`180 frames exactly once`（`45×4`），无重试、无调参、无增量；任一多跑/少跑即 `EVIDENCE_INVALID`。
   - **写出位置**：`comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/`（decoder前建，fail-closed），文件 `polar_replay_frames.json/.csv (180行) + polar_replay_blocks.json/.csv (45行) + polar_replay_manifest.json + v62r1_paired_registry.json (copy) + v62r1_api_readiness.json`；CSV/JSON行对等；禁写NPZ；本轮P0**不创建**此目录，仅冻结契约与空骨架。
   - **不触项**：不跑NB-LDPC，不算PIE/SKR，不改Polar参数，不写Polar Release。

5. **Lifecycle与门禁冻结**：本轮 `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，`production_outputs_created=false`；任何Polar重放正式执行需 `API READY + registry frozen + 独立plan ACCEPT + 显式 POLAR_REPLAY_EXECUTE_AUTH 绑定到精确实现SHA + registry hash + Polar commit + budget180`；pre-EXECUTE review五项必验（`HEAD==origin==SHA`、`ACCEPTED_PLAN_SHA`重推导且 `rg <stale>`0命中、`run_01`不存在、budget/registry/provenance一致、`py_compile+关键测试PASS`），FAIL阻塞执行。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v62r1-polar-per-frame-replay-export/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）+ `scripts/v62r1_polar_api_probe.py` (decoder-free, `rg "decode_nbldpc|construct_" 0 hits`, `py_compile PASS`，只读定位Polar入口/params/I/O/frame_id) + `docs/research_cycles/V62R1/v62r1_api_readiness.json`（探针输出，含 `polar_commit/version/candidates/provenance/missing_fields/readiness`）+ `docs/research_cycles/V62R1/v62r1_paired_registry.json`（若READY则45块权威，否则空骨架+`REGISTRY_INSUFFICIENT`标记）+ `docs/research_cycles/V62R1/V62R1_REPLAY_PREPARATION_REPORT.md`（机械提取表+注册表+契约）。
- **未来实现（本轮不创建，仅预冻结接口）**：`comparison_bench/src/comparison_bench/formal_ir/v62r1_polar_replay.py`（仅组合冻结Polar调用+registry 180帧+逐帧/逐块契约写出）+ `scripts/execute_v62r1_polar_replay.py`（默认拒绝，需 `--execution-authorized --authorized-target-sha <sha>`）；均**仅当API READY + 独立plan ACCEPT + POLAR_REPLAY_EXECUTE_AUTH 后才允许创建**，且预算恰好180一次。
- **只读依赖**：`D:\Code\HD-QKD_Polar_Release`（只读，`git diff -- ../HD-QKD_Polar_Release ==0` 语义）+ `comparison_bench/src/comparison_bench/io/pairs_loader.py` (`load_pairs_table/normalize`) + `dataset_builder.py` (`build_frame_batch`) + `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/*`（仅作兼容源排除与provenance校验参考）+ `comparison_bench/outputs_comparison/v55_intake_20260828` 仅作 incompat排除负例。
- **不修改**：任何既有spec/代码/测试/输出、`V62/V55/V61` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不改 `D:\Code\HD-QKD_Polar_Release`；不创建正式 `polar_replay_v62r1/run_01` 与 `formal_ir_methods/v62_*/run_01`。

## Acceptance Criteria

- [ ] 四工件齐全一致且lifecycle为 `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED`，plan HEAD绑定 `b37c78b7` 前缀（重核完整40位），`branch formal-ir-mainline`，`data SHA 84d62779` 已记录，`implementation_started=false`，`production_outputs_created=false`，明确「未获 `POLAR_REPLAY_EXECUTE_AUTH` 前不得执行重放，不改Polar Release，不跑NB-LDPC，不算PIE/SKR，不自动启动V62 benchmark」。
- [ ] Phase A机械可复现：`D:\Code\HD-QKD_Polar_Release` 上Polar入口/冻结参/输入格式/逐帧输出语义/frame_id稳定性 已通过decoder-free探针机械定位，每项 `file/function/key` 已记录，无手填，`rg`可复现；`verification/leak/runtime/frame_id` 四字段完备性已判定，缺一即 `POLAR_REPLAY_API_NOT_READY` 已正确停止，不伪造。
- [ ] Phase B公平注册可机械校验：`45 blocks (15/source) =180 frames` 的 `block_id/source/frame_ids[4]/materialization_hash/provenance` 已冻结，`1024-block (4×256) + pairing nearest legacy_v1 + dimension 1024 + bin_width 200ps + source分层` 已冻结，`frame_ids[4]` 严格连续递增且全局唯一，不用V55域不兼容输入，不按outcome选块，未满足即 `REGISTRY_INSUFFICIENT` 停止。
- [ ] Phase C输出契约已冻结：每256-frame行 `frame_id/source/block_id/success/verification/exact(null)/disclosure/runtime/provenance` 与每1024-block聚合 `verified_accept/leak(Σ4)/runtime(Σ4)/exact` 已显式，预算恰好180一次，不跑NB-LDPC，输出additive新目录 `polar_replay_v62r1/run_01` 不写Polar Release，`PIE/SKR` 未算已验。
- [ ] 预注册三终态已冻结：`REPLAY_READY / POLAR_REPLAY_API_NOT_READY / EVIDENCE_INVALID` 互斥且 `EVIDENCE_INVALID`优先；`POLAR_REPLAY_API_NOT_READY` 时不创建registry正式版与run_01，不进Phase C执行；`REPLAY_READY` 需 `per-frame verification/leak/runtime/frame_id` 完备且registry 45块可校验。
- [ ] 本轮产出边界已冻结：仅四工件+API探针+registry骨架/报告，**禁production module/CLI/tests/正式output root/执行重放/自授EXECUTE_AUTH**；探针 `rg "decode_nbldpc" 0 hits`、`py_compile PASS`、`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v62/ ==0 && git diff -- ../HD-QKD_Polar_Release ==0`（除本变更外零改），`run_01`不存在，正式重放未触发。
- [ ] 已推送并停在 `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` 等待独立plan review + API探针复核。

## Tasks

见 `tasks.md`（Phase A Polar API只读定位与可行性判定；Phase B 45块公平注册；Phase C 逐帧/逐块输出契约与预算；Pre-EXECUTE门禁与推送后停止）。

## Lifecycle

前代 `formal-ir-v62-nbldpc-polar-reference-benchmark` (`V62P0`, `PLAN_CANDIDATE / DEVELOPMENT_BENCHMARK / EXECUTE_NOT_AUTHORIZED`) 与 `formal-ir-v55`/`formal-ir-v61` 共存；本变更 `V62R1` 为V62前置 `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED`（HEAD `b37c78b7`, branch `formal-ir-mainline`, data SHA `84d62779`），止于plan + API探针，未READY前禁止重放实现/执行；`REPLAY_READY` 后仍需独立 `POLAR_REPLAY_EXECUTE_AUTH` 绑定到精确实现SHA + registry hash + Polar commit + budget180 才可一次性重放180帧；本轮仅四工件+探针+骨架，180帧为future V62 paired的唯一Polar侧输入。
