# Delta Spec: Formal Nonbinary LDPC v2

## Requirement: Independent successor evidence

The successor SHALL use `nbldpc_formal_v2`, `NBLDPC2\n` canonical codebooks, and `NBLDPCQ2` qualification plans. It SHALL preserve `nbldpc_formal_v1` N3 artifacts as immutable non-promoted evidence. v1 confirmation SHALL NOT select, tune, rerun, or qualify v2.

## Requirement: Exact QC48 construction and candidates

v2 SHALL construct the exact 48x64 GF(1024) mother specified in the design: 16 information columns, parity block `I+alpha P` with alpha=2, K16 1-factorization information pairs, one exact SHA256 round permutation, the lexicographically first valid rotation vector from the bounded 8^6 search, SHA256 nonzero coefficients, row weight four, information degree six, parity degree two, prefix checks 24/32/40/48, full pinned-field ranks, and zero 4-cycles. The verifier SHALL recompute every construction input, factorization/round/rotation proof, alpha^48 inequality, B rank, prefix rank, cycle count, bytes, and IDs.

The only candidates SHALL be the named v1 flooding control, QC48 flooding, QC48 damping lambda=.5, and QC48 damping lambda=.5 plus componentwise check-message tempering exponent .8 before damping. Scalar normalization alone SHALL NOT be a candidate operation.

## Requirement: Fresh qualification and accounting

v2 SHALL use the frozen PCG64 roots, 24 fresh sacrificed development frames and 32 fresh confirmation frames per p=.20/.30 stratum, exact generation call order, zero-overlap proof, and unique 703-bit CSPRNG Toeplitz records. Development alone selects a global policy with the frozen entropy formula, margins, iteration limits, and ranking: it SHALL maximize the minimum p=.20/p=.30 verified-success count, then total successes, then minimize disclosure and iterations. The v1 control may select only prefixes 16/24/32; QC48 candidates may select only 24/32/40/48. Candidate ID, permitted-prefix list, and selected per-stratum checks SHALL be policy-hash inputs; an unmet required check count is `unsupported_domain`. Confirmation requires the 22/24 readiness floor in both strata.

A policy SHALL be ineligible exactly when any development outcome is `syndrome_inconsistent`, `decoder_error`, `unsupported_domain`, `codebook_invalid`, `invalid_run`, or outside the allowed retained decoder outcomes. `decode_failed`, `verify_failed`, and `aborted_resource_limit` SHALL remain performance failures and SHALL NOT independently make a policy ineligible. If there are zero eligible policies, selection SHALL be exactly `{"selected_policy":null,"selected_policy_sha256":null,"selection_key":null,"reason":"no_eligible_policy"}`, readiness SHALL be false, status SHALL be `non_promoted_development`, and confirmation SHALL NOT be generated or executed.

A 48-check syndrome SHALL disclose exactly 480 key-dependent bits; an invoked tag SHALL add 64 bits; Toeplitz seed bits remain public control. The q=1024/n=64/check<=48/row-weight=4/max-iter<=20 dense-message domain SHALL be capped at 16 MiB, per-call 20 seconds, one worker, and 21,600 total seconds.

## Requirement: Promotion, artifacts, and provenance

Promotion SHALL require 31/32 verified successes independently in each confirmation stratum, full denominators, no prohibited integrity failure, and exact transcript/accounting/hash-DAG verification. Readiness failure is `non_promoted_development`; all other gate failures are non-promoted. Neither result authorizes N4.

The eight named artifacts and statuses in the design SHALL be additive/no-overwrite. The verifier SHALL gate on scoped qualification source/contract/artifact hashes; live whole-worktree drift SHALL be recorded diagnostically and SHALL NOT independently invalidate a package.

## Requirement: N4 boundary

v2 SHALL NOT process raw `.ttbin` or real sidecars. Only synthetic promotion may authorize a separately reviewed N4 read-only sidecar adapter, lock, verifier, and later explicitly authorized real-data run.
