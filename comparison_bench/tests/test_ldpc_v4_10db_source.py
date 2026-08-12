from __future__ import annotations
import unittest,os,uuid,contextlib
import copy
from pathlib import Path
from unittest.mock import patch
import numpy as np
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_10db_source as lane
def _workspace_tmp():
 p=Path("workspace/v4_10db_transfer_phase2")/uuid.uuid4().hex;p.mkdir(parents=True);return str(p)

class Test10dBSource(unittest.TestCase):
 def test_local_source_lock_has_exact_selection(self):
  lock=lane.build_source_lock()
  self.assertTrue(lock["source_relocation"]);self.assertEqual(len(lock["selected_frames"]),384)
  self.assertEqual({x["stratum"] for x in lock["selected_frames"]},set(lane.STRATA))
  for st in lane.STRATA:self.assertEqual(sum(x["stratum"]==st for x in lock["selected_frames"]),128)
  self.assertEqual(lock,lane.build_source_lock())
 def test_relocation_prefix_and_competing_root_rejected(self):
  rel=lane.relocation_record();old=rel["recorded_root"].replace("\\","/")+"/TypeII_776.1nm_3s/x"
  self.assertTrue(lane._map_old(old,rel).lower().startswith(rel["actual_root"].lower()))
  with self.assertRaises(ValueError):lane._map_old(r"D:\Other\QKD_Loss\x",rel)
  with patch.object(lane.Path,"exists",return_value=True):
   with self.assertRaises(ValueError):lane.relocation_record()
 def test_hash_and_snapshot_tampering_rejected(self):
  with patch.object(lane,"_file",side_effect=lambda p: {"path":str(p),"bytes":0,"sha256":"0"*64}):
   with self.assertRaises(ValueError):lane.build_source_lock()
  rel=lane.relocation_record(); bad=dict(rel);bad["actual_root"]=r"D:\Other"
  with self.assertRaises(ValueError):lane._verify_snapshots(bad)
 def test_snapshot_fixture_rejects_second_root_wrong_target_missing_file_and_suffix(self):
  with contextlib.nullcontext(_workspace_tmp()) as tmp:
   root=Path(tmp);target=root/"capture"/"ok.txt";target.parent.mkdir();target.write_text("ok")
   rel={"recorded_root":r"D:\Data\QKD_Loss","actual_root":str(root)};old=r"D:\Data\QKD_Loss\capture\ok.txt"
   lane.validate_snapshot_paths(rel,[old],[target])
   for value,want in ((r"D:\Other\ok.txt",target),(old,target.with_name("other.txt"))):
    with self.assertRaises(ValueError):lane.validate_snapshot_paths(rel,[value],[want])
   target.unlink()
   with self.assertRaises(ValueError):lane.validate_snapshot_paths(rel,[old],[target])
   suffix=Path(r"TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808")
   self.assertEqual(lane.validate_relocation_suffix(root,root/suffix),suffix)
   with self.assertRaises(ValueError):lane.validate_relocation_suffix(root,root/"other")
 def test_real_lock_records_domain_tail_and_unique_payloads(self):
  lock=lane.build_source_lock()
  self.assertTrue(all(d["complete_frames"]>=128 for d in lock["datasets"]))
  self.assertTrue(all(d["tail_symbols"]>=0 and d["tail_symbols"]<256 for d in lock["datasets"]))
  self.assertEqual(len({x["payload_identity"] for x in lock["selected_frames"]}),384)
 def test_pure_array_fixture_tampering_rejected(self):
  good=np.zeros(128*256,dtype=np.uint16)
  cases=((good.astype(float),good), (good.reshape(128,256),good), (good,good[:-1]), (np.full_like(good,1024),good), (np.full_like(good,-1,dtype=np.int16),good), (good[:127*256],good[:127*256]))
  for a,b in cases:
   with self.assertRaises(ValueError):lane.validate_arrays(a,b)
 def test_metadata_fixture_rejects_each_required_field_and_processing_change(self):
  with contextlib.nullcontext(_workspace_tmp()) as tmp:
   root=Path(tmp);raw=root/"capture"/"main.ttbin";raw.parent.mkdir();raw.write_bytes(b"raw")
   rel={"recorded_root":r"D:\Data\QKD_Loss","actual_root":str(root.resolve())}
   old=r"D:\Data\QKD_Loss\capture\main.ttbin"
   expected={"dimension":1024,"bin_width_ps":120,"block_symbols":256,"mapping":"gray","bit_order":"lsb0","wrap_rule":"floor_div"}
   base={"joint_source_mode":"from_ttbin","joint_origin":"from_ttbin","materialize_origin":"materialized_from_ttbin","sequence_source_mode":"strict","sequence_is_sampled":False,"acquisition_loss":10,"n_symbols":256*128,"symbolization_snapshot":{**expected,"ttbin_file":old},"materialize_params":{"used_params":{"source_ttbin_paths":[old],"pairing_mode":"nearest","dimension":1024,"bin_width_ps":120,"mapping":"gray"}}}
   self.assertEqual(lane.validate_metadata(base,source_paths=[old],raw=raw,bw=120,array_size=256*128,relocation=rel,expected_processing=expected),expected)
   mutations=[
    ("joint_source_mode","other"),("joint_origin","other"),("materialize_origin","other"),("sequence_source_mode","sampled"),("sequence_is_sampled",True),("acquisition_loss",15),("n_symbols",1)]
   for key,value in mutations:
    bad=copy.deepcopy(base);bad[key]=value
    with self.assertRaises(ValueError):lane.validate_metadata(bad,source_paths=[old],raw=raw,bw=120,array_size=256*128,relocation=rel,expected_processing=expected)
   for key,value in (("pairing_mode","all"),("dimension",256),("bin_width_ps",180)):
    bad=copy.deepcopy(base);bad["materialize_params"]["used_params"][key]=value
    with self.assertRaises(ValueError):lane.validate_metadata(bad,source_paths=[old],raw=raw,bw=120,array_size=256*128,relocation=rel,expected_processing=expected)
   for key in ("padding","padded","tail_padding"):
    bad=copy.deepcopy(base);bad[key]=True
    with self.assertRaises(ValueError):lane.validate_metadata(bad,source_paths=[old],raw=raw,bw=120,array_size=256*128,relocation=rel,expected_processing=expected)
   for key,value in (("dimension",256),("bin_width_ps",180),("block_symbols",128),("mapping","natural"),("bit_order","msb0"),("wrap_rule","ceil_div"),("ttbin_file",r"D:\Other\main.ttbin")):
    bad=copy.deepcopy(base);bad["symbolization_snapshot"][key]=value
    with self.assertRaises(ValueError):lane.validate_metadata(bad,source_paths=[old],raw=raw,bw=120,array_size=256*128,relocation=rel,expected_processing=expected)
   bad=copy.deepcopy(base);bad["materialize_params"]["used_params"]["mapping"]="natural"
   with self.assertRaises(ValueError):lane.validate_metadata(bad,source_paths=[old],raw=raw,bw=120,array_size=256*128,relocation=rel,expected_processing=expected)
   with self.assertRaises(ValueError):lane.validate_metadata(base,source_paths=[r"D:\Other\main.ttbin"],raw=raw,bw=120,array_size=256*128,relocation=rel)
 def test_every_bound_hash_and_duplicate_payload_tampering_rejected(self):
  expected={"main":lane.RAW_SHA,"chunk":lane.CHUNK_SHA,"materializer":lane.MATERIALIZER_SHA,**{f"{s}:{i}":h for s,hs in lane.SIDECAR_SHA.items() for i,h in enumerate(hs)},**{f"provenance:{k}":v for k,v in lane.PROVENANCE_SHA.items()}}
  records={k:{"sha256":v} for k,v in expected.items()}
  lane.validate_expected_hashes(records,expected)
  for key in expected:
   bad=copy.deepcopy(records);bad[key]["sha256"]="0"*64
   with self.assertRaises(ValueError):lane.validate_expected_hashes(bad,expected)
   with self.assertRaises(ValueError):lane.validate_file_hash(bad[key],expected[key])
  rows=[{"payload_identity":"a"},{"payload_identity":"b"}];lane.validate_unique_payloads(rows)
  with self.assertRaises(ValueError):lane.validate_unique_payloads([rows[0],rows[0]])
 def test_real_build_exercises_all_registered_hash_bindings(self):
  seen_hashes=[];seen_sets=[];file_hash=lane.validate_file_hash;set_hash=lane.validate_expected_hashes
  def capture_file(record,expected):
   seen_hashes.append(expected);return file_hash(record,expected)
  def capture_set(records,expected):
   seen_sets.append(frozenset(expected.items()));return set_hash(records,expected)
  with patch.object(lane,"validate_file_hash",side_effect=capture_file),patch.object(lane,"validate_expected_hashes",side_effect=capture_set):
   lock=lane.build_source_lock()
  self.assertEqual(len(lock["selected_frames"]),384)
  self.assertEqual(set(seen_hashes),{lane.RAW_SHA,lane.CHUNK_SHA,lane.MATERIALIZER_SHA})
  observed=set().union(*seen_sets)
  required=set(lane.PROVENANCE_SHA.items())
  for st in lane.STRATA:required.update(zip(("a_eff.npy","b_eff.npy","sidecar_meta.json"),lane.SIDECAR_SHA[st]))
  self.assertTrue(required.issubset(observed))
