# G-1 ternary confirmation (2026-10-07, zero-decode on saved counts)

> R15 compliance: error support, per-value probabilities, memory, H closure
> BEFORE any code route. No new real reads (TRAIN tables + pd joints on disk;
> lag-1 + decomposition on existing ordered pair arrays).

| source | n | P0 | P+1 | P−1 | rest | p | p− | H(e) | closure |
|---|---|---|---|---|---|---|---|---|---|
| T2-1M | 315504 | 0.76243 | 0.23619 | 0.001379 | 0 | 0.23757 | 0.00580 | 0.8032 | ✓ |
| T2-1.5M | 441487 | 0.74578 | 0.00118 | 0.253043 | 0 | 0.25422 | 0.99535* | 0.8288 | ✓ |
| T2-2M | 589461 | 0.74298 | 0.00135 | 0.255669 | 0 | 0.25702 | 0.99475* | 0.8344 | ✓ |
| 0dB | 266638 | 0.75234 | 0.24643 | 0.001230 | 0 | 0.24766 | 0.00497 | 0.8187 | ✓ |
| 4dB | 115390 | 0.76160 | 0.23729 | 0.001109 | 0 | 0.23840 | 0.00465 | 0.8026 | ✓ |
| 10dB | 30907 | 0.76979 | 0.22907 | 0.001132 | 0 | 0.23021 | 0.00492 | 0.7887 | ✓ |

\*1.5M/2M sign FLIPPED (dominant e=−1; +50 ps offset vs −50 ps). h2 symmetric →
same level-B cost; per-source dominant direction recorded for sign prior.
lag-1 of 1[e≠0] (T2-1M ordered TRAIN, n=315504): **0.0004** (memoryless ✓).
Per-pair decomposition verified (n=20000/11886 samples): LSB differs iff e≠0
(EXACT); on marked, a1 = b1^a0^sgn (EXACT); higher bits determined given
(b,a0,a1) (exact on e==0; arithmetic reconstruction in decoder).
G-2 synthetic uses T2-1M family (p=0.2376, p₋=0.0058).
