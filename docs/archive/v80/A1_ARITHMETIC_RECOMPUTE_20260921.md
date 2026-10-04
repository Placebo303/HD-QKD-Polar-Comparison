# A1 Design-Point Arithmetic Recompute — 2026-09-21 (correction-execution)

- Scope: verify the REVISE review-supplied N_req values (15487/2700/1754) at FULL PRECISION
  against `workspace/p3_census_3954637c/census_table.json` (READ-ONLY; unmodified).
- Method: repo interpreter only (`.venv/bin/python`), pure arithmetic on already-measured
  H values. No `.ttbin` access, no data parsing, no pipeline/decoder execution, no commit/push.
- Authority: `docs/V80_BASELINE_20260921.md` §3/§5 governs; this file is evidence only.
- Track: implementation-only verification (read-only inputs, no real-data read, no decoder,
  no claim-bearing execution) — no DECIDE gate triggered.

## 1. Inputs read (census_table.json, verbatim)

| dataset | H_full_MM | H_full_plug | support_cells (K_AB) | n_pairs_N |
|---|---|---|---|---|
| T2-1M | 0.8036079281174853 | 0.7981344445358378 | 2395 | 525831 |
| T2-1.5M | 0.8289616869054485 | 0.8249782281516377 | 2439 | 735780 |
| T2-2M | 0.8345846048587662 | 0.8314077735449492 | 2597 | 982182 |

Full-precision contents C = 1024·H_MM: 1M **822.8945183923049** / 1.5M **848.8567673911792** /
2M **854.6146353753766**. (Baseline §3 prints 822.897/848.855/854.610 — those use H rounded
to 5 dp, e.g. 0.80361·1024=822.89664; difference ≤0.005 b, immaterial: no N_req changes.)

## 2. Commands + verbatim outputs

Command 1 (read inputs):
```
.venv/bin/python - <<'EOF'
import json, math
tbl=json.load(open('workspace/p3_census_3954637c/census_table.json'))
for r in tbl:
    print(r['dataset_id'], 'H_MM=',repr(r['H_full_MM']), 'H_plug=',repr(r['H_full_plug']), 'K=',r['support_cells'], 'N=',r['n_pairs_N'])
    C=1024*r['H_full_MM']
    print('  C=1024*H_MM =', repr(C))
EOF
```
Output:
```
T2-1M H_MM= 0.8036079281174853 H_plug= 0.7981344445358378 K= 2395 N= 525831
  C=1024*H_MM = 822.8945183923049
T2-1.5M H_MM= 0.8289616869054485 H_plug= 0.8249782281516377 K= 2439 N= 735780
  C=1024*H_MM = 848.8567673911792
T2-2M H_MM= 0.8345846048587662 H_plug= 0.8314077735449492 K= 2597 N= 982182
  C=1024*H_MM = 854.6146353753766
```

Command 2 (per-source m_max / f / N_req / slopes; rules `f=(64+5m)/C`, `N=ceil(3·4.785675/(1.3−f))`, `inf` if f≥1.3):
Output:
```
=== T2-1M C= 822.8945183923049 m_max= 201
  m=208 f=1.3416057287110053 gap=-0.04160572871100521 N_req=inf
  m=207 f=1.3355296158092345 gap=-0.035529615809234416 N_req=inf
  m=200 f=1.2929968254968385 gap=0.007003174503161569 N_req=2051
  m=199 f=1.2869207125950677 gap=0.01307928740493236 N_req=1098
  m=201 f=1.2990729383986093 gap=0.0009270616013907773 N_req=15487
  slope@200 = 5.006717031059186
  slope@208 = 4.958108127845019
=== T2-1.5M C= 848.8567673911792 m_max= 207
  m=208 f=1.300572773181701 gap=-0.000572773181700903 N_req=inf
  m=207 f=1.2946824979408418 gap=0.005317502059158263 N_req=2700
  m=200 f=1.2534505712548276 gap=0.04654942874517243 N_req=309
  m=199 f=1.2475602960139685 gap=0.052439703986031594 N_req=274
  m=207 f=1.2946824979408418 gap=0.005317502059158263 N_req=2700
  slope@200 = 4.8535867984679415
  slope@208 = 4.806464596541068
=== T2-2M C= 854.6146353753766 m_max= 209
  m=208 f=1.291810313446229 gap=0.008189686553770947 N_req=1754
  m=207 f=1.2859597232585198 gap=0.014040276741480229 N_req=1023
  m=200 f=1.2450055919445542 gap=0.054994408055445865 N_req=262
  m=199 f=1.2391550017568447 gap=0.06084499824315537 N_req=236
  m=209 f=1.2976609036339384 gap=0.002339096366061666 N_req=6138
  slope@200 = 4.820886314672522
  slope@208 = 4.7740815931708465
```

Command 3 (base arithmetic + amortized cost + certifiability):
Output (verbatim, selected):
```
1104/852.544 = 1.2949478267397343
(5120-1040)/852.544 = 4.7856767509946705
3*4.785675/(1.3-1.294947) = 2841.287354047115  ceil= 2842
1.3*852.544-1104 = 4.307199999999966
1.3*(1024*0.83256272)-1104 = 4.307492864000096
1024*0.83256272 = 852.54422528
36/4.3075 = 8.357515960533952
(1108.31-64-36)/5 = 201.66199999999998
key-eligible = [200, 276, 364]
36/200 = 0.18
36/364 = 0.0989010989010989
1M elig=200 m=201 N=15487 -> FAIL
1M elig=200 m=200 N=2051 -> FAIL
1M elig=200 m=199 N=1098 -> FAIL
1.5M elig=276 m=207 N=2700 -> FAIL
1.5M elig=276 m=200 N=309 -> FAIL
1.5M elig=276 m=199 N=274 -> PASS
2M elig=364 m=209 N=6138 -> FAIL
2M elig=364 m=200 N=262 -> PASS
2M elig=364 m=199 N=236 -> PASS
```

