## ADDED Requirements

### Requirement: Prior-cost disclosure in every leakage/key accounting
Any reported leakage (`λ_total`, `leak_EC`) or key (`net`, SKR numerator) accounting SHALL
state whether the prior/calibration cost is included, and if excluded, SHALL say so explicitly
with the exclusion basis (sacrifice-the-sample DEFAULT vs disclose-the-statistic conditional).
A bare `λ_total = leak_EC + 64` with no prior-cost sentence is refused as incomplete accounting
(gap authority: `docs/V80_BASELINE_20260921.md` §2; `docs/SECURITY_MODEL.md` prior-term absence;
[DEC]§B).

#### Scenario: Leakage reported without a prior-cost sentence
- **WHEN** a result reports `λ_total`, `leak_EC`, `net`, or any SKR figure without stating
  whether the prior cost is included or excluded (and under which route)
- **THEN** it is refused pending an explicit included/excluded statement with the route named.

#### Scenario: Withdrawn ratio cited as a cost justification
- **WHEN** the withdrawn 0.12–0.26× sensitivity figure (or the withdrawn 1.8× / 51–256× figures)
  is cited as a planning number or cost justification
- **THEN** it is refused: the 0.12–0.26× figure is history-only (denominator mixed the sacrificed
  TRAIN pool; incompatible with the cross-source reuse ban), and only the one-time factory-calibration
  fact plus the binding 1.50× per-source forgone/key figure may ground planning.

### Requirement: Sacrifice-the-sample exclusion with forgone-key reporting
When the sacrifice-the-sample route is used (THE DEFAULT), the calibration/prior (TRAIN 60 %)
sample SHALL be excluded from key generation, and the forgone key (1.50× the key it enables per
source at constant 4016 b/superframe net; frames 1200/800, 1660/1107, 2187/1458) SHALL be reported
in the SKR numerator. The forgone key SHALL NOT enter `λ_total`.

#### Scenario: Calibration sample counted as key-eligible
- **WHEN** key material is computed over the TRAIN reserve or over uncorrected counts
  500/691/911 without excluding the calibration sample
- **THEN** it is refused: key-eligible counts are 200/276/364 and the TRAIN 60 % is excluded.

#### Scenario: Forgone key charged into lambda
- **WHEN** the sacrifice cost is added to `λ_total` or subtracted from `content`
- **THEN** it is refused: sacrifice cost lives in the SKR numerator only (f untouched).

### Requirement: Key-eligible counts with corrected-count certifiability
Key-eligible block counts SHALL be 200/276/364 (pool 840), never 500/691/911 (pool 2102/2103,
zero prior reserve — SUPERSEDED for planning, history only; [DEC]§C; baseline §§2/5-iii).
Any certifiability statement (`N ≥ ceil(3·4.785675/(1.3−f_super))`, gate (c), "certifiable" or
"literature-comparable" presentation) SHALL use the corrected counts on each arm's OWN H_MM
basis. Pending `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` (ABSENT at drafting), the governing
values are baseline-§3 full-precision results — at own m_max 1M@201 N = 15487 ≫ 200,
1.5M@207 N = 2700 ≫ 276, 2M@208 N = 1754 ≫ 364; at m = 200: 2051/309/262; at m = 199:
1098/274/236 — each cited as **pending recompute**.

#### Scenario: Certifiability asserted on uncorrected counts
- **WHEN** a certifiability or N-rule conclusion uses 500/691/911 (or pool 2103) as available N
- **THEN** it is refused pending re-evaluation against 200/276/364 (pool 840).

#### Scenario: N_req cited without the pending-recompute flag
- **WHEN** any of 15487/2700/1754 (or 2051/309/262, 1098/274/236) is cited before the authorized
  read-only recompute (PC-T5) confirms it
- **THEN** it is refused unless marked `pending recompute` with the baseline-§3 source named.

