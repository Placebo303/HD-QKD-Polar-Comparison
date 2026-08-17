# Tasks: formal-nonbinary-ldpc-v23-met-protograph-de

Status: IN_PROGRESS — protograph scan implemented; regular (2..8)x32..128 all non-converged (entropy plateaus ~0.2)

## T0 Planning
- [ ] P0: freeze V23 task packet
- [ ] P1: define small protograph search grid and stop rules

## T1 Engineering
- [x] I01: add protograph base-matrix DE candidate generator (`nonbinary_v23_protograph.py`)
- [x] I02: protograph DE gate CLI + tests
- [ ] I03: MET extension (if needed)

## T2 Execute
- [x] E01: scan regular protographs on q=1024 structured channel (all non-converged)
- [ ] E02: record DE convergence at target f

## T3 Verify/Closeout
- [ ] V01: verify with V22b semantics
- [ ] C01: docs/memory update
