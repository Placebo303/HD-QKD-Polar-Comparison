# Route C1 Design Draft — Layered / MLC Small-Field Complexity Reduction

Status: DRAFT — planner-level design only; execution gated on user decision

## Goal
Reduce q=1024 FFT-QSPA complexity by decomposing the Gray-mapped 10-bit symbol into
per-bit-plane or small-field layers, reusing the structured-channel observation from
Route B M2.

## Background
- The V17 per-bit-plane error probabilities are strongly MSB→LSB monotone:
  ~3e-5 (MSB) to ~3.75e-2 (LSB).
- A q=1024 NB-LDPC FFT-QSPA check update costs O(dc q log q) per row and dense
  q-length messages are heavy.
- A layered scheme may protect only high-risk planes with a small-field NB-LDPC,
  while low-risk planes need less or no syndrome.

## Candidate designs
1. **Bit-plane binary LDPC layers**:
   - Map Gray symbol bits to 10 binary layers.
   - Use existing binary LDPC methods on selected error-prone planes.
   - Cost: O(n * binary check degree) per layer, much lower than q=1024 FFT-QSPA.
2. **GF(16) folded layer**:
   - Split 10 bits into e.g. 2×5-bit or use GF(16) on groups.
   - Reuses the q=16 folded DE results from V18-B2.
   - Need careful Gray decomposition / syndrome consistency.
3. **Pacher-style hybrid**:
   - Publicly disclose LSBs (high-error planes), run NB-LDPC only on MSB symbols.
   - This is both a rate-adaptation and complexity reduction mechanism.

## Next automatic steps (after user approval)
- Write a small numerical scoping script using V17 per-plane probabilities to estimate
  syndrome and f for each candidate layer split.
- Compare operation counts vs q=1024 FFT-QSPA.
- Do not run a production qualification until a route is selected.

## Dependencies
- Route B channel-aware DE gate should produce the effective per-layer channel models.
- Existing binary LDPC v5 real qualification is the binary-layer reference.
