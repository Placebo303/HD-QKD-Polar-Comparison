# SYMBOL DECOMPOSITION REPORT — V56D3 (EXECUTED, REVISED V56D3R1 2026-08-29)

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free, no `run_01`, no rerun of V55 90.
**Branch**: `formal-ir-mainline` **HEAD**: `b332b8a4a51e94fb905023862b8aed3650bac126` == `origin/formal-ir-mainline` **Data SHA**: `84d62779` (`200ps legacy_v1 nearest 1024`)
**Method frozen**: `V54二阶段 H1-16(80b)+L1-APP via H1 BP+Lane C m2 184/190/192+H_inc1/2 Δ8+8 decoder 90/1.0 poly37 L2-only tag` — zero change, zero decoder.
**Auth**: `V56D3_DIAGNOSIS_AUTH` on `b332b8a4`; execution `python openspec/changes/formal-ir-v56d3-symbol-decomposition/v56d3_symbol_decomposition.py` (default out `v56d3_symbol_decomposition.json`).
**DECODE_FORBIDDEN**: `rg "decode_"` in script = 0 hits (only `lifecycle` string), no decoder import, no prior/code param change, no V55 90 touch.
**Revision V56D3R1 (2026-08-29)**: **终态由 `PAIRING_OR_FRAME_ANCHOR_ERROR` 降级为 `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT`** — 1024分类下 `val 1024` 样本 `plug-in` 互信息严重正偏（`H(A|B)` 被压低→`I≈8.4`），且经验 `MAP val` 比 `identity` 更差说明高 `I` 无泛化；已排除全局 `shift/XOR/轴交换/Gray/U1U2` 与固定 `1024` 置换，`V25 prior` 严重失配，但 `pairing/frame anchor` 与真域迁移尚未区分。

## 0. Provenance Remediation (Phase 0)

- **Issue**: `V56D2 run03` execution modified `src/qkd_io/ttbin_pipeline.py:compute_cross_correlation_histogram` to chunk-single histogram but SHA stayed `8d4df35c`; `src/` is frozen baseline.
- **Fix**: `src` is clean (`git diff -- src/qkd_io/ttbin_pipeline.py` = 0 lines, `git status -- src/` clean, `HEAD == origin/formal-ir-mainline == b332b8a4` verified); chunk optimization lives only as `v56d3_symbol_decomposition.py:hist_chunk()` inline (`# ponytail: chunk-level histogram inline`).
- **Equivalence proof** (synthetic `t_A 800 + t_B bg 200`, `bin100 max819200 chunk256`, always-run): `counts_old == counts_chunk` **PASS** (`sum 2132`, `np.array_equal True`) recorded in `json:provenance.equivalence`.
- **Run03 disposition**: already `RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION` if provenance drift existed; this diagnosis uses reverted baseline SHA `b332b8a4` only.

## 1. Entropy / Mutual Information (Phase A, permutation-insensitive, on validation val=[15,16,17,18] n=1024 each)

| Source | H(A) val | H(B) val | H(A|B) val | I(A;B) val | N_val | vs V13 (H(A|B)~0.80 I~9.2) | sanity all-data |
|---|---|---|---|---|---|---|---|
| 1M (20260123_1M_600k_0dB) | 9.1789 | 9.1797 | 0.6355 | **8.5434** | 1024 | Hc lower than V13 but I>5 (high) | all N=545k Hc=5.60 I=4.40 |
| 1p5M (20260107_PPLN_1p5M) | 9.1378 | 9.1462 | 0.7153 | **8.4225** | 1024 | I>5 high | all N=1.31M Hc=6.49 I=3.50 |
| 2M (20260123_2M_1p2M_0dB) | 9.1652 | 9.1888 | 0.7438 | **8.4214** | 1024 | I>5 high | all N=1.41M Hc=7.43 I=2.55 |

