# Check-node reuse implementation contract

This reduces repeated arithmetic in the 1024-symbol mainline's check-node updates while keeping numerical outputs unchanged, preparing a power-sufficient efficiency comparison. No measured runtime or f gain is presumed.

Scope is implementation plus mathematical helper tests, not a decoder experiment. Main owns requirements and acceptance; Luna owns only `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v10_fftqspa.py` and new `comparison_bench/tests/test_nbldpc_check_reuse.py`. Read each existing file before changing it. Other agents work in this checkout; preserve their edits.

Acceptance:

- E1: add `check_update_all_log(log_messages, coefficients, syndrome, field)` returning outgoing arrays in original target order. Hoist the exact per-message coefficient permutation, exp, existing normalization, stack and fwht_batched once; use the same ordered `others`, np.prod(axis=0), inverse /q, shift and existing output normalization for each target. Do not refactor or change the reference check_update_log.
- E2: candidate stays unconnected to the decoder for this milestone. No signature/default/schema changes. Wiring and complete decoder equivalence need the later frozen gate; this implementation is only a callable kernel candidate.
- E3: deterministic GF32 fixtures cover constant distributions, asymmetric log masses, floored zero support, several nonzero coefficients, nonzero syndromes and degree 2/3/8. Compare every target to check_update_log with np.array_equal. These fixtures test arithmetic identity, not decoding outcomes; no RNG, BER/FER sample, decoder call or timing benchmark.
- E4: preserve explicit errors for invalid field, length, nonfinite messages, invalid coefficients/syndrome and degree below two. Keep the existing validation semantics and do not build a new defensive framework.
- E5: run only the new helper tests using `.venv`, pytest -p no:cacheprovider -o addopts=, fresh workspace/nbldpc_check_reuse/<uuid>, timeout 120 seconds. Retain failures, stop on a concrete inconsistency. Return changed files, exact command/errors and frozen IDs, without commit/push/self-acceptance.

Independent review checks the numerical operation order and scope. No decoder-performance packet is written here; that future packet first needs effect/MDE, calibrated inputs and runtime budget. Return complete frozen items or a concrete blocker with one decision needed.
