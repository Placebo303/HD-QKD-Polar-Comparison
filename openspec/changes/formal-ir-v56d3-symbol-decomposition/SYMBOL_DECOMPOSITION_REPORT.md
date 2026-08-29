# SYMBOL DECOMPOSITION REPORT — V56D3 (TEMPLATE / PLAN READY)

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free, no `run_01`, no rerun of V55 90.
**Branch**: `formal-ir-mainline` **HEAD**: `8d4df35c57fb168a389f591721b562b2baca5a8f` == `origin/formal-ir-mainline` **Data SHA**: `84d62779` (`200ps legacy_v1 nearest 1024`)
**Method frozen**: `V54二阶段 H1-16(80b)+L1-APP via H1 BP+Lane C m2 184/190/192+H_inc1/2 Δ8+8 decoder 90/1.0 poly37 L2-only tag` — zero change, zero decoder.

## 0. Provenance Remediation (Phase 0)

- **Issue**: `V56D2 run03` execution modified `src/qkd_io/ttbin_pipeline.py:compute_cross_correlation_histogram` to chunk-single histogram but SHA stayed `8d4df35c`; `src/` is frozen baseline.
- **Fix**: `src` reverted to frozen baseline (per-pair); chunk optimization moved to `v56d3_symbol_decomposition.py:hist_chunk()` inline.
- **Equivalence proof** (≤1k events, `np.array_equal`): synthetic `t_A 800 + t_B bg 200`, `bin100 max819200 chunk256`, `counts_old == counts_chunk` **PASS** (sum 2132, max diff 0, empty/tiny also PASS). Recorded in `provenance.equivalence`.
- **Code state**: `git diff -- src/qkd_io/ttbin_pipeline.py` = 0 lines after revert; `HEAD == origin/formal-ir-mainline == 8d4df35c`; `rg 8d4df35c` 0 hits outside json.
- **Run03 disposition**: `v56d2_calibration_run03.json` amended → `provenance_deviation: true`, `overall: RESULT_CANDIDATE_WITH_PROVENANCE_DEVIATION`, not authoritative; successor uses reverted SHA.

## 1. Entropy / Mutual Information (Phase A, permutation-insensitive)

| Source | H(A) | H(B) | H(A|B) | I(A;B) | N | vs V13 (H~0.80 I~9.2) |
|---|---|---|---|---|---|---|
| 1M | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 1p5M | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 2M | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

Method: `C(a,b)→P(a,b)→H` via `numpy log2`; `H, I` insensitive to global `b'=π(b)`. If `I>5 bits` but `acc_identity 27-42%` → relabel/anchor, not true entropy.

## 2. Identity vs Empirical MAP (Phase B, fit4/val4 disjoint)

Pre-registered split: `fit=[7,8,9,10] val=[15,16,17,18]` (2 blocks×4 front/back); `assert fit∩val==∅`; `a_MAP(b)=argmax_a C_fit(a,b)`, `b` unseen → `b`.

| Source | acc_identity (val) | acc_map (val) | acc_identity_all | acc_map_all | Δ=map-identity |
|---|---|---|---|---|---|
| 1M | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 1p5M | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 2M | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

If `acc_map - acc_identity >30%` and `acc_map>60%` plus family recovery → reversible relabel.

## 3. Physical Mapping Families (Phase C, <5k candidates, fit→val)

| Family | Candidates | Physical basis | Best k* (fit) | val acc | val NLL | val q_mass | val mass0±1 |
|---|---|---|---|---|---|---|---|
| global_shift `(b+k)%1024` | 1024 | bin_origin/delay bin error | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| global_xor `b xor k` | 1024 | Gray/binary bit flip | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| axis_32x32 (swap×flip) | 8 | F03 5+5 / channel interleave | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| gray_binary (2) | 2 | L02 Gray vs natural | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| u1u2_order | 2 | Lane C order | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

Selection on `fit` (`argmax acc` / min `NLL` via `channel_counts.npz`); report on `val`. Recovery threshold: `val acc>60%` and `NLL 22-28→<5` and `q_mass 57-71%→<10%`. No arbitrary `1024!`.

## 4. Stage-wise Pipeline Check (Phase D)

Stages: `paired timestamps → bin 200ps → frame anchor (peak_center vs global min, period 204800, floor_div) → symbol legacy_v1 → U1/U2 (F03 5+5)`

| Stage | I | acc_identity | acc_map | Note |
|---|---|---|---|---|
| 1 paired timestamps | _TBD_ | — | — | if low → pairing error |
| 2 bin | _TBD_ | _TBD_ | _TBD_ | — |
| 3 frame anchor | _TBD_ | _TBD_ | _TBD_ | high→low ⇒ anchor error |
| 4 symbol | _TBD_ | _TBD_ | _TBD_ | — |
| 5 U1/U2 | _TBD_ | _TBD_ | _TBD_ | family recovery ⇒ order error |

`first_collapse_stage`: _TBD_

## 5. Three-Way Shunt (Phase E, mutually exclusive)

- [ ] `SYMBOL_MAPPING_CONTRACT_ERROR` — `I>5 bits` + some physical `π` recovers `val acc>60% NLL<5`
- [ ] `PAIRING_OR_FRAME_ANCHOR_ERROR` — `I>5 bits` + raw timing healthy (`σ127ps p2bg 378-708`) + no physical `π` recovers
- [ ] `TRUE_ACQUISITION_DOMAIN_SHIFT` — `I<2 bits` and `H(A|B)≈H(A)` (only then plan new `TRAIN-only` prior/leakage `m_total=floor((1.3*1024*H-64)/5)`)

Per-source may be `MIXED_BY_SOURCE`; overall is `MIXED` or `INCONCLUSIVE_NEED_DEEPER_STAGE` if needed (not algorithm negation).

## 6. Guard & Next Steps

- `rg "decode_" 0 hits`, `py_compile PASS`, `fit∩val==∅` verified, `I/H` permutation-insensitive reported, `5 families <5k` verified, no `run_01`, V55 90 never rerun, main algorithm not negated.
- Successor: `SYMBOL_MAPPING` → fix mapping/bin_origin/wrap/frame_anchor/Gray contract, freeze fresh TEST blocks, re-qualification; `TRUE_SHIFT` → plan new prior/leakage; this diagnosis does not directly enter qualification.
