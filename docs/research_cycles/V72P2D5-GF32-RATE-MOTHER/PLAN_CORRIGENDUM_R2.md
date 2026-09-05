# V72P2D5-GF32-RATE-MOTHER Plan Corrigendum R2 (plan-only, no code, no execution)

- cycle_id: V72P2D5-GF32-RATE-MOTHER
- document: PLAN_CORRIGENDUM_R2
- status: PLAN_REVISE_REQUIRED
- cause: DEGREE2_PREFIX_CONNECTIVITY_IMPOSSIBLE
- implementation_candidate_status: UNCOMMITTED_NOT_ACCEPTED
- decoder_executed: false
- full_mother_built: false
- date_utc: 2026-09-05
- lifecycle: PLAN-ONLY. No production code written or modified this turn. No test run, no full-mother construction, no decoder run, no CAL/VAL read, no output creation. No implementation / structure / G0 / G1 / G2 authorization granted (all remain false).
- history_note: PLAN_REVIEW_VERDICT.md (R1 PLAN_ACCEPTED) and IMPLEMENTATION_PACKET.md / IMPLEMENTATION_REVIEW.md are retained byte-identical as history. They are declared SUPERSEDED for the mother-construction path only. This corrigendum does not modify them.

## 1. Decision

- DECISION: PLAN_REVISE_REQUIRED.
- CAUSE: DEGREE2_PREFIX_CONNECTIVITY_IMPOSSIBLE.
- IMPLEMENTATION_CANDIDATE_STATUS: UNCOMMITTED_NOT_ACCEPTED (current 3 untracked .py candidates are partial-candidate only; T0/T1 code uncommitted, unaccepted; no structural conclusion may be drawn from them).
- DECODER_EXECUTED: false. FULL_MOTHER_BUILT: false.
- NEXT_GATE: INDEPENDENT_R2_PLAN_REVIEW. No R2 implementation packet freeze by this turn.

## 2. Strict impossibility proof (degree-2 prefix, any ordering)

Prior math verification (read-only, no construction, no decoder): E=2048 full-graph feasible; all 8 prefixes with k<975 unsatisfiable under degree-2.

- Full mother accounting (corrected): N=1024 variables, M=1000 checks, column-degree 2 gives total edges E=2N=2048 (corrects earlier 2000 figure; 2000->2048). Bipartite nodes V=N+M=2024; single-component connectivity needs at least V-1=2023 edges. Full graph 2048>=2023, so full-mother connectivity is feasible. This corrects the edge count only; it does not rescue any prefix.
- Prefix necessary edge bound (any row ordering, any check selection of size k): each variable contributes at most 2 edges, but every edge touching one of the M-k excluded checks is lost from the prefix. Worst case for the prefix (best case for connectivity) loses at least 2 edges per excluded check only in the loosest counting sense used here as E_prefix<=2N-2(M-k). Any tighter accounting only lowers E_prefix further, so irreparability under this bound implies irreparability under exact accounting.
- L2 smallest prefix k=686: E_prefix<=2048-2(1000-686)=2048-628=1420. Prefix nodes V_prefix=N+k=1024+686=1710; single component needs V_prefix-1=1709. 1420<1709. Deficit 289 edges. No row choice and no row ordering can create missing edges.
- L1 smallest prefix k=782: E_prefix<=2048-2(1000-782)=2048-436=1612. Prefix nodes V_prefix=1024+782=1806; need 1805. 1612<1805. Deficit 193 edges. Same irreparability.
- Larger frozen k values reduce (M-k) and raise the bound, but the verified result is that all 8 frozen prefixes with k<975 remain unsatisfiable under degree-2 single-component connectivity; the two smallest-prefix inequalities above are the exhibited witnesses. Any ordering is irreparable because ordering moves rows, it does not create edges.
- Scope of this proof (explicit): this is NOT a V31 implementation bug verdict; it is NOT a decoder result; it does NOT close the GF32 route. It proves only that column-degree-2 + 1000-nonzero-per-layer + every-frozen-prefix-single-component are jointly unsatisfiable. The natural-prefix route and the row-ordering repair route are therefore both CLOSED for a degree-2 nested mother.

## 3. G1 status (V31 QC)

