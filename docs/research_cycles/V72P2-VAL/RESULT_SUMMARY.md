# V72P2: accepted negative descriptive smoke

Implementation/accepted amended plan: b33664d00b5b22a02b61df95b00c99ae0a0368b8.
Artifacts: comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903/.
Main Pre-EXECUTE and independent Pre-RESULT: PASS; detailed evidence in REVIEW_VERDICT.md.

One invocation, one1M session, CAL702..1725 and fixed non-fresh VAL1726..1761 (nine1024-symbol blocks). CAL-only hierarchical model selected lambda221.22162910704503; selected-CV CE reference7.135005172802673. This is a descriptive reused-VAL observation, not confirmation/FER/SKR/qualification/promotion.

| Block (zero-based) | Frames | Iterations | Seconds | Raw/final bit errors | Raw/final symbol errors |
|---|---|---:|---:|---:|---:|
|0|1726–1729|334|116.313|3100/3100|620/620|
|1|1730–1733|340|117.391|2930/2930|597/597|
|2|1734–1737|339|117.203|3034/3034|611/611|
|3|1738–1741|338|116.938|3066/3066|622/622|
|4|1742–1745|331|114.469|2981/2981|600/600|
|5|1746–1749|336|115.906|2970/2970|610/610|
|6|1750–1753|342|117.657|2996/2996|596/596|
|7|1754–1757|339|116.954|2927/2927|593/593|
|8|1758–1761|338|118.156|2999/2999|622/622|

All9 outcomes LADDER_EXHAUSTED;0 exact accepted,0 protocol accepted,0 accepted-wrong,0 invalid or not-attempted. Final residuals all meet tolerance but syndrome and tag both fail. Error counts show no improvement; they do not establish candidate bitwise identity or the cause of failure.

Each block:9036 syndrome+64tag=9100 leak_IR bits;71 CONTINUE bits;9171 total modelled public bits. Totals81900 and82539; failed blocks are included. All-attempt f_model_relative1.2455097837734632 and public-relative1.2552274974710365; success-conditional=null. ACK/header/authentication/transport excluded. Ratios use selected CAL-CV cross-entropy, not Shannon entropy or a security efficiency. No positive secret-key claim.

Total3037 BP iterations and1057.375s including CAL. No real rerun, tuning, other source or budget change. Raw/large data and matrices are not published; local input location,selected IDs,parameters,command and registry are recorded in manifest for reproduction, not permission to rerun.

Regression:29 tests passed, historical P1C1-iteration1.046s exceeded<1s. That failure is explicitly retained and non-blocking under the pre-execution amendment; historical thresholds and kernel are unchanged. Other P1C numerical checks passed. No claim of an all-pass predecessor regression.

Execution permissions are consumed. Further diagnosis or V73 requires a new separately reviewed task; this result does not authorize expansion or establish an information limit.
