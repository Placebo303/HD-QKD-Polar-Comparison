# Design: formal-nonbinary-ldpc-v22-structured-construction

## Status
DRAFT.

## Gate-first plan
1. Choose a paper-faithful ensemble (MET/protograph or SC-LDPC) for q=1024.
2. Run structured-channel DE; require convergence at rate corresponding to f<=1.3.
3. Only if DE converges, construct finite codes n>=512/1024.
4. Evaluate Bob-only FER and f_total (including public/verification bits).

## Key references
- Müller et al. 2024: q-ary irregular DE + blind reconciliation, f~1.078-1.14.
- Pacher 2016: two-step LSB-public + NB-LDPC high bits (already bounded in N2b).
- Kasai / Martínez-Mateo & Elkouss: low-SNR multiplicative repetition / blind.
