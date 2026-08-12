from __future__ import annotations

import json, os, unittest, uuid
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_real_source as source

TMP = Path(os.environ.get("FORMAL_IR_TEST_TMP", "workspace/formal_ir_test_tmp"))
DEV = Path("comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development/pre_run_plan.json")


class TestV4RealSource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base = json.loads(DEV.read_bytes())["locked_data"]["source_manifest"]

 def root(self):
  p = TMP / f"v4_source_{uuid.uuid4().hex}"; p.mkdir(parents=True); return p

 def acquisition(self, root, name="added", *, duplicate_payload=False, tail=False, strata=True):
  main=root/f"{name}_20dB.ttbin"; chunk=root/f"{name}_20dB.1.ttbin"; main.write_bytes((name+" main").encode()); chunk.write_bytes((name+" chunk").encode())
  sidecars={}
  for offset,(dataset,bw) in enumerate((("d1024_bw120",120),("d1024_bw180",180),("d1024_bw200",200))):
   if not strata and dataset=="d1024_bw200": continue
   d=root/f"{name}_{dataset}"; d.mkdir(); value=600 if duplicate_payload else 600+offset*100
   values=(np.arange(256+(1 if tail else 0),dtype=np.uint16)+value)%1024
   np.save(d/"a_eff.npy",values); np.save(d/"b_eff.npy",values)
   meta={"joint_source_mode":"from_ttbin","joint_origin":"from_ttbin","materialize_origin":"materialized_from_ttbin","sequence_source_mode":"strict","sequence_is_sampled":False,"loss":20,"materialize_params":{"used_params":{"dimension":1024,"bin_width_ps":bw,"pairing_mode":"nearest","source_ttbin_paths":[str(main.resolve())]}}}
   (d/"sidecar_meta.json").write_text(json.dumps(meta),encoding="utf-8"); sidecars[dataset]=d
  return {"main_ttbin":main,"chunk_ttbin":chunk,"sidecar_dirs":sidecars}

 def test_exact_intake_no_overwrite_and_readonly_reconstruction(self):
  root=self.root(); spec=self.acquisition(root); out=root/"extension.json"
  doc=source.write_extension(out,self.base,[spec]); before=out.read_bytes()
  self.assertEqual(doc["schema"],"binary_ldpc_v4_real_source_extension_v1")
  again,record,pool=source.selection_pool(out); self.assertEqual(before,out.read_bytes()); self.assertEqual(doc,again)
  self.assertEqual(set(x["dataset_id"] for x in pool),set(source.STRATA)); self.assertEqual(record["sha256"],source._sha(before))
  with self.assertRaises(FileExistsError): source.write_extension(out,self.base,[spec])

 def test_copied_raw_missing_stratum_payload_and_natural_tail(self):
  root=self.root(); copied=self.acquisition(root,"copy")
  # Rewrite the added raw bytes to the base pair: raw-pair collision must fail.
  copied_main=Path(copied["main_ttbin"]); copied_chunk=Path(copied["chunk_ttbin"])
  copied_main.write_bytes(Path(self.base["main_ttbin"]["path"]).read_bytes()); copied_chunk.write_bytes(Path(self.base["chunk_ttbin"]["path"]).read_bytes())
  with self.assertRaises(ValueError): source.build_extension(self.base,[copied])
  with self.assertRaises(ValueError): source.build_extension(self.base,[self.acquisition(root,"missing",strata=False)])
  tailed=source.build_extension(self.base,[self.acquisition(root,"tail",tail=True)])
  self.assertEqual(next(x for x in tailed["added_acquisitions"][0]["datasets"] if x["dataset_id"]=="d1024_bw120")["complete_frames"],1)
  with self.assertRaises(ValueError): source.build_extension(self.base,[self.acquisition(root,"p1",duplicate_payload=True),self.acquisition(root,"p2",duplicate_payload=True)])

 def test_metadata_array_and_file_tampering_rejected(self):
  root=self.root(); spec=self.acquisition(root); out=root/"extension.json"; source.write_extension(out,self.base,[spec])
  sidecar=Path(spec["sidecar_dirs"]["d1024_bw120"]); meta=json.loads((sidecar/"sidecar_meta.json").read_text()); meta["materialize_params"]["used_params"]["pairing_mode"]="wrong"; (sidecar/"sidecar_meta.json").write_text(json.dumps(meta),encoding="utf-8")
  with self.assertRaises(ValueError): source.selection_pool(out)
  root2=self.root(); spec2=self.acquisition(root2); out2=root2/"extension.json"; source.write_extension(out2,self.base,[spec2]); np.save(Path(spec2["sidecar_dirs"]["d1024_bw180"])/"a_eff.npy",np.array([0.5]*256))
  with self.assertRaises(ValueError): source.selection_pool(out2)
  root3=self.root(); spec3=self.acquisition(root3); sidecar3=Path(spec3["sidecar_dirs"]["d1024_bw200"]); meta3=json.loads((sidecar3/"sidecar_meta.json").read_text()); meta3.pop("loss"); meta3["n_symbols"]=255; (sidecar3/"sidecar_meta.json").write_text(json.dumps(meta3),encoding="utf-8")
  with self.assertRaises(ValueError): source.build_extension(self.base,[spec3])
  root4=self.root(); spec4=self.acquisition(root4); sidecar4=Path(spec4["sidecar_dirs"]["d1024_bw200"]); meta4=json.loads((sidecar4/"sidecar_meta.json").read_text()); meta4["padding"]=True; (sidecar4/"sidecar_meta.json").write_text(json.dumps(meta4),encoding="utf-8")
  with self.assertRaises(ValueError): source.build_extension(self.base,[spec4])
