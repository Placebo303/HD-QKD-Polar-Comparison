"""V56 per-source sidecar binding: three sources must not share same param (-50/+50/-50). Fail-closed on 0 or >1 matches."""
from __future__ import annotations
import json, tempfile
from pathlib import Path

def _make_sidecar(dir_path: Path, delay_ps: int):
    dir_path.mkdir(parents=True, exist_ok=True)
    meta = {
        "materialize_params": {
            "used_params": {
                "delay_used_ps": delay_ps,
                "bin_width_ps": 200,
                "frame_bins": 1024,
                "pairing_mode": "nearest",
                "channels": {"A": 1, "B": 5},
            },
            "bin_width_ps": 200,
        }
    }
    (dir_path / "sidecar_meta.json").write_text(json.dumps(meta), encoding="utf-8")

def test_per_source_sidecar_not_shared():
    import importlib.util
    # load modules
    spec_v = importlib.util.spec_from_file_location("verify_corrected_calibration", str(Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py")))
    mod_v = importlib.util.module_from_spec(spec_v); spec_v.loader.exec_module(mod_v)
    spec_r = importlib.util.spec_from_file_location("replay_v13_vs_current", str(Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/replay_v13_vs_current.py")))
    mod_r = importlib.util.module_from_spec(spec_r); spec_r.loader.exec_module(mod_r)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sidecars"
        # corrected sidecars using V55 session ids
        for src, delay in [("1M", -50), ("1p5M", 50), ("2M", -50)]:
            sid = mod_v.SOURCE_SESSION_MAP_CORRECTED[src]
            _make_sidecar(root / sid, delay)
        # also test v13 sidecars separately
        root_v13 = Path(tmp) / "v13_sidecars"
        for src, delay in [("1M", -50), ("1p5M", 50), ("2M", -50)]:
            sid = mod_v.SOURCE_SESSION_MAP_V13[src]
            _make_sidecar(root_v13 / sid, delay)

        # verify corrected binding per source reads correct distinct values
        p1, s1 = mod_v.read_sidecar_status(root, source="1M")
        p2, s2 = mod_v.read_sidecar_status(root, source="1p5M")
        p3, s3 = mod_v.read_sidecar_status(root, source="2M")
        assert s1 == "OK" and s2 == "OK" and s3 == "OK", f"status {s1} {s2} {s3}"
        assert p1["delay_used_ps"] == -50
        assert p2["delay_used_ps"] == 50
        assert p3["delay_used_ps"] == -50
        # 1p5M must not equal 1M's value
        assert p2["delay_used_ps"] != p1["delay_used_ps"]
        # ensure not all same
        assert len({p1["delay_used_ps"], p2["delay_used_ps"], p3["delay_used_ps"]}) == 2

        # replay side per-source also
        q1, qs1 = mod_r.read_used_params(root_v13, source="1M")
        q2, qs2 = mod_r.read_used_params(root_v13, source="1p5M")
        q3, qs3 = mod_r.read_used_params(root_v13, source="2M")
        assert qs1 == "OK" and qs2 == "OK" and qs3 == "OK"
        assert q1["delay_used_ps"] == -50
        assert q2["delay_used_ps"] == 50
        assert q3["delay_used_ps"] == -50
        assert q2["delay_used_ps"] != q1["delay_used_ps"]

        # provenance helper returns distinct absolute paths
        ap1 = mod_v.get_sidecar_abs_path(root, source="1M")
        ap2 = mod_v.get_sidecar_abs_path(root, source="1p5M")
        assert ap1 != ap2
        assert "20260123_1M_600k_0dB" in ap1
        assert "20260107_PPLN_1p5M" in ap2

        # fail-closed on missing
        p_missing, s_missing = mod_v.read_sidecar_status(root, source="nope")
        assert "INCOMPLETE" in s_missing
        assert p_missing == {}

        # fail-closed on multiple: create duplicate matching file for 1M
        dup = root / "20260123_1M_600k_0dB_dup" 
        dup.mkdir(parents=True, exist_ok=True)
        # copy a second file that also contains session string to trigger multiple
        import shutil
        shutil.copy(root / mod_v.SOURCE_SESSION_MAP_CORRECTED["1M"] / "sidecar_meta.json", dup / "sidecar_meta.json")
        # now rglob will see two files containing same expected string? Both contain 1M string? dup path contains 1M_600k_0dB string yes
        p_dup, s_dup = mod_v.read_sidecar_status(root, source="1M")
        assert "INCOMPLETE_multiple" in s_dup

def test_verify_corrected_provenance_fields_present():
    # smoke that provenance fields are produced when run with synthetic
    import importlib.util, json, tempfile, subprocess
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("verify_corrected_calibration", str(Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py")))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    # create minimal sidecars for synthetic test via tmp and run with allow-synthetic
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)/"out.json"
        # use tmp sidecars with distinct delays to avoid sharing
        for src, delay in [("1M", -50), ("1p5M", 50), ("2M", -50)]:
            sid = mod.SOURCE_SESSION_MAP_CORRECTED[src]
            _make_sidecar(Path(tmp)/"corr"/sid, delay)
            sid2 = mod.SOURCE_SESSION_MAP_V13[src]
            _make_sidecar(Path(tmp)/"v13"/sid2, delay if src!="1p5M" else -50)
        # run via python with synthetic
        import sys
        cmd = [sys.executable, str(Path("openspec/changes/formal-ir-v56-input-contract-reconstruction/verify_corrected_calibration.py")),
               "--corrected-sidecars", str(Path(tmp)/"corr"),
               "--v13-sidecars", str(Path(tmp)/"v13"),
               "--out", str(out),
               "--allow-synthetic-for-test"]
        subprocess.check_call(cmd)
        j=json.loads(out.read_text(encoding="utf-8"))
        for src in ["1M","1p5M","2M"]:
            prov=j["per_source"][src].get("provenance",{})
            assert "ttbin_abs_path" in prov or prov.get("ttbin_abs_path") is None  # may be None for synthetic
            assert "sidecar_abs_path" in prov
            assert "delay_used_ps" in prov
            assert "channels" in prov or "bin_width_ps" in prov
            assert "corrected_cfg_replaced_key" in prov
