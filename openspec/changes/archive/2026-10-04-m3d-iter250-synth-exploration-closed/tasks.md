# Tasks

- [x] M3D-01: add default-preserving optional `max_iter` to the existing soft-marginal block decoder; test that omitted argument still passes 300 to the frozen kernel and explicit 250 is labeled correctly.
- [x] M3D-02: implement a thin Stage-1-only M3D two-arm synthetic CLI using the exact 16 selected M3-b seed indices per graph and fresh output roots, with fake-only tests for seed pairing, exact/undetected isolation, root refusal, resource stops and no production calls in tests.
- [ ] M3D-03: main-thread Pre-EXECUTE: scoped diff, focused tests, exact command, fresh roots, input identity, budget and explicit batch authorization.
- [ ] M3D-04: if granted, execute the two frozen arms sequentially once, keep one append-only exploration log and failed attempts.
- [ ] M3D-05: one independent batch-end review and main-thread instance-level acceptance/rejection against the frozen gate; no real-data or route promotion.
