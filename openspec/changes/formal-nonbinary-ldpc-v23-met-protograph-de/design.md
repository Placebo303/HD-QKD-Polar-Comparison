# Design: formal-nonbinary-ldpc-v23-met-protograph-de

## Status
DRAFT.

## Approach
1. Base matrix B (m_p x n_p), rate R=1-m_p/n_p.
2. Derive edge-perspective lambda/rho:
   - E = sum of B entries.
   - lambda_d = (d * count_var_degree_d)/E, rho_d = (d * count_check_degree_d)/E.
3. Run V22b structured MC-DE at q=1024 with raised degree cap.
4. Search small protographs; stop when DE converges at target f.

## First smoke
- B = ones(2,32): lambda={2:1}, rho={32:1}; non-converged.

## Next
- Scan (m_p,n_p) with column sums 2-3, check degrees < 512.
- Add MET (multiple edge types) if single-edge protographs fail.

## References
- Müller et al. 2024; Kasai / Martínez-Mateo & Elkouss.
