# C-1 只读盘点清单（未改文件、未跑解码、未读 D:/Data）

## 1. A1（两级/多级二元LDPC RA/PEG，利用结构）
- `comparison_bench/src/comparison_bench/formal_ir/msd_g5_bakeoff.py`：
  `_worker_init`、`_decode_one`、`run_real_main`、`main`；
  `ra_matrix_l`/`ra_matrix(q=5)`、`build_peg_code`；
  `TAG_BITS=64`、`B=300`、`RA_GAPS=(0.08,0.10,0.12)`、`PEG_GAPS=(0.15,)`、
  `MARGINS=(2.5,3.0)`；N候选 `(32768,16384)` + `--ns`。
- `comparison_bench/src/comparison_bench/formal_ir/msd_g2_twolevel.py`：
  同函数集；`NS=(16384,32768)`、`GAPS=(0.10,0.15)`、`MARGINS=(2.0,3.0)`。
- `comparison_bench/src/comparison_bench/formal_ir/msd_peg_code.py`：
  `PegConstruction`、`build_peg_code(*,n,m,variable_degree)`。
- `comparison_bench/src/comparison_bench/formal_ir/msd_sparse_code.py`：
  `SparseCodeConstruction`、`build_msd_sparse_code(*,n,m,information_degree,tie_offset)`，H=[A|T]。
- `comparison_bench/src/comparison_bench/formal_ir/msd_syndrome.py`：
  `disclose_syndromes`、`receive_syndromes`、`make_bp_decoder`；
  `SyndromeDisclosure.transmitted_row_count_bits_per_block`。
- `comparison_bench/src/comparison_bench/formal_ir/msd_conditional_prior.py`：
  `ConditionalPriorModel`、`build_conditional_prior_model`、`adapt_soft_error_prior`。
- LLR先验（利用结构）：`lik0=1−P`、`likp=P−PM_ABS`、`likm=PM_ABS`
 （P=0.2376，PM_ABS=0.00138）；`a_cand=[b−1,b,b+1]` 加权 `pa_l` 得 `p1`，
  level-A `LLR=log((1−p1)/p1)`；level-B `chb=where(marked,PM_COND,0)`。
- 记账 per-block：`{block,a_ok,exact_full,undetected,L_A,L_B,extra}`（K_A=400/K2=64 rescue）。

## 2. A2（两级/多级二元Polar SCL，利用结构）
- 同 `msd_g5_bakeoff.py` polar分支：`mask[info]=1`，公开 `u[F]`，
  `scl_decode_batch(...,L=8)`，`polar_encode`；L=8固定，无CRC；
  `POLAR_DISC=(0.85,0.88)` + `de_llr_populations(n_log,P,2048,1)` 选冻结集。
- L/CRC散件（G-5未启用）：`formal_ir/v19_ca_scl_wrapper.py:V19CA_SCLDecoder`（L=32 DLL）、
  `v19_polar_ga.py:ga_llr_means/ga_info_mask`、`v19_polar_crc.py:crc_check/choose_crc16/build_crc_info_bits`。
- sibling只读点：`msd_g5_bakeoff.py:SIBLING_ROOT=D:/Code/HD-QKD_Polar_Release`
  + `polar_core`/`de_frozen`；`msd_s4_sibling.py`（`diff_pmf`平滑LLR表）；
  `msd_d5_factorial.py`/`msd_e1_msdretune.py`（`msd_conditional as mc`）；
  `methods/polar_existing.py:PolarExistingMethod` + `io/polar_existing_bridge.py`。

## 3. A5（不利用结构二元分层/MLC LDPC，Zhou 2013式稠密差分先验）
- 部件：`cli/run_v19_binary_mlc_prototype.py:run_prototype`
 （`codebook_v4.matrix_for` + `codebook_v5_h2.generate_h2`，per-plane BSC独立译码）、
  `run_v19_channel_scoping.py`、`run_v19_three_way_compare.py`（LDPC-MLC f~4.17行）、
  `methods/layered_ldpc_lite.py`、`methods/layered_binary.py`、`methods/binary_spa_*`、
  `formal_ir/nonbinary_v18_b2_structured_de._V17_PER_PLANE_ERROR`。