### Requirement: Disclosure-cost charging model with amortization basis
Any prior-disclosure cost (including the 36 b figure) SHALL state its charging model (per-block
vs once-per-batch) and its amortization basis (batch size, same-source scope). The m ≤ 201
consequence (⌊(1108.3075−64−36)/5⌋ at A208 economics; 36 b = 8.36× the 4.3075 b headroom)
MAY ONLY be asserted under an explicitly per-block model. Under amortization the per-block cost
is 36/200 ≈ 0.18 b (1M) or 36/364 ≈ 0.099 b (2M) and m ≤ 201 does NOT follow. 36 b SHALL NOT
be presented as a proven security-leakage quantity (real C03 is a 1024-bin histogram, ≤1023 dof;
no two-parameter encoding, precision, or public-message protocol exists).

#### Scenario: m-le-201 asserted without a charging model
- **WHEN** m ≤ 201 (or any operating-point relocation) is asserted from the 36 b cost without
  naming per-block vs amortized charging and the batch basis
- **THEN** it is refused pending the explicit model; the amortized reading (0.18 b / 0.099 b)
  stands as the counter-conditional.

#### Scenario: 36 bits presented as proven leakage
- **WHEN** 36 b is quoted as the security-leakage quantity of the prior without a defined
  transcription (encoding, precision, public-message protocol)
- **THEN** it is refused pending the PC-T4 definition.

### Requirement: f_super/f_eff invariance under the prior cost
`f_super`/`f_eff` SHALL remain unaffected by the prior cost: numerator = syndrome + tag only
(`f_super = (5m+64)/content`; `f_eff = f_super + 4.785675·FER` own-basis), and this SHALL be
stated wherever f is reported alongside any prior-cost discussion. No prior term SHALL be added
to the f numerator under either disclosure route.

#### Scenario: Prior term folded into f
- **WHEN** an f_super or f_eff value includes a prior/disclosure adder in its numerator
- **THEN** it is refused: recompute with syndrome + tag only and report the prior cost
  exclusively via the §-route rule (numerator forgone key, or conditional λ accounting).

### Requirement: Estimator estimand with auditable correction
Entropy estimators used for design-point decisions SHALL state their estimand (joint vs
conditional) and the correction applied, with the required counts persisted so the correction
is auditable. Concretely: the A1 `h_full_f03` plug-in is CONDITIONAL `Ĥ(A|B)` but its persisted
Miller–Madow term is the JOINT correction `(K_AB−1)/(2N·ln2)` — over-correcting by
`(K_B−1)/(2N·ln2)` in the optimistic direction (H up ⇒ f down ⇒ m_max up); `K_B` was NOT
persisted. Any future census run SHALL persist minimum `K_B_train` (recommended +`p_b` vector;
ideal sparse `N_ab`) without changing the frozen estimator. Until a re-run lands, per-source
design points are UNVERIFIED for MM-estimand purposes (P-V1), even though no IN↔OUT verdict
flips in range (max plausible over 0.002339/0.001672/0.001252 b, all sub-CI; authority
`docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` §§T1–T2).

#### Scenario: Design point used without an estimand statement
- **WHEN** an `H_full` (plug-in, MM-corrected, or threshold comparison) is used for an
  m_max / in-box / certifiability decision without naming the joint-vs-conditional estimand,
  the correction formula, and the persisted counts that audit it
- **THEN** it is refused pending the full statement; A1-derived points carry the
  UNVERIFIED-for-MM-estimand flag until the `K_B`-persisting re-run.

#### Scenario: Future census run omits K_B
- **WHEN** a new census run persists `H_full`/`MM_correction` without `K_B_train`
- **THEN** it is refused as unauditable under this contract.

### Requirement: Claim ceiling on this accounting basis
NO composable-security, SKR, operating-point, route, qualification, or publication claim SHALL
be made on this accounting basis alone. In particular: sacrifice-the-sample is a DEFAULT
accounting route, NOT a completed Serfling/random-sampling proof under the repo's
continuous-time 60/20/20 split; `docs/SECURITY_MODEL.md` itself excludes composable finite-size
security; parameterization (§5-iv) stays OPEN (decoder-equivalence UNMEASURED).

#### Scenario: Composable-security or SKR claim on accounting alone
- **WHEN** a composable-security result, SKR number, qualification, or publication claim is
  asserted citing only this accounting contract (without the required finite-size proof,
  grants, and independent reviews)
- **THEN** it is refused per the claim ceiling ([REV]§5.2; [P3]§12).
