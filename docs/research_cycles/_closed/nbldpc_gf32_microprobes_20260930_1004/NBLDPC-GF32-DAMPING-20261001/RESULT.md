# Fixed-code probability damping — RESULT

Batch `a3444f81-f091-4ffd-9c16-393c6062f6e3` is closed and main-accepted as one bounded synthetic iid marginal-proxy EXPLORE comparison. It used the six accepted deep H0D matrices, one fixed PMF (`p0=0.55`), and 192 paired holdouts / 384 decoder calls. The only arm difference was damping: control `alpha=1.0`, candidate `alpha=0.5`. All pairs completed.

| Measure | Result |
|---|---:|
| Control exact-and-syndrome successes | 154 / 192 |
| Candidate exact-and-syndrome successes | 153 / 192 |
| Candidate minus control | −1 |
| Paired states (both / candidate-only / control-only / neither) | 153 / 0 / 1 / 38 |

Per-graph counts (control → candidate; delta) for seeds 2026093901–2026093906 were `29→29 (0)`, `24→24 (0)`, `22→21 (−1)`, `27→27 (0)`, `24→24 (0)`, and `28→28 (0)`. Thus `positive Δg=0/6`. The frozen terminal classification is `CONTROL_RANGE_UNINFORMATIVE` because control=154 exceeds the allowed upper bound 153. Keep that classification; do not relabel it as `NO_SUFFICIENT_SIGNAL` or a route outcome.

Total decoder iterations were 4533 for control and 5663 for candidate. Per-arm decoder wall sums were 27.204686 s and 43.927295 s. Batch wall was 121.964675789 s; maximum per-call wall was 0.712394023 s; API-reported maximum RSS was 102313984 B. Integrity, resource and authorization violations were all zero; stop reason was empty. Disclosure was 99840 syndrome bits (260 per call), tag bits were zero, syndrome-consistent wrong rows were zero, verification was `NOT_IMPLEMENTED`, and undetected was `NOT_MEASURED`. `FER`, `f_eff`, and `SKR` were not measured.

Independent `faithful_scope` batch-end review passed P7 (reviewer != operator). Its review covered frozen seeds, metadata and artifact lineage; the actual truth/prior arrays were not saved, so the vectors were not independently re-created value by value. The evidence does not support recommending `alpha=0.5`; keep `alpha=1.0` as the frozen decoder setting for the source-label work. This is an experiment-scoped setting, not a route decision. Historical R21 S0/m100/shifted-source `NO-DAMP-GAIN` remains in its own scope and is neither reopened nor overturned here.

The claim ceiling is this finite synthetic iid marginal-proxy comparison on the six fixed deep H0D graphs. It does not establish conditional-channel performance, causality, FER, `f_eff`, SKR, throughput, qualification, publication or a route outcome, and must not be pooled or ranked with other batches. The four machine artifacts are `workspace/gf32_damping_a3444f81/{manifest.json,frame_records.csv,summary.json,EXPLORATION_LOG.md}`. This batch's execution grant is consumed; no rerun, resume, extra iterations or alpha change is authorized by this packet.
