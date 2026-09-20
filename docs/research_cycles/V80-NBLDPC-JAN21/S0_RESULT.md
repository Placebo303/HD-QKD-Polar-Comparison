# V80 S0 — Jan-21 evidence review + design-point record (read-only)

- Track: read-only review (text records ONLY — 0 parquet/symbol/pool reads, 0 DE/decoder calls).
- Branch: `formal-ir-v72p1-addendum-clean` (verified at write time).
- Charter: `docs/research_cycles/V80-NBLDPC-JAN21/PROGRAM_PLAN.md` (141 lines).
- Question: does Jan-21 evidence support H_full ≤ 1.0 per source with a frozen design point at rate 0.88–0.92?
- Verdict: **S0→S1 GO — all three sources named (1M / 1p5M / 2M).**
- S1+ needs fresh grants; this record consumes nothing and authorizes nothing.

---

## 1. Re-verified quote table (file + line per cell; CSV is authority where noted)

### 1.1 V25 M1 holdout — H(A|B) ≈ 0.80–0.83

Source: `docs/nbldpc-v25-empirical-channel-and-factorization-report-20260818.md:30-37`.

| source | C03 pooled δ | C04 source δ | C05 δ+parity | C01 QSC | C02 V17-product |
|---|---|---|---|---|---|
| 1M | 0.807 | 0.807 | 0.807 | 3.196 | 3.321 |
| 1p5M | 0.827 | 0.827 | 0.827 | 3.347 | 3.497 |
| 2M | 0.828 | 0.828 | 0.828 | 3.335 | 3.478 |

- Quoted from :32-34; interpretation "H(A|B) ≈ 0.80–0.83, far better than QSC/V17" at :36-37. Match, no diff.

### 1.2 V25 M3/F03 factorization — chain-rule closed

Source: same file :55, :61.

- :55 — F03 GF32+GF32 | L1=0.025, L2=0.795 | total 0.820. Match.
- :61 — layer sums close with worst absolute error 5e-9. Match (err ≤ 5e-9).

### 1.3 V49 per-source TRAIN/VAL/HOLD — ALL nine totals ≤ 1.0 (G1)

Authority: `docs/v49_distribution_tables/v49_train_val_hold_nll.csv:2-4,7-9,12-14`;
report mirror `docs/v49-distribution-shift-diagnosis-20260827.md:78-88`.

| source | split | n | NLL_U1 | NLL_U2 | NLL_total |
|---|---|---|---|---|---|
| 1M | TRAIN | 307200 | 0.02428054… | 0.77675727… | 0.80103782… |
| 1M | VAL | 102400 | 0.02511482… | 0.82563511… | 0.85074993… |
| 1M | HOLD | 102400 | 0.02492994… | 0.81940840… | 0.84433835… |
| 1p5M | TRAIN | 424960 | 0.02519949… | 0.80036655… | 0.82556605… |
| 1p5M | VAL | 141568 | 0.02524195… | 0.83494871… | 0.86019066… |
| 1p5M | HOLD | 141824 | 0.02531784… | 0.83192447… | 0.85724232… |
| 2M | TRAIN | 559872 | 0.02566204… | 0.80690067… | 0.83256272… |
| 2M | VAL | 186624 | 0.02626225… | 0.83620169… | 0.86246394… |
| 2M | HOLD | 186624 | 0.02528610… | 0.82768540… | 0.85297151… |

(Full precision in CSV; trailing digits verified exact against :78-86.)
Drift TRAIN→HOLD (:88): 1M +0.0433 / 1p5M +0.0317 / 2M +0.0204 — recomputed exact, match.
Maximum over all nine: 0.86246 (2M VAL) — ≤ 1.0 with margin ≥ 0.13. **G1 PASS, no source narrowed.**

### 1.4 V19 binary prototype — 500/500, f≈4.17 on declared 0.55 constant

Source: `docs/v19-binary-mlc-prototype-result-20260816.md:11-14`.

- :12 — 0 failures across all 500 plane-frame trials. Match.
- :13-14 — ≈587 syndrome bits/frame; f ≈ 4.169 using H_full=0.549955. Match.
- H constant declared at `docs/three-way-ir-comparison-plan-20260816.md:15-16` (V17 model). Match.
- Per `docs/research_cycles/V72P3G8-PRIOR-EFFICIENCY/R18_VERDICT.md:1`: 0.55 is a
  declared independence-model constant (D01 aggregate SER 0.077, synthetic prototype),
  NOT achievable conditional entropy. Recorded both; sizing uses empirical 0.80–0.86,
  never averaged/substituted with 0.55.

### 1.5 R3 correctability — 8284/8412, 0 mismatch

Source: `docs/decision-log.md:3069-3083` (pre-audit :3062-3064).

- :3073-3077 — 8412 frames: 8284 exact_correct / 128 decode_failed (all iteration_limit) / 0 exact_mismatch. Match.
- :3078 — per-source 1p5M 2729/2767, 1M 1970/2000, 2M 3585/3645. Match.
- :3062-3064 — 192-frame pre-audit 188/192. Match.
- Net-ledger rows: `docs/research_cycles/V72P3G8-PRIOR-EFFICIENCY/DECISION_BRIEF.md:252-257`
  (:254 R3 ≈0.80 / 8284-8412 / f≈12.1 / leak 9.7 bits/sym / net ≈−3.7 bits/sym;
  :255 binary ≈0.55 / 500-500 / f≈4.17 / 2.29 bits / +3.7 bits/sym). Match.

