import json
import pathlib


def test_js_table_holdout():
    d = json.loads(pathlib.Path(__file__).with_name("JS_TABLE_HOLDOUT.json").read_text())
    assert abs(d["raw_joint"]["H_U2_given_B"] + d["raw_joint"]["h_U1_given_B_U2"] - 5.07709523) <= 1e-6
    assert abs(d["raw_joint"]["sum"] - 5.07709523) <= 1e-6
    assert sum(1 for h in d["planes_NATURAL"]["mean"] if h < 0.55) == 0
    assert 5.07709523 > 5.0
    for a, b in zip(d["planes_NATURAL"]["EtoO"], d["planes_NATURAL"]["OtoE"]):
        assert abs(a - b) <= 0.005
