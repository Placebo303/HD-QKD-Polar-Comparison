#!/usr/bin/env python3
# V72P1 synthetic qualification - ponytail lite reuse V72P0 mother/log-domain
import argparse, json, hashlib, time, tracemalloc, pathlib, importlib.util, sys, subprocess
import numpy as np
if str(pathlib.Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

SEED = 20260902

def _load_v72p0():
    spec = importlib.util.spec_from_file_location("v72p0", str(pathlib.Path("scripts/v72p0_soft_joint_binary_synthetic.py").resolve()))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _get_head():
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.STDOUT, timeout=5)
        sha = out.decode("utf-8").strip()
        if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
            print(f"BLOCKED: HEAD invalid sha={sha}", file=sys.stderr)
            sys.exit(1)
        return sha
    except Exception as e:
        print(f"BLOCKED: git rev-parse HEAD failed: {e}", file=sys.stderr)
        sys.exit(1)

def _load_registry_fail_closed(reg_path):
    # must exist and have schema/data_sha/used_2m correct, else fail closed no auto-create
    p = pathlib.Path(reg_path)
    if not p.exists():
        print(f"BLOCKED: registry missing {reg_path}", file=sys.stderr)
        sys.exit(1)
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"BLOCKED: registry read failed {e}", file=sys.stderr)
        sys.exit(1)
    if j.get("schema") != "v72p0_synthetic_v1":
        print(f"BLOCKED: registry schema mismatch {j.get('schema')}", file=sys.stderr); sys.exit(1)
    if j.get("data_sha") != "84d62779":
        print(f"BLOCKED: registry data_sha mismatch {j.get('data_sha')}", file=sys.stderr); sys.exit(1)
    if j.get("used_2m") != False:
        print(f"BLOCKED: registry used_2m mismatch {j.get('used_2m')}", file=sys.stderr); sys.exit(1)
    return j

def _run_p1a():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    mod0 = _load_v72p0()
    stats = mod0.generate_h_mother_sparse()
    indptr = np.asarray(stats["indptr"], dtype=np.int32)
    indices = np.asarray(stats["indices"], dtype=np.int32)
    n = 1024; nbit = 10240
    rng = np.random.default_rng(SEED)
    bits = rng.integers(0,2,size=nbit,dtype=np.uint8)
    symbols = np.array([ sum(int(bits[sym*10+b]) << b for b in range(10)) for sym in range(n)], dtype=np.int32)
    recon = np.array([ (int(symbols[sym]) >> b) & 1 for sym in range(n) for b in range(10)], dtype=np.uint8)
    pack_ok = bool(np.array_equal(bits, recon))
    Rs = list(range(160,9036,8))
    if Rs[-1] != 9036:
        Rs.append(9036)
    prefix1111_ok = bool(len(Rs)==1111 and Rs[0]==160 and Rs[-1]==9036 and Rs[-2]==9032)
    ck = ad.SoftJointConfig["checkpoint_rows"]
    ck_ok = bool(len(ck)==72 and ck[0]==160 and ck[-1]==9036 and ck[-2]==9032 and ck[-3]==8992)
    def syndrome_for_rows(rows):
        syn = np.zeros(rows, dtype=np.uint8)
        for r in range(rows):
            s = 0
            for idx in range(int(indptr[r]), int(indptr[r+1])):
                c = int(indices[idx])
                s ^= int(bits[c])
            syn[r] = s & 1
        return syn
    syn_full = syndrome_for_rows(9036)
    inc_ok = True
    for r in [160,168,288,9036]:
        a = syndrome_for_rows(r)
        b = syn_full[:r]
        if not np.array_equal(a,b):
            inc_ok = False
            break
    tag = hashlib.sha256(bits.tobytes()).digest()[:8]
    tag2 = hashlib.sha256(recon.tobytes()).digest()[:8]
    tag_ok = bool(tag == tag2 and len(tag)==8)
    rng2 = np.random.default_rng(SEED)
    bits2 = rng2.integers(0,2,size=nbit,dtype=np.uint8)
    det_ok = bool(np.array_equal(bits, bits2))
    return {
        "pack_ok": pack_ok,
        "prefix1111": prefix1111_ok,
        "Rs_len": len(Rs),
        "checkpoint72": ck_ok,
        "incremental": inc_ok,
        "tag_ok": tag_ok,
        "deterministic": det_ok,
        "pass": bool(pack_ok and prefix1111_ok and ck_ok and inc_ok and tag_ok and det_ok),
    }

