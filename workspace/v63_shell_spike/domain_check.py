from __future__ import annotations
def domain_check(h_drift_bits: float, p_b_chi2_p: float):
    if abs(h_drift_bits) > 0.05 or p_b_chi2_p < 0.01:
        return "DOMAIN_CALIBRATION_REQUIRED"
    return "DOMAIN_OK"
def test_domain():
    assert domain_check(0.02, 0.5)=="DOMAIN_OK"
    assert domain_check(0.06, 0.5)=="DOMAIN_CALIBRATION_REQUIRED"
    assert domain_check(0.01, 0.001)=="DOMAIN_CALIBRATION_REQUIRED"
    print("domain gate PASS")
