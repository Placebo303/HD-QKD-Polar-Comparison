# Independent actual-artifact review and main acceptance

Batch UUID: `67ca7191-3adc-4202-9d78-8bcd1a90a05a`  
Independent review: **A4 PASS**  
Main-thread acceptance: **COMPLETE / COMPLETE_DESCRIPTIVE_ONLY**

The independent A4 review covered the frozen source identity and paired sample lineage, actual constructor/deep endpoint matrices, each endpoint's own GF(32) syndrome and saved raw vectors, pair/graph/call maps, outcome and per-graph counts, and the preregistered cost/resource accounting. It did not construct graphs, search labels, or rerun a decoder. The one-attempt artifacts and counts agree with the accepted result in `RESULT.md`.

The main thread accepts only the completed descriptive comparison: constructor/deep exact-and-own-syndrome counts 1/1, `Delta=0`, paired both/constructor-only/deep-only/neither=1/0/0/191, with the shared successful pair on graph 2026093906. The result shows no separation between these two endpoints on the reused 192 samples. It is not a causal attribution, fresh holdout, route-closing result, or broader NB-LDPC claim. Verification remains `NOT_IMPLEMENTED`; undetected errors remain `NOT_MEASURED`; the authorization is consumed.

The terminal wall/RSS checkpoint occurred after the first-pass diagnostics, summary, attempt-log, and manifest writes. The final small state rewrite was after that checkpoint and is not recursively timed. The independent review and acceptance append to the execution log is also post-checkpoint and does not alter the measured batch wall.
