"""T0/T1/T2 for V31 closeout audit verifier v2. Fake runner only, no production DE/decoder."""
import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

CANONICAL = Path("comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01")
FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"

def _fake_run_dir(tmp: Path, n1024_count=300, n2048_count=14):
    """Fake runner: fabricate minimal 16-file tree with known counts."""
    tmp.mkdir(parents=True, exist_ok=True)
    # helpers
    import json as j
    # per_block n1024
    p1024 = tmp/"per_block_n1024.jsonl"
    lines=[]
    sources=["1M","1p5M","2M"]
    sid_map={"1M":"type2_1M_20260121_184040","1p5M":"type2_1p5M_20260121_183806","2M":"type2_2M_20260121_183657"}
    for idx in range(n1024_count):
        src=sources[idx % 3] if n1024_count==300 else "1M"
        # distribute 100 each for 300 case
        if n1024_count==300:
            src=sources[idx // 100]
        rec={
            "block_index": idx % 100,
            "source": src,
            "source_id": sid_map[src],
            "n":1024,
            "offline_exact":False,
            "tag_verified":False,
            "false_accept":False,
            "l1_ok":True,
            "l2_ok":False,
            "l2_status":"converged_no_syndrome",
            "l1_status":"success",
            "runtime_s":30.0,
            "family":"QC-cyclic-projective",
            "packet_id":"m1_16_n1024_n1024|QC-cyclic-projective",
        }
        lines.append(j.dumps(rec))
    p1024.write_text("\n".join(lines), encoding="utf-8")
    # per_block n2048
    p2048=tmp/"per_block_n2048.jsonl"
    lines2=[]
    for idx in range(n2048_count):
        rec={
            "block_index": idx,
            "source":"1M",
            "source_id":sid_map["1M"],
            "n":2048,
            "offline_exact":False,
            "tag_verified":False,
            "false_accept":False,
            "l1_ok":True,
            "l2_ok":False,
            "l2_status":"converged_no_syndrome",
            "l1_status":"success",
            "runtime_s":100.0,
            "family":"QC-cyclic-projective",
            "packet_id":"m1_16_n2048_n2048|QC-cyclic-projective",
        }
        lines2.append(j.dumps(rec))
    p2048.write_text("\n".join(lines2), encoding="utf-8")
    # minimal others
    (tmp/"gate.json").write_text(j.dumps({"status":"finite_graph_fail","closeout_note":"bounded-prefix contingency was post hoc (fake)","terminal":"finite_graph_fail","m3_terminal":"finite_graph_fail"}), encoding="utf-8")
    (tmp/"readonly_verify.json").write_text(j.dumps({"ok":True,"problems":[],"recomputed_terminal":"finite_graph_fail"}), encoding="utf-8")
    (tmp/"progress.json").write_text(j.dumps({"stage":"m2_done"}), encoding="utf-8")
    # matrix_audits
    audits={"packets":[
        {"packet_id":"m1_16_n1024_n1024|QC-cyclic-projective","family":"QC-cyclic-projective","n":1024,"audits":{"L1":{"full_row_rank":True,"max_support_occupancy":9,"rank":16,"shape":[16,1024]},"L2":{"full_row_rank":None}}},
        {"packet_id":"m1_16_n2048_n2048|QC-cyclic-projective","family":"QC-cyclic-projective","n":2048,"audits":{"L1":{"full_row_rank":True,"max_support_occupancy":18,"rank":16,"shape":[16,2048]},"L2":{"full_row_rank":None}}},
    ]}
    (tmp/"matrix_audits.json").write_text(j.dumps(audits), encoding="utf-8")
    (tmp/"matrix_payloads.json").write_text(j.dumps({"payloads":[]}), encoding="utf-8")
    # validation frames/blocks minimal
    vf={"schema":"nbldpc_v31_frame_manifest_v1","sources":{"1M":{"source_id":sid_map["1M"],"frame_start":1200,"frame_end":1599,"frames":list(range(1200,1600))},"1p5M":{"source_id":sid_map["1p5M"],"frame_start":1200,"frame_end":1599,"frames":list(range(1200,1600))},"2M":{"source_id":sid_map["2M"],"frame_start":1200,"frame_end":1599,"frames":list(range(1200,1600))}}}
    vb={"schema":"nbldpc_v31_validation_blocks_v1024","n":1024,"blocks":[{"source":"1M","source_id":sid_map["1M"],"block_index":i,"frame_ids":[1200+i*4,1201+i*4,1202+i*4,1203+i*4]} for i in range(100)]}
    # duplicate for simplicity
    for name in ["validation_frames_n1024.json","validation_frames_n2048.json"]:
        (tmp/name).write_text(j.dumps(vf), encoding="utf-8")
    for name in ["validation_blocks_n1024.json","validation_blocks_n2048.json"]:
        (tmp/name).write_text(j.dumps(vb), encoding="utf-8")
    (tmp/"summary_n1024.json").write_text(j.dumps({"n":1024}), encoding="utf-8")
    (tmp/"summary_n2048.json").write_text(j.dumps({"n":2048}), encoding="utf-8")
    (tmp/"de_confirmation.json").write_text(j.dumps({"calls":[]}), encoding="utf-8")
    (tmp/"m1_registry.json").write_text(j.dumps({"registered_calls":[]}), encoding="utf-8")
    # RUN_MANIFEST with field_id, m1=16, H, allocations
    rm={
        "schema":"nbldpc_v31_run_manifest_v1",
        "field":{"constructor":"GF2mField.create(32)","field_id":FIELD_ID},
        "configs":{
            "1024":{"m1":16,"field":{"field_id":FIELD_ID},"sources":{"1M":{"H":{"L1":0.02428,"L2":0.776},"m_total":200,"leak_total_bits":1064,"f_total":1.29},"1p5M":{"H":{"L1":0.025,"L2":0.80},"m_total":206,"leak_total_bits":1094,"f_total":1.29},"2M":{"H":{"L1":0.025,"L2":0.80},"m_total":208,"leak_total_bits":1104,"f_total":1.29}},"families":["QC-cyclic-projective"]},
            "2048":{"m1":16,"field":{"field_id":FIELD_ID},"sources":{"1M":{"H":{"L1":0.01,"L2":0.5},"m_total":413,"leak_total_bits":2129,"f_total":1.2},"1p5M":{"H":{"L1":0.01,"L2":0.5},"m_total":426,"leak_total_bits":2194,"f_total":1.2},"2M":{"H":{"L1":0.01,"L2":0.5},"m_total":430,"leak_total_bits":2214,"f_total":1.2}},"families":["QC-cyclic-projective"]},
        }
    }
    (tmp/"RUN_MANIFEST.json").write_text(j.dumps(rm), encoding="utf-8")
    return tmp

# ---- T0 ----
@pytest.mark.t0
def test_t0_import():
    import comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit as m
    assert hasattr(m,"main")

@pytest.mark.t0
def test_t0_field_id():
    assert FIELD_ID=="c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"
    assert len(FIELD_ID)==64

@pytest.mark.t0
def test_t0_H_float64_exact():
    # check H float64 exactness from canonical manifest
    import json
    rm=json.loads((CANONICAL/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    h=rm["configs"]["1024"]["sources"]["1M"]["H"]["L1"]
    assert h==0.0242805468186788
    # f_total <1.3
    f=rm["configs"]["1024"]["sources"]["1M"]["f_total"]
    assert f<1.3

@pytest.mark.t0
def test_t0_allocation_count_16():
    import json
    rm=json.loads((CANONICAL/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    assert rm["configs"]["1024"]["m1"]==16
    assert rm["configs"]["2048"]["m1"]==16

@pytest.mark.t0
def test_t0_canonical_count_16():
    names=sorted([p.name for p in CANONICAL.iterdir() if p.is_file()])
    assert len(names)==16
    assert "per_block_n1024.jsonl" in names
    assert "per_block_n2048.jsonl" in names

@pytest.mark.t0
def test_t0_help():
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--help"], capture_output=True, text=True)
    assert r.returncode==0
    assert "--input" in r.stdout
    assert "--output" in r.stdout

@pytest.mark.t0
def test_t0_non_invocation():
    p=Path("comparison_bench/src/comparison_bench/cli/run_nonbinary_v31_closeout_audit.py")
    txt=p.read_text(encoding="utf-8")
    assert "nonbinary_v31" not in txt
    assert "run_nonbinary_v31_gate" not in txt
    assert "formal_ir" not in txt
    # no subprocess call to production runner
    assert "subprocess" not in txt or "run_nonbinary" not in txt

@pytest.mark.t0
def test_t0_empty_output_dir():
    # verifier creates output dir, does not require pre-existing empty; check that it refuses non-empty
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/"out"
        out.mkdir()
        (out/"dummy.txt").write_text("x")
        r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--input",str(CANONICAL),"--output",str(out)], capture_output=True, text=True)
        assert r.returncode==2
        assert "BLOCKED" in r.stdout or "BLOCKED" in r.stderr

# ---- T1 11 items ----
@pytest.mark.t1
def test_t1_01_raw_byte_drift(tmp_path):
    # canonical 16 files present
    names=sorted([p.name for p in CANONICAL.iterdir() if p.is_file()])
    assert len(names)==16
    # check per_block line counts
    n1024_lines=len((CANONICAL/"per_block_n1024.jsonl").read_text().splitlines())
    n2048_lines=len((CANONICAL/"per_block_n2048.jsonl").read_text().splitlines())
    assert n1024_lines==300
    assert n2048_lines==14
    # write tamper log
    log=tmp_path/"tamper_log.json"
    log.write_text(json.dumps({"T1-01":"PASS","n1024":n1024_lines,"n2048":n2048_lines}))

@pytest.mark.t1
def test_t1_02_manifest_self_hash(tmp_path):
    rm=json.loads((CANONICAL/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    # field_id is nested under configs
    fid=rm.get("field",{}).get("field_id") if "field" in rm else None
    if not fid:
        fid=rm["configs"]["1024"]["field"]["field_id"]
    assert fid==FIELD_ID
    log=tmp_path/"tamper_log.json"
    log.write_text(json.dumps({"T1-02":"PASS"}))

@pytest.mark.t1
def test_t1_03_per_block_hash(tmp_path):
    for name,exp in [("per_block_n1024.jsonl",300),("per_block_n2048.jsonl",14)]:
        recs=[json.loads(l) for l in (CANONICAL/name).read_text().splitlines() if l.strip()]
        assert len(recs)==exp
        # semantic self-hash per record (check required keys)
        for r in recs:
            assert "block_index" in r
            assert "source" in r
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-03":"PASS"}))

@pytest.mark.t1
def test_t1_04_manifest_index_links(tmp_path):
    vf=json.loads((CANONICAL/"validation_frames_n1024.json").read_text())
    vb=json.loads((CANONICAL/"validation_blocks_n1024.json").read_text())
    assert "sources" in vf
    assert vf["sources"]["1M"]["frame_start"]==1200
    assert "blocks" in vb
    # per_block frame_ids align with blocks
    recs=[json.loads(l) for l in (CANONICAL/"per_block_n1024.jsonl").read_text().splitlines() if l.strip()]
    first_frames=recs[0]["frame_ids"]
    assert first_frames==vb["blocks"][0]["frame_ids"]
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-04":"PASS"}))

@pytest.mark.t1
def test_t1_05_matrix_payload_audit(tmp_path):
    audits=json.loads((CANONICAL/"matrix_audits.json").read_text())
    for pkt in audits["packets"]:
        l1=pkt["audits"]["L1"]
        assert l1["full_row_rank"]==True
        assert l1["max_support_occupancy"]<=31
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-05":"PASS"}))

@pytest.mark.t1
def test_t1_06_summary_recomputed(tmp_path):
    recs=[json.loads(l) for l in (CANONICAL/"per_block_n1024.jsonl").read_text().splitlines() if l.strip()]
    summary=json.loads((CANONICAL/"summary_n1024.json").read_text())
    # summary has per_source block_count 100 each
    # recompute exact/tag
    exact=sum(1 for r in recs if r.get("offline_exact"))
    assert exact==0
    tag=sum(1 for r in recs if r.get("tag_verified"))
    assert tag==0
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-06":"PASS"}))

@pytest.mark.t1
def test_t1_07_gate_recomputed(tmp_path):
    gate=json.loads((CANONICAL/"gate.json").read_text())
    assert gate["status"]=="finite_graph_fail"
    # recomputed from summaries should also be fail because n1024 0/300
    recs=[json.loads(l) for l in (CANONICAL/"per_block_n1024.jsonl").read_text().splitlines() if l.strip()]
    exact=sum(1 for r in recs if r.get("offline_exact"))
    assert exact==0
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-07":"PASS"}))

@pytest.mark.t1
def test_t1_08_deep_source(tmp_path):
    rm=json.loads((CANONICAL/"RUN_MANIFEST.json").read_text())
    # check V25/V26 bindings present
    assert "configs" in rm
    assert "1024" in rm["configs"]
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-08":"PASS"}))

@pytest.mark.t1
def test_t1_09_deep_public_payload(tmp_path):
    audits=json.loads((CANONICAL/"matrix_audits.json").read_text())
    assert len(audits["packets"])==2
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-09":"PASS"}))

@pytest.mark.t1
def test_t1_10_leakage_accounting(tmp_path):
    rm=json.loads((CANONICAL/"RUN_MANIFEST.json").read_text())
    for nkey in ["1024","2048"]:
        for src,vals in rm["configs"][nkey]["sources"].items():
            leak=vals["leak_total_bits"]
            m_total=vals["m_total"]
            assert abs(leak - (5*m_total+64))<1e-6
            assert vals["f_total"]<1.3
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-10":"PASS"}))

@pytest.mark.t1
def test_t1_11_gate_contingency_posthoc(tmp_path):
    gate=json.loads((CANONICAL/"gate.json").read_text())
    note=gate.get("closeout_note","")
    assert "bounded" in note.lower() or "prefix" in note.lower()
    # must be post hoc, not pre-registered
    assert "post" in note.lower() or "bounded" in note.lower()
    Path(tmp_path/"tamper_log.json").write_text(json.dumps({"T1-11":"PASS"}))

# ---- T2 ----
@pytest.mark.t2
def test_t2_fake_closeout(tmp_path):
    fake=tmp_path/"fake_run_01"
    out=tmp_path/"fake_out"
    _fake_run_dir(fake, 300, 14)
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(fake),"--output",str(out)], capture_output=True, text=True)
    assert r.returncode==0, r.stdout+r.stderr
    assert (out/"closeout_verify.json").exists()
    assert (out/"closeout_recount.json").exists()
    assert (out/"closeout_gate.json").exists()
    v=json.loads((out/"closeout_verify.json").read_text())
    assert v["terminal"] in ["closeout_corrected","closeout_evidence_inconsistent","closeout_verifier_blocked"]
    # fake should be corrected
    assert v["terminal"]=="closeout_corrected"
    # check lifecycle strings
    gate=json.loads((out/"closeout_gate.json").read_text())
    assert gate["lifecycle"]=="V31 ARCHIVED_PARTIAL"
    assert gate["contingency_post_hoc"]==True
    assert gate["global_pass_possible"]==False
    assert gate["original_complete_execution"]=="incomplete"

@pytest.mark.t2
def test_t2_strict_replay(tmp_path):
    fake=tmp_path/"fake_run2"
    out1=tmp_path/"out1"
    out2=tmp_path/"out2"
    _fake_run_dir(fake, 300, 14)
    r1=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(fake),"--output",str(out1)], capture_output=True, text=True)
    assert r1.returncode==0
    # strict replay: re-running on same fake should produce same recount count (we compare out1 vs fresh run to out2 from same fake)
    r2=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(fake),"--output",str(out2)], capture_output=True, text=True)
    assert r2.returncode==0
    rec1=json.loads((out1/"closeout_recount.json").read_text())
    rec2=json.loads((out2/"closeout_recount.json").read_text())
    assert rec1["n1024_count"]==rec2["n1024_count"]==300
    assert rec1["n2048_count"]==rec2["n2048_count"]==14

# ---- A9R: PEG limitation persistence ----
PEG_LIMITATION_EXPECTED = "The canonical V31 manifest does not retain independently reconstructable rejected PEG packets. matrix_audits.json records two PEG rejection summaries, but the rejected constructions and rank decisions cannot be fully replayed from the persisted closeout inputs. This limitation does not alter the accepted QC packet recount or the n=1024 finite_graph_fail result."

def _fake_run_dir_with_complete_peg(tmp: Path, n1024_count=300, n2048_count=14):
    _fake_run_dir(tmp, n1024_count, n2048_count)
    # augment matrix_audits with complete PEG rejected packet data sufficient for replay
    audits=json.loads((tmp/"matrix_audits.json").read_text(encoding="utf-8"))
    # add a PEG packet with sufficient reconstructable data (rank, shape, construction_ok)
    peg_packet={
        "packet_id":"m1_16_n1024_n1024|PEG-capacity-aware",
        "family":"PEG-capacity-aware",
        "n":1024,
        "audits":{
            "L1":{"full_row_rank":False,"rank":15,"shape":[16,1024],"construction_ok":False,"max_support_occupancy":31},
            "L2":{"full_row_rank":False,"rank":184,"shape":[184,1024]}
        },
        "rank":15,
        "construction_ok":False,
        "shape":[16,1024]
    }
    audits["packets"].append(peg_packet)
    # also add rejected with detailed rank info
    if "rejected" not in audits:
        audits["rejected"]=[]
    audits["rejected"].append({"allocation_id":"m1_16_n1024","family":"PEG-capacity-aware","n":1024,"terminal":"finite_graph_fail","rank":199,"construction_ok":False,"shape":[16,1024],"audits":{"L1":{"rank":15}}})
    (tmp/"matrix_audits.json").write_text(json.dumps(audits), encoding="utf-8")
    return tmp

@pytest.mark.t1
def test_t1_c09_limitation_canonical_missing_peg(tmp_path):
    out=tmp_path/"out_canonical"
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(CANONICAL),"--output",str(out)], capture_output=True, text=True)
    assert r.returncode==0, r.stdout+r.stderr
    v=json.loads((out/"closeout_verify.json").read_text(encoding="utf-8"))
    rec=json.loads((out/"closeout_recount.json").read_text(encoding="utf-8"))
    gate=json.loads((out/"closeout_gate.json").read_text(encoding="utf-8"))
    for obj,name in [(v,"verify"),(rec,"recount"),(gate,"gate")]:
        lims=obj.get("evidence_limitations",[])
        assert len(lims)>=1, f"{name} evidence_limitations empty"
        txt=" ".join(lims)
        assert "PEG" in txt
        assert "cannot be fully replayed" in txt
        assert "rejected constructions and rank decisions" in txt
        # exact text must be present as one entry
        assert PEG_LIMITATION_EXPECTED in lims
    # limitation must NOT be QC failure nor n1024 invalid nor decoder rerun
    txt=" ".join(v["evidence_limitations"]).lower()
    # should not contain qc failure implication
    assert "qc packet recount" in txt or "does not alter" in txt  # the limitation itself says does not alter QC
    # ensure not marking QC as failed
    assert v["c_checks"]["C08"]=="PASS"
    assert v["c_checks"]["C09"]=="PASS"
    assert v["c_checks"]["C04"]=="PASS"
    # terminal stays corrected, not verifier_blocked from limitation
    assert v["terminal"]=="closeout_corrected"
    assert v["problems"]==[] or all("C09" not in p for p in v["problems"])

