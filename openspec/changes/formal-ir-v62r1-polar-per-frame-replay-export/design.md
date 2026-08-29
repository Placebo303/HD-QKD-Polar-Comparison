# OpenSpec Design: formal-ir-v62r1-polar-per-frame-replay-export

**Lifecycle**: `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` — **仅plan + decoder-free API探针，未READY前禁止实现/执行重放，不改Polar Release，不跑NB-LDPC**
**Cycle**: `V62R1`
**Predecessor**: `formal-ir-v62-nbldpc-polar-reference-benchmark` (`V62P0`, HEAD `6a3b873e`) — 本变更为V62的**前置重放准备**，补齐V62缺的逐帧输入/输出层
**Freeze HEAD**: `b37c78b7` (branch `formal-ir-mainline`, 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) — **data SHA** `84d62779` (`d=1024 bw=200 pairing=nearest rule=legacy_v1` 单点)
**Feasibility**: Polar算法在 `D:\Code\HD-QKD_Polar_Release` 上已固化；唯一待验为**外层能否以冻结参数直接输入预构造256-symbol symbols并逐帧取回 verification/leak/runtime/frame_id**（若不可则V62无法逐帧对应，直接 `POLAR_REPLAY_API_NOT_READY`）。

## 1. 科学问题与关键判断

> 在**完全冻结Polar参数**下，能否通过**外层调用**对**未来V62的同一45个NB-LDPC blocks对应180个256-symbol frames**生成**逐帧可审计**的 `success/verification/exact/disclosure/runtime/frame_id`，以**重开**V62的 `Polar_block_verified_accept vs NB_verify_final` paired对比？价值判定不在本变更，**本变更仅冻结重放通道的输入/输出/预算/ provenance**。

- **对照**：单一重放臂为Polar Release冻结实现（只读外层调用，不改源码，不重跑TTBin）；NB-LDPC不参与本变更；V62 future对比为 `Polar 180帧逐帧 → 45块聚合` vs `NB-LDPC 45块`。
- **不改项**：不改Polar `code_len/rate/list/CRC/quant/iter/dimension/bin_width/pairing/threshold` 任一冻结量；不新增Polar参数；不重估先验；不算PIE/SKR。
- **逐帧优先**：`180 frames =45×4` 规模使每1024-block的 `verified_accept=4帧全success&&verify` 可机械判定；预算恰好180一次；每源15块平衡，registry禁换块。
- **通过后的claim边界**：即使 `REPLAY_READY`，仍仅为**Polar侧逐帧导出的准备证据**（绑定 `Polar commit/version` + `registry hash` + 冻结参），不等同V62 `COMPETITIVE`或FER/阈值/SKR/资格/晋升；报告显式 `POLAR_REPLAY_PREPARATION`。

## 2. 冻结语义 — Polar侧只读与V62锚点

### 2.1 固定不变项（跨V62/V62R1共享）

| 项 | 冻结值 | 来源 |
|---|---|---|
| `FRAME_LEN` | 256 symbols/frame | 本变更新增冻结（Polar 256-frame ↔ NB-LDPC 1024-block =4×256） |
| `BLOCK_LEN` | 1024 symbols/block (=4 frames) | V31/V54/V62 |
| `S,B,total` | 3 sources ×15 =45 blocks =180 frames | 本变更冻结（Phase B） |
| `d` | 1024 | `84d62779` 语义 |
| `bw` | 200 ps | `84d62779` 语义 |
| `pairing` | `nearest legacy_v1` | `84d62779` 语义 |
| `q` | 1024 (`0..1023`) | `bits_per_symbol` 10 bits/symbol（Polar symbol域） |
| `data SHA` | `84d62779` (`d=1024 bw=200 pairing=nearest`) | V54/V55 semantics |
| `budget` | 180 frames exactly once | 本变更硬帽（无重试/无调参） |

- NB-LDPC侧 `H1/Lane C/H_inc/m2/decoder/prior/verification 90/1.0 poly37` 仍由V62冻结，本变更不触（`rg "H1|Lane C|H_inc" 0 hits` 在探针侧）。
- Polar侧code/rate/list/CRC/quant/iter待Phase A机械提取后冻结为 `frozen_polar_params`（每项 `file:line:expr`）。

### 2.2 Polar Release只读语义（不改仓）

