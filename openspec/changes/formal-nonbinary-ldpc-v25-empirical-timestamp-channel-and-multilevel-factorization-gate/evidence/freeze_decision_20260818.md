# V25 Freeze Decision (main thread, 2026-08-18) → P102 ACCEPT

## 主线程决策
1. 接受经验规律：三个 Type2 source 中错误几乎全部为 {−1, 0, +1} 相邻 bin 偏移。
2. 偏移方向随 source / delay_used_ps（−50 / +50 / +50）变化 → 视为需要建模的
   source/delay-conditioned channel，**不是 V25 的 alignment blocker**。
3. V25 **不重新读取 .ttbin、不重新估计亚 bin delay**。
4. M4 不选唯一方案：返回 **高域候选 GF(512)/GF(256)** + **中域对照 GF(32)/GF(16)/GF(8)**
   供 V26 分别做小规模 channel-informed DE。
5. 仍禁止：有限码、FER、MET、fresh qualification、公开 residual、Alice-oracle、push。

## 五项 minor spec edits
1. 持久化 P0 inventory → `evidence/data_inventory.json`（本文件旁）。
2. 补齐 frame/symbol/tail 数 → design §6 冻结计表（1M/1p5M/2M）。
3. 冻结 N_ab[a,b]=count(A=a,B=b) 与 P(A|B) 方向 → design §2 / spec R-CHANNEL。
4. 冻结 F01–F05 在 natural/Gray 10-bit label 上按 MSB→LSB 切分 → design §4 / spec
   R-FROZEN-SPACE。
5. M2 改为既有 delay 配置下的 ±1 结构/方向/时间稳定性分析 → design §7 / spec
   R-DELAY。

## Result
P102 = ACCEPT。M0–M4 实现已授权。