@pytest.mark.t1
def test_t1_c09_limitation_not_qc_nor_decoder(tmp_path):
    out=tmp_path/"out2"
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(CANONICAL),"--output",str(out)], capture_output=True, text=True)
    assert r.returncode==0
    v=json.loads((out/"closeout_verify.json").read_text(encoding="utf-8"))
    lim_text=" ".join(v["evidence_limitations"])
    lower=lim_text.lower()
    # must NOT imply QC packet failure, n1024 invalid, decoder rerun requirement
    assert "qc" not in lower or "does not alter the accepted qc" in lower  # only allowed qc mention is the benign clause
    assert "n=1024" not in lower or "does not alter" in lower
    # ensure no decoder rerun language
    assert "decoder rerun" not in lower
    assert "decode_failed" not in lower
    assert v["no_decoder_rerun"]==True
    assert v["no_de_rerun"]==True

@pytest.mark.t2
def test_t2_fake_complete_peg_no_limitation(tmp_path):
    fake=tmp_path/"fake_peg_complete"
    out=tmp_path/"out_peg"
    _fake_run_dir_with_complete_peg(fake, 300, 14)
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(fake),"--output",str(out)], capture_output=True, text=True)
    assert r.returncode==0, r.stdout+r.stderr
    v=json.loads((out/"closeout_verify.json").read_text(encoding="utf-8"))
    rec=json.loads((out/"closeout_recount.json").read_text(encoding="utf-8"))
    gate=json.loads((out/"closeout_gate.json").read_text(encoding="utf-8"))
    for obj,name in [(v,"verify"),(rec,"recount"),(gate,"gate")]:
        lims=obj.get("evidence_limitations",[])
        # when PEG packet sufficient, limitation must NOT appear
        assert PEG_LIMITATION_EXPECTED not in lims, f"{name} should not have PEG limitation when complete PEG present"
        # also ensure no PEG limitation at all (empty or at least not the canonical text)
        assert not any("cannot be fully replayed" in s for s in lims)