- V31 QC column-degree-2 status: EXIT_PREFIX_CONNECTIVITY_IMPOSSIBLE.
- Retained: V31 field definition (GF(32)), rank audit method, decoder interface reuse. These are unaffected by the connectivity exit.
- Excluded: degree-2 support construction as the D5 nested mother. No V31 history file is edited by this turn. This is not a GF32-route failure.

Deleted / replaced stale live semantics (no remaining live assertion in the 5 R2 plan files):

- V31-is-selected-mother (as D5 nested mother).
- natural-prefix-or-reorder-fix (natural order qualified, or one reordering repairs degree-2).
- degree2-fits-700-1000-rows (column-degree 2 suffices for the frozen prefix sets).
- row-ordering-as-repair (post-construction reorder as a live repair path).

## 4. G2 freeze: single new mother G2_MINIMAL_NESTED_DV3_GF32

- Freeze exactly one new mother family: G2_MINIMAL_NESTED_DV3_GF32. No parallel families.
- Parameters (frozen): N=1024 symbols per block, M_max=1000 checks per layer, column_degree=3 for every variable, GF(32) nonzero coefficients (values 1..31).
- Per-layer independent mothers (L1 for U1 alphabet, L2 for U2 alphabet); L1 k_min=782, L2 k_min=686.
- Justification is necessary-edge arithmetic ONLY (no structural PASS pre-claim):
  - Total edges E=3N=3072.
  - L2 k=686: E_prefix<=3072-2(1000-686)=3072-628=2444 vs need 1709. 2444>=1709: necessary condition satisfiable.
  - L1 k=782: E_prefix<=3072-2(1000-782)=3072-436=2636 vs need 1805. 2636>=1805: necessary condition satisfiable.
  - Recorded wording is ONLY "necessary-condition satisfiable". NEVER pre-claim structural PASS (rank / connectivity / 4-cycle outcomes remain to be constructed and audited; any frozen prefix rank shortfall is G2_PREFIX_RANK_BLOCKED).

## 5. G2 support construction (frozen contract, plan-only)

- Per-layer single 1000x1024 mother; L1 k_min=782, L2 k_min=686.
- Per-variable exactly 3 edges:
  - base edge 1 in [0,k_min), base edge 2 in [0,k_min) different check from edge 1 (2 base edges => every variable has degree >=2 inside the earliest frozen prefix);
  - expansion edge 3 in [k_min,1000), with necessary spill of some expansion edges into base rows for row-balance, but every suffix row [k_min,1000) is incident to at least one edge (all suffix checks nonzero).
- Requirements (all frozen):
  - 2 base edges per variable (earliest-prefix per-variable degree >=2).
  - expansion covers all suffix checks (zero suffix rows forbidden).
  - per-row degree >=2 (every check row, base and suffix).
  - no duplicate (check,variable) edge.
  - no two variables share the same unordered check-support triple.
  - fully deterministic construction; L1 seed 2026090501, L2 seed 2026090502; no seed search; any construction failure => BLOCKED (return to planner).
- Minimal deterministic greedy (frozen, no PEG library, no generic framework):
  - iterate variables 0..1023 in order;
  - edge 1: minimum-current-degree base check, minimum index tie-break;
  - edge 2: different base check from edge 1, subject to (1) no repeat of an existing base pair, (2) prefer a check in a different connected component, (3) minimum current degree, (4) minimum index;
  - edge 3: cover uncovered suffix rows first (minimum index among uncovered), else minimum-current-degree check (suffix preferred while suffix rows need coverage, spill to base only for balance), minimum index tie-break;
  - final repair for any row with degree <2: deterministic edge swap that preserves column-degree 3 and introduces no duplicate edge and no duplicate triple; if repair is impossible => BLOCKED.
  - No decoder view, no syndrome view, no Alice/Bob view, no exact-recovery view during construction.

## 6. GF32 coefficient contract (support / coefficient split)

- Support and coefficients are decided in split stages: support first per section 5, coefficients after.
- Per-nonzero coefficient takes values 1..31 via a frozen-seed deterministic PRNG exactly once. Zero coefficient forbidden.
- No reseed on rank failure. No decoder-guided search. No support chasing rank (no re-drawing support to fix a rank shortfall).
- Any frozen prefix rank shortfall under frozen coefficients => G2_PREFIX_RANK_BLOCKED: stop, return to planner, no automatic resampling ("no auto-re-draw").

