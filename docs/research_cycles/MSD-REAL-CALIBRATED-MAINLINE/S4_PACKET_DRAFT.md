# S-4 EXPLORE packet — 只读调用隔壁low_dim_opt同数据对照（草案）

> Track: **EXPLORE**。授权：持续推进（S-4在内）。姊妹仓只读，不改其代码。
> 前置：S-1代理表已建（Tier表在`workspace/s1_proxy/s1_20261006/`）。

## 设计
用隔壁 `low_dim_opt.simulation.msd_eval`（按其README配置，不改代码）在S-1代理的
(1024,200) Tier表上跑；输出与MSD、NB同口径（完整符号，R11）的一行。
若其代码不支持d=1024：记录确切原因（import错误/维度断言/数据接口），改用其模块
（msd_conditional/scl核心）拼最小runner（≤100行，只做已验证调用）。

## 判定
S-4成功 = 同代理同口径对照行落定；同时检验S-2修法是否与隔壁做法同效
（差距在MDE内即同效）。
MDE沿用S-1（B=100 MSD / 60 NB）；上限定21600 s；禁动姊妹仓一字节。