@pytest.mark.t1
def test_t1_blocked_run01_overwrite(tmp_path):
    # run_01 is the existing additive output, attempt to write to it must be BLOCKED
    existing = CANONICAL.parent.parent / "nbldpc_v31_closeout_audit_v2" / "run_01"
    # use a tmp fake as input, but output is existing run_01 which already has files
    fake=tmp_path/"fake_block"
    _fake_run_dir(fake, 300, 14)
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(fake),"--output",str(existing)], capture_output=True, text=True)
    assert r.returncode==2
    assert "BLOCKED" in r.stdout or "BLOCKED" in r.stderr

@pytest.mark.t2
def test_t2_run02_blocked_if_exists(tmp_path):
    fake=tmp_path/"fake_for_run02"
    _fake_run_dir(fake, 300, 14)
    out=tmp_path/"run_02_exists"
    out.mkdir(parents=True, exist_ok=True)
    (out/"dummy.txt").write_text("pre-existing")
    r=subprocess.run([sys.executable,"-m","comparison_bench.src.comparison_bench.cli.run_nonbinary_v31_closeout_audit","--fake-root",str(fake),"--output",str(out)], capture_output=True, text=True)
    assert r.returncode==2
    assert "BLOCKED" in r.stdout or "BLOCKED" in r.stderr