| 提取项 | 机械来源 `file/function/key` | 语义 |
|---|---|---|
| Polar版本/commit/provenance | `D:\Code\HD-QKD_Polar_Release: git rev-parse HEAD + git log -1 --oneline + experiments/run_real_polar_max_pie.py:__version__` | 只读，不改Polar Release |
| decoder入口候选 | `rg "def decode|class.*Decoder|polar.*decode|run_polar|reconcile" D:\Code\HD-QKD_Polar_Release --type py -n` + `src/reconciliation/**` + `experiments/*.py` | Top3 `path:function:signature` |
| 冻结参数 | `rg "code_len|list_size|crc|quant|iterations|dimension|bin_width|threshold|pairing" D:\Code\HD-QKD_Polar_Release --type py -n` + `inspect.signature(candidate)` | 每项 `file:line:expr`，缺一即 `API_NOT_READY` |
| 输入格式 | `inspect.signature(candidate)` 是否接受 `symbols: ndarray[180,256] int in [0,1024)` 或 `FrameBatch` | 需支持预构造symbols直输，不强制TTBin重配对 |
| 输出语义 | candidate return annotation / docstring / `rg "verification|disclosure|runtime|frame_id" -n` | 每帧 `success/verification/disclosure/runtime/frame_id` 是否原生逐帧 |
| frame_id稳定性 | `input_frame_ids == output_frame_ids` 有序相等（dry-run不执行decoder，仅signature校验） | 逐帧可追溯 |

- `verification` 需区分 `decode_fail` vs `success但verify_fail`；`disclosure` 需bits/frame粒度；`runtime` 需秒级per-frame或可分解；`frame_id` 需稳定唯一。
- 任何 `git diff -- ../HD-QKD_Polar_Release !=0` 即 `EVIDENCE_INVALID`。

### 2.3 数据裁决（对齐门，V55 domain-incompatible排除）

- **V55 intake不兼容域**：`comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` 的 `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` 或 `256/frame` 非 `1024-block legacy_v1` 或 `pairing_mode != nearest` 判 `V55_DOMAIN_INCOMPATIBLE` 禁用（探针显式校验）。
- **可重放判定**：`pairs.parquet` 或 `sidecar a_eff.npy+b_eff.npy` 经 `load_pairs_table→normalize_pair_columns→build_frame_batch(q=1024, frame_len=256)` 可无损恢复 `alice/bob ∈[0,1024)` 且 `n_complete == n_rows//256 ≥15*4=60 per source` 且 `rows_used==n_keep` 无尾帧残留，`hash(alice||bob)` 逐块比对将与Polar重放输入一致（registry落盘时记录）。
- **未就绪停止**：若 `K_aligned<45` 或 per source `<15` 或 `pairing/dimension/bw` 不一致或不支持预构造symbols直输或缺逐帧 `verification/disclosure/runtime/frame_id` 任一，则 `V62R1_POLAR_REPLAY_API_NOT_READY` 或 `V62R1_REGISTRY_INSUFFICIENT` 停止，不伪造。

### 2.4 合格注册样本（paired 45-block =180-frame，冻结）

- **目标域**：`D_target = {1M,1p5M,2M} × 15 blocks ×4 frames`，处理点 `d1024 bw200 pairing nearest legacy_v1` 单点 `84d62779`。
- **结构**：每帧256 symbols，每块4连续帧，`frame_ids[4]` 严格递增连续，`0..N-1` 全局唯一，`BLOCK_LENGTH=1024, FRAME_LEN=256`。
- **主样本**：`S=3,B=15,total45/180`，若兼容超集 `K>45` 则 `index_j=floor(j*(K-1)/14) j=0..14` 分散选15/source，否则判 `REGISTRY_INSUFFICIENT`。
- **标识**：`block_id, source, frame_ids[4] (identical future Polar/NB-LDPC), held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, FRAME_LEN 256, sampling_mode=paired_polar_replay_v62r1, Polar source_path+commit, materialization_hash=sha256(alice||bob) per block`，**禁换块**。
- **Provenance**：每源 `pairs` 来源 `source_path + polar_commit + materialization_hash` 三绑定。

## 3. Phase A — API可行性（decoder-free，只读）

### 3.1 探针流程（`scripts/v62r1_polar_api_probe.py`）

```
fetch HEAD == origin/formal-ir-mainline == b37c78b7  (完整40位，不一致阻塞)
locate Polar Release candidates (rg Top3)
for each candidate:
  frozen_params = extract params (file:line:expr)
  input_accepts_prebuilt = inspect.signature accepts symbols/FrameBatch? (bool)
  per_frame_fields = {success, verification, disclosure, runtime, frame_id} native? (bool[5])
  frame_id_stable = input_ids == output_ids ? (signature dry-run, no decode)
readiness = all(frozen_params complete && input_accepts_prebuilt && per_frame_fields all true && frame_id_stable)
if not readiness: overall = V62R1_POLAR_REPLAY_API_NOT_READY
else: overall = V62R1_API_READY  (可进Phase B)
```

