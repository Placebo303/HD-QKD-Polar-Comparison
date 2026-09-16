# V65 Channel Compatibility Report (V65_DATA_NOT_READY)

overall: **V65_DATA_NOT_READY**

| src | lam* | bdry | H1 | H2 | H | CE1 | CE2 | CE_full | dCE | CV | Val | dNLL | MAP | unseen | req_m1 | req_m2 | req_m_total | req_leak | frozen_m2 | frozen_leak | delta_leak | G1-8+G7aux | PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | 200 | 1144 | None | None,None,None,None,None,None,None,None,None | False |
| 1p5M | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | 206 | 1174 | None | None,None,None,None,None,None,None,None,None | False |
| 2M | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | None | 208 | 1184 | None | None,None,None,None,None,None,None,None,None | False |

Frozen: m1<=16 m2 {'1M': 200, '1p5M': 206, '2M': 208} m_total {'1M': 216, '1p5M': 222, '2M': 224} frozen_leak {'1M': 1144, '1p5M': 1174, '2M': 1184} vs required_leak=5*required_m_total+64
CE chain |CE_full-CE1-CE2|<1e-09 H chain <1e-9, delay sign/50ps sigma[50,150] gate200 thr40000
zero_overlap_key=(source,session,frame) forbidden_nonempty=True v66={'status': 'PENDING', 'equals': False, 'reason': 'V66 registry not yet generated (=V65 TEST pending)', 'key': '(source,session,frame)'} binding_ok=True
Sample: CAL 4096*256=1048576 VAL 512*256=131072 real parquet, TEST identity sealed 120 frames/source
TEST: not read - v66 prefreeze 90 blocks 30/src 70/90 & 20/30 undetected 0
