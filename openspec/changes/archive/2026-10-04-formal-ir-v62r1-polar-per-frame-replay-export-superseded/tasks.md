# OpenSpec Tasks: formal-ir-v62r1-polar-per-frame-replay-export — Polar逐帧重放导出 (V62前置)

**Lifecycle**: `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` — **仅plan + decoder-free API探针，未READY前禁止实现/执行重放，不改Polar Release，不跑NB-LDPC，不算PIE/SKR**
**HEAD**: `b37c78b7` → 新Plan SHA (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == b37c78b7` 重核，不一致阻塞) + data SHA `84d62779` (d1024 bw200 nearest legacy_v1)
**Predecessor**: `formal-ir-v62-nbldpc-polar-reference-benchmark` (`V62P0`, HEAD `6a3b873e`) 前置；`formal-ir-v55`/`formal-ir-v61` 共存不改
**Boundary**: 每block 1024 (=4×256 frames), budget 180 exactly once, Polar只读外层调用，缺逐帧verification/leak/runtime/frame_id任一即 `POLAR_REPLAY_API_NOT_READY` 停止

## Phase A — Polar API只读定位与可行性判定（decoder-free，禁止手填，file/function/key）

- [ ] **A1 fetch与HEAD自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline == b37c78b7` 完整40位，不一致阻塞；记录 `HEAD/origin/implementation SHA` 至报告 `provenance`，`rg "6a3b873e|efd34ef" 0 hits` 旧SHA无残留（除历史记录），`rg "b37c78b7"` 新起点已验；`data SHA 84d62779` 已验
- [ ] **A2 Polar Release只读定位（只读，不改）**：对 `D:\Code\HD-QKD_Polar_Release` 执行 `rg "def decode|class.*Decoder|polar.*decode|run_polar|reconcile" --type py -n` + `rg "code_len|list_size|crc|quant|iterations" --type py -n` + `glob experiments/*.py, src/reconciliation/**` 机械定位Top3候选 `path:function:signature`，记录每候选 `stat.mtime/size` 与 `inspect.signature` 形参，`git diff -- ../HD-QKD_Polar_Release ==0` 已验（只读），`rg "polar_existing" 0 hits` 在Polar Release侧无侵入
- [ ] **A3 冻结参数机械提取（file/function/key，零手填）**：对Top1候选解析 `code_len, rate, list_size, crc_bits, quant, iterations, dimension, bin_width_ps, threshold_ps, pairing_rule` 每项记录 `file=path + function=candidate + key=param` 的 `line:expr`，缺一即 `API_NOT_READY`；`rg "PIE|SKR|finite.key" 0 hits` 在本变更不算PIE/SKR已验
- [ ] **A4 输入格式判定（预构造symbols直输）**：`inspect.signature(candidate)` 是否接受 `np.ndarray symbols shape (180,256) dtype int in [0,1024)` 或 `FrameBatch(q=1024,frame_len=256)` 或 `pairs.parquet` 已配对输入，而非强制 `ttbin/raw→pairing` 重跑；以signature与最小可构造symbols dry-run（不触decoder执行，仅 `import + signature`）为准，`input_accepts_prebuilt: bool` 已落盘
- [ ] **A5 逐帧输出语义判定（per-frame完备性）**：对候选return注解/docstring/ `rg "verification|disclosure|runtime|frame_id" -n` 判定是否原生返回每帧 `decode_success(bool) / verification_pass(bool) / disclosure_bits(int) / runtime_s(float) / frame_id(int)`；`verification_pass` 需可区分 `decode_fail` vs `success但verify_fail`；`disclosure` 需 `bits/frame` 粒度非仅aggregate；`per_frame_fields: {success,verification,disclosure,runtime,frame_id}: bool` 已落盘，任一false即 `POLAR_REPLAY_API_NOT_READY`
- [ ] **A6 frame_id稳定性（有序一一映射）**：验证 `input_frame_ids == output_frame_ids` 有序相等（dry-run不执行decoder，仅signature/contract校验）；记录 `frame_id_stable: bool`，`hash(frame_ids)` 一致性已验
- [ ] **A7 API就绪判定（first-match）**：
  ```
  if not frozen_params_complete or not input_accepts_prebuilt or not per_frame_fields_all_true or not frame_id_stable:
      overall = V62R1_POLAR_REPLAY_API_NOT_READY  # 立即停止，不伪造，不手填
  else:
      overall = V62R1_API_READY  # 可进Phase B
  ```
  `first-match` 显式记录，`missing_fields: list[str]` 已落盘 `v62r1_api_readiness.json`

## Phase B — 公平数据注册（机械冻结，逐帧对应优先，按序first-match，未对齐停止）

- [ ] **B1 冻结处理点与块形态（单点84d62779）**：冻结 `dimension 1024, bin_width 200ps, pairing nearest legacy_v1, FRAME_LEN 256, BLOCK_LENGTH 1024, q=1024, FRAME_LEN*4==BLOCK_LEN`，记录 `data SHA 84d62779` 语义，不改
- [ ] **B2 可重放性校验（hash比对，decoder-free）**：对兼容源每块 `source_path` 的 `pairs.parquet / sidecar a_eff.npy+b_eff.npy` 执行 `load_pairs_table(path)->normalize_pair_columns->build_frame_batch(q=1024, frame_len=256)` 无损恢复，校验 `alice/bob ∈[0,1024)` 且 `n_complete==n_rows//256 ≥60 per source` 且 `rows_used==n_keep` 无尾帧残留，抽样 `sha256(alice.tobytes()+bob.tobytes())` 与registry `materialization_hash` 一致性已验
- [ ] **B3 V55 domain-incompatible排除（硬门）**：检查若来源为 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` 的 `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` 或 `256/frame` 非 `1024-block legacy_v1` 或 `dimension≠1024` 或 `bin_width≠200ps` 或 `pairing_mode != nearest`，则判 `V55_DOMAIN_INCOMPATIBLE` 禁用，不纳入注册集，记录 `v55_excluded_blocks.csv`，`rg "v55" 排除已验`
- [ ] **B4 不重估先验校验（只读）**：确认比较集构建不读取新比较块做训练，不触 `V25 channel_counts.npz`，`prior_is_train_only=true` 已验（本变更不重估先验）
- [ ] **B5 不按outcome选块（公平性）**：选块仅按 `index_j=floor(j*(K-1)/14)` 分散或机械可用顺序，不以 `success/verification/leak/runtime` outcome选块，`selection_by_outcome==false` 已验
- [ ] **B6 Paired registry冻结（若API READY）**：落盘 `docs/research_cycles/V62R1/v62r1_paired_registry.json` (authoritative, `S=3 B=15 total45/180`，每块 `block_id, source(1M/1p5M/2M), frame_ids[4] (strict increasing consecutive), held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, FRAME_LEN 256, sampling_mode=paired_polar_replay_v62r1, Polar source_path+commit, materialization_hash`)，`frame_ids` 全局唯一且未来与Polar输出 `frame_id` 一一对应，`K=45` 可机械校验，`gap≥1` 若超集分散则 `index_j` 否则直接取45，`git diff -- ../HD-QKD_Polar_Release ==0` 已验，**禁换块**
- [ ] **B7 对齐判定（first-match，REGISTRY_INSUFFICIENT停止）**：
  ```
  if not api_ready or not frozen_params_complete:
      overall = V62R1_POLAR_REPLAY_API_NOT_READY  # 优先，不进registry
  elif K_aligned<45 or per_source<15 or not replayable or V55_DOMAIN_INCOMPATIBLE or pairing_mismatch:
      overall = V62R1_REGISTRY_INSUFFICIENT  # 停止，不伪造
  else:
      overall = V62R1_REGISTRY_READY  # 可冻结registry，待Phase C
  ```
  `V62R1_REGISTRY_INSUFFICIENT` 时不创建registry正式版（仅空骨架+缺口记录），不进Phase C执行

## Phase C — Polar逐帧输出契约（预算恰好180，一次，decoder-free契约冻结）

- [ ] **C1 每256-frame契约冻结**：冻结 `frame_id, source, block_id, decode_success(bool), verification_pass(bool), exact_truth(bool|null), disclosure_bits(int), runtime_s(float), frozen_provenance{polar_commit/version/code_len/rate/list/crc/quant/iter/dimension/bw/threshold/pairing}`，`exact_truth=null` 当且仅当Polar无ground truth可比，不得由success推导exact，已验
- [ ] **C2 每1024-block聚合冻结（R62-03对齐，禁止aggregate拼帧）**：冻结 `block_id, source, frame_ids[4], verified_accept=(4帧全部success&&verification?1:0), leak=Σ4 disclosure, runtime=Σ4, exact=(4帧exact全真?1:0 else null若任一null else 0)`，禁止 `round(aggregate*45)` / aggregate FER拼per-block / accepted直比exact，已验
- [ ] **C3 预算硬帽180 exactly once**：冻结 `45 blocks ×4 frames =180 frames exactly once`，无重试、无调参、无增量；任一多跑/少跑即 `EVIDENCE_INVALID`，`budget==180` 已验
- [ ] **C4 写出位置与文件契约（additive新目录，不写Polar Release）**：冻结未来授权后写出根 `comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/`（decoder前建，fail-closed），文件 `polar_replay_frames.json/.csv (180行)+polar_replay_blocks.json/.csv (45行)+polar_replay_manifest.json+v62r1_paired_registry.json(copy)+v62r1_api_readiness.json(copy)`，CSV/JSON行对等，禁写NPZ，已验不写Polar Release (`git diff -- ../HD-QKD_Polar_Release ==0`)
- [ ] **C5 不触项冻结**：`rg "decode_nbldpc|compute.*PIE|SKR" 0 hits` 在重放探针/契约中，不跑NB-LDPC，不算PIE/SKR，不改Polar参数，不自动启动V62 benchmark，已验
- [ ] **C6 undetected隔离语义（若exact存在）**：若 `exact_truth` 非null，则 `undetected = verification_pass && !exact_truth` 单独表永不并入 `verified_accept`，`undetected>0` 仅报告不并入success，已验

## Phase D — Pre-EXECUTE门禁与报告交付（PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED，普通推送后停止）

- [ ] **D1 编写 `scripts/v62r1_polar_api_probe.py`** (decoder-free, 必验)：`python scripts/v62r1_polar_api_probe.py [--polar-root D:/Code/HD-QKD_Polar_Release] [--pairs-root ...] [--out docs/research_cycles/V62R1/v62r1_api_readiness.json]` → A2-A6 定位/冻结/输入/逐帧/frame_id判定 → 输出 `v62r1_api_readiness.json` + 控制台摘要，`rg "decode_nbldpc|construct_" 0 hits`，`py_compile PASS`，未创建 `run_01`，不改 `src//experiments//tools/` 且 `openspec/changes/formal-ir-v62/ ==0`
- [ ] **D2 执行API探针（decoder-free，只读）**：执行 `python scripts/v62r1_polar_api_probe.py` 记录 `polar_commit/version/candidates[Top3]/frozen_params/input_accepts_prebuilt/per_frame_fields/frame_id_stable/missing_fields/readiness/overall`，`overall==POLAR_REPLAY_API_NOT_READY` 时落盘缺口报告并停止，不伪造
- [ ] **D3 撰写 `docs/research_cycles/V62R1/V62R1_REPLAY_PREPARATION_REPORT.md`**：`Polar API机械定位表` (commit/version/Top3 candidates/每项file/function/key/输入直输判定/逐帧字段完备性/frame_id稳定性/missing_fields/overall) + `公平注册表` (处理点84d62779, 1024-block=4×256, pairing, source分层, V55排除, 不按outcome选块, registry 45/180) + `Phase C输出契约` (每帧180行/每块45行/budget180/frozen provenance/写出位置) + `三终态与API硬门` + `overall终态 (READY或API_NOT_READY或REGISTRY_INSUFFICIENT)` 与规范闭合声明，数据与 `json` 一致，显式 `Polar只读不改 + budget180 + 不跑NB-LDPC + 不算PIE/SKR + 不自动启动V62`
- [ ] **D4 自检（gate）**：`py_compile PASS, rg "decode_nbldpc" 0 hits && rg "construct_" 0 hits` (探针侧)，`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v62/ ==0 && git diff -- ../HD-QKD_Polar_Release ==0` (除本变更外零改)，`budget==180` 已验，`FRAME_LEN 256` 已验，`BLOCK 4×256` 已验，`45/180` 已验，`HEAD==origin (b37c78b7)` 已验，`run_01`不存在已验，正式重放未触发已验
- [ ] **D5 普通推送新Plan SHA并停留 `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED`**（基于 `b37c78b7`），未创建任何 `run_01` 正式输出，不碰 `V62/V55/V61` 状态，`src//experiments//tools//V62` 零改，普通推送（非force）至 `formal-ir-mainline`，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试PASS`），`V62R1` 仍 `PLAN_CANDIDATE`，返回 `Plan SHA / implementation SHA / Polar provenance / readiness / registry / overall`，**不自动进入Polar重放执行，不实现正式runner**

## 本变更显式禁止

decoder调用（`decode_*` 实际执行）在探针中；改Polar任何冻结参或新增矩阵；跑NB-LDPC；重跑TTBin配对；自创 `PIE/SKR/finite-key/composable` 公式或造 `eps` 参数；用旧数据伪造对齐（无相同符号重放时伪造 `frame_ids`）；重复计算或推导 `frame` 粒度；将aggregate掩盖per-frame阈值；网格调参；把V55非legacy_v1输入当1024-block；宣称 `FER/SKR/阈值/晋升`；创建正式 `run_01` 重放执行；改 `src//experiments//tools//V62`；将本变更直接当V62 `COMPETITIVE`证据；在 `POLAR_REPLAY_API_NOT_READY` 时仍进入registry/重放；实现正式runner/启动正式重放（本轮仅4工件+探针骨架，普通推送新Plan SHA后停止）。

## 验收

- proposal/design/tasks/specs一致HEAD `b37c78b7`→新Plan SHA 84d62779 lifecycle PLAN_CANDIDATE POLAR_REPLAY_PREPARATION EXECUTE_NOT_AUTHORIZED；Polar API机械定位 `file/function/key` 已落盘，三终态按 `EVIDENCE_INVALID > POLAR_REPLAY_API_NOT_READY > REPLAY_READY` 互斥先匹配，**缺逐帧verification/leak/runtime/frame_id任一即 `POLAR_REPLAY_API_NOT_READY` 立即停**，不伪造
- Phase A Polar `入口/冻结参/输入直输/逐帧语义/frame_id稳定性` 逐项 `file/function/key` 已覆盖，每项 `source(file:line:expr)/authority=POLAR_RELEASE_FROZEN/ readiness` 已定义，`per_frame_fields` 完备性已验
- Phase B `45 blocks (15/source)=180 frames` 的 `1024=4×256 + pairing nearest legacy_v1 + dimension 1024 + bin_width 200ps + source分层 + 不按outcome选块 + V55域排除` 已冻结，`frame_ids[4]` 严格连续全局唯一，`materialization_hash` 已验，未满足即 `REGISTRY_INSUFFICIENT` 停止已验
- Phase C 每帧 `frame_id/source/block_id/success/verification/exact(null)/disclosure/runtime/provenance` 与每块 `verified_accept/leak(Σ4)/runtime(Σ4)/exact` 已冻结，预算恰好180一次，不跑NB-LDPC，不算PIE/SKR，已验
- Phase D 探针 `rg 0 hits` `py_compile` PASS 报告与 `json` 一致 未建 `run_01` 未进正式重放 未重跑TTBin 未改 `V62` 已普通推送新Plan SHA `PLAN_CANDIDATE/POLAR_REPLAY_PREPARATION/EXECUTE_NOT_AUTHORIZED` 仅改本目录+`scripts/`+`docs/research_cycles/V62R1/`（`src//experiments//tools//V62` 零改），`HEAD==origin (b37c78b7)` 已验，推送后等待独立审核，**不自动进入Polar重放，不实现正式runner**
