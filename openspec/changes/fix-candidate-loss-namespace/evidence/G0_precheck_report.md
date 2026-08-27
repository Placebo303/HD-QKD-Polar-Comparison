# G0 预检报告 — fix-candidate-loss-namespace

- 生成时间: 2026-08-25T22:17:51.623748
- 原始数据根: `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s`
- 归档 override 根: `D:\Code\HD-QKD_Polar_Release\results\archive\workspace_override_points`

## 1. 原始 ttbin 检查（存在 + 非零 + sha256）

| 档 | 文件 | 存在 | 字节数 | sha256 |
|---|---|---|---|---|
| 20dB 主文件 | `Type2_5s_20dB_2026-01-30_224943.ttbin` | True | 21328 | `8f6848b58ecaef9d9e227c80a5c4f2c4…` |
| 20dB .1 分片 | `Type2_5s_20dB_2026-01-30_224943.1.ttbin` | True | 11729888 | `303aee617075579c36e232a1ded315f5…` |
| 16dB 主文件 | `Type2_5s_16dB_2026-01-30_224900.ttbin` | True | 21328 | `f7ff84d769d0a4f0e0831c006a8c6546…` |
| 16dB .1 分片 | `Type2_5s_16dB_2026-01-30_224900.1.ttbin` | True | 18448752 | `c97175e98124f83d8627d6d5a192647c…` |
| 10dB 主文件 | `Type2_5s_10dB_2026-01-30_224808.ttbin` | True | 21328 | `83f85f54a2e0a8573afe2e252fdb9184…` |
| 10dB .1 分片 | `Type2_5s_10dB_2026-01-30_224808.1.ttbin` | True | 36374336 | `714e7e7171f254b023b352ba024e75f2…` |
| 6dB 主文件 | `Type2_5s_6dB_2026-01-30_224719.ttbin` | True | 21328 | `d6050574eadf74cca1bd7d58f37af35f…` |
| 6dB .1 分片 | `Type2_5s_6dB_2026-01-30_224719.1.ttbin` | True | 56530336 | `435694971b816c4241a285b74be7cdbb…` |

## 2. 归档 override 点指纹抽验（对账 sidecar source_fingerprints；mismatch 允许，仅记录）

| 档 | 对账格数 | 匹配 | 失配 | 归档缺失 | sidecar 无指纹 |
|---|---|---|---|---|---|
| 10dB | 121 | 120 | 1 | 0 | 0 |
| 16dB | 121 | 120 | 1 | 0 | 0 |
| 20dB | 121 | 120 | 1 | 0 | 0 |
| 6dB | 121 | 120 | 1 | 0 | 0 |

说明：归档内 resolved_config.json 已被 2026-04-26 之后的运行覆盖（design.md §1 已知），
ttbin_metrics.json 失配仅作记录，不阻断；主路线为原始 ttbin 直提。失配示例：
- 10dB d1024_bw200: recorded=077609771427… archived=2c22c48c65f4…
- 16dB d1024_bw200: recorded=077609771427… archived=2c22c48c65f4…
- 20dB d1024_bw200: recorded=077609771427… archived=2c22c48c65f4…
- 6dB d1024_bw200: recorded=077609771427… archived=2c22c48c65f4…

## 3. MANIFEST 骨架

- 骨架（仅表头，Phase 3 定稿前不落 results/）：`openspec\changes\fix-candidate-loss-namespace\evidence\MANIFEST_skeleton.csv`
- 表头: `src_tag,d,bw,blk,ttbin_path,ttbin_sha256,a_eff_sha256,b_eff_sha256,params_tag`

## 结论：G0 PASS
## 4. 解读（2026-08-25，Phase 0）

### 归档指纹对账（第 2 节）
- 每档 121 格中 **120 格归档 ttbin_metrics.json 与该档 sidecar 记录的 sha256 完全一致**，
  说明归档 metrics 基本就是 2026-03-18 物化时的原件（design §1 担心的大面积覆盖并未发生）。
- 四档的 recorded 指纹彼此相同 ⇒ 各档当时读到的是**同一份** override 点 metrics
  （metrics 只在缺失时重建，跨档复用），这与「候选序列实际来自共享池」的事件结论自洽：
  joint 实际经 from_sequence 重构，metrics 仅作占位输入。
- 唯一失配格 d1024_bw200：四档 recorded=077609771427…，现归档=2c22c48c65f4…，
  即该格归档 metrics 已被后续运行覆盖。按 design §6 条款在 MANIFEST 标注
  archive_fingerprint_mismatch 即可，不阻断。

### 受影响格精确清单（affected_cells.csv，与事件记录交叉核对）
| 集合 | 精确枚举 | 事件记录 | 结论 |
|---|---|---|---|
| 10∩16 | 56 | 56 | 一致 |
| 6∩16 | 56 | 56 | 一致 |
| 6∩10 | 40 | 40 | 一致 |
| 三档共享（交集） | 29 | （未单列） | 由容斥反推一致 |
| 6dB 并集 | **67** | ≈61 | 事件记录为近似值；67 为指纹精确值 |
| 跨三档并集 | 94 | （未单列） | 56+40+56−2×29=94 自洽 |
| 20dB 与其他档共享 | 0 | 0 | 一致（干净档） |

分解：29 格三档全共享 + 27 格仅 16∩6 + 27 格仅 10∩16 + 11 格仅 10∩6。
6dB 并集 67 = 56 + 40 − 29（容斥），与 ≈61 的差异源于事件记录使用近似估计，无矛盾。
