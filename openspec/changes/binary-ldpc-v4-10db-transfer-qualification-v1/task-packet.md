# Frozen Operator Packet: Binary LDPC v4 10 dB Transfer Qualification v1

The operator codes and tests only. The main thread owns this packet,
acceptance, thresholds, and scientific conclusions.

## Allowed files

- New `comparison_bench/src/comparison_bench/formal_ir/ldpc_v4_10db_source.py`
- New 10 dB runner and verifier modules under
  `comparison_bench/src/comparison_bench/cli/`
- New focused tests named `test_ldpc_v4_10db_*`
- This change's checklist only to report completed implementation IDs

All other files are forbidden. In particular, do not modify any historical
runner, verifier, method, codebook, channel, source adapter, artifact, frozen
baseline directory, handoff, decision log, or project memory.

## Implementation IDs

- **P1-01 Source lock:** implement the exact hashes, relocation, metadata,
  array, framing, capacity, uniqueness, and canonical-source rules in
  `design.md`.
- **P1-02 Selection:** reconstruct every complete-frame identity, reject
  duplicate payloads, apply the exact 10 dB selection domain, and select
  exactly 128 per stratum deterministically.
- **P1-03 Prerequisites:** bind and strictly replay the exact promoted
  synthetic package and exact completed non-promoted 16 dB predecessor.
- **P1-04 Plan:** generate new isolated roots/seeds, bind scoped source hashes,
  exact execution order, caps, backend, gate, and both prerequisite DAGs.
- **P1-05 Execute:** preserve v4 method semantics and nine-file
  prepare/execute/no-overwrite/failure-finalization behavior.
- **P1-06 Verify:** read-only reconstruct every source, prerequisite, plan,
  artifact, transcript/public-payload, leakage/accounting, denominator, and
  promotion relation with `decoder_reexecution=false`.
- **P1-07 Production isolation:** production CLIs expose no test switches;
  tests must explicitly call private helpers with fake runners and disposable
  roots. Never enter a production decoder or output directory from tests.
- **P1-08 Performance:** reuse the accepted bounded replay-cache approach
  without modifying any historically bound file; always restore temporary
  references in `finally`.

## Acceptance IDs

- **T0:** compile/import, exact constants, canonical serialization, tiny
  identity/selection/root math.
- **T1-SOURCE:** accept exact source; reject independently changed raw,
  chunk, each sidecar/provenance file, suffix, competing source, metadata,
  array domain/shape/dtype, tail padding, capacity, and duplicate payload.
- **T1-PLAN:** deterministic 128-per-layer selection; source-aware identity;
  fresh roots/seeds; isolation from every predecessor; source DAG and
  no-overwrite checks.
- **T1-PREREQ:** reject missing, modified, locally re-signed, or semantically
  inconsistent synthetic and 16 dB packages, including altered 16 dB counts
  or promotion state.
- **T2-RUN:** complete fake 384-frame qualification; partial finalization;
  decoder exception; per-frame/complete cap; denominator retention; all gate
  branches; exactly nine files.
- **T2-TAMPER:** reject raw byte drift, locally re-signed outcome/transcript
  semantics, re-signed manifest/index links, public-payload/source/leakage/
  accounting/gate changes, extra/missing artifacts, and source relocation
  changes.
- **T2-READONLY:** verifier changes no bytes, creates no files, never
  reexecutes the decoder, and restores replay patches on success/error.
- **T3:** focused 10 dB suite plus binary v4 codebook/channel/formal,
  development, corrected synthetic, 16 dB source/qualification, formal-real,
  compilation, scoped diff, historical source/artifact hashes, frozen
  directory diff, and absence of a 10 dB production output root.

## Return conditions

Return only when every P1 and T0-T3 item is complete, or on one concrete
blocker with failing command, exact traceback, attempted remedies, and the
single main-thread decision required. Do not run production prepare or
execute. Do not report acceptance or scientific conclusions.

