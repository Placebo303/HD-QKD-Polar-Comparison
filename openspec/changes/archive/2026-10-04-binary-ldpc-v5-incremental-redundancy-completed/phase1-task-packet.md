# Frozen Phase 1 Operator Packet

The main thread owns requirements and acceptance. Terra low is coder/test
operator only.

## Allowed files

- New v5 source-partition and H2 codebook modules under
  `comparison_bench/src/comparison_bench/formal_ir/`
- New v5 formal method module
- New focused `test_ldpc_v5_*` files
- Phase 1 checklist state in this change

Do not modify v1-v4 files, historical packages, frozen baseline directories,
handoff/memory/decision documents, or any production output.

## Implementation IDs

- **P1-01:** exact predecessor and 10 dB source binding. Predecessor file
  sets, hashes, and replay results are frozen in `predecessor-contract.md`.
- **P1-02:** deterministic 128 confirmation + 512 development partition with
  complete exclusion/uniqueness proofs. Exact lock schema/order/digests are
  frozen in `partition-contract.md`.
- **P1-03:** role-scoped APIs; development cannot request confirmation arrays.
  Exact signatures and fail-before-load behavior are frozen in
  `partition-contract.md`.
- **P1-04:** deterministic H2 reconstruction, rank/column/diagnostic/canonical
  manifest contract. Exact construction is frozen in
  `h2-construction-contract.md`.
- **P1-05:** implement exact C0/C1/C2 decoder and transcript state machines.
  The backend and stacked-matrix semantics are frozen in
  `decoder-contract.md`; canonical candidate policies are frozen in
  `policy-contract.md`.
- **P1-06:** exact first/fallback leakage, public-control, seed, epsilon,
  denominator, cap, and status accounting. Policy provenance and caps are
  frozen in `policy-contract.md`.
- **P1-07:** strict validators and public-payload reconstruction helpers.
  Exact event, outcome, CSV, and replay semantics are frozen in
  `transcript-outcome-contract.md`.
- **P1-08:** no test path can call production decoder/source/output implicitly.
  The exact Phase-1-only in-memory runner and verifier are frozen in
  `phase1-test-harness-contract.md`; they must not define or emit a Phase 2
  package.

## Acceptance IDs

- **T0:** compile/import, constants, tiny GF(2), deterministic reconstruction.
- **T1-SOURCE:** exact source acceptance and every raw/sidecar/metadata/
  relocation/hash/tail/domain/capacity/duplicate/overlap tamper.
- **T1-H2:** every plane rank/shape/weight/hash/trial; byte and semantic
  tampering; bounded construction; detached-copy behavior.
- **T1-METHOD:** exact C0/C1/C2 success, mismatch, fallback, malformed decoder,
  syndrome inconsistency, dependency failure, all caps, and exception paths.
- **T1-ACCOUNT:** first-round and fallback transcript, leakage, two-seed,
  epsilon, feedback, denominator, and status reconstruction.
- **T2:** complete fake development-shaped run without production access;
  deep locally re-signed source/method/transcript/public-payload/accounting
  tamper rejection, using `phase1-test-harness-contract.md`.
- **T3:** v5 focused plus v4 codebook/channel/formal/development/synthetic/
  16 dB/10 dB regressions, compile, scoped diff, predecessor hashes, frozen
  directory diff, and absence of v5 production outputs.

Return only after P1-01--P1-08 and T0--T3 are complete, or on a concrete
blocker with exact command, traceback, attempted remedies, and one required
main-thread decision. Never run production.
