from __future__ import annotations
def pa_proxy(reconciled_symbols, actual_disclosure_bits, polar_leak_EC=None):
    if polar_leak_EC is not None:
        raise ValueError("REJECT Polar leak_EC: PA must use actual_disclosure_bits, not Polar leak_EC")
    if actual_disclosure_bits is None:
        raise ValueError("actual_disclosure_bits required")
    total_leak = int(sum(actual_disclosure_bits) if hasattr(actual_disclosure_bits, "__iter__") else actual_disclosure_bits)
    return {"pa_input_leak": total_leak, "key_length_proxy": -total_leak, "note":"POLAR_REFERENCE_PROXY"}
def test_pa_reject():
    try:
        pa_proxy([0], [1064], polar_leak_EC=1000)
        assert False, "should reject"
    except ValueError as e:
        assert "REJECT" in str(e)
    ok = pa_proxy([0], [1064,1104])
    assert ok["pa_input_leak"]==2168
    print("PA reject PASS")