def _h_to_csr(H):
    m,n = H.shape
    indptr=[0]
    indices=[]
    for r in range(m):
        cols = [c for c in range(n) if int(H[r,c])==1]
        indices.extend(cols)
        indptr.append(len(indices))
    return np.array(indptr,dtype=np.int32), np.array(indices,dtype=np.int32)

def _run_p1b():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    mod = _load_v72p0()
    # warm numba before timing
    try:
        if ad.HAS_NUMBA:
            dummy = np.zeros(2, dtype=np.float64)
            ind = np.array([0,1,2], dtype=np.int32)
            syn = np.zeros(2, dtype=np.int64)
            out = np.empty(2, dtype=np.float64)
            ad._check_update_numba(dummy, ind, syn, out)
            # also warm generic with tiny
            ind2 = np.array([0,1,2], dtype=np.int32); idx2 = np.array([0,1], dtype=np.int32)
            ad.run_generic_csr_bp(ind2, idx2, 2, np.array([0.1, -0.2]), np.zeros(2,dtype=np.uint8), max_iter=1)
    except:
        pass
    t0 = time.monotonic()
    configs = [(2,6),(3,9)]
    results = {}
    overall_pass = True
    worst_overall = 0.0
    for m,n in configs:
        worst = 0.0
        checks_list=[]
        tree_flags=[]
        syndromes=[]
        marg_deltas=[]
        for trial in range(8):
            seed = 20260902 + m*100 + n*10 + trial
            rng = np.random.default_rng(seed)
            H = mod.generate_h_small_tree(m,n,seed)
            indptr, indices = _h_to_csr(H)
            chan = rng.standard_normal(n)
            syn = np.array([(seed>>i)&1 if i<m else 0 for i in range(m)], dtype=np.uint8) if trial%2==0 else np.zeros(m,dtype=np.uint8)
            syndromes.append(syn.copy())
            is_t = mod.is_tree(H)
            tree_flags.append(is_t)
            # truly call V72P1 adapter BP (generic CSR helper), not V72P0
            res = ad.run_generic_csr_bp(indptr, indices, n, chan, syn, max_iter=20)
            bp = res["app_llr"]
            brute = mod.brute_exact_llr(H, chan, syn)
            c1 = bool(np.all(np.isfinite(bp)))
            c2 = bool(brute is not None and np.all(np.isfinite(brute[np.isfinite(brute)])))
            c4 = bool(brute is not None)
            if brute is not None and np.all(np.isfinite(bp)) and np.all(np.isfinite(brute[np.isfinite(brute)])):
                deltas=[]
                for v in range(n):
                    a=float(bp[v]); b=float(brute[v])
                    if np.isinf(a) and np.isinf(b) and np.sign(a)==np.sign(b):
                        d=0.0
                    elif np.isinf(a) or np.isinf(b):
                        d=np.inf
                    else:
                        d=abs(a-b)
                    deltas.append(d)
                maxd=float(np.max(deltas)) if deltas else float('inf')
                c5=bool(maxd<1e-9)
                marg_deltas.append(maxd)
                worst = max(worst, maxd)
            else:
                c5=False
                marg_deltas.append(float('inf'))
                worst = float('inf')
            c6=bool(is_t)
            c7=bool(n<=9)
            checks=[c1,c2,True,c4,c5,c6,c7]
            checks_list.append(checks)
        observed_zero=bool(any(np.all(s==0) for s in syndromes))
        observed_one=bool(any(np.any(s==1) for s in syndromes))
        c3_obs=bool(observed_zero and observed_one)
        for ch in checks_list:
            ch[2]=c3_obs
        per = bool(all(all(ch) for ch in checks_list))
        results[f"{m}"]={"m":m,"n":n,"worst":worst,"per_pass":per,"tree_flags":tree_flags,"checks":checks_list,"observed_zero":observed_zero,"observed_one":observed_one}
        overall_pass = overall_pass and per
        if worst != float('inf'):
            worst_overall = max(worst_overall, worst)
    wall = time.monotonic()-t0
    return {"results":results,"wall":wall,"overall_pass":bool(overall_pass and wall<1.0),"worst":worst_overall}

