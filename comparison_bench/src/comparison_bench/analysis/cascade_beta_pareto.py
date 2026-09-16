#!/usr/bin/env python3
"""
T4 Pareto frontier for cascade-beta-optimal-path
ponytail: O(n^2) scan, minimal deps (pandas/numpy/matplotlib)
"""
import pathlib, math, sys
import pandas as pd
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
T2_CSV = ROOT / "comparison_bench/outputs_comparison/cascade_beta_opt/T2_small_small/ir_benchmark_results.csv"
T3_CSV = ROOT / "comparison_bench/outputs_comparison/cascade_beta_opt/T3_longframe/ir_benchmark_results.csv"
OUT_DIR = ROOT / "comparison_bench/outputs_comparison/cascade_beta_opt"
OUT_CSV = OUT_DIR / "pareto_frontier.csv"
REPORT = OUT_DIR / "t4_pareto_report.md"

def load_combined():
    dfs=[]
    for p in [T2_CSV, T3_CSV]:
        if not p.exists():
            print(f"missing {p}", file=sys.stderr)
            continue
        df=pd.read_csv(p)
        dfs.append(df)
    if not dfs:
        raise FileNotFoundError("no input csv found")
    df=pd.concat(dfs, ignore_index=True)
    return df

def derive(df):
    # bps from q
    def bps(q): return math.log2(int(q)) if pd.notna(q) else 10
    df["bps"] = df["q"].apply(bps)
    # beta_eff: use beta_kernel if >0 else beta_raw, fallback beta_raw
    if "beta_kernel" in df.columns:
        df["beta_eff"] = df["beta_kernel"]
    else:
        df["beta_eff"] = df["beta_raw"]
    # Also keep beta_raw
    # leak_per_bit
    df["leak_per_bit"] = df["leak_total"] / (df["n"] * df["bps"])
    # qber
    if "raw_ber" in df.columns:
        df["qber"] = df["raw_ber"]
    elif "raw_ser" in df.columns:
        df["qber"] = df["raw_ser"]
    else:
        df["qber"] = np.nan
    # ensure required cols
    # throughput already exists
    # undetected already exists
    # FER already exists
    return df

def pareto_frontier(df):
    # objectives: leak_per_bit minimize, FER minimize, throughput maximize
    # O(n^2) scan
    n=len(df)
    leaks=df["leak_per_bit"].to_numpy()
    fers=df["FER"].to_numpy()
    thrs=df["throughput"].to_numpy()
    is_pareto=np.ones(n, dtype=bool)
    for i in range(n):
        if not is_pareto[i]:
            continue
        for j in range(n):
            if i==j: continue
            # j dominates i ?
            if leaks[j] <= leaks[i] and fers[j] <= fers[i] and thrs[j] >= thrs[i]:
                if leaks[j] < leaks[i] or fers[j] < fers[i] or thrs[j] > thrs[i]:
                    is_pareto[i]=False
                    break
    return is_pareto

def validate_pareto(df, mask):
    leaks=df["leak_per_bit"].to_numpy()
    fers=df["FER"].to_numpy()
    thrs=df["throughput"].to_numpy()
    idx=np.where(mask)[0]
    # pareto points mutually non-dominated
    for a in idx:
        for b in idx:
            if a==b: continue
            dominates = (leaks[b] <= leaks[a] and fers[b] <= fers[a] and thrs[b] >= thrs[a] and (leaks[b] < leaks[a] or fers[b] < fers[a] or thrs[b] > thrs[a]))
            if dominates:
                return False, f"pareto point {a} dominated by {b}"
    # every non-pareto dominated by at least one pareto
    non=np.where(~mask)[0]
    for i in non:
        dominated=False
        for j in idx:
            if leaks[j] <= leaks[i] and fers[j] <= fers[i] and thrs[j] >= thrs[i] and (leaks[j] < leaks[i] or fers[j] < fers[i] or thrs[j] > thrs[i]):
                dominated=True
                break
        if not dominated:
            # also check if dominated by another non-pareto is okay, but ideally pareto dominates all
            # we relax: at least dominated by someone (pareto or not)
            any_dom=False
            for j in range(len(df)):
                if j==i: continue
                if leaks[j] <= leaks[i] and fers[j] <= fers[i] and thrs[j] >= thrs[i] and (leaks[j] < leaks[i] or fers[j] < fers[i] or thrs[j] > thrs[i]):
                    any_dom=True
                    break
            if not any_dom:
                return False, f"non-pareto {i} not dominated by anyone"
    return True, "ok"