- `Zhou`在src零实现命中（仅docs文献行）；`diff_pmf`仅 `msd_s4_sibling` + `msd_s2_prior.py`
 （`load_half_pairs`/`counts_from_pairs`/`ll_diffpmf`/`ll_gauss`/`ll_floored`，
  TRAIN halves held-out LL选型）。A1为3项ternary `P(x0|b)`；
  A5为per-plane BSC独立 + S-2稠密 `g(b−a)+bg` 候选。
- 缺口：无统一"Zhou2013稠密差分先验→分层LDPC"一键runner，需接入。

## 4. A6（不利用结构NB GF(32)超帧链，差分先验）
- `formal_ir/msd_m4_nbldpc.py:run_nb_point/summarize_nb`
 （N_SYM=1024，B=100，TAG64，frozen v28）；
  `formal_ir/msd_m4_nb_marginal.py:derive_bundle/run_arm`。
- `formal_ir/nonbinary_v26_channel.py:ChannelAdapter/build_adapter`、
  `nonbinary_v28.py`（frozen配置、两层经验译码、tag64/leakage_bits）、
  `nonbinary_field.GF2mField.create(32)`；
  `cli/p1_stage1_runner.py`、`s01_m200_runner.py`、`x1_bundle_build.py`/`x1_arm_runner.py`、
  `m0_realframe_runner.py:superframes(n=1024)`；v80系列campaign；
  `probes_closed/nbldpc_gf32_*`约30个 + `formal_ir/nbldpc_gf32_*`。
- 先验：R1-TRAIN counts→adapter/bundle（empirical）；超帧连续切分 remainder dropped；
  记账含 `L_EC`、`FER_exact`/wilson、`f_expected(+upper)`、`H_A/H_AB`、`tag_bits`。

## 5. A7（不利用结构MLC Polar，隔壁只读调用）——缺失
- `run_v19_three_way_compare._polar_row → {binary_polar_mlc, not_available}`，
  无bridge/调用点；散件仅 `v19_polar_ga`/`ca_scl_wrapper`/`crc` + docs称release repo只读。
- 缺口：需新建只读runner（sibling `low_dim_opt` 只读调用或最小拼装）+ evidence JSON对齐。

## 6. A3/A4空白确认 + k-bin最小接口
- grep `GF(3)`/`GF(5)`/`2k+1`/`Arıkan`在src零实现命中（仅GF(32)）。
- 最小接口：k=窗半宽bins，q=2k+1，S={−k..k}，分组{k=1}/{k=2}/{k≥3}；
  `e=(b−a) mod D`折叠到S_k，先验`g(e)`（≤2参+bg），似然向量长q；
  Z-2/C-0统计→`(q,H_q,理想披露N·H_q)`→C-3选码率；
  衔接 `msd_outcome_accounting.native_block_ledger/aggregate/compare` +
  `transmitted_row_count` + TAG64/undetected单列 + `f=(E_L+tag+kept·FER)/(N·H_AB)`；
  N候选`{1024..65536}`。

## 7. 统一记账现状 vs R16
- 已有：`{N,方法,margin,m_A/m_B,blocks,failures,undetected,E_L,FER_exact,wilson,
  f_expected(+upper),H_A/H_AB,tag_bits,backend,wall_s}` + per-block `{L_A,L_B,extra}`；
  `outcome_accounting`有disclosure/tag/kept/failure_penalty/Y/f。
- 缺：每段采集净密钥、每符合净kept（未按采集对数归一）、尾部浪费（仅报告remainder未进f）、
  段级泄漏/tag/惩罚求和、各自最优N表、相同译码时间f、β附带列。
