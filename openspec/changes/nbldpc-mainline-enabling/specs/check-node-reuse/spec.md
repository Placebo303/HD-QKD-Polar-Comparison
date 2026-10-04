# Check-node reuse candidate

The candidate SHALL compute each check's coefficient permutation, exponentiation, normalization and Walsh transform once, preserving each target's ordered product, inverse transform, syndrome shift and normalization. Reference function remains callable. Default decoder behavior remains the reference until complete equivalence is accepted.

Focused mathematical tests SHALL compare arrays exactly, rather than by tolerance; invalid-input behavior stays explicit. No helper-only test SHALL be described as full-decoder equivalence, measured acceleration, FER or expected-f gain. Decoder performance work requires its own frozen effect/MDE and budget within this same route.
