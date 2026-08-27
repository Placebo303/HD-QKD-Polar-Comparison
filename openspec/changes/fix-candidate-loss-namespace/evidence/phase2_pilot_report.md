# Phase 2 试点报告 — fix-candidate-loss-namespace（T2.1/T2.2）

**状态：BLOCKED（按硬约束停机条款就地停止，现场完整保留）。**
G1 确定性锚点 PASS；C4 对比中 6 个新物化格有 4 格 `map_sanity verdict=FAIL`
（冻结判据 `map_ser < 0.1`），触发"任一格 map_sanity FAIL ⇒ 就地停止"。
下文 §7 给出证据与所需裁决。所有产物均为增量写入，未删改任何既有产物。

执行时间：2026-08-25 22:51–22:57（本地）。任务工作根：`workspace/fix-candidate-loss-namespace/17f4560c/`。

---

## C1 选格清单（done）

依据 `evidence/affected_cells.csv`（6dB 并集=67）选 6 格：3 共享 + 3 非共享。

| 格 | 分类 | affected.csv 记录 |
|---|---|---|
| d4_bw40 | 共享 | 10dB∩16dB\|10dB∩6dB\|16dB∩6dB |
| d64_bw20 | 共享 | 10dB∩16dB\|10dB∩6dB\|16dB∩6dB |
| d1024_bw150 | 共享 | 16dB∩6dB |
| d8_bw180 | 非共享 | 不在清单 |
| d16_bw60 | 非共享 | 不在清单 |
| d32_bw180 | 非共享 | 不在清单 |

## C2 双跑物化 + G1（done）

命令 A（正式命名空间写入）：
```
python tools/materialize_loss_namespaced_candidates.py --tiers 6dB --points "4,40;64,20;1024,150;8,180;16,60;32,180"
```
命令 B（G1 孪生跑，独立 pool/out 根）：同上 +
`--pool-root workspace/fix-candidate-loss-namespace/17f4560c/g1runB_pool
 --out-root-template workspace/fix-candidate-loss-namespace/17f4560c/g1runB_out/e2e_{tier}_runB`

- Run A：ok=6 fail=0，总耗时 **102.1 s**（日志 `workspace/.../17f4560c/runA_log.txt`）
- Run B：ok=6 fail=0，总耗时 **97.1 s**（日志 `runB_log.txt`）
- 每格耗时（Run A，由 sidecar_meta.json mtime 差分）：**16.0–17.8 s/格**
  （d4_bw40≈17.8s 含 ttbin sha256；d64_bw20≈16.0s、d1024_bw150≈16.9s、d8_bw180≈16.9s、d16_bw60≈17.1s、d32_bw180≈16.9s）
- 远低于 30 分钟/格异常线。

**G1 门**：
```
python tools/verify_candidate_namespace_gates.py --gate G1 \
  --g1-root-a results/authoritative_nsfix/e2e_6dB_fullgrid_pairing_v2_candidate_lossfix_v1/sidecars \
  --g1-root-b workspace/fix-candidate-loss-namespace/17f4560c/g1runB_out/e2e_6dB_runB/sidecars
→ [G1] compared 6 cells x 3 file kinds / [G1] PASS: all common cells byte-identical
```
a_eff/b_eff/chan_ll_table 全部 18 个文件字节级一致 ⇒ 工具链确定性成立。

## C3 新命名空间落位（done）

- 池：`results/real_sequences_ns/loss6dB/d{d}_bw{bw}/blk0/{a_eff.npy,b_eff.npy,materialize_meta.json}` ×6 格 ✓（design §2 布局）
- 候选目录：`results/authoritative_nsfix/e2e_6dB_fullgrid_pairing_v2_candidate_lossfix_v1/sidecars/d*_bw*/blk0/` ✓（Q4 `*_lossfix_v1` 命名）
- `results/real_sequences_ns/MANIFEST.csv`：6 行，全量溯源字段齐备
  （src_tag/d/bw/blk/ttbin_path/ttbin_sha256/a_eff_sha256/b_eff_sha256/params_tag）；
  ttbin_sha256=`d6050574eadf74cca…` 与 G0 报告记录一致；params_tag=
  `pairing_v2-nearest_occ0_maxpairs0_thr40000_aligndebug0`。

## C4 新旧对比表（T2.2 — 触发停机条款）

旧档：`results/authoritative/e2e_6dB_fullgrid_pairing_v2_candidate/sidecars`（只读）。
新档 ser 为双跑稳定值。冻结判据 L1682：`PASS ⟺ isfinite(map_ser) 且 map_ser<0.1`。

