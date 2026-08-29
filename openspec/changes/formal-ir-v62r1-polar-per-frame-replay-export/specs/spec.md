# OpenSpec Spec: formal-ir-v62r1-polar-per-frame-replay-export

**Lifecycle**: `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` — 仅plan + decoder-free API探针，未READY前禁止重放实现/执行
**Change**: `formal-ir-v62r1-polar-per-frame-replay-export` (`V62R1`, branch `formal-ir-mainline`, HEAD `b37c78b7`, data SHA `84d62779`)
**Predecessor**: `formal-ir-v62-nbldpc-polar-reference-benchmark` (`V62P0`, HEAD `6a3b873e`) 前置 + `formal-ir-v55`/`formal-ir-v61` 共存

## 1. 变更类型与生命周期

- **Type**: `POLAR_REPLAY_PREPARATION` — Polar逐帧重放导出准备（`45 blocks =180 frames`，budget恰好180一次），非V62 paired benchmark执行、非qualification/promotion/安全证明。
- **Lifecycle**: `PLAN_CANDIDATE / POLAR_REPLAY_PREPARATION / EXECUTE_NOT_AUTHORIZED` — 本轮止于plan四工件 + decoder-free API探针 (`rg "decode_nbldpc" 0 hits`) + 空registry骨架，未READY即 `POLAR_REPLAY_API_NOT_READY` 停止，禁止任何Polar重放实现/执行与正式 `run_01` 创建。
- **Branch**: `formal-ir-mainline`；`HEAD` `b37c78b7` 实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞；本次推送新Plan SHA后停止。
- **Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200 pairing=nearest rule=legacy_v1`) — V62/V62R1共用锚点；Polar侧实际处理点以Phase A机械提取为准，Phase B逐块一致性校验。

## 2. 冻结语义（跨V62/V62R1共享，Polar侧只读）

### 2.1 不变量

- `FRAME_LEN =256 symbols/frame`, `BLOCK_LENGTH =1024 symbols/block (=4×256 frames)`，`S=3 (1M/1p5M/2M), B=15, total blocks 45, total frames 180`。
- `dimension 1024, bin_width 200ps, pairing nearest legacy_v1, q=1024 (0..1023), log2q=10 bits/symbol`，`data SHA 84d62779` 单点。
- `budget =180 frames exactly once`（`45×4`，无重试/无调参/无增量），`FRAME_LEN*4==BLOCK_LENGTH` 硬校验。
- NB-LDPC侧 `H1/Lane C/H_inc/m2/decoder/prior/verification 90/1.0 poly37` 仍由V62冻结，本变更不触（`rg "H1|Lane C|H_inc" 0 hits` 在探针侧）。
- Polar侧code/rate/list/CRC/quant/iter待Phase A机械提取后冻结为 `frozen_polar_params`（每项 `file:line:expr`），本变更不改其值。

### 2.2 禁止

- 禁改Polar任一冻结参、新增Polar参数、重跑TTBin配对、重估先验、算PIE/SKR/finite-key/composable；违者 `EVIDENCE_INVALID`。
- 禁改 `D:\Code\HD-QKD_Polar_Release` 任何文件（只读探针）；禁跑NB-LDPC decoder；禁把 `POLAR_REPLAY_API_NOT_READY` 降级为aggregate拼帧。
- 禁用 `V55 intake_20260828` domain-incompatible输入（`256/frame` 非 `1024-block legacy_v1`）。
- 探针中禁 `decode_*` 实际执行、`construct_*`、`import decoder` 执行路径（`rg "decode_nbldpc|construct_" 0 hits`, `py_compile PASS`），未创建 `run_01`。
- 禁自动启动V62 benchmark；即使 `REPLAY_READY`，V62仍需独立 `EXECUTE_AUTH`。

## 3. Phase A — Polar API只读机械定位（decoder-free）

### 3.1 定位入口

- `D:\Code\HD-QKD_Polar_Release` 上：
  - `rg "def decode|class.*Decoder|polar.*decode|run_polar|reconcile" --type py -n` + `experiments/run_real_polar*.py` + `src/reconciliation/**` → Top3 `path:function:signature`。
  - `rg "code_len|list_size|crc|quant|iterations|dimension|bin_width|threshold|pairing" --type py -n` + `inspect.signature(candidate)` → `frozen_polar_params[]` 每项 `file:line:expr`。
  - `rg "verification|disclosure|runtime|frame_id" --type py -n` → 逐帧语义判定。
- `comparison_bench/src/comparison_bench/io/pairs_loader.py:load_pairs_table` + `normalize_pair_columns` + `dataset_builder.py:build_frame_batch(q=1024,frame_len=256)` 仅作可重放性校验，不触Polar源码。

### 3.2 逐项记录（file/function/key，零手填）

每项Polar提取记录 `symbol, meaning, unit, source(file:line:expr or data_path:provenance), authority=POLAR_RELEASE_FROZEN, readiness`：

| 符号 | 含义 | 单位 | 来源 `file/function/key` |
|---|---|---|---|
| `polar_commit/polar_version` | Polar Release版本/commit | — | `D:\Code\HD-QKD_Polar_Release: git rev-parse HEAD / git log -1 --oneline / experiments/run_real_polar_max_pie.py:__version__` |
| `frozen_polar_params` |code/rate/list/crc/quant/iter/dimension/bw/threshold/pairing | — | `candidate file:line:expr` via `inspect.signature` + `rg` |
| `input_accepts_prebuilt` | 是否接受预构造symbols直输 | bool | `inspect.signature(candidate)` 含 `symbols/FrameBatch/ndarray[180,256]` |
| `per_frame_success` | 每帧decode_success原生 | bool | `rg "success|decode" -n` + return annotation |
| `per_frame_verification` | 每帧verification_pass原生 | bool | `rg "verification|verify|tag" -n` + return annotation |
| `per_frame_disclosure` | 每帧disclosure bits原生 | bool | `rg "disclosure|leak" -n` + return annotation |
| `per_frame_runtime` | 每帧runtime_s原生 | bool | `rg "runtime|elapsed|time" -n` + return annotation |
| `per_frame_frame_id` | 每帧frame_id稳定 | bool | `rg "frame_id" -n` + `input_ids==output_ids` |
| `frame_id_stable` | 输入输出frame_id有序一一映射 | bool | dry-run `hash(frame_ids)` 相等（不执行decoder） |

- `per_frame_fields = {success,verification,disclosure,runtime,frame_id}` 任一false → `POLAR_REPLAY_API_NOT_READY`。
- `beta_eff_empirical` 与 `PIE/SKR` 在本变更不算（V62侧 `POLAR_REFERENCE_PROXY` 语义保留）。

### 3.3 门G1-G5（decoder-free分层）

| 门 | 检查项 | 探针判定 |
|---|---|---|
| G1 | Polar文件可读且入口可定位 | `rg` Top3非空且 `inspect.signature` 可得 |
| G2 | 冻结参数完整 | `code_len/rate/list/crc/quant/iter/dimension/bw/threshold/pairing` 每项 `file:line:expr` 齐全 |
| G3 | 支持预构造symbols直输 | `input_accepts_prebuilt==true` |
| G4 | 逐帧输出完备 | `success && verification && disclosure && runtime && frame_id` 均为per-frame原生 |
| G5 | frame_id稳定 | `input_frame_ids == output_frame_ids` 有序相等 |

- G1-G5全PASS ⇒ `API_READY`；任一FAIL ⇒ `POLAR_REPLAY_API_NOT_READY` 停止，落盘 `v62r1_api_readiness.json` 显式缺口。

## 4. Phase B — 公平数据注册（逐帧对应优先，按序first-match）

### 4.1 处理点单点冻结

- `84d62779` 语义单点：`dimension 1024, bin_width 200ps, pairing nearest legacy_v1, FRAME_LEN 256, BLOCK_LENGTH 1024` — 单点，不泛化。

### 4.2 可重放性（hash比对）

- `load_pairs_table(path)->normalize_pair_columns->build_frame_batch(q=1024, frame_len=256)` 必须对同一 `source_path` 可恢复 `alice/bob ∈[0,1024)` 且 `n_complete==n_rows//256` 且 `rows_used==n_keep`。
- 抽样 `sha256(alice.tobytes()+bob.tobytes())` 逐块记录 `materialization_hash`，与未来Polar输入一致。

### 4.3 V55 domain-incompatible排除

- `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` 的 `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` 或 `256/frame` 非 `1024-block legacy_v1` 判 `V55_DOMAIN_INCOMPATIBLE=true`，禁止纳入注册集。

### 4.4 对齐判定（first-match）

```
if not api_ready or not frozen_params_complete:
    overall = V62R1_POLAR_REPLAY_API_NOT_READY  # 优先
elif K_aligned<45 or per_source<15 or not replayable or V55_DOMAIN_INCOMPATIBLE or pairing_mismatch:
    overall = V62R1_REGISTRY_INSUFFICIENT  # 停止，不伪造
else:
    overall = V62R1_REGISTRY_READY  # 可冻结registry
```

- `K_aligned` 为兼容超集可重放的block数；`per_source` 每源15才合法。
- `REGISTRY_INSUFFICIENT` 时不创建正式registry，报告仅记录缺口，不进Phase C。

### 4.5 Paired registry（若REGISTRY_READY）

- `docs/research_cycles/V62R1/v62r1_paired_registry.json` (authoritative): `S=3 B=15 total45/180`，每块 `block_id, source(1M/1p5M/2M), frame_ids[4] (strict increasing consecutive), held_out_ordinal_start/end, pairs_count 1024, BLOCK_LENGTH 1024, FRAME_LEN 256, sampling_mode=paired_polar_replay_v62r1, Polar source_path+commit, materialization_hash`。
- 若兼容超集 `K>45` 则 `index_j=floor(j*(K-1)/14) j=0..14` 分散选15/source，否则判 `REGISTRY_INSUFFICIENT`。
- `frame_ids` 全局唯一且将来与Polar输出 `frame_id` 一一对应；`git diff -- ../HD-QKD_Polar_Release ==0` 已验，禁换块。

## 5. Phase C — Polar逐帧输出契约（预算恰好180）

### 5.1 每256-frame行（180行）

- **schema**：`frame_id:int (global unique stable), source:enum 1M/1p5M/2M, block_id:str, decode_success:bool, verification_pass:bool, exact_truth:bool|null, disclosure_bits:int, runtime_s:float, frozen_provenance:{polar_commit, version, code_len, rate, list, crc, quant, iter, dimension, bw, threshold, pairing}`。
- `exact_truth=null` 当且仅当Polar无ground truth可比；不得由 `success` 推导 `exact`。
- `disclosure/runtime` 需per-frame可计费；若Polar仅aggregate则判 `API_NOT_READY`（本契约不允许Σ推导单帧）。

### 5.2 每1024-block聚合（45行）

- **schema**：`block_id, source, frame_ids[4], verified_accept=(4帧全部success&&verification ?1:0), leak=Σ4 disclosure, runtime=Σ4, exact=(4帧exact全真?1:0 else null若任一null else 0)`。
- **禁止** `round(aggregate*45)` / aggregate FER拼per-block / accepted直比exact。

### 5.3 预算与写出（预冻结，未来执行）

- **预算**：`180 frames exactly once`（`45×4`），无重试、无调参、无增量；任一多跑/少跑即 `EVIDENCE_INVALID`。
- **写出根**（decoder前建，fail-closed，仅future授权后）：`comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/`。
- **文件**：`polar_replay_frames.json/.csv (180行) + polar_replay_blocks.json/.csv (45行) + polar_replay_manifest.json + v62r1_paired_registry.json(copy) + v62r1_api_readiness.json(copy)`；CSV/JSON行对等；禁写NPZ；本轮P0不创建此目录，仅冻结契约。
- **不触**：不跑NB-LDPC，不算PIE/SKR，不改Polar参数，不写Polar Release。

### 5.4 undetected语义（若exact存在）

- `undetected = verification_pass && !exact_truth` 单独表，永不并入 `verified_accept`；仅当 `exact_truth` 非null时计。

## 6. Phase D — 执行守卫（预冻结，未来执行前）

### 6.1 三终态（first-match）

```
if not api_ready or not frozen_params_complete or missing_per_frame_field or not frame_id_stable:
    overall = V62R1_POLAR_REPLAY_API_NOT_READY  # 未就绪停止，不进registry/重放
elif K_aligned<45 or per_source<15 or not replayable or V55_DOMAIN_INCOMPATIBLE or pairing_mismatch:
    overall = V62R1_REGISTRY_INSUFFICIENT  # 停止，不伪造
elif not yet_executed (本轮):
    overall = V62R1_REPLAY_PREPARATION_DONE  # 仅plan+探针+骨架
# 未来执行后（需API READY + registry READY + 独立plan ACCEPT + POLAR_REPLAY_EXECUTE_AUTH）:
# elif executed 180 frames exactly once with per-frame fields complete → V62R1_REPLAY_READY
# else → V62R1_EVIDENCE_INVALID (优先)
```

- `EVIDENCE_INVALID` 优先于 `POLAR_REPLAY_API_NOT_READY` / `REGISTRY_INSUFFICIENT`；`REPLAY_READY` 需逐帧完备且registry 45/180可校验。

### 6.2 Pre-EXECUTE五项（未来执行前）

1. `HEAD == origin/formal-ir-mainline == implementation SHA`（无漂移）
2. `ACCEPTED_PLAN_SHA` 等于accepted plan SHA — 重推导自 `git log` / `cycle_state.yaml`；`rg <stale-SHA>` 返回0 hits
3. 目标 `run_01` 不存在于 `polar_replay_v62r1/` 下（不覆盖）
4. budget180、registry hash、Polar commit、frozen_params与冻结plan一致
5. `py_compile + 关键测试PASS`

- FAIL → 执行阻塞，`revise-required`/返工，新SHA重审。

## 7. 证据写出（预冻结，未来执行）

- 固定增量根（decoder前建，fail-closed）：`comparison_bench/outputs_comparison/polar_replay_v62r1/run_01/`。
- 文件：`polar_replay_frames.json/.csv (180行)、polar_replay_blocks.json/.csv (45行)、polar_replay_manifest.json、v62r1_paired_registry.json、v62r1_api_readiness.json`；CSV/JSON行对等；禁写NPZ。本轮仅在 `docs/research_cycles/V62R1/` 紧凑记录 `v62r1_api_readiness.json + v62r1_paired_registry.json(或空骨架)`。
- 不写 `D:\Code\HD-QKD_Polar_Release`；不写 `formal_ir_methods/v62_*/run_01`。

## 8. 与V62衔接与守卫

- `V62R1` 为 `V62` 前置；`V62R1` 的 `180帧 registry + 逐帧Polar输出` 将作为 `V62` 的Polar侧输入（`frame_ids` 一一对应，`verified_accept` 按 `4帧全success&&verify` 聚合为45块）。
- 若 `V62R1` 为 `POLAR_REPLAY_API_NOT_READY` 或 `REGISTRY_INSUFFICIENT`，则 `V62` 保持 `COMPARISON_DATA_NOT_ALIGNED`（不伪造aggregate拼帧）。
- 守卫：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v62/ ==0 && git diff -- ../HD-QKD_Polar_Release ==0`（除本变更外零改），`rg "decode_nbldpc" 0 hits`（探针侧），`py_compile PASS`，`HEAD==origin (b37c78b7)` 已验，`run_01`不存在，正式重放未触发已验。
