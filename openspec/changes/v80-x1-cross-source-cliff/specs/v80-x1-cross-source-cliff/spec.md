## ADDED Requirements

### Requirement: Per-source standalone cliff measurement
Each X1 arm SHALL cold-decode 240 paired blocks (`2026095601+idx`, `o1_blk:{seed}`) with the standalone per-m construct of SINGLE instance 2026092001 on the arm's OWN source channel bundle (2M frozen `gamma_f03.npz`+pb; 1M/1.5M A1-derived), using the b2f soft-marginal prior and v28 decoder (max_iter 300/streak 3, exact_match); no `.ttbin` read occurs.

#### Scenario: Cross-source channel proposed
- **WHEN** a run binds a channel bundle whose source label differs from the arm source
- **THEN** it is refused as out of scope for this change.

### Requirement: Frozen per-source grids with own-basis gates
The arm SHALL use its source grid (1M {185,189,193,197,201}; 1.5M {191,195,199,203,207}; 2M {192,196,200,204,208}) and pass only with fails/240 ≤ 12 AND f_super ≤ 1.3 on its OWN corrected H AND N ≥ ceil(3·4.785675/(1.3−f_super)).

#### Scenario: Single-source f_eff quoted as certifiable
- **WHEN** an f_eff from one source (N ≤ 240, rule (c) failed) is presented as literature-comparable
- **THEN** it is refused per the no-certifiable-single-source rule.

### Requirement: No pooling, no generality-alone claim
X1 arms SHALL be reported as separate per-(source, m) FER numbers; any pooled cross-source FER and any cross-source generality claim resting on X1 alone are forbidden (generality needs P1 §9 rescue on 1M).

#### Scenario: Pooled FER proposed
- **WHEN** a combined FER across sources or m-points is proposed
- **THEN** it is refused per the no-pooling rule.

### Requirement: Gated execution with explicit grant
No X1 execution SHALL occur without materialized per-source bundles plus Pre-EXECUTE Q0–Q6 plus a fresh explicit user grant per arm; this change alone authorizes nothing and the single-window/no-resume budget (≤1800 s/arm, ≤27000 s total) holds.

#### Scenario: Execution requested citing freeze alone
- **WHEN** execution is requested citing this frozen change without bundles/grants/Pre-EXECUTE
- **THEN** it is refused pending all three.
