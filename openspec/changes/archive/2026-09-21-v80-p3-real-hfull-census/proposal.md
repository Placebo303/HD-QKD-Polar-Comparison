# V80-P3 Real-Data H_full Census — Proposal

- Charter: `docs/ROADMAP-20260921.md` §3 **P3** (real-frame memory/consistency audit, the S3/P5 pre-gate) + §2 DECISION-1 (certifiability arithmetic) + §5 wording rule 3 (the differentiation claim explicitly rests on "explicit memory checks") + §8 review table.
- Packet: `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md` (Acceptance ID **G-P3**, frozen NOT granted) + `P3_CENSUS_PREREG_AND_AUTH.md` (signature required) + `P3_CENSUS_PROMPT.md`.
- Track: **DECIDE** — real/raw acquisition data, and the outputs feed a design-point/route decision and eventual publication numbers. Per the `AGENTS.md` §1.2 applicability matrix this cannot be EXPLORE. This change itself authorizes no execution and consumes no budget; execution needs the signed preregistration + Pre-EXECUTE + a fresh explicit user grant naming the alignment branch, then independent Pre-RESULT and main-thread acceptance.
- Data authority: `docs/DATA_INVENTORY_20260921.md` (10 datasets, 4 families A–D; derived artifacts excluded as untrusted).

## Why (what changed)

- The V80 program's binding constraint is budget certifiability: at n=1024/A208 a zero-failure arm needs `N ≥ 2842` blocks while per-source superframe counts are only 500/691/911 (pool 2103), so `f_eff ≤ 1.3` is not certifiable on Jan-21 at that basis (roadmap §1.2 item 1). Finding a dataset with a genuinely lower `H_full` (with a correspondingly lower required `m`) is the scientific prize of a census.
- All V80 synthetic frames are driven by a **memoryless** symbol-level model (`gamma_f03`) built from the 2M measured joint histogram. Whether real frames carry drift/memory has never been tested; if they do, every existing synthetic FER result is systematically optimistic for real data (roadmap §1.2 item 5, risk R2). P3 is the cheapest possible falsification and is a hard pre-gate for P5/S3.
- Two scientific hazards must be handled in the design, not patched later: (i) plug-in entropy bias is LOW and worst exactly where a low `H_full` looks attractive (sparse histograms); (ii) `.ttbin` → ToA symbols needs per-dataset free parameters the repo's loader cannot recover, so the alignment question must be an explicit, user-authorized branch choice rather than a silent default.
- **Amendment 2026-09-21 (nothing executed/signed; authorities `docs/TTBIN_MEMBER_SEMANTICS_20260921.md`, `docs/TTBIN_ENV_SETUP_20260921.md`): HARD PROHIBITION — never open both members of a `.ttbin` pair and concatenate (members are NESTED/SUPERSET via vendor auto-follow, NOT disjoint; both-member UNION double-counts every event and corrupts `pairs`/`counts_ab`/`H_full`); legal pattern is open `X.ttbin` only with auto-follow, or `.1` shard-only fallback, guarded by a span-continuity assertion (span > 0 and consistent with `.1`−base mtime gap). Measured-duration rule replaces filename tags (`duration_measured_s` / `filename_duration_tag` / `tag_disputed`; Jan-12 quarantined as 30.0 s, tag disputed). Stage 0 env PASS (`.venv` `Swabian-TimeTagger==2.22.6`, alias shim `comparison_bench/src/comparison_bench/io/ttbin_compat.py::install_timetagger_alias()` required before import, `src/` frozen). `FileReader.getConfiguration()` exists (accessor proven, payload relevance to PM/EB unproven — `[TO BE DETERMINED BY STAGE 0.5]`); the separately-signable Stage 0.5 probe (`P3_STAGE05_PACKET.md`) must pass before any Stage 1 census read.

## Scope (frozen)

- One bounded, zero-decode, read-only census over the offered datasets, producing per-dataset `H_full` under ONE frozen estimator (`H_L1 + H_L2`, F03, plug-in on the TRAIN pool) plus support/occupancy, Miller–Madow correction, held-out gap, bootstrap CI, per-frame error-weight distribution, block-to-block drift, lag-1/2 autocorrelation, and a V49 60/20/20 consecutive-time split declared before any statistic.
- Alignment gating decision tree with four branches (A1 configured-only control / A2 + Family A under its own convention / B empirical alignment estimation with a pre-registered acceptance rule and an explicit identifiability limit / C exclude unconfigured). **The user selects the branch; the packet does not.**
- Conditional certification arithmetic only: `content = 1024·H_full`, `f_super(m) = (5m+64)/content`, `headroom = 1.3·content − (5m+64)`, `N ≥ ⌈3·4.785675/(1.3 − f_super)⌉`. No operating point is selected.
- Budgets: ≤1800 s/dataset single window; ≤5400 s (A1) / ≤18000 s (B); RSS < 4 GiB; 0 decoder/DE/graph/`tools/*` calls; ≥200 bootstrap resamples per dataset.
- Additive output root `workspace/p3_census_<uuid8>`; `results/` and `comparison_bench/outputs_comparison/` forbidden; all excluded derived artifacts unread.

## Non-goals

- No FER, SKR, operating-point, route, qualification, or publication claim; the route decision belongs to the main thread.
- No decoder, DE, graph construction, `tools/longrun_*`/`minrerun_*`/`routeA_*`, or `experiments/run_e2e_pipeline.py` invocation.
- No change to the frozen accounting constants (`n=1024`, `n_bits=5120`, `H_full=0.83256272`, `content=852.544`, slope `4.785675`, tag 64, `f_super ≤ 1.3`, `m1+m2 ≤ 208`).
- No new estimator convention, no re-estimation of the V80 anchor, no averaging of V19's `0.549955` (a declared synthetic independence constant) with an empirical number.
- No ttbin header/binary parser, no vendor-package probe beyond an import check, no reading of excluded derived artifacts.
- No commit, push, PR, or AGENTS.md/roadmap/inventory edit in this change.
- No both-member open/concatenation of any `.ttbin` pair (hard prohibition, §Why amendment); no filename-tag duration (measured span only); no Stage 1 census read before the separately-signed Stage 0.5 probe passes.

## Affected specs

- `specs/v80-p3-real-hfull-census/spec.md` (delta: census estimator + bias/uncertainty rule, memory/stationarity battery, alignment gating decision tree, conditional certification arithmetic, gated execution with explicit grant).

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved to the consolidated baseline; retained for history. No new OpenSpec change created (consolidation is documentation-only).

> **ARCHIVED 2026-09-21 — SUPERSEDED BEFORE EXECUTION.** Planning authority moved to
> `docs/V80_BASELINE_20260921.md` (§0.1 retained-clause index). This change was frozen
> but NEVER executed and NEVER granted; its spec delta is intentionally NOT merged into
> `openspec/specs/`. Retained for history. Do not cite its frozen clauses as current
> without checking the baseline. Note: the banner's earlier closing sentence
> "No new OpenSpec change created (consolidation is documentation-only)" is falsified by
> the subsequent creation of `openspec/changes/v80-prior-cost-accounting/`.
