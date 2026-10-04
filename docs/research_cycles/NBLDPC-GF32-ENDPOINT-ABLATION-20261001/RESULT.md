# GF32 endpoint ablation EXPLORE result

Batch UUID: `67ca7191-3adc-4202-9d78-8bcd1a90a05a`  
Track: `EXPLORE`  
Machine root: `workspace/gf32_endpoint_67ca7191/`

The single authorized same-sample replay completed 192 paired frames / 384 decoder calls using the 192 truths, seeds, and source lineage from degree-admitted batch `a9352bc1-ae56-443b-ae93-9dcfa85d4229`. It compared only the fixed constructor and deep label endpoints on the six admitted DV3 graphs; it added no holdout samples, graph construction, label search, or arm. Terminal status is `COMPLETE`. After independent A4 PASS, the main thread accepted the result as `COMPLETE_DESCRIPTIVE_ONLY`.

Constructor and deep each produced 1 exact output with its own GF(32) syndrome valid, for `Delta=0`. Paired both/constructor-only/deep-only/neither counts were 1/0/0/191. Each arm had 191 raw syndrome failures and zero syndrome-valid-wrong outputs. Per-graph exact counts for graph IDs 2026093901–2026093906 were 0, 0, 0, 0, 0, 1 in both arms; the one shared successful pair was on graph 2026093906. Thus the two tested endpoints were equally low on these reused samples. This is a fixed-endpoint association only; it does not identify label causality, provide a fresh holdout, or close/reject a route.

Iteration totals were 17198/17199 (constructor/deep). The nominal `E×iteration` proxy was 13208448 of the frozen 13271040 cap; it is not a count of measured operations. Decoder-wall sums were 147.9759043/147.9588459 s, and batch wall through the final completion checkpoint was 298.137325806 s. The final wall/RSS checkpoint followed the first-pass diagnostics, summary, attempt-log, and manifest writes. The small terminal-state rewrite followed that checkpoint and is not recursively timed. Sampled maximum RSS was 103182336 B over 1347 samples, not a continuous peak. Disclosure was 99840 syndrome bits (260 per attempted arm); tag bits were zero. Verification remains `NOT_IMPLEMENTED` and undetected errors `NOT_MEASURED`. Integrity, resource, and authorization violations were zero; no stop reason was recorded.

The machine root contains `manifest.json`, `summary.json`, `frame_records.csv` (384 rows), `diagnostics.npz`, and the append-only `EXPLORATION_LOG.md`. The four JSON/CSV/NPZ artifacts were left unchanged during closeout. The exact one-shot command was:

```sh
wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_endpoint_ablation_probe --execute --out-root workspace/gf32_endpoint_67ca7191
```

The accepted evidence is limited to this same-sample association between the two frozen endpoint labels on six graphs. It is not a causal label attribution, fresh-holdout result, route decision, FER/`f_eff`/SKR, throughput/security, real-channel, qualification, publication, or cross-batch ranking result. The one-shot authorization is consumed; no rerun, resume, repair, or extension is authorized.
