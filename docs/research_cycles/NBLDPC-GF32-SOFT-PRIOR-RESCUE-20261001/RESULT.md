# EXPLORE — accepted finite synthetic description

Main accepts S4 independent PASS for batch `31dca97b-808c-4205-ac01-7c5ab7b9e9b5`, machine root `workspace/gf32_softprior_31dca97b/`. One attempt completed; no rerun/repair/resume. The frozen classification is **CONTROL_RANGE_UNINFORMATIVE**: control155 exceeds the preregistered39–153 interval. It remains unchanged despite the descriptive gain.

Same six accepted CONTROL/DV2 H_deep, frozen PMF and v35 BP90/alpha1;192 fresh pairs. Baseline-valid candidates pass through; failed baselines get all six cold SOFT one-row-prior restarts, selected by ORIGINAL effective-prior score without truth. These are soft trajectories, not hard clamps.

| graph | control exact | candidate exact | delta |
| --- | ---: | ---: | ---: |
| 2026093901 | 23 | 28 | +5 |
| 2026093902 | 27 | 28 | +1 |
| 2026093903 | 26 | 28 | +2 |
| 2026093904 | 30 | 31 | +1 |
| 2026093905 | 25 | 27 | +2 |
| 2026093906 | 24 | 25 | +1 |
| total | 155/192 | 167/192 | +12 |

Exact requires truth equality AND own syndrome. Paired both/candidate-only/control-only/neither=155/12/0/25. Syndrome failures37/25; selected syndrome-valid-wrong0/0, an observation without certification. Twelve of37 baseline failures were rescued. Selected rescue guesses:0:1,1:1,3:1,7:4,15:3,31:2. No post-hoc branch screen or threshold change.

Physical calls414=192+6×37; control logical calls192, candidate pipeline414. Iterations control4519/candidate23591, nominal E×iterations6039296 (cap30965760), not measured operations. Measured call-wall sums control27.92505s, candidate145.03111s (branch117.10606s); max call0.595664s. Resource checkpoint145.379914s through first-pass artifacts; excludes frozen terminal rewrites/log EOF and return serialization, and is not full-process wall/throughput. High-water ru_maxrss138113024B=131.715MiB; diagnostics1217935B. Data/integrity/auth/resource violations all0.

Syndrome260bits per METHOD frame once, internal restarts add0 disclosure; benchmark logical total99840bits, tag0. Verification NOT_IMPLEMENTED, undetected NOT_MEASURED. No FER/f_eff/SKR, statistical/causal/general-channel claim, cross-batch ranking, n256, qualification, publication, promotion or route decision follows. The descriptive recovery suggests a prospective same-condition independent replication; it does not relabel this batch.

S1/S3 independent PASS, explicit-fake tests17passed, T0/dry zero source/sample/decoder/writes. S4 independently recomputed actual GF32/poly37 source/seed/syndrome/entropy/selection/vector/accounting. Exact command and grant: PREREG_AND_AUTH.md. No commit/push/merge/add/archive.
