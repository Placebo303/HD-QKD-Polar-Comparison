# D6 graph/mother Pre-EXECUTE review R1d (read-only, fresh pass)

Reviewer: fresh independent Pre-EXECUTE pass over landed commits `8e8e4ae`
(freeze) and `cddaaed9` (implementation+tests), after the R1d implementation
review (`D6_R1D_IMPLEMENTATION_REVIEW_PASS`). No files edited during review
(this file excepted at commit time). This review grants NO authorization:
R1d execution requires a separate explicit main-thread grant naming this
packet, branch, widths, arms, and budget.

## Checks (packet §7: all 8)

1. Branch / scoped diff / decision / candidate set: branch is
   `formal-ir-v72p1-addendum-clean`; commits `8e8e4ae` (9 freeze files) +
   `cddaaed9` (11 files: R1d layer, `--r1d` mode, tests, count corrections)
   stage exact paths only; Option C ruling recorded with A/B rejection
   reasons; candidate set exactly {B0_D5_DV3_NATIVE,
   B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3}. PASS.
2. Complete schedule vs validity matrix: 22 distinct structure cells
   (canary n64 f1.2+square ×3 arms; confirmation n64 f1.0/f1.2/square ×T1;
   scaling n128/n256 f1.2+square ×T1) tabulated in
   `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md` §4; reviewer re-derived the
   set from `ROW_BUDGETS` + role rules (22 == 22, set-equal) and confirmed
   0 matrix-invalid cells plus one live spot recompute (T1 n256-L2-square
   rmin 2). Guard + 13 tests pin the transcription. PASS.
3. Code/tests and A4/A6 performance path: mother diff append-only (builders
   untouched); default runner call shapes preserved (A4 callsite pin green);
   A4/A6 equivalence tests green inside the 356/356 suite run; R1d arms
   build in seconds at every width (A5 matrix `build_wall_s` ≤0.34 s) —
   no structure-cost breach, no Track B dependency. PASS.
4. Fresh R1d target absence + old-root no-reuse: `workspace/` contains no
   `d6_graph_mother_r1d_*` root (checked 2026-09-10); historical A2 root
   holds exactly the 6 frozen files and is git-clean; `R1D_REFUSED_ROOTS`
   + `--r1d` named refusal tested (`SystemExit(2)`); no A2/VOID/formal
   science-input path exists in R1d config. PASS.
5. Authorization keys + G2: all 12 authorization/promotion keys false in
   `cycle_state.yaml` (`development_decoder_authorized` false,
   `evidence_root`/`terminal` null); `g2_execution_authorized` false; no D6
   G2 root exists (the two `v72p2d5_p0g1g2_*` workspace names are
   pre-existing unrelated V72P2D5 dirs). PASS.
6. Exact future command / workers / budgets / watchdog / stop rules:
   `python scripts/v72p2d6_graph_mother_development.py --r1d
   --model-f-root <CAL-ONLY-Model-F> --out-root
   workspace/d6_graph_mother_r1d_<uuid>/ [--workers 18]`; requested 18 with
   RSS-gated 18→14→12→8; ≤2500 total calls (worst case 552 + setup); ≤12 h
   wall with `poll=min(120 s,remaining)`; 120 s/call watchdog; aggregate
   RSS <2 GiB strict; chunk ≥5400 s blocks dispatch; no retry; task-owned
   processes only. PASS.
7. Protected-root metadata + dirty-tree scope: 6 files present with frozen
   names; path git-clean; historical header still old-schema (test-pinned);
   unrelated V35/perf-v38/CRLF dirty state preserved (exact-path staging
   only); test basetemps task-owned (`workspace/d6_r1d_tests_*`, not an R1d
   output root). PASS.
8. Claim ceiling + Pre-RESULT: at most the T1-vs-controls comparison under
   the frozen contract with I1-gated dispatch; no SC/M/T2, recovery,
   performance-beyond-structure, or authorization claim; independent
   Pre-RESULT review remains mandatory before any solidification. PASS.

## Verdict

`D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` — the R1d
packet is complete, eligible-only, guarded, tested, and frozen. R1d is NOT
authorized and NOT executed by this review; no R1d root exists; historical
A2 roots unreused; G2 un-authorized and un-executed.
