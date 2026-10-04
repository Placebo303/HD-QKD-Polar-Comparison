# Proposal: Formal Nonbinary LDPC v3 Covered Layered Successor

## Why

The immutable `nbldpc_formal_v2` development package was strictly replayed
but was not ready for confirmation.  Its QC48 prefixes also have a structural
coverage defect: the 24/32/40-check prefixes leave 23/15/7 of 64 columns at
degree zero (only the 48-check prefix has minimum degree two).  This is a
plausible contributor to the observed `verify_failed` outcomes, but is not a
causal diagnosis or a performance claim.

This successor tests a scientifically different bounded route: a covered
quasi-cyclic, PEG-like mother codebook and full-message *layered* FFT-QSPA.
It uses wholly fresh development and confirmation frames.  The old data,
policies, outcomes and confirmation boundary remain immutable.

## Scope

- Add the independent identity `nbldpc_formal_v3` and a planning-only
  contract for q=1024, n=64 synthetic qualification.
- Freeze a deterministic 6-by-8, Z=8 QC/PEG-like codebook whose supported
  24/32/40/48 row prefixes cover all 64 columns and have minimum column
  degree at least two from the 24-row prefix onward.
- Freeze two full-message layered FFT-QSPA damping candidates, fresh PCG64
  roots, fresh CSPRNG Toeplitz records, development-only selection, strict
  replay and an immutable 31/32 confirmation gate.
- Record the rejected independent SHA-shift salt probe as planning validation;
  it creates no production or qualification artifact.

## Out of Scope

- Executing a plan, generating qualification frames, modifying existing
  formal packages, real sidecars/raw `.ttbin`, EMS/list decoding, extra
  dependencies, or N4 work.

## Affected Specs

- Add `formal-nonbinary-ldpc-v3`.
