# G-M2-ACCT-CORRECTION — T2 independent recomputation check (DECIDE, read-only)

- 日期: 2026-09-27 · 任务: `tasks.md` T2，验收 AC-3 · 执行者: 独立线程（未撰写 T1）
- 授权: `CORRECTION_PREREG_AND_AUTH.md` §1 grant + §9.1 main T0 接受（该门同时覆盖 T1→T2→T3）
- 受审记录: `docs/research_cycles/M2-REALCOMP/CORRECTION_RESULT.md`（由另一线程撰写，本任务未编辑）

**AC-3 裁决: PASS。** A–F 全部核验，无不符，未触发任何 stop rule，无输入漂移。

## 0. 方法与边界

- 解释器仅用仓内 venv `.venv/bin/python`；全部脚本经 stdin heredoc 传入，**未创建任何暂存文件**（`workspace/` 下无 t2 产物）。
- 脚本仅 import `json`（个别用 `math`），**不 import 任何译码 / 构造 / 信道模块**；未开任何 `.ttbin` 或 bundle。
- `CORRECTION_RESULT.md`、prereg、`diagnostic.json`、三份 `rows.json`、`docs/` 下任何文件均未修改（`git status --porcelain -- docs/research_cycles/M2-REALCOMP/` 仅 `??` 未跟踪目录；`git diff --stat -- src/ experiments/ tools/` 为空）。
- RSS 处理: 逐个加载一份 `rows.json`（14–26 MB），加载下一份前释放，远低于 2 GiB 帽。单进程，数秒 wall。

## A. 输入完整性 — PASS

五项冻结输入对 §2 表与 replay Pre-EXECUTE 记录（`TZ=UTC stat` 复测）全部吻合:

| 输入 | 字节 | mtime (UTC) |
|---|---|---|
| `workspace/m2real_d4e5f6a7/rows.json` | 14,042,522 | 2026-09-25 16:13:17.826477200 +0000 |
| `workspace/m2real_b8c9d0e1/rows.json` | 19,734,691 | 2026-09-25 16:25:17.810531000 +0000 |
| `workspace/m2real_f2a3b4c5/rows.json` | 26,471,294 | 2026-09-25 16:39:46.585827700 +0000 |
| `workspace/m2_accounting_replay_20260926/diagnostic.json` | 10,664 | 2026-09-25 17:21:33.366234000 +0000 |
| `workspace/m2_accounting_replay_20260926/resource.txt` | 916 | 2026-09-25 17:21:33.498898900 +0000 |

分支 `formal-ir-v72p1-addendum-clean`、HEAD `ce85d61f5f625a323765481cb726f77e0380b86a` 与 T0 门一致。无漂移。

## B. 逐源分母 — PASS

`H_corr` 自各 `rows.json` summary 取得，与 prereg §3 及 `diagnostic.json` 源行**精确相等**（非近似）: 1M `0.8012690084416184`、1p5M `0.8272902027770036`、2M `0.8333327179427281`。

`D = superframes_done · 1024 · H`:

| 源 | superframes | D (bit) |
|---|---:|---|
| 1M | 205 | 168,202.39025206454 |
| 1p5M | 287 | 243,130.66311372805 |
| 2M | 383 | 326,826.42531539442 |

全部 `D > 0`。各臂 `leak_EC` / `tag` 取自 `rows.json` `summary.arms[].lambda_parts`，与 `diagnostic.json` 臂行一致；`lambda_total == E + T` 在全部 12 臂成立（例: 1M-hdc-m197 `1707485 + 209920 = 1917405 = lambda_total`）。

## C. 12 个 (source, family, m) 恒等式 — PASS（12/12，全精度 `==`）

自持久化 summary 值（`E = lambda_parts.leak_EC`、`T = lambda_parts.tag`、`sf`、`bd`、`H`）重算，与 `diagnostic.json` 及记录 C-1/C-2 以 Python `==` 比对（repr 完全相同，即**逐位精确**，非四舍五入）:

| 臂 | D | E | T_rec = 64·bd == T | f_ec_actual | f_with_recorded_tags | one-tag CF | f_notag / f_super | 判定 |
|---|---|---:|---:|---|---|---|---|---|
| 1M hdc 197 | 168202.39025206454 | 1707485 | 209920 ✓ | 10.1513717934757 | 11.399392108082516 | 10.229373063138626 | 1.2004882909059704 / 1.2784895605688964 | PASS |
| 1M lb 197 | 同上 | 646160 | 209920 ✓ | 3.8415625308991053 | 5.089582845505921 | 3.919563800562031 | 同上 | PASS |
| 1M hdc 201 | 同上 | 1707681 | 209920 ✓ | 10.152537056345665 | 11.40055737095248 | 10.23053832600859 | 1.2248636876756347 / 1.3028649573385607 | PASS |
| 1M lb 201 | 同上 | 659280 | 209920 ✓ | 3.919563800562031 | 5.167584115168847 | 3.997565070224957 | 同上 | PASS |
| 1p5M hdc 203 | 243130.66311372805 | 2402144 | 293888 ✓ | 9.88005366841105 | 11.088819342950956 | 9.955601523069793 | 1.1981417574785196 / 1.2736896121372638 | PASS |
| 1p5M lb 203 | 同上 | 932176 | 293888 ✓ | 3.8340536239312626 | 5.042819298471168 | 3.9096014785900066 | 同上 | PASS |
| 1p5M hdc 207 | 同上 | 2401719 | 293888 ✓ | 9.87830563714853 | 11.087071311688435 | 9.953853491807275 | 1.221750462059377 / 1.2972983167181213 | PASS |
| 1p5M lb 207 | 同上 | 950544 | 293888 ✓ | 3.9096014785900066 | 5.118367153129912 | 3.9851493332487506 | 同上 | PASS |
| 2M hdc 204 | 326826.42531539442 | 3205668 | 392192 ✓ | 9.808472484764543 | 11.00847337092767 | 9.883472540149738 | 1.1953133827015512 / 1.2703134380867467 | PASS |
| 2M lb 204 | 同上 | 1250112 | 392192 ✓ | 3.825002824644964 | 5.02500371080809 | 3.900002880030159 | 同上 | PASS |
| 2M hdc 208 | 同上 | 3205151 | 392192 ✓ | 9.806890605332667 | 11.006891491495793 | 9.881890660717863 | 1.2187509000094248 / 1.29375095539462 | PASS |
| 2M lb 208 | 同上 | 1274624 | 392192 ✓ | 3.900002880030159 | 5.100003766193285 | 3.975002935415355 | 同上 | PASS |

