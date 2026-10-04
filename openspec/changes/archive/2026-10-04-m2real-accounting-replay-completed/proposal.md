# M2 real accounting replay

Status: proposed, implementation-only until the separate DECIDE replay gate. This change corrects how existing M2 disclosures are *described*; it does not change or rerun a decoder.

## Why

`m2real_runner.py` displays the same nominal `5m` efficiency for HDC and LB although their recorded `leak_EC` differs greatly. It records one 64-bit tag per 64-symbol block but displays one tag per 1024-symbol superframe. The original independent review missed this, and D2 was evaluated with the wrong input. See `docs/research_cycles/M2-REALCOMP/MAIN_ADJUDICATION_20260926.md`.

## Scope

Add one small, read-only accounting replay module and one fake-summary test. The replay reads only the three existing `rows.json` summaries when explicitly named. It prints a new diagnostic table with actual EC disclosure normalized by each source's `H_corr`, recorded block-tag accounting, and a clearly labeled one-tag-per-superframe counterfactual. The original `f_notag`, `f_super`, `f_eff`, result roots, and review remain untouched. No D2 branch, method-family ranking, SKR, or publication claim is produced.

## Non-goals

No `.ttbin` or bundle read; no decoder or construction call; no original-root write; no backend inference; no method tuning; no retrofit of a 1024-symbol `f_eff` slope onto 64-block FER. Any future-runner change is a separate change.

## Affected specs

`specs/m2-accounting-replay/spec.md` (new delta). The claim ceiling remains diagnostic until a separately preregistered DECIDE replay and independent Pre-RESULT review.
