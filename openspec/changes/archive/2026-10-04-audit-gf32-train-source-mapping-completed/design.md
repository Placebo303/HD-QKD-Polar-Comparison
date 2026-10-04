# Design

One CLI inspects zip/NPY headers before materializing admitted train counts.
It validates the named run provenance, finite nonnegative integer-valued
float64 counts and axis
roles, accumulates E1=(A>>5) XOR (B>>5) counts against complete B, and emits
only per-source 32-bin marginal data and specified scalar diagnostics.
Conditional arrays stay in memory. Fake NPZ/count tests use fresh test roots.
The exact scientific contract is the linked packet; operator cannot amend it.