Method: `C(a,b)→P(a,b)→H` via `numpy log2` on `1024×1024` joint counts; `H/I` insensitive to any global `b'=π(b)`.
**Caveat (REVISED V56D3R1 — critical bias correction)**: `val4 = 1024` samples over `1024×1024` bins is **severely undersampled** → `H(A|B)` severely underestimated, `I(A;B)` severely overestimated (plug-in positive bias → `I≈8.4` is artifact). Larger sanity: `val128 (32k) I=5.9-6.5`, `all-data I=2.5-4.4` although `>2` threshold, the per-sample `1024` plug-in cannot be used for shunt. Moreover **empirical MAP on `val` is worse than `identity` (`Δ≈-0.14 to -0.15` all sources)** — high plug-in `I` has **no generalization**: no `a_MAP(b)` learned on `fit` predicts `val` better than identity, so high `I` is not evidence for `pairing/frame` error either. Therefore `pairing/frame anchor` vs `TRUE_ACQUISITION_DOMAIN_SHIFT` **cannot be distinguished** by `1024` plug-in `MI` alone; larger-sample `I` (2.5-4.4) remains moderate but not conclusive without bias correction or low-dim (32-state) verification. Raw timing `σ127ps p2bg 378-708` partially healthy still recorded, but insufficient to resolve the ambiguity.

## 2. Identity vs Empirical MAP (Phase B, fit4=[7,8,9,10] → val4=[15,16,17,18], disjoint, decoder-free)

Pre-registered split `fit=[7,8,9,10] val=[15,16,17,18]` `assert fit∩val==∅`; `a_MAP(b)=argmax_a C_fit(a,b)`, unseen b → identity; MAP is upper bound of any single-symbol relabel.

| Source | acc_identity (val) | acc_map (val) | Δ=map-identity | Interpretation |
|---|---|---|---|---|
| 1M | **0.428711** | **0.275391** | **-0.153** | MAP *worse* than identity — no predictable relation |
| 1p5M | **0.367188** | **0.222656** | **-0.145** | MAP worse — no predictable relation |
| 2M | **0.274414** | **0.130859** | **-0.144** | MAP worse — no predictable relation |

Sanity with val 8960 (frames 15-50): same pattern `Δ≈-0.13 to -0.14`. **No source shows MAP recovery** (`acc_map>60%` threshold nowhere met; actually MAP degrades). Means arbitrary 1024-permutation does not exist that makes `a` predictable from `b` — not a reversible single-symbol relabel. **V56D3R1 addendum**: `MAP < identity` together with known `1024` plug-in bias confirms `I≈8.4` does not generalize; it excludes `SYMBOL_MAPPING_CONTRACT_ERROR` (already excluded by 5-family + fixed-1024 permutation failure) but **does not by itself prove `PAIRING_OR_FRAME_ANCHOR_ERROR`**.

## 3. Physical Mapping Families (Phase C, 2060 candidates total, fit→val, 5 pre-registered families)

Selection rule: `k* = argmax_k mean_fit(a==π_k(b))` on fit, report on val (threshold for recovery: `val acc>60%` and `NLL 22-28→<5` and `q_mass 57-71%→<10%`).

| Family | Candidates | Physical basis | 1M val acc / NLL / q_mass | 1p5M val acc / NLL / q_mass | 2M val acc / NLL / q_mass | Best fit pick |
|---|---|---|---|---|---|---|
| global_shift `(b+k)%1024` | 1024 | bin_origin/delay bin error | 0.428711 / 22.49 / 0.571 | 0.367188 / 25.01 / 0.633 | 0.274414 / 28.60 / 0.726 | all `shift_0` (identity) |
| global_xor `b xor k` | 1024 | Gray/binary bit flip | 0.428711 / 22.49 / 0.571 | 0.367188 / 25.01 / 0.633 | 0.274414 / 28.60 / 0.726 | all `xor_0` |
| axis_32x32 (swap×flip) | 8 | F03 5+5 / channel interleave | 0.428711 / 22.49 / 0.571 | 0.367188 / 25.01 / 0.633 | 0.274414 / 28.60 / 0.726 | all `swap0_flip00` |
| gray_binary (2) | 2 | L02 Gray vs natural | 0.0 / 39.69 / 1.0 | 0.00293 / 39.75 / 0.997 | 0.00293 / 39.71 / 0.997 | ~gray_to_binary/binary_to_gray near 0 |
| u1u2_order `32U1+U2 vs 32U2+U1` | 2 | Lane C order | 0.428711 / 22.49 / 0.571 | 0.367188 / 25.01 / 0.633 | 0.274414 / 28.60 / 0.726 | all `swapped_0` |

