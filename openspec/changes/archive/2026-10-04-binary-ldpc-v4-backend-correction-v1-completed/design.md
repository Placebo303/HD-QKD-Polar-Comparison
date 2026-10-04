# Design: Binary LDPC v4 Backend Correction v1

## 1. Additive Compatibility Boundary

Do not edit any source file bound by
`20260727_v1_binary_ldpc_v4_development`. Add:

- `formal_ir/ldpc_v4_development_v2.py`;
- `cli/run_ldpc_v4_development_v2.py`;
- `cli/verify_ldpc_v4_development_v2.py`;
- focused tests.

The v2 evaluator preserves the v4 evaluator contract and logic. Its only
production semantic difference is:

```python
error_channel=np.asarray(error_channel, dtype=np.float64).tolist()
```

at decoder construction. It must still compute the channel through
`plane_error_channel`; no clipping, probability, decoding, or status rule may
change. Test injection remains explicit and cannot masquerade as the production
backend.

## 2. Constructor Regression

The focused regression must:

1. reconstruct a real v4 candidate matrix and Bob-conditioned channel;
2. assert length 256, Python `list`, finite float elements in `[1e-6,.49]`;
3. construct the actual pinned `ldpc==2.4.1` `BpOsdDecoder`;
4. demonstrate that the unconverted NumPy array raises the recorded `TypeError`;
5. run at least one corrected development decode through the production path
   and show it does not become `development_decoder_error`.

Dependency mismatch or absence fails the production regression; it is not
skipped or replaced by a fake decoder.

## 3. Fresh Development Package

The production output is a fresh explicit directory with package identity
`binary_ldpc_v4_development_v2`. Prepare/execute remain separate,
no-overwrite, and non-resumable. The plan binds:

- the same verified v3 TTBIN lock used by v4;
- the predecessor v4 plan, report, and outcome file SHA256 values;
- all existing channel/codebook inputs;
- the v2 evaluator, runner, verifier, and reused relevant source hashes;
- `ldpc==2.4.1`;
- exact execution order and expected 40,960 plane outcomes;
- 512 frame denominators in each stratum and readiness floor 495.

The seven-artifact shape is retained with versioned schemas and run ID. The
read-only verifier reconstructs source, model, matrices, deterministic frames,
selection, artifact DAG, accounting, and readiness with
`decoder_reexecution=false`.

## 4. Production Stop Rule

After focused and regression acceptance, the main thread:

1. prepares one fresh plan;
2. audits its hashes, predecessor binding, counts, order, caps, and gate;
3. executes once;
4. verifies once.

If either stratum has fewer than 495/512 successes, or any forbidden
backend/source/internal/accounting/unclassified failure occurs, retain the
package and stop. Do not tune, rerun, or create synthetic output.

If both strata pass, record `ready_for_synthetic_prepare=true` and stop this
change. A later main-thread action may invoke the already implemented fresh
synthetic tooling only after a separate plan review; this change does not
prepare or execute it.