- `rg "decode_nbldpc|construct_" 0 hits` 在探针侧；`py_compile PASS`；不调用实际decoder（`no decode_* execution`）。
- 落盘 `docs/research_cycles/V62R1/v62r1_api_readiness.json`（`polar_commit, polar_version, candidates[], frozen_params[], input_accepts_prebuilt, per_frame_fields, frame_id_stable, missing_fields, readiness, overall`）。

### 3.2 门G1-G5（decoder-free分层）

| 门 | 检查项 | 探针判定 |
|---|---|---|
| G1 | Polar文件可读且入口可定位 | `rg` Top3非空且 `inspect.signature` 可得 |
| G2 | 冻结参数完整 | `code_len/rate/list/crc/quant/iter/dimension/bw/threshold/pairing` 每项 `file:line:expr` 齐全 |
| G3 | 支持预构造symbols直输 | `input_accepts_prebuilt==true`（`symbols ndarray` 或 `FrameBatch`） |
| G4 | 逐帧输出完备 | `success && verification && disclosure && runtime && frame_id` 均为per-frame原生 |
| G5 | frame_id稳定 | `input_frame_ids == output_frame_ids` 有序相等（signature dry-run） |

- G1-G5全PASS ⇒ `API_READY`；任一FAIL ⇒ `POLAR_REPLAY_API_NOT_READY` 停止。

## 4. Phase B — 公平注册（机械冻结，逐帧对应优先）

### 4.1 处理点单点冻结

- `84d62779` 语义单点：`dimension 1024, bin_width 200ps, pairing nearest legacy_v1, FRAME_LEN 256, BLOCK_LENGTH 1024`。

### 4.2 可重放性（hash比对）

- `load_pairs_table→normalize→build_frame_batch(q=1024, frame_len=256)` 对同一 `source_path` 可恢复 `alice/bob ∈[0,1024)` 且 `n_complete==n_rows//256` 且 `rows_used==n_keep`。
- 抽样 `sha256(alice.tobytes()+bob.tobytes())` 逐块记录 `materialization_hash`。

### 4.3 对齐判定（first-match）

```
if not api_ready or not frozen_params_complete:
    overall = V62R1_POLAR_REPLAY_API_NOT_READY  # 优先于registry
elif K_aligned<45 or per_source<15 or not replayable or V55_DOMAIN_INCOMPATIBLE or pairing_mismatch:
    overall = V62R1_REGISTRY_INSUFFICIENT  # 停止，不伪造
else:
    overall = V62R1_REGISTRY_READY  # 可冻结registry
```

- `K_aligned` 为兼容超集可重放的block数；`per_source` 每源15才合法。
- `REGISTRY_INSUFFICIENT` 时不创建正式registry，报告仅记录缺口。

### 4.4 Registry权威

- `docs/research_cycles/V62R1/v62r1_paired_registry.json` (authoritative): `S=3 B=15 total45/180`，每块 `block_id, source, frame_ids[4] (strict increasing consecutive), held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, FRAME_LEN 256, sampling_mode=paired_polar_replay_v62r1, Polar source_path+commit, materialization_hash`。
- 分散 `index_j=floor(j*(K-1)/14)`；`frame_ids` 全局唯一且将来与Polar输出 `frame_id` 一一对应；`git diff -- ../HD-QKD_Polar_Release ==0` 已验，禁换块。

## 5. Phase C — Polar逐帧输出契约（预算恰好180）

### 5.1 每256-frame行（180行）

```
frame_id: int (global unique, stable)
source: enum 1M/1p5M/2M
block_id: str (e.g. 1M_00 .. 2M_14)
decode_success: bool
verification_pass: bool
exact_truth: bool | null (若Polar侧有ground truth比对否则null)
disclosure_bits: int (per-frame leak)
runtime_s: float
frozen_provenance: {polar_commit, polar_version, code_len, rate, list_size, crc, quant, iter, dimension, bin_width, threshold, pairing}
```

- `exact_truth=null` 当且仅当Polar输出无ground truth可比；不得由 `success` 推导 `exact`。
- `disclosure` 与 `runtime` 需per-frame可计费；若Polar原生仅aggregate则判 `API_NOT_READY`（本契约不允许Σ推导单帧）。

### 5.2 每1024-block聚合（45行，R62-03对齐）

- `block_id, source, frame_ids[4], verified_accept = (4帧全部success&&verification ?1:0), leak = Σ4 disclosure_bits, runtime = Σ4 runtime_s, exact = (4帧exact全真?1:0 else null若任一null else 0)`。
- **禁止** `round(aggregate*45)` / aggregate FER拼per-block / accepted直比exact。

### 5.3 预算与写出

