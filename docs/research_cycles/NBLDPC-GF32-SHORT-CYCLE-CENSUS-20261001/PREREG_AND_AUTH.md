# Decoder-free short-cycle inventory — EXPLORE

2026-10-01. State **CLOSED / MAIN ACCEPTED WITH COMMENTS**.
UUID `475c2ad3-bd5a-4000-8498-ea989bad1bba`.
Fresh root `workspace/gf32_cycle_census_475c2ad3/`.
User ongoing authorization verbatim:

> 可以尽可能往下推进，我目前的codex额度非常充足而且得尽快用掉，因此我批准你做一些未授权但合理的操作，尽可能往下持续推进本项目，本项目的目的与要求你也清楚，后续我一并检查就行了，我比较信赖你

Apply ../NBLDPC-CONTINUOUS-EXPLORE-20261001.md within bounded synthetic scope.
One frozen decoder-free batch; no extra user reply needed. Execution only
after independent implementation PASS/main dispatch AND main acceptance of
edge-label1efed423. No repair/rerun/resume/range change or automatic decoder.

## C1 Question, inputs and authority

Before designing a cancellation experiment, inventory whether natural
unit-product short simple cycles exist in the accepted matrices. Retain
fixed six3901..3906 D10 graphs n128/m52/E256/GF32poly37 from EDGE-LABEL
packet. Reconstruct its unchanged accepted deep control and accepted one-pass
edge-label candidate exactly per EDGE-LABEL F1 (all256 edges in one sweep,
not a new single-edge flip), with the same frozen PMF/helpers. No coefficient optimization
beyond that reconstruction, no new graph/source/prior/decoder. Both matrices
share support. Reproduce admission and compare reconstructed per-graph
J/change/gauge diagnostics with accepted edge artifacts; mismatch STOP.
No production decoder call, no sampled frames or truth/prior arrays and
no actual NPZ/raw/private/TTBin/parquet/real source reads.

Enumerate the shared support once per graph. Scope: every simple Tanner
cycle with variable length ell=2..6 (Tanner length4..12), including ell2
from two distinct variables connecting the same check pair. All variable
columns have degree2 globally, and all checks/variables within each cycle
are distinct except start closure. No composite walks or repeated vertices.
No data-driven extension beyond6 or graph subset selection.

## C2 Canonical enumeration and GF witnesses

Use deterministic DFS, start checks ascending, neighbor variables ascending;
each degree2 variable connects to its other check. A start check is the
smallest check in the cycle, repeated non-start checks/variables forbidden.
Canonical key is the lexicographically smaller of the two oriented alternating
vertex sequences rooted at that smallest check, using row IDs0..51 and
variable IDs52+v. Deduplicate by key; sorting keys gives reproducible output.
Count DFS states as each entry to a recursive path state, including starting
states; cap2,000,000 states and100,000 unique cycles per graph. Exceed either
means ENUMERATION_CAP_STOP, no larger cap or subsequent execution.

For a cycle r0,v0,r1,v1,...,r(ell-1),v(ell-1), use
P=product_i H[r_i,v_i]/H[r_(i+1 mod ell),v_i] in GF32.
Record both matrices' ordered edge coefficients, P and P==1. Only unit P
supports a nonzero codeword confined to this cycle: normalize first cycle
variable value1, solve successive degree2 check equations, and verify every
check including closure. Store the local normalized support values for
unit witnesses (algebraic codeword, not sampled truth). No binary Hamming
weight, global minimum-distance or FER inference. Nonunit does not rule
out joint-cycle/composite-support codewords.

Primary source: Poulliat/Fossorier/Declercq ISIT2006, §IV.A Eq2 printedp94,
§IV.B p95 on other stopping sets:
https://perso.etis-lab.fr/declercq/PDF/ConferencePapers/Poulliat_2006_ISIT.pdf
Direct degree2-cycle algebra underlies the witness, no uniform-label
probability assumption. Independent literature check already retrieved
author original; arXiv0906.2061 Theorem10's1/(q-1) requires iid uniform
nonzero labels and SHALL NOT be applied to optimized frozen labels.

## C3 Reporting and mechanical outcomes

After all6 complete, report per-graph/per-ell shared cycle counts, control
unit counts, edge unit counts, and changed unit/nonunit states, with exact
cycle witnesses. For each matrix separately: UNIT_PRESENT_IN_RANGE if any
unit cycle, otherwise NO_UNIT_CYCLE_IN_RANGE. These are availability
diagnostics only, not route/life-death gates. No pooled performance/ranking,
f-family numbers, claim of global distance or decoder benefit. An all-zero
inventory does not justify longer-cycle search under this packet.
Partial STOP retains inventory rows/attempts and completed-graph markers;
full-batch aggregate/comparisons remain unknown/null. No decoder automatically
follows this inventory; next bounded candidate needs a new frozen packet
under the ongoing grant and independent review/main dispatch.

## C4 Cost, artifacts and implementation

