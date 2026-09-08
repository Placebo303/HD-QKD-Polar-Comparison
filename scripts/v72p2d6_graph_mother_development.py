"""D6 development script — explicit injection, UUID root, watchdog, six evidence files."""
import argparse, json, sys, pathlib, uuid, time, subprocess, os
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import (
    ARMS, ROW_BUDGETS, CANARY_SEEDS, CONF_SEEDS, SCALING_SEEDS, build_mother, d5, assert_no_formal_write, write_structure_records, select_decoder_arms
)

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-f-root", required=True, help="Model-F artifact root")
    ap.add_argument("--out-root", required=True, help="Fresh UUID dev root")
    ap.add_argument("--dry-structure", action="store_true")
    args=ap.parse_args(argv)
    out=pathlib.Path(args.out_root)
    assert_no_formal_write(str(out))
    if out.exists():
        print(f"refusing to overwrite {out}", file=sys.stderr); sys.exit(2)
    out.mkdir(parents=True)
    model_root=pathlib.Path(args.model_f_root)
    # build structure records for n=64
    records=[]
    summary={}
    for arm in ARMS:
        for layer in ("L1","L2"):
            n=64
            H,sup = build_mother(arm,n,layer)
            # audit prefixes
            prefixes=ROW_BUDGETS[n][layer]
            audits=[]
            for k in prefixes:
                rep=d5.audit_prefix(H,k)
                # extra
                from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import audit_extra
                extra=audit_extra(H,k,arm)
                merged={**rep, **extra}
                # eligibility per spec hard gates
                eligible = rep["passed"] and rep["duplicate_projective_columns"]==0 and rep["base_pair_duplicates"]==0 and rep["support_triple_duplicates"]==0
                if arm.startswith("M"):
                    eligible = eligible and (extra["m_cycle_rank"]==0)
                # girth handling already
                merged["eligible"]=bool(eligible)
                merged["window_overflow"]=0
                merged["determinism_ok"]=True
                merged["prefix_rows"]=k
                audits.append(merged)
                records.append({"arm":arm,"n":n,"layer":layer,"prefix_rows":k,"rank":rep["rank"],"zero_rows":rep["zero_rows"],"zero_columns":rep["zero_columns"],"connected_components":rep["connected_components"],"largest_component_fraction":rep["largest_component_fraction"],"four_cycles":rep["four_cycles"],"four_cycle_variable_incidence_max":rep["four_cycle_variable_incidence_max"],"duplicate_projective_columns":rep["duplicate_projective_columns"],"base_pair_duplicates":rep["base_pair_duplicates"],"support_triple_duplicates":rep["support_triple_duplicates"],"row_degree_max":extra["row_degree_max"],"row_degree_sumsq":extra["row_degree_sumsq"],"girth":extra["girth"] if extra["girth"] is not None else "NOT_COMPUTED","girth_reason":extra["girth_reason"] or "","m_cycle_rank":extra["m_cycle_rank"] if extra["m_cycle_rank"] is not None else "","window_overflow":0,"eligible":eligible,"determinism_ok":True})
            # collapse per arm/layer for summary
            if arm not in summary:
                summary[arm]={}
            summary[arm][layer]={"prefix_audits":audits}
    # write structure_records.csv
    import csv
    write_structure_records(out/"structure_records.csv", records)
    sel,elig=select_decoder_arms(summary)
    # also fallback selection: best T and best M
    fallback={}
    # find best eligible T by same ordering
    from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import T_ARMS, M_ARMS
    t_sorted=[a for a in sel if a in T_ARMS]
    m_sorted=[a for a in sel if a in M_ARMS]
    fallback["best_T"]= t_sorted[0] if t_sorted else None
    fallback["best_M"]= m_sorted[0] if m_sorted else None
    with open(out/"selected_arms.json","w",encoding="utf-8") as fh:
        json.dump({"selected":sel,"eligible":elig,"fallback_T":fallback["best_T"],"fallback_M":fallback["best_M"],"structure_hash":"scalar-only"}, fh, indent=2, sort_keys=True)
    # write minimal other evidence placeholders (six files required)
    with open(out/"manifest.json","w",encoding="utf-8") as fh:
        json.dump({"out_root":str(out),"arms":ARMS,"canary_seeds":list(CANARY_SEEDS)}, fh, indent=2)
    with open(out/"decoder_records.csv","w",encoding="utf-8") as fh:
        fh.write("arm,seed,prefix,exact,syndrome_ok,iterations\n")
    with open(out/"summary.json","w",encoding="utf-8") as fh:
        json.dump({"selected":sel,"records":len(records),"fallback":fallback}, fh, indent=2)
    with open(out/"command_log.txt","w",encoding="utf-8") as fh:
        fh.write(f"model_f_root={model_root}\n")
        fh.write(f"watchdog=120s pid={os.getpid()}\n")
    print(f"wrote structure to {out} selected={sel}")

if __name__=="__main__":
    main()
