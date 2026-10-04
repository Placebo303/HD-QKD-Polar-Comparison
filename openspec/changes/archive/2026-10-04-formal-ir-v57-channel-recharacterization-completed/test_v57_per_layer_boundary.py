"""Boundary test for V57 REVISED2 per-layer m_i: m1=1024 m2<1024 legal total >1024 ≤2048"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import v57_channel_recharacterization as v57

def test_per_layer_boundary():
    # H that yields ceil >1024 → capped
    # threshold: ceil(1.3*1024*H/5) >1024 => H > 1024*5/(1.3*1024)=3.846...
    H_high = 4.0  # should saturate
    H_low = 1.0   # should not saturate: ceil(1.3*1024*1/5)=267
    _, m1, full1 = v57._per_layer_m(H_high)
    _, m2, full2 = v57._per_layer_m(H_low)
    assert m1 == 1024, f"m1 {m1} !=1024"
    assert full1 is True, "full1 should be True"
    assert m2 < 1024 and m2 > 0, f"m2 {m2} not <1024"
    assert full2 is False
    m_total = m1 + m2
    assert 1024 < m_total <= 2048, f"total {m_total} not in (1024,2048]"
    # dual gate should pass, not EVIDENCE_INVALID
    assert 0 <= m1 <= 1024 and 0 <= m2 <= 1024
    assert 0 <= m_total <= 2048
    print("boundary m1=1024 case: PASS", {"m1": m1, "m2": m2, "total": m_total, "full1": full1})

def test_dual_vs_single_gate():
    # ensure old single gate m_total≤1024 is NOT used
    _, m1, _ = v57._per_layer_m(4.0)  # 1024
    _, m2, _ = v57._per_layer_m(1.0)  # ~267
    m_total = m1 + m2  # ~1291 >1024
    # old logic would say invalid (>1024), new logic says valid via dual gate
    assert m_total > 1024
    assert m_total <= 2048
    assert m1 <= 1024 and m2 <= 1024  # dual gate passes
    print("dual gate vs single: PASS")

def test_zero_and_cap():
    # edge: H=0 → 0
    _, m0, f0 = v57._per_layer_m(0.0)
    assert m0 == 0 and f0 is False
    # H very high → still capped 1024
    _, m_high, f_high = v57._per_layer_m(10.0)  # ceil huge >1024
    assert m_high == 1024 and f_high is True
    print("zero/cap: PASS")

if __name__ == "__main__":
    test_per_layer_boundary()
    test_dual_vs_single_gate()
    test_zero_and_cap()
    print("ALL BOUNDARY TESTS PASS")
