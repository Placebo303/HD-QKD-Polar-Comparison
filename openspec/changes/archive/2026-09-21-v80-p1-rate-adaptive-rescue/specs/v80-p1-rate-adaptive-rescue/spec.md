## ADDED Requirements

### Requirement: Nested single-segment rescue procedure
Each P1 arm SHALL decode 240 paired blocks cold at m_base = 200 (leading-200 submatrix of the frozen same-instance A208 matrix) and COLD re-decode exactly the Stage-1 non-success blocks with the full 208-row matrix after disclosing rows [200,208); warm-start and non-nested fallback are forbidden.

#### Scenario: Rescue of a Stage-1 failure
- **WHEN** a block fails Stage 1 (exact_match false)
- **THEN** it is re-decoded cold with rows [0,208) and counted in trigger rate r, with E[leak] = 1064 + 40·r.

#### Scenario: Warm-start proposed
- **WHEN** a warm-started rescue is proposed
- **THEN** it is refused as out of scope for this change.

### Requirement: Zero-failure hard gate with headroom
The arm SHALL pass only with final fails/240 = 0 AND f ≤ 1.3 on its own basis AND headroom 1108.31 − E[leak] ≥ 21.5 b.

#### Scenario: One final failure
- **WHEN** an arm reports final fails/240 = 1
- **THEN** the arm FAILs (Clopper–Pearson upper ≈ 1.94% exceeds the allowance; no f_eff certification).

### Requirement: Per-instance reporting without pooling
P1-R1 (2026092001) and P1-R2 (2026092011) SHALL be reported as separate FER numbers; any pooled cross-instance FER is forbidden.

#### Scenario: Cross-instance sum proposed
- **WHEN** a combined FER (e.g. 6+4-style summation) is proposed
- **THEN** it is refused per the no-pooling rule.

### Requirement: Gated execution with explicit grant
No P1 execution SHALL occur without Pre-EXECUTE Q0–Q6 plus a fresh explicit user grant per arm; this change alone authorizes nothing and the single-window/no-resume budget holds.

#### Scenario: Execution requested citing freeze alone
- **WHEN** execution is requested citing this frozen change without a fresh grant
- **THEN** it is refused pending the grant and Pre-EXECUTE.
