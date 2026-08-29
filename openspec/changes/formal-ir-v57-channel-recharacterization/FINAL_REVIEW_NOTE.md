# V57 R5 Final Review Note — RESULT_ACCEPTED_FAIL / PREDICTIVE_MODEL_NOT_STABLE

**HEAD == origin/formal-ir-mainline == implementation SHA: e81a88f23f76dd313f0ab7390495389f39f9bdcd**

R5 复审通过：hierarchical λ·P_global 恢复，λ Cal内4-fold择优 Val单次评估，三源 EG1 true / EG2 false / EG3 true，Fano/零重叠有效，2M FULL_DISCLOSURE，V58阻断。

- 判定：V57_CHANNEL_RECHARACTERIZATION_RESULT_ACCEPTED_FAIL / PREDICTIVE_MODEL_NOT_STABLE — 不扩λ网格，不判EVIDENCE_INVALID，不允decoder TEST，DECODE_FORBIDDEN。
- 科学结论：新session非不可编码，但当前1024态 hierarchical在131k平滑下不稳定（Cal self NLL 4.6-5.5 vs Cal-fold/Val NLL 8-10，λ三源均选上界10）。1p5M接近完整公开U1（raw_m1=1024 capped m1=1024），2M需完整公开U1（raw_m1=1123→1024 capped FULL_DISCLOSURE_LAYER True，m_total=1540 leak=7764 f_eff 1.23），1M m1=981/m2=424 total 1405。
- 边界：V55 90永久禁用，V25 184/190/192废弃，前版8192 MLE保留为negative control，链式|H-H1-H2|<1e-9，per-layer m1=min1024 ceil(1.3*1024*H1/5) dual-gate m1≤1024&&m2≤1024。
- 下一步止损：停在ACCEPTED_FAIL，V58仍PENDING；先算密钥余量（key remainder / SKR budget with leak 7089/7439/7764）再决定V58是否值得，不直接进入decoder TEST。

R5 head即implementation SHA，已固化。
