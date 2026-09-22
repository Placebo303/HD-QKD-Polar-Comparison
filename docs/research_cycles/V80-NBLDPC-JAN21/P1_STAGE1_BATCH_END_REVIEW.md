# P1 Stage-1 Batch-End Review (EXPLORE_HEAVY, independent) — 2026-09-23

- Packet: `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_PACKET.md` (P1S1-1, FROZEN) + `P1_STAGE1_PROMPT.md` (P1S1-2).
- Pre-EXECUTE: `P1_STAGE1_PREEXEC.md` (Q0–Q6, FROZEN, NOT GRANTED).
- Log: `P1_STAGE1_EXPLORATION_LOG.md` (entries 0–3 + appendix, append-only).
- Arms (frozen order R1→R2):
  - `workspace/P1_STAGE1/P1S1-R1_ef7da79b/` — instance 2026092001 (girth 8), k=84, res 83/84, F=1/240, f_eff=1.284196, wall 1478.4 s.
  - `workspace/P1_STAGE1/P1S1-R2_22754019/` — instance 2026092011 (girth 6), k=138, res 138/138, F=0/240, f_eff=1.275008, wall 1554.4 s.
  - Batch wall 3032.8 s / ceiling 7200 s.
- Baseline: grant HEAD `e2236766` (full `e22367662124e6e4622e24b8d61a86fded3d9ef2`); branch `formal-ir-v72p1-addendum-clean` (no switch, no commit, no push).
- Reviewer role: independent batch-end review only (AGENTS.md §10.3). Read-only verification + this one new file. No decode executed, no evidence modified, no commit/push.
- Verdict: **PASS_WITH_FINDINGS** (execution contract clean; science gates mixed per-arm — valid measured outcomes, not violations; see §7–§8).

## §1 Authorization boundary — PASS

- Single fill place respected: full grant lives only in packet §10(d) line 97; `P1_STAGE1_PREEXEC.md` Q6 stays blank (`________`, not a second auth path); log entry 0 is explicitly marked transcription ("全包唯一填充处 = packet §10(d)，本条目只转录"; "PREEXEC Q6 …不是第二授权路径").
- Grant verbatim character-match (packet §10(d) ↔ log entry 0): `G-P1S1 GRANT：授权P1 Stage-1速率自适应救援执行（2臂 P1S1-R1/P1S1-R2，m_base=200+Δm=8→总行208≤208硬顶，Stage-2=Stage-1非success全集，分列禁合并，双旗标 --execute-real --execution-authorized，基线HEAD e2236766）` — grep confirms identical string in both files, no second variant.
- Dual UUIDs frozen in Pre-EXECUTE + absence-proven, then signed: `P1S1-R1_ef7da79b` / `P1S1-R2_22754019`; actual roots match exactly; commands use `--execute-real --execution-authorized` dual flags with frozen literals (`--m-base 200 --m-total 208 --blocks 240 --seed-base 2026096401`, per-arm `--arm/--instance/--root` only).
- Budget confirmed in grant (6 items, all ✓): per-arm wall ≤3600 s; batch ceiling = 7200 s (proposal accepted at sign); per-decode ≤300 s (timeout = terminal, fail, no rerun); RSS < 2 GiB; 1 CPU; zero `.ttbin` / zero real data / zero `results/` + `outputs_comparison/` writes. Date/main `2026-09-22/main`, signature `from kai`.
- Baseline drift disposition: packet frozen at `85e0771f`; Pre-EXECUTE measured actual HEAD `e2236766`; grant pins `e2236766`; reviewer re-measured HEAD = `e2236766`, branch = `formal-ir-v72p1-addendum-clean`. `git log` shows the delta is one docs commit ("record S0.1 gate PASS…", parent = `c98c5ae9`) with `git diff -- src/ experiments/ tools/` EMPTY and `git status` showing only the 6 additive untracked files (runner + test + packet + prompt + preexec + log). No code change; drift recorded, not concealed. Acceptable.
- Q0–Q6 independently re-checked: Q0 branch/HEAD PASS; Q1 additive-only + `src/` EMPTY PASS; Q2 F1–F10 runner mapping PASS; Q3 absence/FRESH/protection PASS (reviewer re-confirmed `results/` = 0 B empty, seed range `2026096401..2026096640` unique per-arm below); Q4 `16 passed` PASS (log 5.95 s vs preexec 6.37 s — same count, benign timing delta, warning = known benign `cache_dir`); Q5 dry zero-decode pins PASS (`decode_calls=0`, base_rank 200 REQUIRED both instances, girth recorded-not-gated); Q6 closure PASS (S0.1-gate + G0=B cited-not-reproven, ceiling fixed at sign).
- No execution before grant: Q5 declares grant-front production decodes = 0; arm commands carry dual flags post-grant only. No violation found.

