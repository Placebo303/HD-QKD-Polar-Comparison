# Frozen Phase 2 Task Packet

Owner: main thread  
Operator: Terra low  
Return condition: all IDs complete, or one concrete reproducible blocker.

## File Scope

Allowed:

- `comparison_bench/src/comparison_bench/cli/run_ldpc_v4_16db_transfer_qualification.py`
- `comparison_bench/src/comparison_bench/cli/verify_ldpc_v4_16db_transfer_qualification.py`
- `comparison_bench/src/comparison_bench/formal_ir/ldpc_v4_16db_source.py`
  only if required to expose an already-frozen read-only accessor
- `comparison_bench/tests/test_ldpc_v4_16db_transfer_qualification.py`
- `comparison_bench/tests/test_ldpc_v4_16db_source.py`

Forbidden:

- `src/`, `experiments/`, `tools/`, historical outputs, existing v1-v4
  runners/verifiers, OpenSpec requirements, thresholds, and production output
  directories.

## Acceptance IDs

### P2-C Contract

- **P2-C01**: Production prerequisite is exactly the frozen corrected-v2
  synthetic directory and all registered prerequisite artifact hashes.
- **P2-C02**: Plan validation uses exact key sets and exact schema, run ID,
  method, strata, count, caps, gate, backend, test flag, source hashes,
  source-lock hash, synthetic binding, order, roots, and self-hash.
- **P2-C03**: Data lock is rebuilt from external 16 dB source files in both
  production and test verification; never trust the package copy as the
  reference.
- **P2-C04**: Three fresh 16-byte roots and all derived 2623-bit Toeplitz
  seeds reconstruct exactly and are disjoint within the package and from v3,
  development, synthetic, and existing real-plan roots/seeds.
- **P2-C05**: Prepare exclusively creates only plan and data lock; execute
  requires exactly those two files and finalizes exactly nine immutable
  artifacts on success or exception.
- **P2-C06**: Production code exposes no CLI test switch and tests always pass
  an explicit fake/zero decoder to test-only execution.

### P2-V Verifier

- **P2-V01**: Rebuild source, synthetic prerequisite, scoped source hashes,
  method manifests, roots/seeds, selection, arrays, order, and frame
  provenance without decoder reexecution.
- **P2-V02**: Rebuild canonical event grouping, transcript lengths/hashes,
  outcome semantics, verification seed/public payload, leakage components,
  and all outcome accounting.
- **P2-V03**: Enforce exact run-manifest key set/schema/run ID/status/stop
  reason/plan hash/outcome count/artifact index and
  `decoder_reexecution=false`.
- **P2-V04**: Enforce exact report key set/schema/run ID/status/stop reason,
  plan/run-manifest linkage, reconstructed gates, promoted iff completed and
  every stratum promotes, `decoder_reexecution=false`, and
  `source_relocation=true`.
- **P2-V05**: A completed package contains exactly 384 outcomes and 128
  denominators per stratum. A failed package may be partial but cannot
  promote; all retained outcomes remain accounted. Forbidden, internal,
  source, accounting, and unclassified failures prevent promotion.
- **P2-V06**: Verifier is read-only; every package-file SHA256 is identical
  before and after verification and it reports
  `decoder_reexecution=false`.

### P2-T Tests

- **P2-T00**: T0 compile/import passes for source, runner, verifier, and tests.
- **P2-T01**: Fresh private prepare-execute-verify succeeds with an explicit
  zero/fake decoder; no production path or output is entered.
- **P2-T02**: Synthetic non-promotion/path/hash drift, insufficient source,
  no-overwrite, execute-contract, root/seed collision, and partial exception
  finalization are rejected or retained as specified.
- **P2-T03**: Raw byte tampering is rejected for every one of the nine
  artifacts.
- **P2-T04**: Re-signed semantic cases cover plan contract/order, source-lock
  frame/source binding, synthetic artifact binding, root/seed, frame
  provenance, outcome status/verification seed/leakage/accounting,
  transcript event/canonical hash, public payload, run manifest,
  denominator/gates, report status/linkage/promoted, and source relocation.
  Each case recomputes directly affected self-hashes and artifact indexes so a
  superficial hash check cannot be the rejecting layer.
- **P2-T05**: T2 complete private qualification plus strict read-only replay
  passes, including directory-hash equality before/after.

## Commands

Use a fresh additive writable root below
`workspace/v4_16db_transfer_phase2/<uuid>` and disable pytest cache:

```powershell
python -m py_compile `
  comparison_bench/src/comparison_bench/formal_ir/ldpc_v4_16db_source.py `
  comparison_bench/src/comparison_bench/cli/run_ldpc_v4_16db_transfer_qualification.py `
  comparison_bench/src/comparison_bench/cli/verify_ldpc_v4_16db_transfer_qualification.py `
  comparison_bench/tests/test_ldpc_v4_16db_source.py `
  comparison_bench/tests/test_ldpc_v4_16db_transfer_qualification.py

python -m pytest -q -p no:cacheprovider `
  comparison_bench/tests/test_ldpc_v4_16db_source.py `
  comparison_bench/tests/test_ldpc_v4_16db_transfer_qualification.py
```

## Required Delivery

Report only:

- acceptance IDs completed;
- changed files;
- exact commands and results;
- any remaining frozen ID.

Do not edit `tasks.md`, make acceptance claims, run production prepare or
execute, or return merely because an intermediate batch is complete.
