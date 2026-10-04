# P1 numeric table draft

Primary JSON source: `workspace/msd_p1/e76e3e7aa8bb453a885a5fca0c69333a`; source role is TRAIN.
All rows are `NORMAL_APPROX_SCENARIO` planning scenarios; joint failure assumption ε=0.01 (per-plane ε=0.001), one shared verification tag of 64.0 bits per block.
The budget is the explicit projection `1040*N_symbols/1024 + 64 shared tag bits`; it is an assumption, not an observed long-block baseline. Entropies use the primary unsmoothed plug-in results. Same-source practical-code gap: UNKNOWN. No route verdict or scientific acceptance is included.

## Entropy summary

One row per source and encoding uses the LSB_FIRST primary JSON row; both orders remain available at full precision in P1_NUMBERS.json.

| Source | Encoding | H(A given B) (bits/symbol) | Σh₂(marginal bit error) (bits/symbol) | ΣH(bit given full B) (bits/symbol) |
|---|---|---:|---:|---:|
| T2-1M | GRAY | 0.7981344445 | 1.294901888 | 0.7986686554 |
| T2-1M | NATURAL | 0.7981344445 | 2.071881539 | 1.583503791 |
| T2-1.5M | GRAY | 0.8249782282 | 1.35965661 | 0.8254783523 |
| T2-1.5M | NATURAL | 0.8249782282 | 2.162314167 | 1.63617082 |
| T2-2M | GRAY | 0.8314077735 | 1.368435658 | 0.8319847748 |
| T2-2M | NATURAL | 0.8314077735 | 2.167965237 | 1.642143513 |

## Gray encoding (primary)

| Source | Order | N (symbols/block) | L_EC (bits/block) | Tag (bits/block) | Failure penalty (bits/block) | f_expected (dimensionless) | Nominal slack (bits/block) | Expected-numerator slack (bits/block) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T2-1M | LSB_FIRST | 1024 | 1061 | 64 | 91.77 | 1.4888 | -21.00 | -112.77 |
| T2-1M | LSB_FIRST | 16384 | 14038 | 64 | 1497.64 | 1.1929 | 2602.00 | 1104.36 |
| T2-1M | MSB_FIRST | 1024 | 1061 | 64 | 91.77 | 1.4888 | -21.00 | -112.77 |
| T2-1M | MSB_FIRST | 16384 | 14039 | 64 | 1497.63 | 1.1930 | 2601.00 | 1103.37 |
| T2-1.5M | LSB_FIRST | 1024 | 1086 | 64 | 91.52 | 1.4696 | -46.00 | -137.52 |
| T2-1.5M | LSB_FIRST | 16384 | 14465 | 64 | 1493.47 | 1.1854 | 2175.00 | 681.53 |
| T2-1.5M | MSB_FIRST | 1024 | 1085 | 64 | 91.53 | 1.4685 | -45.00 | -136.53 |
| T2-1.5M | MSB_FIRST | 16384 | 14467 | 64 | 1493.45 | 1.1856 | 2173.00 | 679.55 |
| T2-2M | LSB_FIRST | 1024 | 1094 | 64 | 91.45 | 1.4676 | -54.00 | -145.45 |
| T2-2M | LSB_FIRST | 16384 | 14573 | 64 | 1492.46 | 1.1841 | 2067.00 | 574.54 |
| T2-2M | MSB_FIRST | 1024 | 1094 | 64 | 91.45 | 1.4676 | -54.00 | -145.45 |
| T2-2M | MSB_FIRST | 16384 | 14575 | 64 | 1492.44 | 1.1842 | 2065.00 | 572.56 |

## Natural encoding sensitivity rows

| Source | Order | N (symbols/block) | L_EC (bits/block) | Tag (bits/block) | Failure penalty (bits/block) | f_expected (dimensionless) | Nominal slack (bits/block) | Expected-numerator slack (bits/block) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T2-1M | LSB_FIRST | 1024 | 911 | 64 | 93.27 | 1.3071 | 129.00 | 35.73 |
| T2-1M | LSB_FIRST | 16384 | 13447 | 64 | 1503.55 | 1.1482 | 3193.00 | 1689.45 |
| T2-1M | MSB_FIRST | 1024 | 1061 | 64 | 91.77 | 1.4888 | -21.00 | -112.77 |
| T2-1M | MSB_FIRST | 16384 | 14039 | 64 | 1497.63 | 1.1930 | 2601.00 | 1103.37 |
| T2-1.5M | LSB_FIRST | 1024 | 934 | 64 | 93.04 | 1.2915 | 106.00 | 12.96 |
| T2-1.5M | LSB_FIRST | 16384 | 13871 | 64 | 1499.41 | 1.1419 | 2769.00 | 1269.59 |
| T2-1.5M | MSB_FIRST | 1024 | 1085 | 64 | 91.53 | 1.4685 | -45.00 | -136.53 |
| T2-1.5M | MSB_FIRST | 16384 | 14467 | 64 | 1493.45 | 1.1856 | 2173.00 | 679.55 |
| T2-2M | LSB_FIRST | 1024 | 942 | 64 | 92.97 | 1.2908 | 98.00 | 5.03 |
| T2-2M | LSB_FIRST | 16384 | 13983 | 64 | 1498.36 | 1.1412 | 2657.00 | 1158.64 |
| T2-2M | MSB_FIRST | 1024 | 1094 | 64 | 91.45 | 1.4676 | -54.00 | -145.45 |
| T2-2M | MSB_FIRST | 16384 | 14575 | 64 | 1492.44 | 1.1842 | 2065.00 | 572.56 |
