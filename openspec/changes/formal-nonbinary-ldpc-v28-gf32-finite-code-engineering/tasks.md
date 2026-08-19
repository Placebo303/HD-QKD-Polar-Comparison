# V28 Tasks — GF32×GF32 Deterministic Finite-Code Engineering

Ordered, each with an acceptance item id.

## T1 — Config + field binding
Build `v28_config.json` from the frozen V27 split (block_len=1024, three sources, m1/m2/R1/R2,
seeds, shifts, field spec, 64-bit tag derivation). Bind `GF2mField.create(32)`.
- **A-T1**: `v28_config.json` contains every parameter; `field_id` matches the pinned GF(32)
  spec; m1=6 shared, m2 ∈ {194,200,202} per source.

## T2 — Mother-matrix construction
Generalize the three-shift-cyclic GF(32) construction to `(m, n)`.
- **A-T2**: `H_mother_L1` is 6×1024, `H_mother_L2` is 202×1024; all entries ∈ GF(32);
  `gf_rank(H_mother_L1)==6` and `gf_rank(H_mother_L2)==202`; layer matrix = prefix
  `H_mother[:m_layer(source), :]` with correct dims for each source.

## T3 — Syndrome consistency
- **A-T3**: for a known `x`, `s = H · x` (GF(32) mult) reproduces and `H · x' = s` only when
  `x'=x` within the code (consistency gate); dimensions of `s` equal `m_i`.

## T4 — Two-layer sequential decoder binding
Wire `decode_nonbinary_fft_qspa` for L1 (from L1 posterior) then L2 (conditioned on decoded
x1). Bob-only, no Alice oracle.
- **A-T4**: decoder returns a decoded `x1` then `x2`; order is strictly L1→L2; no top-K truth
  selection; failure is surfaced, not replaced.

## T5 — Noiseless + controlled-error decode
- **A-T5**: on noiseless `x` (s = H·x) decode recovers `x` exactly (both layers, all sources);
  on injected bounded errors the decoder corrects up to the designed capability and reports
  otherwise (no silent mismatch).

## T6 — Source row-prefix accounting
- **A-T6**: each source uses its own public `m2` prefix of `H_mother_L2`; prefixes are
  documented and leak-accounted; structure identical across sources (only prefix length differs).

## T7 — Deterministic seed replay
- **A-T7**: re-running with the same `v28_config.json` reproduces identical `H_mother`,
  syndromes, and decode outcomes (byte-exact manifest hash).

## T8 — 64-bit tag + leakage
- **A-T8**: tag derived from decoded block; `total_leak_bits = m_total·5 + 64`; f < 1.3 for
  all three sources (shown in design §5).

## T9 — Read-only verifier + manifest
`verify_v28(root)` reconstructs matrices/checks from `v28_config.json` + persisted artifacts,
re-runs structural + decode checks, and writes `RUN_MANIFEST.json`.
- **A-T9**: `verify_v28` `ok=true`; recomputed terminal == `engineering_ready_for_retrospective_gate`.

## T10 — Docs + local commit (no push)
Update CURRENT_TASK / decision-log / PROJECT_MEMORY / HANDOFF; commit locally, no push.
- **A-T10**: docs reflect V28 engineering completion; commit present locally; no remote push.