## 7. Prefix gates (kept sets, strengthened)

- Frozen disclosure sets kept: L1 {782,821,860,938}, L2 {686,720,755,823}.
- Every frozen prefix reports: rank==k, zero_rows 0, zero_columns 0, isolated 0, components 1, largest 1.0, dup_proj 0, coeff_nonzero, variable-degree min/median/max, degree-1/2/3 counts, row-degree histogram, 4-cycle count (variable pairs sharing a check pair).
- NEW hard gate: variable_degree_min>=2 inside every frozen prefix (follows from 2 base edges), non-decreasing as k grows (prefix rows only add edges, never remove).
- Minimum PASS set = prior items plus the new variable_degree_min>=2 gate. Full enumeration lives in the R2 spec delta.

## 8. 4-cycle contract

- Count definition frozen: number of variable pairs sharing at least one check pair, i.e. sum over check pairs of C(shared_vars,2) aggregated to variable-pair incidence (mechanical count on the full prefix support).
- Base construction bans repeat base pairs => base-only 4-cycle target is 0 by construction.
- Expansion edges may create shared pairs; the full prefix count is mechanically counted and reported.
- No absolute PASS threshold is invented in this plan. The report SHALL include total count, per-variable incidence distribution, and maximum incidence.
- Outcome rule: rank + coverage + connectivity PASS but nonzero cycles => STRUCTURE_PASS_WITH_CYCLE_RISK (proceed with recorded risk; G1/G2 decoder trends judge; never retune the graph from decoder results).

## 9. Row-ordering path deleted

- Natural order = construction order (base checks first in construction index order, suffix expansion checks after). Disclosure H[:k] uses this order directly.
- No order_rows_for_prefix_coverage function. No post-construction row reorder. No decoder-driven reorder.
- Note: the future R2 implementation delta deletes the row-ordering implementation from code, but this plan-only turn does NOT touch any .py file.

## 10. Future R2 implementation delta (tasks.md records; not executed here)

- Drop the degree-2 V31 adapter as a production candidate path.
- Drop the row-ordering implementation path.
- Add the minimal dv3 support builder per sections 5-6 (no PEG library, no generic framework).
- Retain prior-math adapter, matched generator, prefix audit, and phase isolation contracts unchanged.
- Current uncommitted 3 .py files are partial-candidate only. No code change occurs until a new R2 implementation packet is frozen and accepted.

## 11. G0 / G1 / G2 gates kept

- OQ1: M_max=1000 is a D5 synthetic construction cap only (not production sufficiency).
- OQ2: 90% line is a qualification grading line, not a route-death line.
- Oracle remains diagnostic-only.
- P0 preflight kept. G1 100 APP blocks kept. G2 200 APP blocks kept. Staged authorization kept (no single authorization across G0/G1/G2; no automatic advance to n=1024 real).
- The 5 R2 plan files were swept for live stale assertions (V31-selected-mother as live mother, degree-2-fits as live target, row-ordering-as-repair as live path, GF32-route-dead as live verdict). No live assertion of any of these remains. Historical deletion notes and this corrigendum's impossibility record are the only remaining mentions.

## 12. File discipline (this turn)

- Allowed (exactly 7 docs): 5 R2 OpenSpec plan files revised in place (proposal.md, design.md, tasks.md, specs/spec.md, PLAN_FREEZE.md) + NEW PLAN_CORRIGENDUM_R2.md (this file) + MODIFIED cycle_state.yaml.
- Forbidden (untouched): the 3 .py candidates, IMPLEMENTATION_REVIEW.md, old PLAN_REVIEW_VERDICT.md, old IMPLEMENTATION_PACKET.md, AGENT_PROJECT_MEMORY.md, docs/decision-log.md, all other code and outputs, unrelated dirty worktree files.
- No hash / checksum / tag fields added.

## 13. Handoff

- Independent R2 plan review (18 checks) plus commit/push are left to the reviewer / main thread. This turn does not commit or push.
- Allowed verification only: read-only inspection plus git diff --check / git status / diff --stat and stale-semantics grep (no tests, no builds, no decoders). Execution tooling for git is unavailable in this planner turn; the reviewer / main thread runs those commands.
