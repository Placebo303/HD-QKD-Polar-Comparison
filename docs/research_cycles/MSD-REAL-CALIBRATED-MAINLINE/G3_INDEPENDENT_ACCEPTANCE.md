# G-3 INDEPENDENT ACCEPTANCE（主线程接受记录）

- Pre-RESULT 独立审查 **PASS**（复审确认 L_B 修正：块记录 L_B=1203/602，
  E_L 可由块重算，代码与产物一致；35 块全 exact，und 0；跳过有理由）。
- 主线程接受本 DECIDE 结果（ceiling 内）：两级二元在三段真实数据上 35/35
  成功，E_L 与代理一致，f=1.2275/1.23。
- 证据链：G3_PREEXECUTE.md → blocks_g3.jsonl（35 超帧逐块）→ g3_summary.json
  → G3_RESULT.md → 本接受记录。旧根 g3_20261007（L_B=0 缺陷版）superseded。