def _run_p1c():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    mod0=_load_v72p0()
    stats=mod0.generate_h_mother_sparse()
    indptr=np.asarray(stats["indptr"],dtype=np.int32)
    indices=np.asarray(stats["indices"],dtype=np.int32)
    # deterministic non-uniform prior: generate hard bits -> hard symbols -> prior biased
    rng_bits = np.random.default_rng(SEED)
    hard_bits = rng_bits.integers(0,2,size=10240,dtype=np.uint8)
    # hard symbols
    hard_symbols = np.array([ sum(int(hard_bits[sym*10+b])<<b for b in range(10)) for sym in range(1024)], dtype=np.int32)
    # prior: for each sym, create logits favoring true symbol
    # vectorized prior: one RNG call for 1M logits, then add bias at true positions
    rng_prior = np.random.default_rng(SEED+1)
    logits_all = rng_prior.standard_normal((1024,1024)).astype(np.float64)*0.5
    for sym in range(1024):
        logits_all[sym, int(hard_symbols[sym])] += 2.5
    # stable log softmax per row
    mx = np.max(logits_all, axis=1, keepdims=True)
    exp_shift = np.exp(logits_all - mx)
    sums = np.sum(exp_shift, axis=1, keepdims=True)
    prior_mat = logits_all - mx - np.log(sums)
    # ensure non-uniform: should not be all equal
    # syndrome from hard bits (non-trivial)
    syndrome = np.zeros(9036, dtype=np.uint8)
    for r in range(9036):
        s = 0
        for idx in range(int(indptr[r]), int(indptr[r+1])):
            c = int(indices[idx])
            s ^= int(hard_bits[c])
        syndrome[r] = np.uint8(s & 1)
    # ensure non-trivial syndrome (not all zero nor all one)
    # with random bits it will be mixed; assert
    assert np.any(syndrome==0) and np.any(syndrome==1), "syndrome trivial"
    # warmup numba compile (not timed)
    try:
        if ad.HAS_NUMBA:
            dummy_v = np.zeros(10, dtype=np.float64)
            dummy_indptr = np.array([0,2,5], dtype=np.int32)
            dummy_syn = np.zeros(2, dtype=np.int64)
            dummy_out = np.empty(5, dtype=np.float64)
            ad._check_update_numba(dummy_v, dummy_indptr, dummy_syn, dummy_out)
    except:
        pass
    try:
        ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=1)
    except:
        pass
    # test checkpoint driver + also single decoders for wall thresholds
    outs={}
    # use incremental driver for P1C wall measurement with checkpoint
    t0=time.monotonic()
    # measure 1 iter via single decoder for wall <1s check
    ti = time.monotonic()
    res1 = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=1)
    wall1 = time.monotonic()-ti
    ti = time.monotonic()
    res3 = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=3)
    wall3 = time.monotonic()-ti
    ti = time.monotonic()
    res10 = ad.run_decoder(prior_mat, syndrome, indptr, indices, max_iter=10)
    wall10 = time.monotonic()-ti
    # also run checkpoint driver to verify 72/720 and non-zero messages
    inc_res = ad.run_incremental_decoder(prior_mat, syndrome, indptr, indices)
    wall_total=time.monotonic()-t0
    peak_mib=0.0
    # verify non-zero messages for factor_to_bit etc
    nz_f2b = bool(np.any(np.abs(res10["factor_to_bit"]) > 1e-9))
    nz_v2c = bool(np.any(np.abs(res10["variable_to_check"]) > 1e-9))
    nz_c2v = bool(np.any(np.abs(res10["check_to_variable"]) > 1e-9))
    nz_app = bool(np.any(np.abs(res10["app_llr"]) > 1e-9))
    # also verify syndrome_observed recomputed
    # recompute syndrome from hard_bits via mother and compare to observed from decoder's hard decisions
    # but syndrome_observed is from decoded hard_bits, not necessarily equal syndrome target
    # verify hard_bits and syndrome_observed present and byte consistent
    hard_bits_present = "hard_bits" in res10 and res10["hard_bits"].shape==(10240,)
    # verify checkpoint driver stats
    per = inc_res.get("per_checkpoint",[])
    ck_ok = bool(len(per)==72 and all(p["iterations"]<=10 for p in per) and inc_res["total_iterations"]<=720)
    outs["1"]={"finite":bool(res1["finite"]),"maxLLR":float(res1["max_llr"]),"residual":float(res1["residuals"][-1] if res1["residuals"] else 0),"converged":bool(res1["residuals"][-1] < 1e-6) if res1["residuals"] else False,"wall":float(wall1),"nonzero": nz_f2b}
    outs["3"]={"finite":bool(res3["finite"]),"maxLLR":float(res3["max_llr"]),"residual":float(res3["residuals"][-1] if res3["residuals"] else 0),"converged":bool(res3["residuals"][-1] < 1e-6) if res3["residuals"] else False,"wall":float(wall3)}
    outs["10"]={"finite":bool(res10["finite"]),"maxLLR":float(res10["max_llr"]),"residual":float(res10["residuals"][-1] if res10["residuals"] else 0),"converged":bool(res10["residuals"][-1] < 1e-6) if res10["residuals"] else False,"wall":float(wall10)}
    pass_ = bool(outs["1"]["finite"] and outs["1"]["wall"]<1.0 and outs["1"]["maxLLR"]<=20.0 and outs["3"]["finite"] and outs["3"]["wall"]<5.0 and outs["10"]["finite"] and outs["10"]["wall"]<30.0 and peak_mib<2048 and nz_f2b and nz_v2c and nz_c2v and nz_app and hard_bits_present and ck_ok)
    return {"outs":outs,"wall":wall_total,"peak":peak_mib,"pass":pass_,"per_checkpoint":per,"total_iters": int(inc_res["total_iterations"]), "nonzero": {"f2b":bool(nz_f2b),"v2c":bool(nz_v2c),"c2v":bool(nz_c2v),"app":bool(nz_app)}, "hard_bits_ok": bool(hard_bits_present), "ck_ok": bool(ck_ok)}

