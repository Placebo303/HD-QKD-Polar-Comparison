# 48h Acceleration Plan — Proposal

- Change: `accel-48h-plan`
- Branch: `formal-ir-v72p1-addendum-clean`
- Type: **doc-only planning increment** (AGENTS.md §1.2 matrix: documentation-only, no track gate). This change authorizes no execution, no workspace write, no commit/push.
- Authority (frozen, read-only): `docs/NOW.md` (2026-09-28); `docs/research_cycles/JOINT-PRICING-R2/PREREG_AND_AUTH.md` (FROZEN, §14 grant EMPTY); `docs/research_cycles/PERPLANE-BINARY-LDPC/STAGE0_PACKET.md` (§§5/16, KILL 1875/excess 771, review S0-01…S0-08 pending); `docs/research_cycles/PROXY-RECAL-R2/PREREG_AND_AUTH.md` (DRAFT-FROZEN, execution grant PENDING); `docs/research_cycles/U1-CEILING-PROBE/PREREG_AND_AUTH.md` (§5 ceiling); `docs/research_cycles/CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` Part B.1 (fenced forms); decision-log 2026-09-28 entries (M+64 correction §17, fence repairs, audit); `AGENTS.md` §1.2 / §10.3.

## Goal

Within 48 hours, close every cheap frozen verdict before spending any heavy compute: (1) re-evaluate the joint-pricing question under the corrected total form (anticipated MARGINAL 1100 fits-by-4 / 1319 excess-215, THIN-MARGIN<64 blocks downstream); (2) formalize the provisional Stage-0 KILL (1875 vs 1104, excess 771) via its pending batch-end review; (3) implement + review the segmented proxy driver (code-only); (4) run the segmented proxy execution only after 1–3 are closed and a new explicit grant lands; (5) close U1 + dead-route fences (M3C STOP / M3D narrow-mechanical-only / M2 WITHHELD / two void baselines) doc-only; (6) land a 48h decision record + memory triage with a scoped manifest. Order is ROI-gated: seconds-scale analytics and reviews first, the single 3h EXPLORE_HEAVY last, no parallel heavy spends.

## Non-Goals

- No re-decision of any frozen science input, `f` grid, backoff, budget (1104/2064/1040), tag accountings, thresholds, seeds, graphs, decoder settings, or decision rules. Total-form fix is a carried label correction, not a new hypothesis.
- No reopening of M3C (STOP), M3D (beyond the single narrow mechanical sentence), M2 (WITHHELD), HDC/LB baselines (both `void-no-correction`, never ranked), option F (closed by U1 header ceiling ≈24.6 bit/≈0.03 f under every outcome), or Stage-0 scope (ten independent per-plane allocations only; joint/layered designs not excluded by it).
- No decoder/construction call, no `.ttbin`/bundle/`pairs.parquet`/raw-data contact, no FER/efficiency/leakage/`f`/SKR/key/method claim beyond each packet's frozen ceiling.
- No headline tag designation (D-1 stays DEFERRED; both comparisons carried distinctly, excess invariant `M−1104`).
- No edit to any frozen packet, existing `workspace/` root, `results/`, `comparison_bench/outputs_comparison/`, `src/`, `experiments/`, `tools/`; no workspace write and no commit/push by this change.
- No grant is issued by this change. P-1 and P-4 each need their own new explicit verbatim grant + Pre-EXECUTE before any command runs.

## Impact Scope

- New: `openspec/changes/accel-48h-plan/` (`proposal.md`, `design.md`, `tasks.md` — this increment only).
- Read-only references: the six JOINT-PRICING-R2 inputs, five Stage-0 inputs, nine PROXY-RECAL-R2 inputs, six U1 inputs, CHAN-QUALITY five-capture `ser` 0.23856707–0.25433839 with fenced structure forms. Nothing is opened for content by this change.
- Untouched: all code, all packets, all workspace roots, all outputs, `docs/NOW.md`, `docs/decision-log.md`, `openspec/` (beyond this directory), `AGENTS.md`.
- Downstream (separately granted, not by this change): one fresh `workspace/jp_<uuid8>` (P-1), review docs in existing roots (P-2/P-5), two additive proxy files + tests (P-3), one fresh `workspace/proxy_recal_r2_<uuid8>` (P-4), decision-log/NOW/memory entries (P-6).

## Acceptance Criteria

- AC-1: P-1…P-6 ordered with per-item owner, packet-vs-doc-only, single track (or doc-only/implementation-only with no-gate reason), cost ceiling, and mechanical pass/kill conditions.
- AC-2: Frozen numbers carried exactly: Stage-0 1875/excess 771 stands; joint nominal 1100 fits-by-4 / backoff 1319 excess-215 anticipated MARGINAL §5.3(a); THIN-MARGIN (<64 nominal margin) blocks any downstream design packet until the user addresses it on record; CHAN-QUALITY cited only in fenced forms with the ~1e-6 detection floor and `0.098260`-never-a-measurement.
- AC-3: Dead routes fenced: M3C STOP (no two-graph/FER decision), M3D single narrow sentence only, M2 WITHHELD with five blocks, both baselines `void-no-correction` never ranked, option F closed under every U1 outcome.
- AC-4: No execution, workspace write, or commit authorized or performed by this increment; each execution P names its frozen packet, grant block, and Pre-EXECUTE checklist as the sole authorization path.
