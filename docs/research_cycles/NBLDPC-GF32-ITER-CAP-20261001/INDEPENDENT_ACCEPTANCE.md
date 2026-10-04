# Independent batch-end acceptance

Batch UUID: `eb0eb231-b295-4c1c-9ddd-4d775bc74352`  
Reviewer: `iter_contract` (independent of operator `iter_operator`)  
Verdict: **P6 PASS**, limited to this frozen synthetic screen.

The reviewer checked that the five machine artifacts, UUID, contract, namespace, and `COMPLETE` status agree. The CSV contains 384 rows. The NPZ contains six `52×128` deep H matrices, 192 truth/syndrome pairs, and 384 raw decoder vectors with pair/call/vector graph, stream, frame, seed, arm, and cap mappings. The reviewer independently recomputed all 384 GF(32) syndromes and exact/syndrome-valid-wrong/raw-fail classifications and matched them to CSV and summary. All six graphs had GF(32) rank 52, one connected component, 256 edges, variable degree 2 throughout, and check degrees 4 (four checks) plus 5 (48 checks). The fixed seed plan and seed formula matched.

Independent totals were control/candidate exact-and-syndrome successes 146/146, `Delta=0`, positive `Delta_g` graphs 0/6; paired both/neither 146/46; control-fail to candidate exact/wrong/still-fail 0/0/46; prefix-consistent control passes 146. Frozen classification `NO_SUFFICIENT_SIGNAL` follows. Iteration totals were 5127/12487; decoder-wall sums 30.894529954/74.938742763 s; maximum arm wall 0.623469105/1.553238648 s; batch wall 156.382415121 s; sampled RSS maximum 103010304 B. The attempt made 384 BP calls, disclosed 99840 syndrome bits, wrote a 36456 B NPZ from 189744 B payload, and recorded zero resource, integrity, or authorization violations. No decoder rerun was performed.

Main-thread scientific acceptance is limited to this bounded finite synthetic observation and the mechanical `NO_SUFFICIENT_SIGNAL` screen classification. Sampled RSS is not a continuous peak; verification remains `NOT_IMPLEMENTED`, and undetected errors remain `NOT_MEASURED`. No FER, `f_eff`, SKR, throughput, security, qualification, publication, real-channel, causal, route, family-rejection, or cross-batch ranking claim follows. The batch grant is consumed; no rerun or continuation is authorized.