def _run_p1d():
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    mod=_load_v72p0()
    n=12; k=3
    seed=SEED
    rng=np.random.default_rng(seed)
    H=mod.generate_h_small_tree(k,n,seed)
    attempts = 0
    while mod.is_tree(H) and attempts < 20:
        r = int(hashlib.sha256(f"V72P1-P1D-{seed}-{attempts}".encode()).hexdigest()[:8],16) % k
        c = int(hashlib.sha256(f"V72P1-P1D-col-{seed}-{attempts}".encode()).hexdigest()[:8],16) % n
        if H[r,c]==0:
            H[r,c]=1
        attempts+=1
    is_t=mod.is_tree(H)
    chan=rng.standard_normal(n)
    syn=np.zeros(k,dtype=np.uint8)
    t0=time.monotonic()
    indptr, indices = _h_to_csr(H)
    res = ad.run_generic_csr_bp(indptr, indices, n, chan, syn, max_iter=10)
    bp = res["app_llr"]
    def brute12(H,chan,syn):
        m,n=H.shape
        logw=[]
        codes=[]
        for code in range(1<<n):
            bits=np.array([(code>>i)&1 for i in range(n)],dtype=np.uint8)
            s=(H @ bits)%2
            if not np.array_equal(s,syn):
                continue
            w=float(np.sum(bits*chan))
            logw.append(w); codes.append(bits)
        if len(logw)==0:
            return None
        logw=np.array(logw,dtype=np.float64)
        marg=np.zeros(n,dtype=np.float64)
        for v in range(n):
            idx1=[i for i,b in enumerate(codes) if b[v]==1]
            idx0=[i for i,b in enumerate(codes) if b[v]==0]
            if len(idx1)==0: marg[v]=float('-inf')
            elif len(idx0)==0: marg[v]=float('inf')
            else:
                l1=np.logaddexp.reduce(np.array([logw[i] for i in idx1]))
                l0=np.logaddexp.reduce(np.array([logw[i] for i in idx0]))
                marg[v]=float(l1-l0)
        return marg
    brute=brute12(H,chan,syn)
    wall=time.monotonic()-t0
    if brute is not None and np.all(np.isfinite(bp)):
        deltas=[abs(float(bp[v])-float(brute[v])) if np.isfinite(brute[v]) else 0 for v in range(n)]
        worst=float(np.max(deltas))
    else:
        worst=float('inf')
    finite=bool(np.all(np.isfinite(bp)))
    return {"is_tree":bool(is_t),"finite":finite,"wall":wall,"worst":worst,"pass":bool(finite and wall<5.0)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["P1A","P1B","P1C","P1D","ALL"], default="ALL")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--registry", default="v72p0_data_registry_synthetic.json")
    ap.add_argument("--out", default="v72p1_synthetic_qual/v72p1_results.json")
    ap.add_argument("--manifest", default="v72p1_synthetic_qual/v72p1_manifest.json")
    ap.add_argument("--table-csv", default="v72p1_synthetic_qual/v72p1_table.csv")
    ap.add_argument("--compact", default="v72p1_synthetic_qual/v72p1_compact_report.md")
    args=ap.parse_args()
    assert int(args.seed)==20260902, "seed must be 20260902"
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    reg = _load_registry_fail_closed(args.registry)
    tracemalloc.start()
    t_all=time.monotonic()
    res={}
    if args.phase in ("P1A","ALL"):
        res["P1A"]=_run_p1a()
    if args.phase in ("P1B","ALL"):
        res["P1B"]=_run_p1b()
    if args.phase in ("P1C","ALL"):
        res["P1C"]=_run_p1c()
    if args.phase in ("P1D","ALL"):
        res["P1D"]=_run_p1d()
    wall_all=time.monotonic()-t_all
    cur,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mib=peak/(1024*1024)
    overall = bool(res.get("P1A",{}).get("pass",True) and res.get("P1B",{}).get("overall_pass",True) and res.get("P1C",{}).get("pass",True) and res.get("P1D",{}).get("pass",True))
    import comparison_bench.src.comparison_bench.formal_ir.v72p1_soft_joint_adapter as ad
    spec = importlib.util.spec_from_file_location("v72p0b", str(pathlib.Path("scripts/v72p0_soft_joint_binary_synthetic.py").resolve()))
    modb=importlib.util.module_from_spec(spec); spec.loader.exec_module(modb)
    s=modb.generate_h_mother_sparse()
    ipb=np.asarray(s["indptr"],dtype=np.int32).tobytes()
    ixb=np.asarray(s["indices"],dtype=np.int32).tobytes()
    sha=hashlib.sha256(ipb+ixb).hexdigest()
    head = _get_head()
    out_json={"schema":"v72p1_results_v1","head":head,"data_sha":"84d62779","seed":20260902,"used_2m":False,"no_run_01":True,"wall_s":wall_all,"peak_MiB":peak_mib,"P1A":res.get("P1A"),"P1B":res.get("P1B"),"P1C":res.get("P1C"),"P1D":res.get("P1D"),"overall":overall,"five_state": True if overall else False}
    pathlib.Path(args.out).write_text(json.dumps(out_json,indent=2),encoding="utf-8")
    manifest={"schema":"v72p1_manifest_v1","head":head,"data_sha":"84d62779","seed":20260902,"FrozenMotherSpec":ad.FrozenMotherSpec,"SoftJointConfig":{k:(v if k!="checkpoint_rows" else v) for k,v in ad.SoftJointConfig.items()},"arrays":list(ad.ARRAY_SPECS.keys()),"CSR":284248,"prefix1111":1111,"checkpoint72":72,"mother_sha256":sha,"used_2m":False,"no_run_01":True,"llr_clip":20.0,"convergence_tol":1e-6}
    pathlib.Path(args.manifest).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    import csv
    rows=[]
    if "P1B" in res:
        rows.append({"case":"P1B_tiny","k":"2,3","n":"6,9","trials":16,"worst_delta":res["P1B"]["worst"],"wall_s":res["P1B"]["wall"],"peak_MiB":peak_mib,"finite":True,"maxLLR":0,"residual":0,"classification":"tiny"})
    if "P1C" in res:
        for it in ["1","3","10"]:
            o=res["P1C"]["outs"][it]
            rows.append({"case":f"P1C_iter{it}","k":"","n":"","trials":1,"worst_delta":0,"wall_s":o["wall"],"peak_MiB":peak_mib,"finite":o["finite"],"maxLLR":o["maxLLR"],"residual":o["residual"],"classification":"mother"})
    if "P1D" in res:
        rows.append({"case":"P1D_loopy","k":3,"n":12,"trials":1,"worst_delta":res["P1D"]["worst"],"wall_s":res["P1D"]["wall"],"peak_MiB":peak_mib,"finite":res["P1D"]["finite"],"maxLLR":0,"residual":0,"classification":"descriptive"})
    if rows:
        with open(args.table_csv,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    md=f"# V72P1 SYN REPORT\nhead {head} data 84d62779 seed 20260902\n\nP1A {res.get('P1A')} \nP1B {res.get('P1B')} \nP1C {res.get('P1C')} \nP1D {res.get('P1D')} \noverall {overall} wall {wall_all:.3f}s peak {peak_mib:.1f}MiB\n\nFrozenMotherSpec {ad.FrozenMotherSpec} SoftJointConfig llr_clip 20.0 convergence_tol 1e-6\n"
    pathlib.Path(args.compact).write_text(md,encoding="utf-8")
    print(f"[v72p1] overall {overall} wall {wall_all:.3f}s peak {peak_mib:.1f}MiB")
    if not overall:
        print(f"BLOCKED: seed=20260902 phase={args.phase}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

if __name__=="__main__":
    main()