## §2 Machine gates — PASS (all EXPLORE mechanics)

- 240/240 both arms: `blocks_done=240/blocks_target=240`; csv stage1 = 240 rows each; rows.json stage1 = 240 each. No bar-12 early stop (both ran full 240; `route_ctx` FAIL rows are report-only, never trimmed Stage-2).
- attempted==k identity, double pass + set equality (reviewer recomputed from rows.json AND csv):
  - R1: attempted 84 == k 84; Stage-2 block set == Stage-1 fail set exactly (84/84 both sources).
  - R2: attempted 138 == k 138; Stage-2 block set == Stage-1 fail set exactly (138/138 both sources).
- Failure retention + repair rule: both verdicts COMPLETE, zero INCOMPLETE-wall arms, zero infra failures; `no repair path used` declared in entry 3 and appendix and consistent with evidence (pre-registered ≤1 repair never invoked; inputs/seeds/thresholds unchanged). No retry/resume/adaptive.
- undetected isolation: reviewer census — R1 `failed&undet=81, failed&!undet=3, !failed&undet=0`; R2 `failed&undet=134, failed&!undet=4, !failed&undet=0`. Zero rows with `failed=False + undetected=True`; summary undetected (81/134) == csv undetected-True totals; all undetected sit in Stage-1 (Stage-2 undet = 0 both arms). Never merged into success (success = ¬failed). PASS. Note on `decoded` column semantics, see §7 finding F3 (non-blocking).
- Merge ban (incl. 6+4): respected. RESULT/summary/log all carry per-arm-only numbers with explicit "分列禁合并 / pooling incl. 6+4 FORBIDDEN" lines; appendix tallies list R1/R2 columns separately with "未做任何跨实例合并" declaration. Reviewer found no summed FER/conversion/trigger/leakage. PASS.
- f_super/f_eff dual-number discipline: both RESULTs carry `f_super` baseline 1.248029 + worst-case 1.294948 as DISTINCT恒等行 with "NEVER quoted as f_eff" guard, plus own-arm `f_exp`/`f_eff` from own final F. No substitution. (Packet prints worst-case as 1.294947 = 5dp truncation; evidence prints 1.294948 = 6dp rounding of 1104/852.544 — 1e-6 rounding delta, non-material; see §7.)
- N_req report-only: 402 (R1) / 575 (R2), both labeled report-only with zero-failure relevance rule; no operating-point selection. PASS.

## §3 Evidence triple-consistency (RESULT ↔ rows.json summary ↔ rows.json rows ↔ csv) — PASS

Reviewer recomputed every field from raw rows (both `rows.json` row lists and `block_accounting.csv`):

| check | R1 | R2 |
|---|---|---|
| csv data rows (excl. header; `wc -l` 325/379) | 324 = 240 + 84 ✓ | 378 = 240 + 138 ✓ |
| rows.json `rows` len | 324 ✓ | 378 ✓ |
| stage split json vs csv | 240 / 84 both ✓ | 240 / 138 both ✓ |
| Stage-1 k (failed=True) json vs csv vs summary vs RESULT | 84/84/84/84 ✓, FER 0.35 ✓ | 138/138/138/138 ✓, FER 0.575 ✓ |
| rescued + final == attempted | 83 + 1 == 84 ✓ | 138 + 0 == 138 ✓ |
| final F json vs csv-stage2-fail vs summary vs RESULT | 1 / 1 / 1 / 1/240 = 0.004167 ✓ | 0 / 0 / 0 / 0/240 = 0.000000 ✓ |
| seeds stage1 range/uniq | 2026096401..2026096640, 240 uniq ✓ FRESH | same, 240 uniq ✓ FRESH |
| csv columns | 10-col contract ✓ | 10-col contract ✓ |
| accounting E/leak→f_exp→f_eff→headroom→N_req→f_super | exact recompute diff 0 (see §4) | exact recompute diff 0 |
| wall rows-sum vs elapsed | 1475.0 vs 1478.4 (overhead 3.4 s, sane) | 1550.2 vs 1554.4 (overhead 4.2 s, sane) |

