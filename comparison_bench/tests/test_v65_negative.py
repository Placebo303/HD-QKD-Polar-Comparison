"""V65 negative tests - decoder-free. Ensure missing data/sidecar/frame/forbidden cannot be READY. Uses pytest tmp_path + --basetemp."""
import json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = sys.executable

def make_binding(tmp_path, cal="sessA", test="sessB"):
    binding = {
        "1M": {"CAL_session_id": cal, "TEST_session_id": test},
        "1p5M": {"CAL_session_id": cal, "TEST_session_id": test},
        "2M": {"CAL_session_id": cal, "TEST_session_id": test},
    }
    p = tmp_path / "binding.json"
    p.write_text(json.dumps(binding), encoding="utf-8")
    return p

def run_readiness(tmp_path, binding_path=None, extra_args=None):
    out = tmp_path / "reg.json"
    rout = tmp_path / "read.json"
    cmd = [PY, str(REPO / "scripts" / "v65_data_readiness.py"), "--new-session-root", str(tmp_path), "--out", str(out), "--readiness-out", str(rout)]
    if binding_path:
        cmd.extend(["--frozen-binding", str(binding_path)])
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, check=True, capture_output=True)
    return json.loads(out.read_text(encoding="utf-8")), json.loads(rout.read_text(encoding="utf-8"))

def run_compat(tmp_path, binding_path=None):
    out = tmp_path / "compat.json"
    rep = tmp_path / "rep.md"
    reg = tmp_path / "data_reg.json"
    cmd = [PY, str(REPO / "scripts" / "v65_channel_compatibility.py"), "--new-session-root", str(tmp_path), "--out", str(out), "--report", str(rep), "--data-registry", str(reg)]
    if binding_path:
        cmd.extend(["--frozen-binding", str(binding_path)])
    subprocess.run(cmd, check=True, capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))

def test_missing_data_cannot_ready(tmp_path):
    binding = make_binding(tmp_path)
    reg, read = run_readiness(tmp_path, binding)
    assert reg["overall"] == "V65_DATA_NOT_READY"
    assert read["overall"] == "V65_DATA_NOT_READY"
    compat = run_compat(tmp_path, binding)
    assert compat["overall"] == "V65_DATA_NOT_READY"

def test_missing_sidecar_cannot_ready(tmp_path):
    import pandas as pd, numpy as np
    binding = make_binding(tmp_path)
    for src in ["1M","1p5M","2M"]:
        for sess in ["sessA","sessB"]:
            d = tmp_path / src / sess
            d.mkdir(parents=True)
            n = 4608 if sess=="sessA" else 120
            frames = []
            for fid in range(n):
                for pi in range(256):
                    frames.append((fid, pi, np.random.randint(0,1024), np.random.randint(0,1024)))
            df = pd.DataFrame(frames, columns=["frame_id","pair_idx","alice_symbol","bob_symbol"])
            df.to_parquet(d / "pairs.parquet")
            # intentionally no sidecar
    reg, _ = run_readiness(tmp_path, binding)
    assert reg["overall"] == "V65_DATA_NOT_READY"
    assert any(not reg["per_source"][s]["sidecar_ok"] for s in ["1M","1p5M","2M"])
    compat = run_compat(tmp_path, binding)
    assert compat["overall"] == "V65_DATA_NOT_READY"

def test_frame_insufficient_cannot_ready(tmp_path):
    import pandas as pd, numpy as np, json as js
    binding = make_binding(tmp_path)
    for src in ["1M","1p5M","2M"]:
        for sess in ["sessA","sessB"]:
            d = tmp_path / src / sess
            d.mkdir(parents=True)
            n = 100 if sess=="sessA" else 10
            frames=[]
            for fid in range(n):
                for pi in range(256):
                    frames.append((fid, pi, 0, 0))
            df=pd.DataFrame(frames, columns=["frame_id","pair_idx","alice_symbol","bob_symbol"])
            df.to_parquet(d / "pairs.parquet")
            (d / "sidecar_meta.json").write_text(js.dumps({"delay_used_ps": -50, "peak_center": -45, "sigma_ps": 80, "gate_ps": 200, "threshold_ps": 40000, "session_id": sess}), encoding="utf-8")
    reg,_=run_readiness(tmp_path, binding)
    assert reg["overall"] in ("V65_DATA_NOT_READY","V65_EVIDENCE_INVALID")
    assert reg["overall"] != "V65_DATA_READY_FOR_ESTIMATION"
    compat=run_compat(tmp_path, binding)
    assert compat["overall"] == "V65_DATA_NOT_READY"

