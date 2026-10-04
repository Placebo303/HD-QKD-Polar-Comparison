# NB-LDPC next mechanism: fixed-graph GF(32) edge labels

Date: 2026-09-30. Draft UUID: `8d1102a8-4558-44e9-9613-ffb7acd637c1`.
Track: **DECIDE route proposal**. State: **DRAFT / NOT GRANTED / NO SCIENTIFIC EXECUTION**.

Successor note (2026-09-30): the user subsequently granted the fixed-graph
GF32-label mechanism and requested continuation. The concrete first batch is
the separate EXPLORE `PREREG_AND_AUTH.md` (UUID `a74e912c`), with its paired
`EXECUTION_PROMPT.md`. That packet tests synthetic L1 column-label alignment;
this broader draft and its read-only prompt remain proposal history, not a
full-pair or real-data execution contract.

This document continues the NB-LDPC mainline in parallel with NB-Polar. It
proposes a *new, single-factor* mechanism after the completed L1-degree2 n128
batch gave Δ=+1 and positive Δ_g on 2/6 graphs. That batch's COND-3 NOT MET,
n256 absence and claim ceiling remain unchanged. Its result root is
`workspace/nbldpc-l1d2-s2c-n128-b07b0f91/`. This proposal is neither a
retry of that batch nor permission to enter its n256 arm.

## 1. Why this mechanism is next

The D10 coefficient rule samples each GF(32) nonzero edge label independently
and uniformly from 1..31. D10/D12 PEG/BFS/ACE, D13 decoder adjustments and
the recent degree2 batch changed topology, degree or dynamics, not a frozen
label allocation on an identical L055 graph. A proposed label candidate would
keep **H1 adjacency, L055 degree counts, m1/m2, H2, prior, decoder, data,
syndrome length and total public bits** fixed. Each arm computes its own
syndrome *value* from its actual H1. Only the nonzero H1 edge
coefficients would differ. That separates it from further degree2 layout
micro-tuning.

The hypothesis is conditional: a nonuniform GF(32) additive-error law may
make check messages depend on the *relative* edge labels. At the same check
count, a label choice may change finite-length L1 decoding and downstream
U1+U2 pair recovery. There is no established gain, and preserving syndrome
row count alone does not prove the eventual full-frame budget or net yield.

Internal evidence pointers: `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/
READINESS_R1.md:111-114`, `comparison_bench/src/comparison_bench/formal_ir/
v72p2d10_mixed_degree_l1.py:589-599`, and
`docs/research_cycles/NBLDPC-L1D2-SYNTH-BATCH/RESULT.md:54`.

## 2. Cheapest falsification: paper T0 before any new decoder batch

For independent errors e_i in GF(32), nonzero labels h_i, and a check sum
S=Σ_i h_i e_i, write the exact check distribution

`P(S=s) = Σ_{e_1,...,e_d : Σ h_i e_i=s} Π_i P_i(e_i)`.

Two predeclared controls keep the argument honest:

1. **QSC negative control.** If every nonzero error has equal probability,
   multiplication by any nonzero h only permutes equal-probability outcomes.
   The check distribution is label invariant. A claimed advantage in this
   control would indicate a formula, labeling or comparison error.
2. **Explicit nonuniform positive example.** Let each error be 0 with
   probability 0.8 and one fixed nonzero `a` with probability 0.2. With two
   edges labeled `(1,1)`, `P(S=0)=0.68` and `P(S=a)=0.32`. With `(1,α)` for
   any GF(32) α≠0,1, the masses at `0,a,αa,(1+α)a` are
   `0.64,0.16,0.16,0.04`. Thus the local distribution can depend on relative
   labels. This is a constructed math example, **not** the measured L1 source
   law or evidence of decoder/FER improvement.

T0 asks whether the exact field arithmetic, the QSC invariance and one
nonuniform contrast hold on paper. A deterministic oracle would need a
separate frozen packet and authorization. If the paper identities fail,
STOP this hypothesis. If they do, the next question is whether a **publicly
usable, frozen L1 error law** exists. Passing T0 alone licenses no graph
construction, decoder run or scientific claim.

## 3. The missing source mapping is a real gate

The current CQ survey reports ten Gray-plane marginal errors, direction mass
and a single-plane aggregate; it does not provide the L1 GF(32) *additive*
error PMF needed to select labels. The older S01 aggregate is q=1024 and from
a different source setting. Neither may be silently projected to this L1 law.
Model-F synthetic blocks use the same calibrated law at each position; no
stable public position-reliability types have been established. Thus a
"source-informed protograph by position" is not adopted as the next route.