- R1 intermediate-state question (task-nominated): whether a transient mid-run `F/240 = 0.000000` display contradicts the final `1/240 = 0.004167`. Finding: **no retained inconsistency — final triple consistent.** RESULT final, summary (`final_fails=1`, `f_over_240=1/240`, `fer_final=0.004167`), csv (1 stage2-fail row: blk178, `max_iter_reached`, iters 300, undetected 0), and rows.json row census all agree on F=1. The appendix already dispositions the transient as "Stage-2 进行中 RESULT 的 r 曾短暂 0.000000" (progressive-write observation, not evidence). No file in the frozen roots retains `0.000000` for R1 final (reviewer grep: only `0.004167` present). The single residual is positively identified (blk178, seed 2026096579, stage2 iters 300, detected timeout — not an undetected escape). Transient displays during a long run do not enter the frozen evidence; nothing to repair, no rerun authorized under this grant.
- R2 nominated check `attempted 138 == k`: **confirmed in both sources plus set equality** (138/138, block-index sets identical). rescued 138/138 full conversion, final 0/240.

## §4 Accounting recomputation (frozen V80 anchor basis, single basis) — PASS

Content = 852.544 b; cap = 1108.31 b; slope = 4.785675. Reviewer formula replay `E=1064+40·r; f_exp=E/852.544; f_eff=f_exp+4.785675·(F/240); hr=1108.31−E; N=⌈3·4.785675/(1.3−f_exp)⌉`:

- R1 (r=83/240=0.345833, F=1): E=1077.8333 ✓, f_exp=1.264255 ✓, f_eff=1.284196 ✓, hr=30.4767→30.48 ✓, N=402 ✓, f_super base 1.248029 ✓ / full 1.294948 ✓.
- R2 (r=138/240=0.575, F=0): E=1087.00 ✓, f_exp=1.275008 ✓, f_eff=1.275008 (slope term zero) ✓, hr=21.31 ✓, N=575 ✓, f_super identical ✓.
- All diffs 0 to printed precision. Single-basis rule kept (no second basis). `f_super` never presented as `f_eff`. R2's F=0 ⇒ f_eff==f_exp is correct per frozen rule, not a copy error.

## §5 Budget envelope — PASS

- Per-arm wall 1478.4 s / 1554.4 s ≤ 3600 s ✓ (single window, both stages combined).
- Batch total 1478.4+1554.4 = 3032.8 s ≤ 7200 s ✓ (headroom 4167.2 s; unspent ≠ authorization, correctly stated).
- Per-decode max 76.5 s (R1) / 74.6 s (R2) < 300 s ✓ (no timeout-terminal rows on timing grounds; the one R1 residual is max_iter 300, not wall-timeout).
- Peak RSS 0.502 GiB < 2 GiB ✓ both arms; budgets record `cpus: 1` ✓; zero `.ttbin` (runner grep: only 2 assertive docstring/report literals "no read path", no import/path/read); zero real data (frozen channel pair, synthetic-only); zero `results/`/`outputs_comparison/` writes (reviewer: `results/` 0 B empty; output roots untouched beyond pre-existing files).

## §6 Claim ceiling + scope — PASS

- Both RESULTs carry the full packet-§9 ceiling sentence (synthetic efficiency ONLY; NOT SKR/qualification/route/operating-point/real-FER/certifiable-`f_eff≤1.3`/publication; key-eligible cited-not-consumed; later citation must list both instances separately). Log entries 0/3/appendix repeat it. No cert sentence asserted.
- N_req vs eligibility supports the ceiling rather than undermining it: 402 (R1, moot — F=1) and 575 (R2, F=0) both exceed every key-eligible count 200/276/364, consistent with X1 joint-∅ (no certifiable single point). R1 f_eff 1.284 <1.3 is non-certifiable by F=1; R2 f_eff 1.275 <1.3 with F=0 is still N-gated out (575 > 364). No `f_eff≤1.3` certification language appears anywhere. Correct.
- S0.1 anchors used as mechanism context only, per-instance columns (79/240 vs 84/240; 119/240 vs 138/240), with "新帧实现、无主张/非预测/非配对身份" declarations. No cross-packet prediction, no monotonicity inference, no second-basis computation.
- Forbidden surface clean: no P1-§9 per-source / P2 / X1 arms; no decoder/DE/graph change; no prior refit; no warm-start / non-nested / multi-segment; no `results/`/`outputs_comparison/` writes; `src/` diff EMPTY; no `longrun_*`/`minrerun_*`/`routeA_*`, no e2e pipeline; no touching EXECUTION_PLAN/NOW/decision-log/memory/S0.1 family; no commit/push (HEAD still `e2236766`).

## §7 Non-blocking findings (3, none bars promotion of the evidence itself)

