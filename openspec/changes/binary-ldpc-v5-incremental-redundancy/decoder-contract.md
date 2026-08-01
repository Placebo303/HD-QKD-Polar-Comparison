# Frozen v5 Decoder Contract

This file resolves P1-05 implementation ambiguity. It changes no candidate,
gate, or claim boundary.

## 1. Exact backend call

Use the same import and factory seam as v4:

```python
from ldpc import BpOsdDecoder
decoder = factory(h, **params)
error = np.asarray(decoder.decode(delta)).reshape(-1)
```

`h` is a detached `np.uint8` binary matrix. `delta` is the `np.uint8`
syndrome difference. `error` must be exactly 256 binary values.

Common parameters are:

- `bp_method="product_sum"`
- `schedule="serial"`
- `omp_thread_count=1`
- `serial_schedule_order=list(range(256))`
- `error_channel=np.asarray(channel, dtype=np.float64).tolist()`

C0 and C2 round 0 use `max_iter=50`, `osd_method="OSD_0"`,
`osd_order=0`. C1 and C2 fallback use `max_iter=100`,
`osd_method="OSD_CS"`, `osd_order=2`.

No other constructor argument or implicit default may determine semantics.

## 2. H1 and stacked fallback

For plane `p`:

- round 0 uses `h1`, `s1 = h1 @ alice`, and
  `delta1 = s1 XOR (h1 @ bob_original)`;
- fallback uses
  `h12 = np.vstack((h1, h2)).astype(np.uint8)`,
  `s12 = concatenate(s1, s2)`, and
  `delta12 = s12 XOR (h12 @ bob_original)`.

`s2` alone is disclosed during fallback because `s1` was already public.
The decoder receives the full stacked `delta12`.

Save the original Bob bit planes before round 0. Fallback decoding starts
from `bob_original` for every plane; it must not apply corrections on top of
the possibly wrong round-0 Bob estimate. After exact stacked-syndrome
validation, set:

`bob_fallback[:, p] = bob_original[:, p] XOR error`.

The same frozen per-position channel vector is used for H1 and H1/H2.

## 3. Preflight and failure mapping

Before the first key-dependent event, require `ldpc==2.4.1` and construct one
decoder for every distinct matrix/policy shape the selected candidate may
use. Any import, version, or constructor failure is `backend_unavailable`,
not attempted, with no transcript.

After disclosure:

- decoder call raises and elapsed time reached cap:
  `aborted_resource_limit`, reason `wall_s`;
- decoder call raises below cap: `decoder_error`, reason
  `decoder_exception`;
- output length/domain invalid: `decoder_error`, reason
  `malformed_decoder_output`;
- decoded error does not reproduce the exact supplied syndrome delta:
  `syndrome_inconsistent`, reason `decoder_syndrome_mismatch`;
- event/call/time cap reached: `aborted_resource_limit` with the exact cap
  name.

All attempted terminal states remain in the denominator. No exception may
escape the formal method.

## 4. Seeds and verification

The formal v5 method receives `locked_seeds`, an exact two-element sequence
of independently derived 2623-bit seed records.

- C0/C1 use only `locked_seeds[0]`; seed 1 is never emitted or checked.
- C2 round 0 uses seed 0.
- C2 fallback uses seed 1 and must prove distinct seed IDs.

Round-0 mismatch is followed by a `FALLBACK_NACK` event with
`direction="bob_to_alice"`, `pass_id=1`, zero key-dependent bits, and one
public control bit. H2 syndrome events use `pass_id=1`. The second seed/tag/
check also uses `pass_id=1`.

Round-0 success returns `epsilon_ec=2^-64`. C2 fallback success or final
failure returns `epsilon_ec=2^-63`, reflecting two tag checks. A tag mismatch
is never silently treated as decoder failure or success.

## 5. Caps and calls

- C0/C1: at most 10 decoder calls and one verification check.
- C2: at most 20 decoder calls and two verification checks.
- All candidates: at most 32 events and 10 seconds.

The caller supplies the exact frozen cap object. Production code exposes no
test switch; tests inject the clock, preflight result, and decoder factory
through private function parameters only.