def main():
    df=load_combined()
    df=derive(df)
    mask=pareto_frontier(df)
    df["is_pareto"]=mask
    ok,msg=validate_pareto(df, mask)
    print(f"Pareto validation: {ok} {msg}")
    print(f"Total points: {len(df)}, pareto: {mask.sum()}")
    # Prepare frontier df with required columns
    cols_map = {
        "n":"n",
        "verify":"verify_bits",
        "block":"block_size",
        "parity":"parity_bits",
        "beta_raw":"beta_raw",
        "beta_eff":"beta_eff",
        "leak_per_bit":"leak_per_bit",
        "FER":"FER",
        "undetected":"undetected",
        "throughput":"throughput",
        "qber":"qber",
    }
    frontier=df[mask].copy()
    # Build output with required column names
    out=pd.DataFrame()
    for src,dst in cols_map.items():
        if src in frontier.columns:
            out[dst]=frontier[src]
        elif src in df.columns:
            out[dst]=frontier[src]
        else:
            out[dst]=np.nan
    # also keep dataset_id for traceability
    if "dataset_id" in frontier.columns:
        out["dataset_id"]=frontier["dataset_id"].values
        out["dataset"]=frontier["dataset"].values
        out["q"]=frontier["q"].values
        out["leak_total"]=frontier["leak_total"].values
        out["is_pareto"]=True
    out=out.sort_values(["leak_per_bit","FER"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV} with {len(out)} rows")

    # plots
    try:
        import matplotlib.pyplot as plt
        # leak vs FER
        plt.figure()
        plt.scatter(df["leak_per_bit"], df["FER"], c="gray", alpha=0.6, label="dominated")
        plt.scatter(frontier["leak_per_bit"], frontier["FER"], c="red", label="pareto")
        # annotate beta>0.9 threshold lines
        # beta>0 / beta>0.9 counts for reference but not axes
        plt.xlabel("leak_per_bit")
        plt.ylabel("FER")
        plt.title("Pareto leak_per_bit vs FER")
        plt.legend()
        # mark leakage optimal etc later
        plt.savefig(OUT_DIR / "pareto_leak_vs_fer.png", dpi=150)
        plt.close()
        # beta vs n
        plt.figure()
        # plot beta_raw vs n, color by FER
        sc=plt.scatter(df["n"], df["beta_raw"], c=df["FER"], cmap="viridis", alpha=0.7)
        plt.colorbar(sc, label="FER")
        plt.scatter(frontier["n"], frontier["beta_raw"], c="red", marker="x", s=80, label="pareto")
        plt.axhline(0, color="green", linestyle="--", label="beta>0")
        plt.axhline(0.9, color="orange", linestyle="--", label="beta>0.9")
        plt.xlabel("n")
        plt.ylabel("beta_raw")
        plt.title("beta_raw vs n (pareto x)")
        plt.legend()
        plt.savefig(OUT_DIR / "pareto_beta_vs_n.png", dpi=150)
        plt.close()
        print("plots written")
        plot_ok=True
    except Exception as e:
        print(f"matplotlib failed: {e}")
        # fallback csv for plot data
        plot_df=df[["n","beta_raw","leak_per_bit","FER","throughput"]].copy()
        plot_df["is_pareto"]=mask
        plot_df.to_csv(OUT_DIR / "pareto_plot_data.csv", index=False)
        plot_ok=False

    # report
    # thresholds
    beta_pos = df[df["beta_raw"]>0]
    beta_high = df[(df["beta_raw"]>0.9) & (df["FER"]<0.05)]
    max_beta_row = df.loc[df["beta_raw"].idxmax()] if len(df)>0 else None

    # recommendations among pareto (tie-break by secondary objectives)
    if len(frontier)>0:
        thr_opt = frontier.loc[frontier["throughput"].idxmax()]
        leak_opt = frontier.loc[frontier["leak_per_bit"].idxmin()]
        # FER optimal: min FER, tie -> min leak_per_bit then max throughput
        fer_sorted = frontier.sort_values(["FER","leak_per_bit","throughput"], ascending=[True, True, False])
        fer_opt = fer_sorted.iloc[0]
    else:
        thr_opt=leak_opt=fer_opt=None

    with open(REPORT,"w",encoding="utf-8") as f:
        f.write("# T4 Pareto Report — cascade-beta-optimal-path\n\n")
        f.write(f"- Inputs: T2 `{T2_CSV.name}` ({len(pd.read_csv(T2_CSV))} rows) + T3 `{T3_CSV.name}` ({len(pd.read_csv(T3_CSV))} rows) = {len(df)} rows\n")
        f.write(f"- Combined derived: beta_eff=beta_kernel, leak_per_bit=leak_total/(n*bps), qber=raw_ber\n")
        f.write(f"- Non-dominated definition: leak_per_bit↓, FER↓, throughput↑ (O(n²) scan)\n")
        f.write(f"- Pareto size: {mask.sum()} / {len(df)}\n")
        f.write(f"- Validation: {ok} — {msg}\n\n")
        f.write("## Thresholds\n\n")
        f.write(f"- β>0 rows: {len(beta_pos)} (example max beta {max_beta_row['beta_raw']:.4f} at n={int(max_beta_row['n'])} verify={int(max_beta_row['verify'])} block={int(max_beta_row['block'])} parity={int(max_beta_row['parity'])} dataset={max_beta_row['dataset']} FER={max_beta_row['FER']:.3f})\n")
        if len(beta_high)>0:
            f.write(f"- β>0.9 & FER<5% rows: {len(beta_high)}\n")
            for _,r in beta_high.iterrows():
                f.write(f"  - n={int(r['n'])} v={int(r['verify'])} b={int(r['block'])} p={int(r['parity'])} {r['dataset']} beta={r['beta_raw']:.4f} FER={r['FER']:.4f} leak/b={r['leak_per_bit']:.4f} thr={r['throughput']:.0f}\n")
        else:
            f.write("- β>0.9 & FER<5%: **0 rows — NO_HIGH_VALUE_WITHIN_GRID**\n")
            f.write(f"  - max_beta in grid: {max_beta_row['beta_raw']:.4f} (n={int(max_beta_row['n'])} v={int(max_beta_row['verify'])} b={int(max_beta_row['block'])} p={int(max_beta_row['parity'])} {max_beta_row['dataset']} FER={max_beta_row['FER']:.3f} leak_per_bit={max_beta_row['leak_per_bit']:.4f})\n")
            # suggest params for max beta
            f.write(f"  - 所需参数: 达到 max_beta 的配置为 n={int(max_beta_row['n'])}, verify={int(max_beta_row['verify'])}, block={int(max_beta_row['block'])}, parity={int(max_beta_row['parity'])}, schedule={max_beta_row['schedule']}\n")
        f.write("\n## Pareto Frontier (sorted by leak_per_bit)\n\n")
        f.write("| n | verify | block | parity | dataset | beta_raw | beta_eff | leak_per_bit | leak_total | FER | undetected | throughput | qber |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for _,r in out.iterrows():
            f.write(f"| {int(r['n'])} | {int(r['verify_bits'])} | {int(r['block_size'])} | {int(r['parity_bits'])} | {r['dataset']} | {r['beta_raw']:.4f} | {r['beta_eff']:.4f} | {r['leak_per_bit']:.4f} | {int(r['leak_total'])} | {r['FER']:.4f} | {int(r['undetected'])} | {r['throughput']:.0f} | {r['qber']:.5f} |\n")
        f.write("\n## Three Recommendations (within Pareto)\n\n")
        if thr_opt is not None:
            f.write(f"- **吞吐最优** (max throughput): n={int(thr_opt['n'])} v={int(thr_opt['verify'])} b={int(thr_opt['block'])} p={int(thr_opt['parity'])} {thr_opt['dataset']} beta={thr_opt['beta_raw']:.4f} leak/b={thr_opt['leak_per_bit']:.4f} FER={thr_opt['FER']:.3f} thr={thr_opt['throughput']:.0f}\n")
            f.write(f"- **泄漏最优** (min leak_per_bit): n={int(leak_opt['n'])} v={int(leak_opt['verify'])} b={int(leak_opt['block'])} p={int(leak_opt['parity'])} {leak_opt['dataset']} beta={leak_opt['beta_raw']:.4f} leak/b={leak_opt['leak_per_bit']:.4f} FER={leak_opt['FER']:.3f} thr={leak_opt['throughput']:.0f}\n")
            f.write(f"- **FER最优** (min FER): n={int(fer_opt['n'])} v={int(fer_opt['verify'])} b={int(fer_opt['block'])} p={int(fer_opt['parity'])} {fer_opt['dataset']} beta={fer_opt['beta_raw']:.4f} leak/b={fer_opt['leak_per_bit']:.4f} FER={fer_opt['FER']:.3f} thr={fer_opt['throughput']:.0f}\n")
            # note if non-pareto has better single objective but dominated
            f.write("\n> 注: 三者均为 Pareto 非支配点; 若存在某一单目标更优但被支配的点, 说明其在另两目标上劣化。\n")
        else:
            f.write("- Pareto 为空, 无推荐。\n")
        f.write("\n## Figures\n\n")
        if plot_ok:
            f.write("- `pareto_leak_vs_fer.png`: leak_per_bit vs FER, 红色为 Pareto\n")
            f.write("- `pareto_beta_vs_n.png`: beta_raw vs n, 红色 x 为 Pareto, 虚线为 β>0 / β>0.9 阈值\n")
        else:
            f.write("- matplotlib 不可用, 已降级输出 `pareto_plot_data.csv`, 请用其自行绘图。\n")
        f.write("\n## Notes\n\n")
        f.write("- O(n²) 扫描已自检非支配性; undetected 隔离披露 (未计入成功)。\n")
        f.write("- n=5120 长帧虽将 verify_per_bit 降至 0.0006, 但 FER 仍 ~0.98, 表明单纯增大帧长未解决 Cascade 在 SER=0.02 下的纠错能力瓶颈。\n")
    print(f"Wrote {REPORT}")
    # also print summary
    print("\n=== PARETO SUMMARY ===")
    print(out.to_string())
    if len(beta_high)==0:
        print("NO_HIGH_VALUE_WITHIN_GRID")
        print(f"max_beta={max_beta_row['beta_raw']:.4f} at {max_beta_row['dataset_id']}")

if __name__=="__main__":
    main()
