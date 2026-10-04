# Tasks

- [x] M3B-01: implement truthful, additive M3-b graph-to-P1 adapter and any minimal optional P1-core parameters; preserve default P1 behavior.
- [x] M3B-02: fake-only tests for exact frozen graph selection, identity/prefix pins, dual execution gate, zero-production dry path, truthful loaded-twice versus constructed-twice provenance, output label/root, Stage-2 non-exact set, disclosure charged on attempted rescues including one failed rescue, and old P1 defaults.
- [x] M3B-03: main-thread Pre-EXECUTE with exact command, output absence, frozen inputs, budget, tests, branch/scope, and user grant; no decoder before PASS.
- [x] M3B-04: run two frozen arms sequentially under one EXPLORE_HEAVY grant, retain attempts in one append-only log, stop on a terminal gate failure.
- [x] M3B-05: one independent batch-end review of per-arm machine evidence and paired old P1 records before main-thread acceptance. Never promote a route or real-data claim from this synthetic batch.