- F1 (rounding, trivial): packet prints worst-case `f_super` as 1.294947 (5dp) while evidence prints 1.294948 (6dp rounding of 1104/852.544 = 1.2949478…). 1e-6 display delta, formulas identical, no scientific effect. Suggest future packets print 6dp canonical to avoid grep flagging. Non-blocking.
- F2 (transient display, dispositioned): mid-run progressive RESULT briefly showed r/F 0.000000 before completion (appendix-noted). Final evidence unanimously F=1/240 (R1). This is expected progressive-write behavior, not an inconsistency. No action; retained here as the nominated-point answer. Non-blocking.
- F3 (column semantics, readability): `decoded=1` on ALL rows including fails (R1 census: failed rows all carry `decoded=1`; the R1 residual blk178 is `decoded=1, failed=1, undetected=0, status=max_iter_reached`). So `decoded` means decoder-returned/syndrome-path, NOT success; success = `failed=False` (equivalently `exact_match`). Isolation still holds (§2), but a future reader joining `decoded==True` to "success" would miscount. Suggest a one-line legend in the successor packet/runner docstring (`success := ¬failed; decoded := returned`). No data change. Non-blocking.

No blocking issues found. No authorization breach, no machine-gate breach, no evidence mismatch, no budget breach, no ceiling breach, no scope creep.

## §8 Route input to main thread (not a route adjudication — decision stays with main thread under a future DECIDE gate)

- Mechanical rescue outcome (valid EXPLORE evidence): 221/222 Stage-1 fails rescued overall (R1 83/84 = 98.8%, R2 138/138 = 100%), both stages COLD, nested single-segment 200→208 within the 208 hard cap, attempted==k exact both arms. Δm=8 single-segment rescue is mechanically effective on these two synthetic realizations — the "cliff is rescuable in cold full-matrix form" hypothesis survives contact with measurement on this slice.
- Gate-mapped outcome per frozen packet §4 (recorded, not裁决 by this review): **neither arm satisfies all three gates simultaneously** — R1: (a) FAIL (F=1/240≠0), (b) PASS, (c) PASS (30.48≥21.5); R2: (a) PASS (F=0), (b) PASS, (c) FAIL marginal (21.31<21.5 by 0.19 b; r=57.5% > 57.0% cap). Under the packet §4 decision tree both arms map to the FAIL branch (any-gate FAIL ⇒ P4 elevation as S3 prerequisite; the packet text: "本身即对 P4 的决定性输入"). This batch therefore **does not constitute a P1-PASS ticket into P3 memory-audit DECIDE**; promoting R2's zero-fail alone while dropping its (c) FAIL and R1's (a) FAIL would be single-arm/single-gate cherry-picking, explicitly forbidden by the per-instance/claim-ceiling rules.
- Suggested main-thread handling: (i) accept this batch as closed EXPLORE evidence (no rerun under G-P1S1 — grant spent; wall-partial/retry rules already terminal); (ii) follow the frozen decision tree — route the FAIL-branch input toward P4 (second-generation) deliberation rather than opening P3-DECIDE on the back of this batch; (iii) if main thread wishes to pursue P3 despite the marginal (c) miss, do so only via a NEW packet that explicitly re-justifies thresholds/scope (e.g., headroom sensitivity ±0.2 b, blk178 class) — never by re-reading this batch as a PASS. Any "primeiro" supplement (single-residual diagnosis, headroom-sensitivity note) is documentation/analysis work, not a re-execution; any new decode needs a fresh grant.
- Memory triage pointer (for main thread, not executed here): packet + prompt + preexec + log (0–3+appendix) + two arm roots (RESULT + rows.json + csv each) + this review.

## §9 Provenance of this review

- Re-measured: branch/HEAD/status/diff, `wc -l` + headers, full `rows.json` summary dump, json-vs-csv flag census (incl. `failed&undet` isolation and Stage-2⊆Stage-1-failset set equality), accounting formula replay, N_req replay, f_super replay, wall/RSS/max-per-decode extraction, grant-verbatim grep, UUID grep, `.ttbin` grep, `results/` emptiness, git log. No decoder invoked; no evidence file written, modified, or moved; no commit/push. Only new file: this review.

Checklist:
- [x] Matches OpenSpec spec — N/A (no OpenSpec change in scope; matches frozen packet §§1–11 / F1–F10 / gates / ceiling)
- [x] Tests pass — Q4 focused fake-only `16 passed` recorded in both preexec and log entry 0 (timing-only delta 6.37 s vs 5.95 s, benign)
- [x] No scope creep — additive roots only; forbidden surfaces untouched; no P1-§9/P2/X1 arms
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? — No (main thread decides at milestone triage; this EXPLORE batch introduces no new durable failure mode: the only residual blk178 is a plain `max_iter_reached` detected timeout, already classified)