- **预算**：`180 frames exactly once`（`45×4`），无重试、无调参、无增量；任一多跑/少跑即 `EVIDENCE_INVALID`。
- **写出根**（decoder前建，fail-closed，仅future授权后）：`comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/`。
- **文件**：`polar_replay_frames.json/.csv (180行) + polar_replay_blocks.json/.csv (45行) + polar_replay_manifest.json + v62r1_paired_registry.json(copy) + v62r1_api_readiness.json(copy)`；CSV/JSON行对等；禁写NPZ；本轮P0不创建此目录，仅冻结契约。
- **不触**：不跑NB-LDPC，不算PIE/SKR，不改Polar参数，不写Polar Release。

## 6. 预算与门禁（已冻结，180硬帽）

- `180 frames exactly once`（`45 blocks ×4`），与V62的 `Polar 180帧 ↔ NB-LDPC 45块` 一一对应。
- 未来执行前守卫（pre-EXECUTE五项）：`HEAD==origin==implementation SHA`、`ACCEPTED_PLAN_SHA`重推导且 `rg <stale>`0命中、`run_01`不存在、budget180/registry/polar_commit一致、`py_compile+关键测试PASS`。
- `POLAR_REPLAY_EXECUTE_AUTH` 显式绑定 `implementation SHA + registry hash + Polar commit + budget180` 才可执行一次；FAIL阻塞执行。

## 7. 记录、聚合、summary（预冻结，未来执行）

每frame record schema（含 `tag_scope` 若Polar有tag则记录）：

```
frame_id, source, block_id, block_frame_index(0..3),
decode_success, verification_pass, exact_truth(null|bool),
disclosure_bits, runtime_s,
frozen_provenance{polar_commit, version, code_len, rate, list, crc, quant, iter, dimension, bw, threshold, pairing},
materialization_hash(block), held_out_ordinal
```

Summary含：`per-frame 180明细 + per-block 45聚合 + overall/per-source verified_accept/leak/runtime/exact + frozen provenance + registry hash + Polar commit`；`undetected` 语义在Polar侧按 `verification_pass && !exact_truth` 单独表（若exact存在）；`PIE/SKR` 不算。

## 8. 证据写出（预冻结，未来执行，不在本轮）

固定增量根（decoder前建，fail-closed）：

```
comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/
```

文件：`polar_replay_frames.json/.csv (180行) + polar_replay_blocks.json/.csv (45行) + polar_replay_manifest.json + v62r1_paired_registry.json + v62r1_api_readiness.json`；CSV/JSON行对等；禁写NPZ。**本轮P0不创建上述输出**，仅在 `docs/research_cycles/V62R1/` 紧凑记录 `v62r1_api_readiness.json + v62r1_paired_registry.json(或空骨架) + V62R1_REPLAY_PREPARATION_REPORT.md`。

## 9. 实现草图（后继轮次，当前未授权，需API READY + 独立plan ACCEPT + POLAR_REPLAY_EXECUTE_AUTH）

- `comparison_bench/src/comparison_bench/formal_ir/v62r1_polar_replay.py`：import Polar冻结入口，确定性180帧Polar调用（per frame `success/verification/exact/disclosure/runtime/frame_id`），逐帧/逐块契约写出，registry 45块一一对应，预算恰好180一次。
- `scripts/execute_v62r1_polar_replay.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin精确绑定未来实现SHA（plan `b37c78b7` + data SHA `84d62779` + registry hash + Polar commit）；五项pre-EXECUTE门；任一gate失败非零退出。
- 仅fake-runner测试通过后才可进入正式重放；不以outcomes选块或调参；不改Polar Release；不算PIE/SKR；不自动启动V62 benchmark。

## 10. 自由裁量 D1–D8（修订至 PLAN_CANDIDATE）

- D1 完全冻结Polar侧处理点与V62锚点（`d1024 bw200 nearest legacy_v1 FRAME256 BLOCK1024`），本变更不新增Polar参数。
- D2 单一预算180 frames exactly once，per-frame→per-block严格聚合，可机械校验。
- D3 Polar Release只读机械定位，`POLAR_REPLAY_API_NOT_READY` 时直接停止，不伪造接口。
- D4 paired 45-block注册：每源15块，若超集更大则分散 `index_j=floor(j*(K-1)/14)`，否则判 insufficient，禁换块。
- D5 每帧 `verification/leak/runtime/frame_id` 完备性硬门，缺一即 `API_NOT_READY`。
- D6 预注册三终态：`REPLAY_READY / POLAR_REPLAY_API_NOT_READY / EVIDENCE_INVALID`，`EVIDENCE_INVALID`优先。
- D7 哨兵frame_id稳定性抽检 + materialization_hash逐块绑定。
- D8 本轮仅交付四工件+API探针+registry骨架/报告，future重放仍仅Polar侧导出证据，不扩大为V62 `COMPETITIVE`或资格/晋升/安全证明。