Command 4 (thresholds / halfwidth ratios / margins):
Output (verbatim):
```
threshold H@m=208 = 0.829326923076923
threshold H@m=200 = 0.7992788461538461
threshold H@m=199 = 0.7955228365384616
1M gap208= 0.025718994959437746 ratio= 9.036562351965067
1.5M gap208= 0.0003652361714745478 ratio= 0.16528315795396853
2M gap208= -0.00525768178184316 ratio= -2.7173493371789164
36/4.3075 = 8.357515960533952
(1108.31-64-36)/5 = 201.66199999999998
full-prec budget 1.3*852.54422528 = 1108.307492864
36/200 = 0.18  36/364 = 0.0989010989010989
2M H-margin @208 = 0.00525768178184316  f-margin = 0.008189686553770947
```

## 3. Corrected per-source table (full precision; governs)

| src | H_MM | content | m_max (raw) | f@208 | f@207 | f@200 | f@199 | f@m_max | N_req@m_max | N@200 | N@199 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | 0.8036079281174853 | 822.8945183923049 | 201 | 1.34160573 (inf) | inf | 1.29299683 | 1.28692071 | 1.29907294 | **15487** | 2051 | 1098 |
| 1.5M | 0.8289616869054485 | 848.8567673911792 | 207 | 1.30057277 (inf) | 1.29468250 | 1.25345057 | 1.24756030 | 1.29468250 | **2700** | 309 | 274 |
| 2M | 0.8345846048587662 | 854.6146353753766 | 209→cap 208 | 1.29181031 | 1.28595972 | 1.24500559 | 1.23915500 | 1.29766090 (raw 209) | 6138 raw / **1754 @cap 208** | 262 | 236 |

Arm-vs-fixed slopes `(5120−5m)/C`: 1M 5.00672 (@200) / 4.95811 (@208);
1.5M 4.85359 / 4.80646; 2M 4.82089 / 4.77408 — recorded for the P-V2 slope file, no conclusion drawn here.

## 4. Review-value verification — ALL REPRODUCE, none fail loudly

- 1M N_req@201 = **15487** ✓ (previously recorded 15438 — CORRECTED, Δ+49).
- 1.5M N_req@207 = **2700** ✓ (previously recorded 2708 — CORRECTED, Δ−8).
- 2M value **1754** ✓ reproduces exactly at m=208 — with one precision of language:
  the raw formula gives m_max=209 (N=6138 there); 1754 is N_req at the FROZEN CAPPED
  m_max 208 (`m1+m2 ≤ 208`). Baseline §3 already records this as "209→cap 208 … @208 1754",
  so the triple 15487/2700/1754 is CONFIRMED as stated (first two at raw m_max, third at capped m_max).
- m=200/199 rows CONFIRMED as previously computed: 2051/309/262 and 1098/274/236
  (2M m=200 N=262 confirmed by review).
- Certifiability claims CONFIRMED: 2M m=200 needs 262 ≤ 364 YES; 1.5M m=199 needs
  274 ≤ 276 YES by 2 blocks (PROVISIONAL — zero-failure still required); 1M fails at
  m_max/200/199 (15487/2051/1098 > 200); 1.5M fails at m_max/200 (2700/309 > 276).

## 5. Headroom precision (4.3072 vs 4.3075)

- With ROUNDED content: `1.3*852.544 − 1104 = 4.3072` (4.307199999999966).
- With FULL-PRECISION content: `1.3*(1024*0.83256272) − 1104 = 4.307492864 ≈ 4.3075`.
- The frozen basis uses **4.3075** (full-precision; baseline §2: "headroom 4.3075 b").
  Documents writing `1.3·852.544−1104 = 4.3075` mix rounded content with the full-precision
  result (off by 0.0003 b) — noted, immaterial (36/4.3075 = 8.3575 → 8.36× unaffected).

## 6. Amortized prior-disclosure cost — does NOT force m≤201

- Per-block under amortization: 36/200 = **0.18 b** (1M), 36/364 ≈ **0.0989 b** (2M).
- As an m-shift these are 0.036 and 0.020 rows — two orders below the 7-row (35 b)
  per-block-model relocation (m 208→201). CONFIRMED: amortized charging does not imply m≤201.

## 7. CONFIRMED vs CORRECTED ledger

- CONFIRMED: census H_MM/plug-in/K_AB/N (§1); thresholds 0.829327/0.799279/0.795523;
  A208 N=2842; key-eligible 200/276/364; 36/4.3075=8.36; (1108.31−64−36)/5=201.66→m≤201;
  f@208 1.341606/1.30055/1.29181; certifiability verdicts (§4).
- CORRECTED: N_req 15438→**15487** (1M@201); 2708→**2700** (1.5M@207); "~9σ" phrasing →
  halfwidth-ratio form (gap 0.025719 ≈ **9.04×** CI hw 0.00284610; interval-halfwidth multiple,
  NOT σ; bootstrap percentile interval does not bracket the plug-in point estimate).
- Flag (open, unchanged, for main thread): baseline §3 "2M @208 IN (margin 0.0021)" —
  provenance unclear (H-margin is 0.00526, f-margin 0.00819); not verified here, not changed.