**No family recovers on validation**: best val acc = identity itself (27-43%), no improvement, NLL stays 22-28 (not <5), q_mass 57-72% (not <10%). Three sources **jointly** show same failure — **not source-specific**, **三源共同** pairing/anchor-or-domain ambiguity. `SYMBOL_MAPPING_CONTRACT_ERROR` is excluded (no physical π recovers, including Gray/U1U2/fixed 1024 permutation); `V25 prior` is severely mismatched (`q_mass 57-72%` on p-zero cells, `NLL 22-28 bits/sym` far from `~0.8`), but **remaining two hypotheses — `PAIRING_OR_FRAME_ANCHOR_ERROR` vs `TRUE_ACQUISITION_DOMAIN_SHIFT` — are not separated** by this test due to 1024 plug-in bias (see §1 caveat). Hence V56D3R1 downgrades to `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT`.

## 4. Stage-wise Pipeline Check (Phase D)

Stages: `paired timestamps → bin 200ps → frame anchor (peak_center vs global min, period 204800, floor_div) → symbol legacy_v1 → U1/U2 (F03 5+5)`

- **Raw timing**: prior V56D2 reported `σ~127ps` narrow peak healthy, `p2bg 378-708` PARTIAL — Stage 1 paired timestamps not collapsed.
- **This diagnosis**: I(val4) high (8.4) but with bias; all-data I 2.5-4.4 moderate; MAP collapses and no π recovery at symbol stage → collapse not at reversible `symbol/U1U2` relabel stage, but earlier **pairing/frame anchor** stage.
- `first_collapse_stage`: `frame anchor or pairing` — Stage 3 (frame anchor `peak_center vs global min, wrap floor_div, period 204800`) or Stage 1 pairing `threshold/policy/direction` are suspects (non-single-symbol-reversible). Symbol-stage families already ruled out.
- No occupancy/sync grid searched (single point `200ps legacy_v1 nearest 1024` per data SHA).

## 5. Three-Way Shunt (Phase E, REVISED V56D3R1 — downgraded to INCONCLUSIVE)

Pre-registered criteria (original, now recognized as biased for 1024 plug-in):
- `I_val<2` & `H(A|B)≈H(A)` → `TRUE_ACQUISITION_DOMAIN_SHIFT`
- `I_val>5` & ∃π val acc>60% NLL<5 → `SYMBOL_MAPPING_CONTRACT_ERROR`
- `I_val>5` & raw healthy & ∀π val acc<50% → `PAIRING_OR_FRAME_ANCHOR_ERROR`
- else `INCONCLUSIVE_NEED_DEEPER_STAGE` (mixed allowed)

Observed (val4 = 1024 samples, 1024-state plug-in, **severely biased**):

| Source | I_val (biased plug-in) | best π val acc | acc_map vs identity | Original shunt (superseded) |
|---|---|---|---|---|
| 1M | 8.54 (>5, biased) | 0.429 (<50%) | 0.275 < 0.429 (MAP worse) | ~~PAIRING_OR_FRAME_ANCHOR_ERROR~~ |
| 1p5M | 8.42 (>5, biased) | 0.367 (<50%) | 0.223 < 0.367 (MAP worse) | ~~PAIRING_OR_FRAME_ANCHOR_ERROR~~ |
| 2M | 8.42 (>5, biased) | 0.274 (<50%) | 0.131 < 0.274 (MAP worse) | ~~PAIRING_OR_FRAME_ANCHOR_ERROR~~ |

**V56D3R1 Revised overall**: `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT` (downgraded from `PAIRING_OR_FRAME_ANCHOR_ERROR`; 3/3 agree on exclusion of `SYMBOL_MAPPING_CONTRACT_ERROR`, but `pairing/frame` vs `true domain shift` not distinguished).

