# Design: formal-nonbinary-ldpc-v21-bob-only-selector-validation

## Status

CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE.

## Implemented strategies

- S0 BP-only: accept syndrome-consistent FFT-QSPA output, otherwise fail.
- S1 bounded4-only: run the bounded-weight decoder and accept its selected
  candidate.
- S2 BP-first-fallback-bounded4: accept syndrome-consistent BP output;
  otherwise use bounded4.

The intended runtime inputs were `(field, matrix, syndrome, w, max_iter)`.
Alice was used for offline `exact_correct`/FER metrics.

## Stop conclusion

The retained summary reports S0/S1/S2 FER 0.625/0.5625/0.5625 on 64 frames.
Because all are at least 0.45, the short-block branch concluded at its stop
gate. No further tuning, finite qualification, or promotion follows.

## Verification limitation

The design called for two complementary checks:

1. static AST rejection of decoder functions referencing Alice;
2. runtime injection proving that replacing Alice cannot change selected
   candidates.

Only the static AST form was included in tests. Runtime injection and the V01
independent semantic verifier were not run. Therefore “tests passed” must not
be rewritten as “Bob-only semantic verification passed.” P0/P1 were also not
pre-frozen; their task states are cancelled/unverified rather than completed.

## Closeout rule

Preserve the observed stop result and these limitations. Closeout review may
classify incomplete work but must not run missing science or retrofit
pre-registration. Archive only after user authorization.
