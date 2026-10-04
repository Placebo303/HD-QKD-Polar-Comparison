# RESULT — NB-LDPC GF32 common-paired construction canary

**Track:** EXPLORE  
**Batch UUID:** `a9a18abe-3547-4d16-aa50-1f7150182f31`  
**Status:** `COMPLETE` (`CONSTRUCTION_FEASIBLE` under the frozen protocol)  
**Contract:** [PREREG_AND_AUTH.md](PREREG_AND_AUTH.md)  
**Machine root:** `workspace/gf32_construct_a9a18abe/`

## Attempt and selection

The authorized command was run once after confirming the output root was absent; it exited 0. The six fixed graph groups used paired attempts: both profiles were tried at the same construction seed, and a group selected the first attempt where both profiles were admitted. Five groups selected `j=0` using their graph ID as seed. For graph ID `2026093905`, the control was admitted at `j=0`, while the candidate's expected construction failure was retained (`no eligible check placement at variable 127 socket 2`). Both `j=0` arms were attempted; both profiles were then admitted at `j=1` with common seed `2560859716`.

The batch made 14 constructor calls (7 control, 7 candidate), retained 13 actual matrices, selected all six groups, and exhausted none. The 13 matrices are `52×128`, use the frozen GF(32)/poly-37 profiles, have rank 52, and are connected. Control has `E=256` (`dv=2`, `dc=4×4 + 5×48`); candidate has `E=384` (`dv=3`, `dc=7×32 + 8×20`). Independent C4 review checked the saved matrices, degree/edge and coefficient maps, group/attempt mappings, and common-seed selection.

## Artifacts and cost

At terminal output, before the append-only review/acceptance text was added to the log, the three artifacts totaled 1,489,010 bytes: `manifest.json` (1,736 bytes), `constructions.json` (1,485,310 bytes), and `EXPLORATION_LOG.md` (1,964 bytes). The two JSON artifacts remain unchanged; the current log is 2,952 bytes. Batch wall time was `0.227312384 s`; summed constructor elapsed time was `0.220091314 s` (control `0.081202122 s`, candidate `0.138889192 s`). Sampled RSS peaked at `102088704` bytes over 28 samples. There were no resource-stop markers. The frozen limits were 96 calls, 180 seconds, 4 GiB sampled RSS, and 10 MiB of results.

No labels, BP, OSD, decoder calls, or performance screen ran. The accepted `CONSTRUCTION_FEASIBLE` classification means only that all six paired groups were admitted within this fixed protocol. It is not evidence about an unbiased random-graph population, decoder performance, or route choice, and supports no FER, throughput, security, qualification, or publication claim. The one-shot authorization is consumed; no rerun, repair, resume, or extension is authorized.

Independent C4 review and main acceptance are recorded in [INDEPENDENT_ACCEPTANCE.md](INDEPENDENT_ACCEPTANCE.md).
