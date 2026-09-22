"""R4 hierarchical per-layer tests: λ*P_global, no +alpha, Val non-participant, m1=1024 boundary, EG2→V58 block"""
import json, math, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = REPO / "openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.py"
JSON = REPO / "openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization_r4_hierarchical_per_layer.json"

def test_estimator_contains_lambda_p_global():
    txt = PY.read_text(encoding="utf-8")
    assert "lam * p_global" in txt or "lam*P_global" in txt or "P_global(a)" in txt, "hierarchical estimator missing lam * P_global"
    assert "_counts_to_p_hier" in txt, "hierarchical helper missing"
    # hierarchical formula
    assert "(C_ab+lam * p_global)" in txt or "lam * p_global" in txt

def test_production_path_no_per_cell_alpha():
    txt = PY.read_text(encoding="utf-8")
    # production smoothing must be hierarchical, not Laplace per-cell +alpha
    # ensure the per-cell Laplace expression not present as active code (allow deprecated alpha alias handling but not as estimator)
    # The forbidden pattern is "(counts[:, b] + alpha) / (nb + alpha * Q)"
    assert "alpha * Q" not in txt, "production path contains per-cell +alpha (Laplace) – should be hierarchical lam*P_global only"
    assert "_counts_to_p_smooth" not in txt, "Laplace smooth function should not exist in R4"

def test_val_not_in_lambda_selection():
    txt = PY.read_text(encoding="utf-8")
    # _select_lambda_4fold should only use cal_frames, not val
    # crude: function body should not reference val_frames or VAL
    start = txt.index("def _select_lambda_4fold")
    body = txt[start:txt.index("\ndef main", start)]
    assert "val" not in body.lower().replace("val_",""), "Val should not appear in lambda selection (should be Cal 4-fold only)"  # loose
    # stronger: ensure selection called with CAL only
    assert "_select_lambda_4fold(df, CAL, grid)" in txt

def test_per_layer_boundary_1024_267():
    sys.path.insert(0, str(PY.parent))
    import v57_channel_recharacterization as v57
    # raw_m1=ceil(1.3*1024*4/5)=1065 -> capped 1024 full True
    # raw_m2=ceil(1.3*1024*1/5)=267 -> capped 267 full False
    raw1, m1, f1 = v57._per_layer_m(4.0)
    raw2, m2, f2 = v57._per_layer_m(1.0)
    assert raw1 == 1065 and m1 == 1024 and f1 is True, f"raw1 {raw1} m1 {m1}"
    assert raw2 == 267 and m2 == 267 and f2 is False, f"raw2 {raw2} m2 {m2}"
    total = m1 + m2
    assert total == 1291, f"total {total} !=1291"
    assert 1024 < total <= 2048
    assert 0 <= m1 <= 1024 and 0 <= m2 <= 1024
    # ensure not marked INVALID: dual gate passes
    assert total <= 2048

def test_three_source_eg2_fail_blocks_v58():
    j = json.loads(JSON.read_text(encoding="utf-8"))
    assert j["verdict"]["overall"] == "V57_CHANNEL_RECHARACTERIZATION_FAIL"
    assert j["verdict"]["PREDICTIVE_MODEL_NOT_STABLE"] is True
    for src in ["1M","1p5M","2M"]:
        ps = j["per_source"][src]
        assert ps["EG2_pass"] is False, f"{src} EG2 should fail"
        assert ps["PASS_s"] is False
    # boundary: only all PASS allows V58, so this blocks
    assert j["boundary"]["only_all_pass_allows_V58"] is True

if __name__ == "__main__":
    test_estimator_contains_lambda_p_global()
    test_production_path_no_per_cell_alpha()
    test_val_not_in_lambda_selection()
    test_per_layer_boundary_1024_267()
    test_three_source_eg2_fail_blocks_v58()
    print("ALL R4 TESTS PASS")