### 1.6 V8/V26 basis — method-only, not GF(1024)

- `openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_muller2024_table1_extract.txt:33-38`:
  λ row-0.75 + DET 0.069 + EEff 1.053. Match.
- `openspec/changes/archive/2026-08-05-formal-nonbinary-ldpc-v9-gf1024-long-ir/evidence/v9_00_freeze.json:112-114`:
  threshold_proxy 0.062421875, delta 0.006578 ≤ 0.012; method-only statement (NOT a GF(1024) result). Match.
- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_common.py:85-88`:
  DET 0.069 / TOL 0.012 constants. Match.

### 1.7 V29 ban — carried into S2

Source: `docs/nbldpc-v29-retrospective-finite-code-report-20260820.md:56-64`:
15 support groups / max multiplicity 69 / 303 duplicate projective classes /
922 columns in duplicate classes / 1107 proportional-column pairs → d_min ≤ 2. Match.
**Three-shift-cyclic GF(32) mothers FROZEN-excluded for S2.**

---

## 2. Gate verdict

- **G1 PASS** — per-source H_full ≤ 1.0 on TRAIN/VAL/HOLD totals for 1M, 1p5M, 2M (§1.3).
  No source narrowed; hottest HOLD (1p5M 0.85724) is sized single-column (§3), not dropped.
- **G2 FROZEN** — n=256; m-grid 24–31 (covers HOLD maxima m=29, §3); formula
  m=ceil(f·n·H/10), leak_total=10·m+64, rate=1−m/n, gross=Â·10·n (Â=0.6);
  f=1.3; 64-bit additive tag; q-architecture **TBD** (owner: V80 program owner to
  assign reader — recorded TBD, not chosen here).
- **G3 CARRIED** — §1.7 ban intact.
- **Verdict: S0→S1 GO with all sources named (1M / 1p5M / 2M).**

---

## 3. Frozen design numbers (recomputed, frozen formula, n=256 / f=1.3 / gross 1536)

| case | H | m | rate (1−m/n) | leak_total (10·m+64) | net (1536−leak) |
|---|---|---|---|---|---|
| nominal | 0.80 | 27 | 0.895 (0.8945) | 334 | 1202 |
| 1M HOLD max | 0.84434 | 29 | 0.887 (0.8867) | 354 | 1182 |
| 1p5M HOLD max | 0.85724 | 29 | 0.887 (0.8867) | 354 | 1182 |
| 2M HOLD max | 0.85297 | 29 | 0.887 (0.8867) | 354 | 1182 |
| V19-0.55 reference only | 0.549955 | 19 | 0.926 (0.9258) | 254 | 1282 |

- Frame-budget rows (±1 bit): R3 2486/−1014; binary 587/+885; NB-target 267+64/+1205 @H=0.8.
  (R3/binary leak figures exclude tag; net subtracts the 64-bit tag. NB leak_total includes it.)
- Grid 24–31 → rate 0.906–0.879; covers HOLD maxima (m=29). Nominal 0.895 and
  worst-case 0.887 both inside 0.88–0.92.

---

## 4. Conflicts / dispositions

- **V70R1 sessions** (`v70r1_table.csv:1-4`, actual IDs quoted verbatim):
  `20260123_1M_600k_0dB` / `20260107_PPLN_1p5M` / `20260123_2M_1p2M_0dB`
  (packet shorthand `20260123_1M / 20260107_PPLN_1p5M / 20260123_2M` matches by prefix;
  full IDs recorded here). Jan-23/Jan-07 pools, NOT Jan-21 → **out-of-scope**,
  does not constrain the design point.
- **V19-vs-V25**: 0.55 (declared independence constant, synthetic) vs 0.80–0.86
  (empirical conditional). Both recorded; sizing uses 0.80–0.86 only. No averaging.
- **v49_block provenance** (text headers + `v48_summary.json` session fields only, no parquet):
  V48 heldout_confirm (`mechanism_id` L1-APP soft-transfer + Lane C ordinal-2 90/1.0 +
  V35 tag, H1 `V31-H1-QC-16×1024`); held-out = split_manifest hold interval
  (1M 400 / 1p5M 554 / 2M 729 frames, frame_ids ≥1600, Jan-21 geometry, TRAIN-only
  V25 prior). Disposition: **S0-relevant real-block evidence** — same three Jan-21
  sources and frame geometry; corroborates H≈0.8 scale (block NLL success ≈0.82 /
  fail ≈0.89). Not Jan-23, so not out-of-scope; H_full gate itself rests on V25/V49 NLL.

---

## 5. S1 entry state

- S0-table: all values verified, zero diffs. S0-gate: GO. S0-design: table §3.
  S0-conflicts: three dispositions §4. S0-calls: 0.
- This record is NOT accepted (requires independent review + main-thread acceptance).
- S1+ (DE ensemble work and anything beyond) needs fresh grants; nothing consumed here.

## Acceptance (main-thread, this session): independent reviewer-go PASS (15+ cells zero-diffs, gates hold, arithmetic recomputed); main-thread ACCEPTS S0→S1 GO with all sources named; S1+ needs fresh grants; Jan-23 pools untouched.
