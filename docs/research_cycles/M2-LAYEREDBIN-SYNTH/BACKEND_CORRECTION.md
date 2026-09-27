# T2 B3 后端错标纠正 (M2-LAYEREDBIN-SYNTH, additive-only)

- 日期: 2026-09-24; HEAD `8e9c8526`; Track: implementation-only (additive, 无 track gate, 不重跑)。
- 性质: 纠正说明 + sidecar 指针。**不改任何既有 `rows.json` / `M2LB_RESULT_*.md` / `block_accounting.csv`** (旧文件只读校验 md5, 见下)。

## 1. 错标说明 (12 臂)

12 臂 `M2LB_RESULT_*.md` 中的 decoder 行均写为 (逐字):

```text
- decoder: true binary SPA max_iter 300 / streak 3 (machine-checked), `exact_match` accept; NO genie/argmax; success = exact + accepted + syndrome + toeplitz (double gate); report-only `prior_entropy_bits`, `messages_actual`
```

该行中 `true binary SPA` 为**错标**。实际后端以 sidecar 为准:

```text
numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)
```

即: 臂 RESULT md decoder 行 `true binary SPA` → `assumed fallback`, **以各臂 `backend_used.sidecar.json` 为准**。
claim 口径: **合成诊断 assumed, 不可比、不可消费为真体 SPA**。

## 2. Sidecar 指针 (12 根, 每根一文件)

| # | 臂根 | RESULT md (错标行所在, 未改) | sidecar (为准) |
|---|---|---|---|
| 01 | `workspace/m2lb_18eb57a9/` | `M2LB_RESULT_1M_197_matched.md` | `workspace/m2lb_18eb57a9/backend_used.sidecar.json` |
| 02 | `workspace/m2lb_99d2bfef/` | `M2LB_RESULT_1M_201_matched.md` | `workspace/m2lb_99d2bfef/backend_used.sidecar.json` |
| 03 | `workspace/m2lb_d4d24a1a/` | `M2LB_RESULT_1p5M_203_matched.md` | `workspace/m2lb_d4d24a1a/backend_used.sidecar.json` |
| 04 | `workspace/m2lb_2c09cb2d/` | `M2LB_RESULT_1p5M_207_matched.md` | `workspace/m2lb_2c09cb2d/backend_used.sidecar.json` |
| 05 | `workspace/m2lb_bb3120fc/` | `M2LB_RESULT_2M_204_matched.md` | `workspace/m2lb_bb3120fc/backend_used.sidecar.json` |
| 06 | `workspace/m2lb_261d611c/` | `M2LB_RESULT_2M_208_matched.md` | `workspace/m2lb_261d611c/backend_used.sidecar.json` |
| 07 | `workspace/m2lb_24f99582/` | `M2LB_RESULT_2M_204_blind.md` | `workspace/m2lb_24f99582/backend_used.sidecar.json` |
| 08 | `workspace/m2lb_407d9236/` | `M2LB_RESULT_2M_208_blind.md` | `workspace/m2lb_407d9236/backend_used.sidecar.json` |
| 09 | `workspace/m2lb_b9a4fdd7/` | `M2LB_RESULT_1p5M_203_blind.md` | `workspace/m2lb_b9a4fdd7/backend_used.sidecar.json` |
| 10 | `workspace/m2lb_aae025fc/` | `M2LB_RESULT_1p5M_207_blind.md` | `workspace/m2lb_aae025fc/backend_used.sidecar.json` |
| 11 | `workspace/m2lb_84150bd6/` | `M2LB_RESULT_1M_197_blind.md` | `workspace/m2lb_84150bd6/backend_used.sidecar.json` |
| 12 | `workspace/m2lb_fc719214/` | `M2LB_RESULT_1M_201_blind.md` | `workspace/m2lb_fc719214/backend_used.sidecar.json` |

各 sidecar 内容 (12 根同一字面量):

```json
{
  "backend_used": "numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)",
  "decoder_label_correction": "臂RESULT md decoder行 true binary SPA → assumed fallback, 以本sidecar为准",
  "claim": "合成诊断assumed, 不可比不可消费为真体SPA"
}
```

## 3. 下游消费规则 (强制)

- Claim 固定句（逐字）：“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”
- 下游任何消费本批 12 臂 FER/效率/泄漏数值的动作, **必须先读对应臂 `backend_used.sidecar.json`**。
- **未读 sidecar 即禁止消费**: 不得将本批数值当作真体 SPA (`ldpc.BpOsdDecoder`) 结果引用、比较或计入任何 claim。
- 本批口径恒为合成诊断 `assumed`, 与真体 SPA **不可比**。

## 4. 只读校验 (旧三件未改)

- 36 个旧文件 (`rows.json` / `M2LB_RESULT_*.md` / `block_accounting.csv` × 12 臂) md5 在 sidecar 落盘前后一致, 无修改、无重写、无 `results/`、`outputs_comparison/` 写入。