`fer_blocks`、`sf_success` / `sf_total`、`blocks_done`、`superframes_done` 亦在 `rows.json` ↔ `diagnostic.json` ↔ 记录三者间全精度相等。`round(full, 6)` 可复现 `ACCOUNTING_REPLAY_RESULT.md` 每一个显示格（36/36）。**零不符。**

## D. 结构恒等式 — PASS（12/12）

- `blocks_done = 16 · superframes_done`: 3280 = 16·205; 4592 = 16·287; 6128 = 16·383。
- `tag = 64 · blocks_done`: 209920 = 64·3280; 293888 = 64·4592; 392192 = 64·6128。等价于每 1024 符号超帧 1024 tag bit（各臂 `T/(64·sf) = 16.0`，独立重算一致）。
- `lambda_total = E + T` 逐臂成立（见 B）。

## E. 1M / m=197 差异复现 — PASS，六个数全部复现

`D = 168202.39025206454`。`f_notag = 5·197 / (1024·0.8012690084416184) = 985/820.49946464422 = 1.2004882909059704`（两族相同，记录 §8 line 181–182 精确）。

`f_ec hdc = 1707485/D = 10.1513717934757004` → 记录 10.15137。`f_ec lb = 646160/D = 3.8415625308991053` → 3.84156。
`f_with hdc = 1917405/D = 11.3993921080825160` → 11.39939。`f_with lb = 856080/D = 5.0895828455059213` → 5.08958。
one-tag: `(1707485+13120)/D = 10.229373063138626`；`(646160+13120)/D = 3.919563800562031`。

### E-1. 跨族显示相等是**机械强制**的: 是

`f_notag = 5m/(1024·H)` 与 `f_super = (5m+64)/(1024·H)` 只取 `(m, H)` —— 公式内**不存在 `E`、`T` 或任何族相关项**。故同 `m` 下 HDC 与 LB 必然相等，**与两者实际泄漏多少无关**。已在两族的 `rows.json` 臂与 `diagnostic.json` 标签中逐 m 验证相同。

> 这是比原裁决「实际公开量与显示 f 不符」更锋利的表述: 显示 f 根本不包含泄漏项，因此它**在结构上无法区分方法**——无论实际发生了什么。

## F. 范围守卫 — PASS，无违规

对 `CORRECTION_RESULT.md` 全文 grep + 逐行读取:

- 无 D2 分支评估或报告（§6 line 159–167: 「No D2 rule exists… Every D2 branch cell carries `retired-m2`」）。
- 无 HDC 对比列填充（§11 line 223 明示）。
- 无 LB 后端推断 — 6 个 LB 行全为 `UNKNOWN (not recorded at execution; not inferable post hoc)`，状态 `unknown`（line 117–127, §9）。
- 无 `f_eff` 当方法效率 — C-1 全部 12 个 `f_eff` 修正格为 `not-defined`，原值标 `historical-nominal`（line 93–104, 107–109）。
- 无头条 tag 比 — §7 line 169–174: 「no column is designated the headline tag ratio」。
- 无 `undetected` 合并 — line 50–51, 79 及 C-2 隔离列。
- 6 个 HDC 行**均带两个 void 标签**: C-2 中 `void-no-correction`（E/T/f 列）与 `void-stub-artifact`（success/exact_match/FER/undetected），加 `assumed-v1` scope（line 116–127, §5, line 130 note）。

## 1M lb 巧合 — 真算术恒等式，非抄录错误

记录中 1M-lb-m201 的 `f_ec_actual = 3.919563800562031` 与 1M-lb-m197 的 one-tag 值相同。精确复现:

```
D(1M)          = 168202.39025206454
f_ec(lb,201)   = 659280 / D
f1(lb,197)     = (646160 + 64·205) / D = (646160 + 13120) / D = 659280 / D
```

`==` 为 True。机制: LB 泄漏在两个 m 之间**恰好增加了 one-tag 额度**（`659280 − 646160 = 13120 = 64·205`）。两个分子字面同为 659280、除以同一 D。**记录正确。**

## 后续门

AC-3 PASS。T3 独立 Pre-RESULT 审查与 T4 main 接受仍未进行；本文件不构成接受、不构成方法排名、不构成 SKR / 资格化 / 发表数字。
