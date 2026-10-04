# Independent acceptance — GF32 construction canary

**Batch UUID:** `a9a18abe-3547-4d16-aa50-1f7150182f31`  
**Independent reviewer:** `iter_contract`  
**Independent C4 verdict:** `PASS`  
**Main acceptance:** `CONSTRUCTION_FEASIBLE` within the frozen protocol

The independent review checked that the three artifacts agree on UUID, contract, seed namespace, terminal status, and selection. It inspected all 13 saved matrices: each is `52×128`, has GF(32) symbols, matches its requested degree profile and edge count, has GF(32)/poly-37 rank 52, and has one connected component. Edge/coefficient-to-matrix maps and matrix/attempt/group/pair indices were consistent.

The reviewer also checked the paired-seed rule and retained failure. Graphs `2026093901`–`2026093904` and `2026093906` first selected at `j=0`; graph `2026093905` retained its candidate `j=0` construction failure alongside the admitted control, then selected both profiles at `j=1` with common seed `2560859716`. The failed placement was `no eligible check placement at variable 127 socket 2`. The reviewer did not rebuild graphs, run a decoder, or modify files.

Main accepts the attempt only as `COMPLETE / CONSTRUCTION_FEASIBLE`: all six fixed groups obtained a common admitted pair, with 14 constructor calls, 13 actual matrices, no exhausted groups, and no resource stop. This supports feasibility only for the frozen constructor and paired-seed protocol. It does not establish an unbiased random-graph performance population, decoder performance, a route decision, or FER/throughput/security/qualification/publication claims. The one-shot grant is consumed; no rerun or extension is authorized.
