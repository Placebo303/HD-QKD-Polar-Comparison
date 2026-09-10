# D7-B preregistration R1 (frozen BEFORE any new production-decoder observation)

- Branch `formal-ir-v72p1-addendum-clean`; baseline HEAD `f98dde08`
  (provenance only). Prior R1 STOP recorded as packet-specification feasibility
  defect (A1-01): frozen R1 TREE_6 `[2,3,2]` impossible; zero commits, zero file
  changes, zero decoder calls, zero roots, zero observations; consumes no D7-B
  authorization (A1-02).
- R1d `R1D_PAUSED_PENDING_DECODER_CERTIFICATION_AND_EASY_REGIME`; G2 absent;
  R1d root absent; D7-B root absent. All execution authorization keys false.
  D7-A dependency accepted: `D7_A_DECODER_CERTIFICATION_PASS` (report + review
  in `docs/research_cycles/V72P2D7-GF32-DECODER-CERTIFICATION/`).
- This prereg freezes science; implementation results and any
  historical-decoder calibration call occur only after its commit.

## 1. Superseded R1 tuple and 7<8 impossibility proof (retained, inactive)

R1 §3.3 item 2 specified TREE_6 n=6,m=3, row degrees `[2,3,2]`, connected
acyclic, no isolated variable. Tanner vertices V=n+m=9. Edges
E=2+3+2=7. A connected graph on 9 vertices needs ≥ 8 edges; a connected
acyclic graph (tree) needs exactly V-1=8. Since 7 < 8, no such graph exists.
The attempt correctly stopped before writes. This tuple is superseded and must
never dispatch; a spec-regression test rejects it (A1-06).

## 2. Accepted A1 replacement and 8-edge tree proof (active, literal)

TREE_6 active: n=6,m=3, row degrees `[3,3,2]` (A1-03), incidence c0=[0,1,2],
c1=[2,3,4], c2=[4,5], coeffs [1,7,13]/[29,1,7]/[13,29] (A1-04). Proofs
(independent, no production tables/decoder; rank via D7-A oracle arithmetic):

1. V=6+3=9. 2. E=3+3+2=8. 3. Row degrees in order [3,3,2] by literal incidence
   cardinalities. 4. Variable degrees: v0:{c0}=1, v1:{c0}=1, v2:{c0,c1}=2,
   v3:{c1}=1, v4:{c1,c2}=2, v5:{c2}=1 → [1,1,2,1,2,1]. 5. One component: c0–c1
   share v2, c1–c2 share v4, so BFS from c0 reaches c1,c2 and all vars. 6.
   Acyclic: E=8=V-1 plus explicit DFS from c0 visits 9 vertices with no
   back-edge (each new edge reaches an unvisited vertex; two articulation
   vars v2,v4, no alternative path). 7. No isolated check/variable: min row
   deg 2, min var deg 1. 8. Coeffs {1,7,13,29,1,7,13,29} all in 1..31 nonzero.
   9. GF32 rank 3: forward elimination with oracle mul/add/inv gives 3 pivots
   (rows pairwise independent via disjoint private vars v0/v3/v5). All nine
   pass (A1-05); any failure → STOP, no substitution. No dynamic
   topology/label/seed search introduced (A1-07).

## 3. Other tiers (frozen)

- SINGLE_CHECK_D3: n=3,m=1, H=[[1,7,13]]; rank 1; exact via 32^3 enumeration.
- CYCLE_8: n=8,m=8, H[r,r]=1, H[r,(r+1)%8]=7 (r<7), 13 (r=7); every check/var
  degree 2; connected 8-cycle; independent GF32 rank 8; syndrome unique.
- FULL_RANK_64: n=64,m=64, H[r,r]=1, H[r,(r+1)%64]=7 (r<63), 13 (r=63);
  degree 2 everywhere; connected cycle-like; rank 64; syndrome unique.
- Truths: `rng=np.random.default_rng(seed)` per fixture seed, uniform
  `0..31` length n. Syndromes: `H x_true` via D7-A oracle `syndrome_reference`.
  One deterministic rule + four seeds only; failure → STRUCTURE_FREEZE_BLOCKED.

## 4. Priors / caps / budgets / diagnostics / terminals

Per R1 §3.1/§3.2/§3.4/§3.5/§4 and design: q=32, damping 1.0, cold, caps
[1,2,4,8,16,32,90], 120 s/call, 1800+30 s outer, 1500 s run wall, 420-call
global stop, <2 GiB RSS, 1e-10 posterior tol, 1e-12 determinism, scalar-only
diagnostics with CAP_PREFIX_PROXY, terminal priority T1–T9. P60/PAIR never
veto. Exact tiers: SINGLE_CHECK_D3 (oracle exact_posterior) and TREE_6 (dual
tree-exact, never 32^6, never production/FFT).

## 5. Cell manifest template (64 rows; identities frozen, values at run time)

tier,prior,seed,n,m,rank,deg_min,deg_max,construction,x_true_digest(not
stored: seed+rule only),syndrome_digest(rule only). Schedule: 4 tiers × 4
priors × 4 seeds = 64 cells; per-cell cap ladder with early stop and global
420 accounting (scheduled/invoked/not-needed/budget-not-reached).

## 6. Allowed files / commands / lifecycle

New: `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_easy_regime.py`,
`comparison_bench/tests/test_v72p2d7_gf32_easy_regime.py`,
`scripts/v72p2d7_gf32_easy_regime.py`; docs here; this OpenSpec. v35/D5
read-only; D7-A oracle reused. Root `workspace/d7_b_easy_regime_<uuid>/`
five-file only. Future command frozen (not run):
`& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 1800 python
scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>`.
Authorization `d7b_execution_authorized:false`; single use consumes on first
historical-decoder attempt. Pre-RESULT review mandatory. No Model-F/CAL/VAL/
real/raw/formal/VOID reads; no --phase/R1d/G1/G2.
