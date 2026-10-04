# Normal-approximation allocation diagnostic

These rows use only the accepted P1 scalar summary and its TRAIN scope.
They are not empirical FER, achieved code rates, OOS guarantees, or a decoder result.
The 1040*N/1024 + 64-bit value is a planning projection, not an observed long-block baseline.
Negative rounded improvement is retained when clipped integer leakage rises.

| Source | Encoding | Order | N (symbols) | Uniform L (bits) | Allocated continuous L (bits) | Allocated clipped L (bits) | Uniform minus allocated clipped (bits) | Uniform minus allocated f |
|---|---|---|---:|---:|---:|---:|---:|---:|
| T2-1M | NATURAL | LSB_FIRST | 1024 | 911 | 892.410791011 | 893 | 18 | 0.0218037748767 |
| T2-1M | NATURAL | LSB_FIRST | 16384 | 13447 | 13377.119218502 | 13378 | 69 | 0.00522382106421 |
| T2-1M | NATURAL | MSB_FIRST | 1024 | 1061 | 1048.020155917 | 1052 | 9 | 0.0109018874384 |
| T2-1M | NATURAL | MSB_FIRST | 16384 | 14039 | 13999.556678122 | 14004 | 35 | 0.00264976430793 |
| T2-1M | GRAY | LSB_FIRST | 1024 | 1061 | 1047.590932578 | 1052 | 9 | 0.0109018874384 |
| T2-1M | GRAY | LSB_FIRST | 16384 | 14038 | 13997.839784770 | 14004 | 34 | 0.00257405675628 |
| T2-1M | GRAY | MSB_FIRST | 1024 | 1061 | 1048.020155917 | 1052 | 9 | 0.0109018874384 |
| T2-1M | GRAY | MSB_FIRST | 16384 | 14039 | 13999.556678122 | 14004 | 35 | 0.00264976430793 |
| T2-1.5M | NATURAL | LSB_FIRST | 1024 | 934 | 916.852369493 | 917 | 17 | 0.0199224007545 |
| T2-1.5M | NATURAL | LSB_FIRST | 16384 | 13871 | 13804.741945500 | 13806 | 65 | 0.00476086782737 |
| T2-1.5M | NATURAL | MSB_FIRST | 1024 | 1085 | 1072.907804610 | 1077 | 8 | 0.0093752474139 |
| T2-1.5M | NATURAL | MSB_FIRST | 16384 | 14467 | 14428.963685969 | 14434 | 33 | 0.0024170559739 |
| T2-1.5M | GRAY | LSB_FIRST | 1024 | 1086 | 1072.444048223 | 1078 | 8 | 0.0093752474139 |
| T2-1.5M | GRAY | LSB_FIRST | 16384 | 14465 | 14427.108660418 | 14432 | 33 | 0.0024170559739 |
| T2-1.5M | GRAY | MSB_FIRST | 1024 | 1085 | 1072.907804610 | 1077 | 8 | 0.0093752474139 |
| T2-1.5M | GRAY | MSB_FIRST | 16384 | 14467 | 14428.963685969 | 14434 | 33 | 0.0024170559739 |
| T2-2M | NATURAL | LSB_FIRST | 1024 | 942 | 925.189432848 | 926 | 16 | 0.0186054911828 |
| T2-2M | NATURAL | LSB_FIRST | 16384 | 13983 | 13917.096452711 | 13918 | 65 | 0.00472405049563 |
| T2-2M | NATURAL | MSB_FIRST | 1024 | 1094 | 1079.770631008 | 1084 | 10 | 0.0116284319892 |
| T2-2M | NATURAL | MSB_FIRST | 16384 | 14575 | 14535.421245353 | 14540 | 35 | 0.00254371949765 |
| T2-2M | GRAY | LSB_FIRST | 1024 | 1094 | 1079.313562826 | 1085 | 9 | 0.0104655887903 |
| T2-2M | GRAY | LSB_FIRST | 16384 | 14573 | 14533.592972626 | 14540 | 33 | 0.00239836409778 |
| T2-2M | GRAY | MSB_FIRST | 1024 | 1094 | 1079.770631008 | 1084 | 10 | 0.0116284319892 |
| T2-2M | GRAY | MSB_FIRST | 16384 | 14575 | 14535.421245353 | 14540 | 35 | 0.00254371949765 |

All failure penalties, tags, expected yields, f values, and budget slacks are present in the per-scenario JSON files.
Same-source practical code gap remains UNKNOWN; no experiment or route decision follows from this diagnostic.