The mapping contract must specify the 1024-symbol Gray-to-(U1,U2) split,
the GF(32) basis/addition used by the code, Bob's available side information,
the source and CAL/held-out roles, plus uncertainty in rare differences. It
must decide whether labels are scored against Bob-marginal `P(E1)` or a
declared aggregation of Bob-conditional `P(E1|B)`; a frozen public code cannot
silently choose its edge labels from each test frame's private Bob values.
An accepted public aggregate may suffice for a read-only feasibility audit;
reading a new private/model/real array or fitting a new prior is **DECIDE** and
requires its own packet and authorization. Without the mapping, any label
experiment remains a synthetic mechanism probe and cannot be called
"source-informed for the measured HD-QKD channel".

Evidence pointers: `docs/research_cycles/CHAN-QUALITY-SURVEY/RESULT.md:46-64`,
`docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/FINDINGS.md:88-90`,
`comparison_bench/src/comparison_bench/formal_ir/
v72p2d5_gf32_rate_mother.py:873-905`.

## 4. Conditional synthetic experiment, in a separate future packet

If T0 supports label sensitivity, freeze **one** candidate label rule and
one uniform-label control on the **same admitted L055 adjacency**. Both arms
must use their own H1 to form their actual syndrome; all other inputs and
scientific parameters remain paired. Label assignment may be constructed
from a declared synthetic nonuniform law only; it cannot peek at test-frame
truth or tune on observed failures. Code rank and graph admission are checked
for both arms, with failed candidates retained rather than silently replaced.

Report U1 exact, U2 exact, pair exact, syndrome/verify_accept,
accepted_wrong/undetected, every attempted public bit, wall, RSS and
per-graph differences. The primary question is pair recovery at identical
row and message budgets. QSC is a negative control for the *single-check
distribution* only: changing cycle gains can still change finite-graph
decoding under QSC, so whole-graph FER neutrality is not a required gate. One graph
or a lower local check entropy is not a pass. Pre-register multiple graph and
data seeds, an informative control operating range, a machine gate, budgets,
one fresh UUID root, one append-only exploration log, and independent
batch-end review in a new **EXPLORE** packet if all five EXPLORE conditions
hold. If the input is a fitted private Model-F bundle or the result will
close a route, use **DECIDE** instead.

The completed degree2 n128 Δ=+1 result is background, not a reusable arm or
sample pool. No default n256 arm follows from a positive synthetic result.

## 5. Alternative with greater scope

A pair-state factor using `P(U1,U2|B)` could let the L2 constraints inform
L1. Its local joint alphabet has 32²=1024 states versus 32 per layer,
before accounting for factorization and check-node cost. Merely passing a
one-way L1 APP to L2 is already covered by D11; a genuinely bidirectional
scheme must state its new messages, extrinsic isolation and cost. It also
encounters the rejected D7-H reverse route and JOINT-PRICING-R2's terminal
**MARGINAL** design block: nominal 1100 against 1104 leaves 4 bit, while the
+20% case 1319 exceeds 1104 by 215 bit. These two figures must travel
together. That terminal is not repealed by this paper. A new pair-state
mechanism needs a separate user-level DECIDE proposal, packet and grant.

The fixed-label route is cheaper to falsify and does not change row count.
If its T0 or paired mechanism test fails, close that local hypothesis; do not
automatically dispatch a pair-state construction or switch to an easier
channel. Neither local failure settles the NB-LDPC family.

## 6. Boundaries and next decision

Stage-0's independent bit-plane KILL, N2048 B/C conclusions, P3/P4 and
Joint Pricing retain their exact scopes. HDC/LB void are never a baseline.
No mixed f families, merged cross-method ranking or single-point
`f_eff≤1.3` certification. The currently accepted evidence does not support
real full U1+U2 FER, throughput qualification, SKR or publication claims.

This draft authorizes paper analysis only. A new frozen packet+prompt must
name its one track, exact method/input/seed/budget/root/command/STOP, explicit
user grant and independent review before any scientific execution. The next
main-thread decision is whether the label mechanism merits that packet after
T0 and the source-mapping audit, or whether to reserve effort for a separately
priced pair-state proposal. No commit/push or change to old result roots is
part of this draft.
