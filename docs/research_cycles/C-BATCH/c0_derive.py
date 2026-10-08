"""C-0 RESULT derivation (R5: numbers by script). Reads landed c0_summary.json only."""

import json

d = json.load(open("workspace/c0_delayscan/c0_20261008/c0_summary.json"))
rows = [r for r in d["rows"] if not r["repaired"]]
print("rows:", len(d["rows"]), "wall_total:", d["wall_s_total"])
for key in sorted(set((r["source"], r["bw_ps"]) for r in rows)):
    src, bw = key
    cell = [r for r in rows if r["source"] == src and r["bw_ps"] == bw]
    nom = next(r for r in cell if r["delta_ps"] == 0)
    best = min(cell, key=lambda r: r["p"])
    s_nom = sorted(e for e, _ in nom["top_errors"])
    s_best = sorted(e for e, _ in best["top_errors"])
    gain = round(nom["p"] - best["p"], 6)
    print(src, "bw=" + str(bw), "d=" + str(nom["d"]), "n=" + str(nom["n"]),
          "off=" + str(nom["offset_ps"]))
    # Curve shape around minimum: p at delta*-5, delta*, delta*+5 (grid flatness).
    by_d = {r["delta_ps"]: r for r in cell}
    nbrs = [(dd, by_d[dd]["p"]) for dd in
            (best["delta_ps"] - 5, best["delta_ps"], best["delta_ps"] + 5)
            if dd in by_d]
    print("  curve: " + str(nbrs))
    print("  best_dist: " + str(best["top_errors"]))
    print("  nom : p=" + str(nom["p"]) + " pm=" + str(nom["p_minus_cond"]) +
          " sup=" + str(nom["support_size"]) + " " + str(s_nom))
    print("  best: p=" + str(best["p"]) + " @ " + str(best["delta_ps"]) +
          "ps pm=" + str(best["p_minus_cond"]) +
          " sup=" + str(best["support_size"]) + " " + str(s_best) +
          " gain=" + str(gain))
print("--- controls (re-paired) ---")
for r in d["rows"]:
    if r["repaired"]:
        print(r["source"], r["delta_ps"], r["offset_ps"], r["pairs"],
              "p=" + str(r["p"]), "pm=" + str(r["p_minus_cond"]),
              "sup=" + str(r["support_size"]))