Singleprocess total1800s including reconstruction/enumeration,4GiB RSS,
six fixed graph inventories,0 decoder calls. Resource checks before/after
each graph and every1024 DFS states; STOP retains original error/partial
inventory, no subsequent graph. Root fresh only. Exactly manifest.json,
cycles.csv,summary.json,EXPLORATION_LOG.md; accepted-edge inputs readonly.
No overwrite/hash/integrity framework, no commit/push/merge/archive/real
data/n256/security/qualification/publication or route-closing DECIDE claims.
Retain all prior fenced-result restrictions and unrelated dirty files.

Allowed new code cli/nbldpc_gf32_cycle_census.py and
comparison_bench/tests/test_nbldpc_gf32_cycle_census.py only. Reuse pure
accepted graph/control/edge/field helpers, do not edit old modules/globals.
OpenSpec explore-gf32-short-cycle-census precedes implementation.
Exact command after independent PASS and main dispatch:
`wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env PYTHONPATH=comparison_bench/src .venv/bin/python -m comparison_bench.cli.nbldpc_gf32_cycle_census --execute --out-root workspace/gf32_cycle_census_475c2ad3`

## C5 Complete acceptance matrix

P1 fixed6graphs/profile/poly/accepted matrix reconstruction+identity,0decoder;
P2 tiny simplecycle enumeration ell2 parallel/triangle/ell6/ell7 excluded,
no repeated vertices,rotation/reversal dedup/determinism/full expectedcounts;
P3 GFunit/nonunit products,normalized unit witness check equations,known
cycle submatrix rank ell-1 vsell, row/column scaling invariance and oneedge
flip, composite support limits; P4 complete pergraph/perell inventory/state
changes,outcomes and partial/null totals; P5 state/cycle caps,totalwall/RSS,
exceptions/no nextgraph,absentroot refusal and no overwrite; P6 fake graph/
candidate fixtures/tiny tests,no actual D10graph or decoder from tests,
dryrun no reconstruction/enumeration/input/output; P7 independent plan/
implementation then raw inventory/count/GF witness/budget/grant review;
P8 main acceptance and append-only projectmemory/decisionlog triage.
WSL repo .venv,focused pytest -p no:cacheprovider -o addopts='',freshtestroot.
Workers notalone; preserve others, complete frozen matrix or exact blocker.
Independent reviewer != operator; main owns science and successor priority.

## Independent planning clarification

2026-10-01 faithful_scope identified the ambiguous phrase single-edge
candidate. Main corrected it before implementation: inventory the accepted
full one-pass edge-label candidate, never a newly invented one-edge flip.
All remaining C1–C5 clauses reviewed without issue; final PLAN release
awaits reviewer confirmation of this exact clarification. No scientific
reconstruction/enumeration has occurred.

Reviewer confirmed the corrected C1 and reported final C1–C5 PLAN PASS.
Main accepts and releases scoped implementation/fake tests. Scientific
inventory still waits for accepted edge predecessor and independent
implementation PASS/main dispatch. Ownership: shape_closeout owns both
new census CLI/test; faithful_scope is independent reviewer; main freezes
science/acceptance, operator returns facts without self-acceptance.

## Independent batch-end review and main closeout

`faithful_scope` independently reviewed P1–P7 and passed with comments; reviewer != operator. Main accepted the completed decoder-free inventory only within the frozen six-graph, ell=2..6 availability scope. Result: `RESULT.md`; machine artifacts: `workspace/gf32_cycle_census_475c2ad3/`.

All six graphs completed with no stop reason: 3,026 cycles, control unit-product count 105 and edge-candidate count 121. The per-ell counts and arm-state transitions are in `RESULT.md` and `summary.json`; normalized witnesses and ordered coefficients are in `cycles.csv`. Independent review matched 69,412 reconstructed coefficients through the accepted edge-coordinate lookup without rebuilding D10, and independently recomputed all 6,052 matrix-cycle GF(32) products/ranks; all unit witnesses satisfy the cycle checks.

The caps were 1,800 s wall, 4 GiB RSS, 2,000,000 DFS states and 100,000 cycles per graph. No STOP occurred; actual elapsed wall and peak RSS were not persisted (`NOT_RECORDED`) and are not imputed. Decoder calls and sampled frames were zero. Acceptance does not imply binary Hamming weight, global minimum distance, composite-support exclusion, FER, decoder benefit, route, qualification, or publication. No rerun, range extension, decoder, or extra graph is authorized by this frozen batch. The separate `W_cycle` source-aware overlap metric remains an unexecuted pointer; any successor requires its own packet and main dispatch under the bounded ongoing EXPLORE scope.

## Independent implementation review / main dispatch

faithful_scope P1–P7 PASS:8focusedfake tests in2.49s,only knowncache_dir
warning; deterministicDFS/canonicalization/caps/GFwitnesses/reference
reconstruction checks/partialunknowns conform. Dryrun0reconstruction,
enumeration,reference reads,decoder,writes; root absent. Edge1efed423 now
independently reviewed/mainaccepted and closed. Main verified formal-IR
branch/no tracked frozenbaseline differences/absent census root, accepts
scoped review and dispatches the exact frozen decoder-free command once
under ongoing authorization. Census evidence still pending batchreview/main
acceptance; no implicit decoder or range extension.
