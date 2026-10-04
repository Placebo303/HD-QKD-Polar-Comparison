# Design: formal-nonbinary-ldpc-v19-channel-aware-de-gate

## Status
DRAFT — successor proposal after V18-B2 M2 QSC control.

## Channel model
- Real structured channel: q=1024 V17 per-bit-plane model + Gray average; folded to q=16 for DE.
- Equal-entropy QSC control (p=0.038) already separates search limitation from structure limitation.

## Candidate mechanisms
1. Per-symbol-class puncture: use the low-entropy clean mass of the folded channel to
   puncture variable classes; effective channel DE should be derived from the punctured ensemble.
2. LSB-public two-step: disclose noisy LSB planes; protect high planes with NB-LDPC;
   model the effective channel for DE.
3. Structured edge labels: replace single aggregate w with per-plane/per-class labels in the
   DE objective where feasible.

## Gate flow
- Build deterministic effective channel from each mechanism.
- Run V10 DE/rand/1/bin with same frozen constraints; rate ladder.
- If any mechanism reaches rate≥0.875 with entropy_converged=True and error_prob=0, record as DE PASS.
- Full-channel honest f calculated with two-part leakage decomposition.

## Reproducibility
- New seeds/evidence identities; no reuse of V18 run IDs.
- execute-once + strict replay; no-rerun/no-tuning.