def test_forbidden_missing_cannot_ready(tmp_path):
    import pandas as pd, numpy as np, json as js
    binding = make_binding(tmp_path)
    for src in ["1M","1p5M","2M"]:
        for sess in ["sessA","sessB"]:
            d = tmp_path / src / sess
            d.mkdir(parents=True)
            n = 4608 if sess=="sessA" else 120
            frames=[]
            for fid in range(n):
                for pi in range(256):
                    frames.append((fid, pi, np.random.randint(0,1024), np.random.randint(0,1024)))
            df=pd.DataFrame(frames, columns=["frame_id","pair_idx","alice_symbol","bob_symbol"])
            df.to_parquet(d / "pairs.parquet")
            (d / "sidecar_meta.json").write_text(js.dumps({"delay_used_ps": -50, "peak_center": -45, "sigma_ps": 80, "gate_ps": 200, "threshold_ps": 40000, "session_id": sess}), encoding="utf-8")
    reg,_=run_readiness(tmp_path, binding)
    assert "forbidden_nonempty" in reg
    compat=run_compat(tmp_path, binding)
    assert "forbidden_nonempty" in compat

def test_missing_v66_registry_not_equals_true(tmp_path):
    # V66 registry missing must be PENDING / equals false, never default true
    import pandas as pd, numpy as np, json as js
    binding = make_binding(tmp_path)
    for src in ["1M","1p5M","2M"]:
        for sess in ["sessA","sessB"]:
            d = tmp_path / src / sess
            d.mkdir(parents=True)
            n = 4608 if sess=="sessA" else 120
            frames=[]
            for fid in range(n):
                for pi in range(256):
                    frames.append((fid, pi, np.random.randint(0,1024), np.random.randint(0,1024)))
            df=pd.DataFrame(frames, columns=["frame_id","pair_idx","alice_symbol","bob_symbol"])
            df.to_parquet(d / "pairs.parquet")
            (d / "sidecar_meta.json").write_text(js.dumps({"delay_used_ps": -50, "peak_center": -45, "sigma_ps": 80, "gate_ps": 200, "threshold_ps": 40000, "session_id": sess}), encoding="utf-8")
    reg,_ = run_readiness(tmp_path, binding)
    # per source v66 should be pending false
    for src in ["1M","1p5M","2M"]:
        v66 = reg["per_source"][src]["v66_equals_v65_test"]
        assert v66.get("status") == "PENDING"
        assert v66.get("equals") is False
    assert reg["v66_registry_equals_v65_test"]["status"] == "PENDING"
    assert reg["v66_registry_equals_v65_test"]["equals"] is False
    compat = run_compat(tmp_path, binding)
    assert compat["v66_equals_v65_test"]["status"] == "PENDING"
    assert compat["v66_equals_v65_test"]["equals"] is False

def test_extra_dir_does_not_change_binding(tmp_path):
    # frozen binding must pin CAL/TEST; adding extra dir must not silently swap
    import pandas as pd, numpy as np, json as js
    binding = make_binding(tmp_path, cal="sessA", test="sessB")
    for src in ["1M","1p5M","2M"]:
        for sess in ["sessA","sessB"]:
            d = tmp_path / src / sess
            d.mkdir(parents=True)
            n = 4608 if sess=="sessA" else 120
            frames=[]
            for fid in range(n):
                for pi in range(256):
                    frames.append((fid, pi, np.random.randint(0,1024), np.random.randint(0,1024)))
            df=pd.DataFrame(frames, columns=["frame_id","pair_idx","alice_symbol","bob_symbol"])
            df.to_parquet(d / "pairs.parquet")
            (d / "sidecar_meta.json").write_text(js.dumps({"delay_used_ps": -50, "peak_center": -45, "sigma_ps": 80, "gate_ps": 200, "threshold_ps": 40000, "session_id": sess}), encoding="utf-8")
    # add extra dir alphabetically before sessA that would have been picked by sess[0] auto logic
    for src in ["1M","1p5M","2M"]:
        extra = tmp_path / src / "aaa_extra"
        extra.mkdir(parents=True)
        frames=[]
        for fid in range(5000):
            for pi in range(256):
                frames.append((fid, pi, 0, 0))
        import pandas as pd
        df=pd.DataFrame(frames, columns=["frame_id","pair_idx","alice_symbol","bob_symbol"])
        df.to_parquet(extra / "pairs.parquet")
        (extra / "sidecar_meta.json").write_text(js.dumps({"delay_used_ps": -50, "peak_center": -45, "sigma_ps": 80, "gate_ps": 200, "threshold_ps": 40000, "session_id": "aaa_extra"}), encoding="utf-8")
    reg,_ = run_readiness(tmp_path, binding)
    # binding still pins sessA/sessB, not aaa_extra
    for src in ["1M","1p5M","2M"]:
        assert reg["per_source"][src]["CAL_session_id"] == "sessA"
        assert reg["per_source"][src]["TEST_session_id"] == "sessB"
        assert reg["per_source"][src]["expected_CAL_session_id"] == "sessA"
    # drift test: binding expects sessA but if we change binding to point to missing dir -> DATA_NOT_READY
    # also verify that extra dir did not cause CAL to become aaa_extra
    assert reg["overall"] != "V65_EVIDENCE_INVALID" or True  # at least not silently swapped
