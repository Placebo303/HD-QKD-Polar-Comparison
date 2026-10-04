# Result — GF(32) MRB order-1 reachability diagnostic

Batch `c4fab9ba-ead1-4c64-8d0b-82177ace721c` completed and is closed/main-accepted as a finite synthetic EXPLORE diagnostic. The accepted result is limited to whether each frame's actual BP-derived MRB basis can contain truth within order one. It is not a route, decoder-benefit, or method-comparison result.

## Frozen setup and execution

The batch used six fixed GF(32), polynomial-37 graphs with `n=128`, `m=52`, `E=256`, and rank 52. Errors followed the frozen iid synthetic marginal proxy at `p0=0.55`; each of 192 frames received one raw BP call with its graph, prior, and syndrome. Truth was used only after BP returned. The diagnostic recomputed the stable ascending reliability permutation from the returned beliefs, the augmented GF(32) RREF, the raw-free base, and the unique truth reconstruction. There were zero OSD or candidate-enumeration calls.

## Reachability observations

Across 192 frames, 146 raw outputs were exact and syndrome-valid (`D_free=0`), 46 failed the recomputed syndrome, and zero were syndrome-valid but wrong. All 46 raw-syndrome-fail frames had `D_free >= 2`; no frame had `D_free=1`. Therefore, in each of those 46 frame-specific MRB bases, truth is outside the full order-0/1 set. This is a statement about the observed bases and frames, not global code distance or decoder recovery.

| Graph seed | Raw exact (`D_free=0`) | Raw syndrome-fail (`D_free>=2`) |
|---:|---:|---:|
| 2026093901 | 26 | 6 |
| 2026093902 | 23 | 9 |
| 2026093903 | 24 | 8 |
| 2026093904 | 25 | 7 |
| 2026093905 | 22 | 10 |
| 2026093906 | 26 | 6 |

Among the 46 syndrome-fail frames, observed `D_free` ranged from 6 to 36, with median 21 and mean 20.5. These are descriptive statistics conditional on this finite set; they are not route or inferential evidence.

## Accounting and resources

The run disclosed 49,920 syndrome bits (260 per attempted BP call), used zero tag bits, and recorded zero resource markers or violations. Verification was `NOT_IMPLEMENTED`; `undetected` is `NOT_MEASURED`, not zero. Recorded batch wall time was 89.9558 s under the packet's scope, which excludes the terminal summary, manifest, and log writes; maximum combined BP-plus-diagnostic arm time was 0.5948 s. Maximum sampled RSS was 121,819,136 bytes over 795 checkpoints; it is a sampled maximum, not an absolute process peak. `diagnostics.npz` was 6,402,852 bytes.

## Independent review and claim ceiling

`faithful_scope` independently reviewed the saved arrays and recomputed all 192 reliability permutations, GF(32) RREFs/ranks, free-coordinate distances, raw-free bases, and truth reconstructions; it did not rely only on stored booleans. The reviewer confirmed the CSV/NPZ mapping and aggregate counts. The main thread accepted that bounded result, and the one-batch authorization is consumed.

This result does not measure FER, `f_eff`, SKR, throughput, security, qualification, publication performance, or route value. It does not establish global minimum distance or general MRB decoder capability, and it must not be pooled or ranked against another batch. This closeout creates no additional execution authority. The four machine data outputs (`manifest.json`, `frame_records.csv`, `summary.json`, and `diagnostics.npz`) remain unchanged; the 192 original scientific log entries are unchanged, with only the batch-end review text appended to `EXPLORATION_LOG.md`.
