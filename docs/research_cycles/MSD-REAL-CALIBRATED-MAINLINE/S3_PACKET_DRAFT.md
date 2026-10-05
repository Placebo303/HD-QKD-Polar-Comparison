# S-3 EXPLORE packet — NB加u1层 + 完整符号口径（草案，可与S-2并行）

> Track: **EXPLORE**。授权：持续推进（S-3在内）。结果根：`workspace/s3_nbfull/`（待建）。

## 设计（二选一，探针定）
A. u1 平面加短二元 syndrome 码 + tag：H(U1|B)≈0.024 b/符号，约25 bit/超帧；
   u2 GF32面不动；成功=两层全对。
B. NB改造成「u1二元面 + u2 GF32面」MSD两级。

探针（N=1024合成，B=60，便宜）：A方案u1面码率阶梯（m1u ∈ {32,64,128} bits），
测u1面FER + 全符号f；若u1面在m1u=64仍FER>5%，转B。

## 口径（R11）
全量起所有臂一律完整符号计成功/FER/f；u2-layer只作诊断列，禁入比较表与结论句。
S-3产出：NB完整符号f（合成代理上）+ 与MSD同口径对照行。

## MDE/预算
u1面FER~1%在B=300（MSD侧用）/B=100（NB侧）下±60%/±30%；上限21600 s；逐块JSONL。