Rationale:
- **Excluded**: `SYMBOL_MAPPING_CONTRACT_ERROR` — all 5 physical families (global shift/XOR/32×32 swap/flip/Gray-binary/U1U2 order) fail on `val`, and fixed `1024` permutation `a_MAP(b)` also fails (`acc_map < acc_identity`); no reversible single-symbol relabel exists.
- **Not proven either way**: `PAIRING_OR_FRAME_ANCHOR_ERROR` requires `I` truly high + raw timing healthy. But `I≈8.4` is **plug-in severely positive-biased** at `N=1024` over `1024×1024` bins (`H(A|B)` underestimated); high plug-in `I` **does not generalize** (MAP degrades on `val`). Larger-sample `I` (val128 5.9-6.5, all-data 2.5-4.4) is moderate, not collapsed to `<2` but also not the `8.4` reported; raw timing `σ127ps p2bg 378-708` partially healthy but insufficient to separate pairing vs domain.
- **`TRUE_ACQUISITION_DOMAIN_SHIFT` not excluded**: requires `I<2` & `H(A|B)≈H(A)` — biased `I>5` falsely excludes it; with bias correction and low-dim (32-state) check pending, domain shift remains plausible, especially given `V25 prior` severe mismatch (`NLL 22-28→39` for Gray, `q_mass 57-73%` on p-zero cells) and `NLL/q_mass` not recovered by any physical `π`.
- **Conclusion**: evidence supports **complement of `SYMBOL_MAPPING`** but is **inconclusive between `pairing/frame-anchor error` and `true acquisition-domain shift`**; requires **V56D4 low-dim (32-state) decomposition** (U1/U2 32-state MI + fixed train/val CE/accuracy + stage-wise V13-contract replay) without 1024 plug-in MI shunt, and without `1024!` search or grid择优.

## 6. Guard & Next Steps — DECODE_FORBIDDEN maintained (REVISED V56D3R1)

- `py_compile PASS`, `fit∩val==∅` asserted, `I/H` permutation-insensitive reported but **biased at N=1024 for 1024-state** (hence downgrade), `5 families 2060<5k` verified, `no run_01`, `V55 90 never rerun`, main algorithm `V54二阶段` **not negated** (diagnosis is contract/pairing/domain ambiguity, not LDPC falsification).
- **Next (V56D4, separate successor, DECODE_FORBIDDEN)**: **decoder-free low-dim (32-state) decomposition** — compute `I(U1A;U1B) / I(U2A;U2B) / I(U1A;U2B) / I(U2A;U1B)` (32-state, `N=1024` gives `~1k/1024≈1` per bin vs `1024×1024` severely undersampled; bias far smaller), use **fixed train/val cross-entropy or accuracy** (not 1024 plug-in MI) for shunt; stage-wise compare `V13` vs new session: `raw coincidence → pairing Δt → per-frame occupancy → frame-anchor (before/after pair index) → U1/U2 consistency` first drop position; replay **exactly V13 known contract** (`pairing policy/direction/threshold/frame-start`, from `workspace/v13r3fresh_20260816/sidecars`) vs current intake contract (only two-way comparison, **no grid择优**); if V13 contract recovers low-dim association & NLL on `val` → `PAIRING_OR_FRAME_ANCHOR_ERROR`, if still low → `TRUE_ACQUISITION_DOMAIN_SHIFT`. Only `TRUE_SHIFT` then plans new `TRAIN-only prior/leakage m_total=floor((1.3*1024*H-64)/5)` — not triggered here.
- All numerical conclusions are validation-only (`val4`) and decoder-free; prior (`channel_counts.npz`) untouched (only read for NLL column-norm, not re-estimated); code params frozen; V56D3R1 explicitly records that **no successor has yet proven pairing/frame error**.

---
*Artifacts*: `v56d3_symbol_decomposition.json` (per_source H/I/acc_map/families_val/best_family_val/shunt_per_source/overall_shunt) + `v56d3_symbol_decomposition.py` (decoder-free, `hist_chunk` equivalence proof). Original V55 90-block remains disclosed and never rerun.*