| 格 | 分类 | 旧 verdict | 旧 map_ser | 新 verdict | 新 map_ser | a_eff 字节相同 | joint_fp 相同 |
|---|---|---|---|---|---|---|---|
| d4_bw40 | 共享 | FAIL | 0.26867 | **FAIL** | 0.32526 | 否 | 否 |
| d64_bw20 | 共享 | FAIL | 0.41176 | **FAIL** | 0.44711 | 否 | 否 |
| d1024_bw150 | 共享 | FAIL | 0.10502 | **FAIL** | 0.23192 | 否 | 否 |
| d8_bw180 | 非共享 | PASS | 0.088637 | PASS | 0.088637 | **是** | **是** |
| d16_bw60 | 非共享 | FAIL | 0.24177 | **FAIL** | 0.24177 | **是** | **是** |
| d32_bw180 | 非共享 | PASS | 0.088637 | PASS | 0.088637 | **是** | **是** |

解读（关键）：
1. **共享格：字节不同 ✓（预期方向确认）**。三格 a_eff/b_eff/joint_fingerprint 全部改变，
   且新 ser 均高于旧值——污染池使 6dB 格曾"看起来更好"，修复后回归真实（更高）ser。
2. **非共享格：字节完全相同 = 正确结果，非异常**。这些格旧池本就来自正确的 6dB ttbin，
   同源+钉死参数+确定性链 ⇒ 逐字节复现 2026-03 输出（跨 5 个月的复现锚点，
   同时证明新提取管线的数据摄取路径与当年一致）。
   任务书"预期字节不同（源 ttbin 不同）"的前提仅对共享格成立。
3. **BLOCKER 点：4/6 新格 map_sanity FAIL**。但该失败模式追踪的是"格"而非"修复"：
   - 这 4 格在旧数据中同样 FAIL（含全部四档，见 §5 census）；
   - 旧 6dB 全档 FAIL 率 94/121（10dB 89/121、16dB 89/121、20dB 77/121），
     高 ser 格是该网格在冻结判据下的已知普遍属性；
   - 新 ser 量级与旧同格同数量级（0.09–0.45 带），非退化（n_symbols 50 万–69 万，正常）。
   是否按 design §4 G3 处置条款"标记 fail 并隔离"放行，需主线程裁决（§7）。

## C5 门校验

- **G3**（新 sidecar 根，单档）：`EXIT=1 FAIL: 4 violations` —— d1024_bw150 / d16_bw60 /
  d4_bw40 / d64_bw20 verdict=FAIL；2 个 PASS 格（d8_bw180、d32_bw180）无档位序检查可做（单档）。
  补充序校验（新旧混排，仅指示性）：新 6dB ser 在全部 6 格均高于旧 10/16/20dB 同格 ser，
  与 design §4 序 ser(6dB)>10>16>20 方向一致。
- **G4**：`[G4] provenance fields checked on 6 sidecars / PASS`（metrics 指纹、joint 指纹、
  source_ttbin_path、pairing_v2、sequence_is_sampled=0、ttbin 归档匹配全通过）。
- **G2-lite**（本批记录，全量留 Phase 3）：新 6dB vs 旧 10/16/20dB 同格 a_eff/b_eff
  sha256 共 36 组比较，**碰撞 0**。

## 旁证观察（不在本变更修复范围，仅记录）

- 旧数据中 d8_bw180 与 d32_bw180 在所有四档 map_ser 完全相同（如 6dB 均 0.088637），
  新干净重跑仍精确复现 ⇒ 这是源数据/管线的可复现属性（两格 a_eff 哈希不同，非同数组）。
  Phase 3 G2 全量扫描会覆盖此类格间关系，建议届时关注。
- 四档主 ttbin 文件均 21,328 B（`.1` 分片承载数据）；非共享格逐字节复现证明摄取正确。

## 产物清单（本次新增，均为增量）

- `results/real_sequences_ns/loss6dB/d*_bw*/blk0/*` ×6 格 + `MANIFEST.csv`（新池根）
- `results/authoritative_nsfix/e2e_6dB_fullgrid_pairing_v2_candidate_lossfix_v1/sidecars/*` ×6 格
- `workspace/fix-candidate-loss-namespace/17f4560c/{runA_log.txt,runB_log.txt,g1runB_pool/,g1runB_out/}`
- 本报告。未触碰 20/16/10dB、未改任何既有 results/ 路径、旧候选只读。

## 所需裁决（单一决策）

新物化 4 格（d4_bw40、d64_bw20、d1024_bw150、d16_bw60）map_sanity FAIL（ser≥0.1，
冻结判据），但这些格在旧数据中同样 FAIL 且属网格已知普遍现象（各档 FAIL 94–89/121）：

- **选项 1**：认定其为已知坏格点，按 design §4 G3 处置条款"标记 fail 并隔离"继续
  Phase 2 收尾（G1/G4/G2-lite 已 PASS 的部分有效），Phase 3 全量沿用同一处置规则；
- **选项 2**：维持严格停机，先由 planner 明确"G3 单档试点期 FAIL 格占比阈值/白名单"
  再恢复；
- **选项 3**：缩小试点至 PASS 格重选（不推荐——将系统性避开高 ser 区，削弱试点代表性）。

现场保留：全部输出原样未动，未执行任何清理或重跑。
