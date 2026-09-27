# G-M2-ACCT-REPLAY — result record (2026-09-26)

Track **DECIDE**. This is a read-only replay of stored T3 summaries, not a decoder rerun. Pre-EXECUTE is recorded in `ACCOUNTING_REPLAY_PREREG_AND_AUTH.md`; the user grant is quoted there. The one frozen command exited **0**. Machine root: `workspace/m2_accounting_replay_20260926/` with only `diagnostic.json` and `resource.txt`. Wall **0.51 s** (cap 300 s), peak RSS **124,128 KiB** (<2 GiB), one process. Input `rows.json` lengths remain 14,042,522 / 19,734,691 / 26,471,294 bytes; modification times remain the pre-execution values. `git diff -- src/ experiments/ tools/` is empty. No `.ttbin`, bundle, decoder or construction was accessed.

Each ratio below divides by `superframes_done*1024*H_corr` for that source. `f_ec_actual` uses recorded `leak_EC`. `f_recorded_tag` adds the **recorded 16 tags per superframe**. `f_one_tag_CF` adds only one tag per superframe and is a **counterfactual, not an executed verification protocol**. These are disclosure arithmetic for the specific recorded implementations, not accepted `f_eff` or a method comparison.

| source | family | m | f_ec_actual | f_recorded_tag | f_one_tag_CF |
|---|---|---:|---:|---:|---:|
| 1M | hdc | 197 | 10.151372 | 11.399392 | 10.229373 |
| 1M | lb | 197 | 3.841563 | 5.089583 | 3.919564 |
| 1M | hdc | 201 | 10.152537 | 11.400557 | 10.230538 |
| 1M | lb | 201 | 3.919564 | 5.167584 | 3.997565 |
| 1p5M | hdc | 203 | 9.880054 | 11.088819 | 9.955602 |
| 1p5M | lb | 203 | 3.834054 | 5.042819 | 3.909601 |
| 1p5M | hdc | 207 | 9.878306 | 11.087071 | 9.953853 |
| 1p5M | lb | 207 | 3.909601 | 5.118367 | 3.985149 |
| 2M | hdc | 204 | 9.808472 | 11.008473 | 9.883473 |
| 2M | lb | 204 | 3.825003 | 5.025004 | 3.900003 |
| 2M | hdc | 208 | 9.806891 | 11.006891 | 9.881891 |
| 2M | lb | 208 | 3.900003 | 5.100004 | 3.975003 |

All 12 identities match the frozen source/m grid; each arm is COMPLETE with `blocks_done=16*superframes_done` and `lambda_parts.tag=64*blocks_done`. `diagnostic.json` preserves the original nominal f labels under `original_f_labels` and marks itself `DIAGNOSTIC_UNREVIEWED` pending review. No `f_eff_actual`, D2, backend identity, family ranking, SKR, certification or publication claim is inferred. The original `M2-REALCOMP/RESULT.md`, review and three T3 roots are unchanged.
